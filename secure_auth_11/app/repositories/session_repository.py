from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.session import UserSession


class SessionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **kwargs) -> UserSession:
        session = UserSession(**kwargs)
        self.db.add(session)
        self.db.flush()
        return session

    def list_for_user(self, user_id: int) -> list[UserSession]:
        stmt = select(UserSession).where(UserSession.user_id == user_id).order_by(UserSession.created_at.desc())
        return list(self.db.scalars(stmt).all())

    def get_by_refresh_jti(self, refresh_jti: str) -> UserSession | None:
        return self.db.scalar(select(UserSession).where(UserSession.current_refresh_jti == refresh_jti))

    def get_by_id(self, session_id: int) -> UserSession | None:
        return self.db.scalar(select(UserSession).where(UserSession.id == session_id))

    def get_active_by_user_and_device(self, user_id: int, device_id: str) -> UserSession | None:
        stmt = select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.device_id == device_id,
            UserSession.revoked_at.is_(None),
        )
        return self.db.scalar(stmt)

    def touch(self, session: UserSession, *, ip_address: str | None = None, user_agent: str | None = None) -> None:
        session.last_seen_at = datetime.now(timezone.utc)
        if ip_address is not None:
            session.ip_address = ip_address
        if user_agent is not None:
            session.user_agent = user_agent
        self.db.add(session)

    def update_refresh_jti(self, session: UserSession, refresh_jti: str, *, ip_address: str, user_agent: str) -> None:
        session.current_refresh_jti = refresh_jti
        self.touch(session, ip_address=ip_address, user_agent=user_agent)

    def revoke(self, session: UserSession) -> None:
        session.revoked_at = datetime.now(timezone.utc)
        self.db.add(session)
