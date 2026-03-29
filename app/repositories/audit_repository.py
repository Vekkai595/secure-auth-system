import json
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, *, action: str, ip_address: str, user_id: int | None = None, metadata: dict | None = None) -> AuditLog:
        log = AuditLog(
            user_id=user_id,
            action=action,
            ip_address=ip_address,
            metadata_json=json.dumps(metadata or {}),
        )
        self.db.add(log)
        self.db.flush()
        return log

    def list_all(self) -> list[AuditLog]:
        return list(self.db.scalars(select(AuditLog)).all())
