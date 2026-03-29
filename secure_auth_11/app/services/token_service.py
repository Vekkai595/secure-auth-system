import hashlib
import secrets
from datetime import datetime, timezone

from app.core.exceptions import InvalidRefreshTokenError
from app.core.tokens import (
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    decode_password_reset_token,
    decode_refresh_token,
)
from app.repositories.password_reset_repository import PasswordResetRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.session_repository import SessionRepository
from app.schemas.token import TokenPairResponse


class TokenService:
    def __init__(self, refresh_tokens: RefreshTokenRepository, sessions: SessionRepository, password_resets: PasswordResetRepository | None = None):
        self.refresh_tokens = refresh_tokens
        self.sessions = sessions
        self.password_resets = password_resets

    def issue_token_pair(self, *, user_id: int, ip_address: str, user_agent: str, device_id: str, token_family: str | None = None) -> TokenPairResponse:
        token_family = token_family or secrets.token_urlsafe(18)
        provisional_jti = secrets.token_urlsafe(24)
        session = self.sessions.get_active_by_user_and_device(user_id, device_id)
        if session is None:
            session = self.sessions.create(
                user_id=user_id,
                device_id=device_id,
                current_refresh_jti=provisional_jti,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        else:
            self.sessions.update_refresh_jti(session, provisional_jti, ip_address=ip_address, user_agent=user_agent)

        access_token, access_expires_at = create_access_token(user_id, session.id)
        refresh_token, refresh_jti, refresh_expires_at = create_refresh_token(user_id, session.id)
        self.sessions.update_refresh_jti(session, refresh_jti, ip_address=ip_address, user_agent=user_agent)
        self.refresh_tokens.create(
            user_id=user_id,
            session_id=session.id,
            jti=refresh_jti,
            token_family=token_family,
            expires_at=refresh_expires_at,
        )
        return TokenPairResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            access_expires_at=access_expires_at,
            refresh_expires_at=refresh_expires_at,
        )

    def rotate_refresh_token(self, refresh_token: str, *, ip_address: str, user_agent: str) -> TokenPairResponse:
        payload = decode_refresh_token(refresh_token)
        record = self.refresh_tokens.get_by_jti(payload.jti)
        expires_at = record.expires_at.replace(tzinfo=timezone.utc) if record and record.expires_at.tzinfo is None else (record.expires_at if record else None)
        if record is None or record.revoked_at is not None or expires_at <= datetime.now(timezone.utc):
            raise InvalidRefreshTokenError('Refresh token is invalid, revoked, or expired')

        session = self.sessions.get_by_id(record.session_id)
        if session is None or session.revoked_at is not None:
            raise InvalidRefreshTokenError('Session is invalid or revoked')

        access_token, access_expires_at = create_access_token(int(payload.sub), session.id)
        new_refresh_token, new_jti, refresh_expires_at = create_refresh_token(int(payload.sub), session.id)
        self.refresh_tokens.revoke(record, replaced_by_jti=new_jti)
        self.refresh_tokens.create(
            user_id=record.user_id,
            session_id=session.id,
            jti=new_jti,
            token_family=record.token_family,
            expires_at=refresh_expires_at,
        )
        self.sessions.update_refresh_jti(session, new_jti, ip_address=ip_address, user_agent=user_agent)
        return TokenPairResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            access_expires_at=access_expires_at,
            refresh_expires_at=refresh_expires_at,
        )

    def revoke_refresh_token(self, refresh_token: str, *, expected_user_id: int | None = None) -> None:
        payload = decode_refresh_token(refresh_token)
        record = self.refresh_tokens.get_by_jti(payload.jti)
        if record is None:
            return
        if expected_user_id is not None and record.user_id != expected_user_id:
            raise InvalidRefreshTokenError('Refresh token does not belong to current user')
        self.refresh_tokens.revoke(record)
        session = self.sessions.get_by_id(record.session_id)
        if session:
            self.sessions.revoke(session)

    def create_password_reset(self, *, user_id: int) -> str:
        if self.password_resets is None:
            raise RuntimeError('Password reset repository not configured')
        token, expires_at = create_password_reset_token(user_id)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        self.password_resets.create(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        return token

    def consume_password_reset(self, token: str):
        if self.password_resets is None:
            raise RuntimeError('Password reset repository not configured')
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        record = self.password_resets.get_by_hash(token_hash)
        payload = decode_password_reset_token(token)
        expires_at = record.expires_at.replace(tzinfo=timezone.utc) if record and record.expires_at.tzinfo is None else (record.expires_at if record else None)
        if record is None or record.used_at is not None or expires_at <= datetime.now(timezone.utc):
            raise InvalidRefreshTokenError('Password reset token is invalid or expired')
        return record, int(payload['sub'])
