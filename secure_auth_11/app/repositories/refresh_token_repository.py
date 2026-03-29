from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **kwargs) -> RefreshToken:
        token = RefreshToken(**kwargs)
        self.db.add(token)
        self.db.flush()
        return token

    def get_by_jti(self, jti: str) -> RefreshToken | None:
        return self.db.scalar(select(RefreshToken).where(RefreshToken.jti == jti))

    def revoke(self, token: RefreshToken, *, replaced_by_jti: str | None = None) -> None:
        token.revoked_at = datetime.now(timezone.utc)
        token.replaced_by_jti = replaced_by_jti
        self.db.add(token)

    def revoke_all_for_user(self, user_id: int) -> None:
        tokens = self.db.scalars(select(RefreshToken).where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))).all()
        now = datetime.now(timezone.utc)
        for token in tokens:
            token.revoked_at = now
            self.db.add(token)

    def delete_expired(self) -> int:
        tokens = self.db.scalars(select(RefreshToken).where(RefreshToken.expires_at <= datetime.now(timezone.utc))).all()
        count = len(tokens)
        for token in tokens:
            self.db.delete(token)
        return count
