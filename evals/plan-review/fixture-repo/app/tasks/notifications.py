_OUTBOX: list[dict] = []


def notify_org_owner(org_id: int, event: str, **payload) -> None:
    _OUTBOX.append({"org_id": org_id, "event": event, "payload": payload})


def notify_user(user_id: int, event: str, **payload) -> None:
    _OUTBOX.append({"user_id": user_id, "event": event, "payload": payload})
