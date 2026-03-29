from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import secrets

from jose import JWTError, jwt

from app.core.config import settings
from app.core.exceptions import InvalidTokenError


@dataclass
class AccessTokenPayload:
    sub: str
    type: str
    exp: int
    sid: int
    iss: str
    aud: str
    iat: int
    nbf: int


@dataclass
class RefreshTokenPayload:
    sub: str
    type: str
    exp: int
    sid: int
    iss: str
    aud: str
    iat: int
    nbf: int
    jti: str


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _base_claims(subject: str, token_type: str, expires_at: datetime, session_id: int) -> dict:
    now = _utcnow()
    now_ts = int(now.timestamp())
    return {
        'sub': subject,
        'type': token_type,
        'iss': settings.token_issuer,
        'aud': settings.token_audience,
        'iat': now_ts,
        'nbf': now_ts,
        'exp': int(expires_at.timestamp()),
        'sid': session_id,
    }


def create_access_token(user_id: int, session_id: int) -> tuple[str, datetime]:
    expires_at = _utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    payload = _base_claims(str(user_id), 'access', expires_at, session_id)
    return jwt.encode(payload, settings.access_token_secret_key, algorithm=settings.algorithm), expires_at


def create_refresh_token(user_id: int, session_id: int) -> tuple[str, str, datetime]:
    expires_at = _utcnow() + timedelta(days=settings.refresh_token_expire_days)
    jti = secrets.token_urlsafe(24)
    payload = _base_claims(str(user_id), 'refresh', expires_at, session_id)
    payload['jti'] = jti
    return jwt.encode(payload, settings.refresh_token_secret_key, algorithm=settings.algorithm), jti, expires_at


def create_password_reset_token(user_id: int) -> tuple[str, datetime]:
    expires_at = _utcnow() + timedelta(minutes=settings.password_reset_expire_minutes)
    now = _utcnow()
    now_ts = int(now.timestamp())
    payload = {
        'sub': str(user_id),
        'type': 'password_reset',
        'iss': settings.token_issuer,
        'aud': settings.token_audience,
        'iat': now_ts,
        'nbf': now_ts,
        'exp': int(expires_at.timestamp()),
        'nonce': secrets.token_urlsafe(16),
    }
    return jwt.encode(payload, settings.password_reset_secret_key, algorithm=settings.algorithm), expires_at


def _decode(token: str, *, secret_key: str) -> dict:
    try:
        return jwt.decode(
            token,
            secret_key,
            algorithms=[settings.algorithm],
            issuer=settings.token_issuer,
            audience=settings.token_audience,
        )
    except JWTError as exc:
        raise InvalidTokenError('Invalid token') from exc


def decode_access_token(token: str) -> AccessTokenPayload:
    payload = _decode(token, secret_key=settings.access_token_secret_key)
    if payload.get('type') != 'access':
        raise InvalidTokenError('Invalid token type')
    return AccessTokenPayload(**payload)


def decode_refresh_token(token: str) -> RefreshTokenPayload:
    payload = _decode(token, secret_key=settings.refresh_token_secret_key)
    if payload.get('type') != 'refresh':
        raise InvalidTokenError('Invalid token type')
    return RefreshTokenPayload(**payload)


def decode_password_reset_token(token: str) -> dict:
    payload = _decode(token, secret_key=settings.password_reset_secret_key)
    if payload.get('type') != 'password_reset':
        raise InvalidTokenError('Invalid token type')
    return payload
