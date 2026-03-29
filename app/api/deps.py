import hashlib

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.tokens import decode_access_token
from app.db.session import get_db
from app.repositories.user_repository import UserRepository
from app.services.session_service import SessionService

bearer_scheme = HTTPBearer(auto_error=False)


def get_request_meta(request: Request) -> dict[str, str]:
    forwarded_for = request.headers.get('x-forwarded-for')
    ip = forwarded_for.split(',')[0].strip() if forwarded_for else (request.client.host if request.client else 'unknown')
    device_id = request.headers.get('x-device-id')
    if not device_id:
        seed = f"{ip}|{request.headers.get('user-agent', 'unknown')}"
        device_id = hashlib.sha256(seed.encode()).hexdigest()[:32]
    return {
        'ip_address': ip,
        'user_agent': request.headers.get('user-agent', 'unknown'),
        'device_id': device_id,
    }


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Missing bearer token')

    payload = decode_access_token(credentials.credentials)
    user = UserRepository(db).get_by_id(int(payload.sub))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid or inactive user')
    meta = get_request_meta(request)
    SessionService(db).touch_session(payload.sid, ip_address=meta['ip_address'], user_agent=meta['user_agent'])
    return user
