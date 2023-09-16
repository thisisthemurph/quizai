from datetime import datetime
from pydantic import BaseModel


class SessionModel(BaseModel):
    id: str
    user_id: str
    login_time: datetime
    expiration_time: datetime
    ip_address: str
    user_agent: str
    valid: bool

    def __str__(self):
        return self.email

    def __repr__(self):
        return f"Session(id={self.id}, user_id={self.user_id})"
