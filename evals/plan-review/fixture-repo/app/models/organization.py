from dataclasses import dataclass
from datetime import datetime


@dataclass
class Organization:
    """组织。注意字段名是 max_members，不是 seat_limit。"""

    id: int
    name: str
    owner_id: int
    max_members: int = 5
    plan_tier: str = "free"
    created_at: datetime | None = None
