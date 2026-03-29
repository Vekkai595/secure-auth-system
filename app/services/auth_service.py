import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import InvalidCredentialsError, InvalidRefreshTokenError, UserAlreadyExistsError
from app.core.rate_limit import RateLimitExceeded, check_login_attempt, clear_login_attempts
from app.core.security import hash_password, verify_password
from app.repositories.audit_repository import AuditRepository
from app.repositories.login_attempt_repository import LoginAttemptRepository
from app.repositories.password_reset_repository import PasswordResetRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, ResetPasswordConfirmRequest
from app.schemas.token import TokenPairResponse
from app.services.token_service import TokenService

logger = logging.getLogger('app.auth')


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.refresh_tokens = RefreshTokenRepository(db)
        self.sessions = SessionRepository(db)
        self.password_resets = PasswordResetRepository(db)
        self.audit = AuditRepository(db)
        self.login_attempts = LoginAttemptRepository(db)
        self.token_service = TokenService(self.refresh_tokens, self.sessions, self.password_resets)

    def register(self, payload: RegisterRequest) -> None:
        if self.users.get_by_email(payload.email) or self.users.get_by_username(payload.username):
            raise UserAlreadyExistsError('A user with this email or username already exists')
        self.users.create(
            email=payload.email,
            username=payload.username,
            password_hash=hash_password(payload.password),
        )
        self.db.commit()

    def login(self, payload: LoginRequest, meta: dict[str, str]) -> TokenPairResponse:
        key_ip = f"login:ip:{meta['ip_address']}"
        key_identifier = f"login:id:{payload.identifier.lower()}"
        try:
            check_login_attempt(key_ip)
            check_login_attempt(key_identifier)
        except RateLimitExceeded:
            self.login_attempts.create(identifier=payload.identifier, ip_address=meta['ip_address'], success=False, failure_reason='rate_limited')
            self.audit.create(action='login_rate_limited', ip_address=meta['ip_address'], metadata={'identifier': payload.identifier})
            self.db.commit()
            raise

        user = self.users.get_by_identifier(payload.identifier)
        if user is None or not verify_password(payload.password, user.password_hash):
            self.login_attempts.create(identifier=payload.identifier, ip_address=meta['ip_address'], success=False, failure_reason='invalid_credentials')
            self.audit.create(action='login_failed', ip_address=meta['ip_address'], metadata={'identifier': payload.identifier})
            self.db.commit()
            raise InvalidCredentialsError('Invalid credentials')

        clear_login_attempts(key_ip)
        clear_login_attempts(key_identifier)
        self.login_attempts.create(identifier=payload.identifier, ip_address=meta['ip_address'], success=True)
        self.audit.create(action='login_success', ip_address=meta['ip_address'], user_id=user.id)
        logger.info('login_success', extra={'user_id': user.id, 'action': 'login', 'status': 'ok'})
        tokens = self.token_service.issue_token_pair(
            user_id=user.id,
            ip_address=meta['ip_address'],
            user_agent=meta['user_agent'],
            device_id=meta['device_id'],
        )
        self.db.commit()
        return tokens

    def refresh(self, refresh_token: str, meta: dict[str, str]) -> TokenPairResponse:
        tokens = self.token_service.rotate_refresh_token(
            refresh_token,
            ip_address=meta['ip_address'],
            user_agent=meta['user_agent'],
        )
        self.audit.create(action='token_refreshed', ip_address=meta['ip_address'])
        self.db.commit()
        return tokens

    def logout(self, refresh_token: str, current_user) -> None:
        self.token_service.revoke_refresh_token(refresh_token, expected_user_id=current_user.id)
        self.audit.create(action='logout', ip_address='user-request', user_id=current_user.id)
        self.db.commit()

    def logout_all(self, current_user) -> None:
        self.refresh_tokens.revoke_all_for_user(current_user.id)
        for session in self.sessions.list_for_user(current_user.id):
            if session.revoked_at is None:
                self.sessions.revoke(session)
        self.audit.create(action='logout_all', ip_address='user-request', user_id=current_user.id)
        self.db.commit()

    def request_password_reset(self, email: str) -> str:
        user = self.users.get_by_email(email)
        if user is None:
            return 'If the account exists, password reset instructions would be sent.'
        token = self.token_service.create_password_reset(user_id=user.id)
        self.audit.create(action='password_reset_requested', ip_address='system', user_id=user.id)
        self.db.commit()
        return token

    def confirm_password_reset(self, payload: ResetPasswordConfirmRequest) -> None:
        record, user_id = self.token_service.consume_password_reset(payload.reset_token)
        user = self.users.get_by_id(user_id)
        if user is None:
            raise InvalidRefreshTokenError('Password reset user not found')
        user.password_hash = hash_password(payload.new_password)
        record.used_at = datetime.now(timezone.utc)
        self.refresh_tokens.revoke_all_for_user(user.id)
        for session in self.sessions.list_for_user(user.id):
            if session.revoked_at is None:
                self.sessions.revoke(session)
        self.audit.create(action='password_reset_completed', ip_address='system', user_id=user.id)
        self.db.commit()

    def cleanup_expired(self) -> dict[str, int]:
        removed_refresh = self.refresh_tokens.delete_expired()
        removed_resets = self.password_resets.delete_expired()
        self.db.commit()
        return {'expired_refresh_tokens_removed': removed_refresh, 'expired_password_resets_removed': removed_resets}
