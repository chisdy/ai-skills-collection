from dataclasses import dataclass
from datetime import datetime


@dataclass
class Membership:
    id: int
    org_id: int
    user_id: int
    role: str = "member"
    status: str = "active"
    joined_at: datetime | None = None


@dataclass
class Invitation:
    id: int
    org_id: int
    email: str
    role: str
    status: str = "pending"
    expires_at: datetime | None = None
