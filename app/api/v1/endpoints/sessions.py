from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.common import MessageResponse
from app.schemas.session import SessionListResponse
from app.services.session_service import SessionService

router = APIRouter()


@router.get('', response_model=SessionListResponse)
def list_sessions(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    sessions = SessionService(db).list_user_sessions(current_user.id)
    return SessionListResponse(items=sessions)


@router.delete('/{session_id}', response_model=MessageResponse)
def revoke_session(session_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    SessionService(db).revoke_session(current_user.id, session_id)
    return MessageResponse(message='Session revoked successfully')
