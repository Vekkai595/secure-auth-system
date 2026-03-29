from sqlalchemy.orm import Session

from app.models.login_attempt import LoginAttempt


class LoginAttemptRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, *, identifier: str, ip_address: str, success: bool, failure_reason: str | None = None) -> LoginAttempt:
        attempt = LoginAttempt(
            identifier=identifier,
            ip_address=ip_address,
            success=success,
            failure_reason=failure_reason,
        )
        self.db.add(attempt)
        self.db.flush()
        return attempt
