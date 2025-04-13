from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class InvitationBase(BaseModel):
    code: str
    email: Optional[EmailStr] = None


class InvitationCreate(InvitationBase):
    pass


class Invitation(InvitationBase):
    id: int
    is_used: bool
    created_at: datetime
    used_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
