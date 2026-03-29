from datetime import datetime

from pydantic import BaseModel


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'
    access_expires_at: datetime
    refresh_expires_at: datetime
