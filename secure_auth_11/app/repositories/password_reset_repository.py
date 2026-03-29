from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.password_reset import PasswordResetToken


class PasswordResetRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **kwargs) -> PasswordResetToken:
        item = PasswordResetToken(**kwargs)
        self.db.add(item)
        self.db.flush()
        return item

    def get_by_hash(self, token_hash: str) -> PasswordResetToken | None:
        return self.db.scalar(select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash))

    def delete_expired(self) -> int:
        items = self.db.scalars(select(PasswordResetToken).where(PasswordResetToken.expires_at <= datetime.now(timezone.utc))).all()
        count = len(items)
        for item in items:
            self.db.delete(item)
        return count
