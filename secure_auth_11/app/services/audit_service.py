from sqlalchemy.orm import Session

from app.repositories.audit_repository import AuditRepository


class AuditService:
    def __init__(self, db: Session):
        self.repo = AuditRepository(db)

    def log(self, *, action: str, ip_address: str, user_id: int | None = None, metadata: dict | None = None):
        return self.repo.create(action=action, ip_address=ip_address, user_id=user_id, metadata=metadata)
