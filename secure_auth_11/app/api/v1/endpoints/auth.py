from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_request_meta
from app.db.session import get_db
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordConfirmRequest,
)
from app.schemas.common import MessageResponse
from app.schemas.token import TokenPairResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post('/register', response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    AuthService(db).register(payload)
    return MessageResponse(message='User registered successfully')


@router.post('/login', response_model=TokenPairResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    meta = get_request_meta(request)
    return AuthService(db).login(payload, meta)


@router.post('/refresh', response_model=TokenPairResponse)
def refresh(payload: RefreshRequest, request: Request, db: Session = Depends(get_db)):
    meta = get_request_meta(request)
    return AuthService(db).refresh(payload.refresh_token, meta)


@router.post('/logout', response_model=MessageResponse)
def logout(payload: RefreshRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    AuthService(db).logout(payload.refresh_token, current_user)
    return MessageResponse(message='Session logged out successfully')


@router.post('/logout-all', response_model=MessageResponse)
def logout_all(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    AuthService(db).logout_all(current_user)
    return MessageResponse(message='All sessions revoked successfully')


@router.post('/forgot-password', response_model=MessageResponse)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    AuthService(db).request_password_reset(payload.email)
    return MessageResponse(message='If the account exists, password reset instructions would be sent.')


@router.post('/reset-password', response_model=MessageResponse)
def reset_password(payload: ResetPasswordConfirmRequest, db: Session = Depends(get_db)):
    AuthService(db).confirm_password_reset(payload)
    return MessageResponse(message='Password reset successfully')
