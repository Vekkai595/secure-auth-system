from sqlalchemy.orm import Session

from app.core.exceptions import InvalidCredentialsError, UserAlreadyExistsError
from app.core.security import hash_password, verify_password
from app.repositories.audit_repository import AuditRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import ChangePasswordRequest, UserUpdate


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.audit = AuditRepository(db)

    def update_profile(self, current_user, payload: UserUpdate):
        if payload.username and payload.username != current_user.username:
            existing = self.users.get_by_username(payload.username)
            if existing and existing.id != current_user.id:
                raise UserAlreadyExistsError('Username already in use')
            current_user.username = payload.username
        self.db.add(current_user)
        self.db.commit()
        self.db.refresh(current_user)
        return current_user

    def change_password(self, current_user, payload: ChangePasswordRequest) -> None:
        if not verify_password(payload.current_password, current_user.password_hash):
            raise InvalidCredentialsError('Current password is incorrect')
        current_user.password_hash = hash_password(payload.new_password)
        self.db.add(current_user)
        self.audit.create(action='password_changed', ip_address='user-request', user_id=current_user.id)
        self.db.commit()
