from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.common import MessageResponse
from app.schemas.user import ChangePasswordRequest, UserPublic, UserUpdate
from app.services.user_service import UserService

router = APIRouter()


@router.get('/me', response_model=UserPublic)
def me(current_user=Depends(get_current_user)):
    return current_user


@router.patch('/me', response_model=UserPublic)
def update_me(payload: UserUpdate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return UserService(db).update_profile(current_user, payload)


@router.patch('/me/password', response_model=MessageResponse)
def change_password(payload: ChangePasswordRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    UserService(db).change_password(current_user, payload)
    return MessageResponse(message='Password changed successfully')
