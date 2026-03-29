from datetime import datetime

from pydantic import BaseModel


class SessionPublic(BaseModel):
    id: int
    device_id: str
    ip_address: str
    user_agent: str
    created_at: datetime
    last_seen_at: datetime
    revoked_at: datetime | None

    model_config = {'from_attributes': True}


class SessionListResponse(BaseModel):
    items: list[SessionPublic]
