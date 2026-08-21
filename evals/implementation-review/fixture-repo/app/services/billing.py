from app.repositories import membership as membership_repo

_SEAT_USAGE: dict[int, int] = {}


def sync_seat_usage(org_id: int) -> int:
    """把当前活跃成员数同步到计费侧。成员数变化后必须调用，否则账单会算错。"""
    seats = membership_repo.count_active_members(org_id)
    _SEAT_USAGE[org_id] = seats
    return seats


def current_seat_usage(org_id: int) -> int:
    return _SEAT_USAGE.get(org_id, 0)
