from sqlalchemy.orm import Session

from app.core.exceptions import SessionOwnershipError
from app.repositories.session_repository import SessionRepository


class SessionService:
    def __init__(self, db: Session):
        self.db = db
        self.sessions = SessionRepository(db)

    def list_user_sessions(self, user_id: int):
        return self.sessions.list_for_user(user_id)

    def revoke_session(self, user_id: int, session_id: int) -> None:
        session = self.sessions.get_by_id(session_id)
        if session is None or session.user_id != user_id:
            raise SessionOwnershipError('Session not found for current user')
        self.sessions.revoke(session)
        self.db.commit()

    def touch_session(self, session_id: int, *, ip_address: str | None = None, user_agent: str | None = None) -> None:
        session = self.sessions.get_by_id(session_id)
        if session is None or session.revoked_at is not None:
            return
        self.sessions.touch(session, ip_address=ip_address, user_agent=user_agent)
        self.db.commit()
