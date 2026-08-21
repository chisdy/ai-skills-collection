_AUDIT_LOG: list[dict] = []


def record(org_id: int, action: str, target: str, actor_id: int | None = None) -> None:
    _AUDIT_LOG.append(
        {"org_id": org_id, "action": action, "target": target, "actor_id": actor_id}
    )


def recent(org_id: int, limit: int = 50) -> list[dict]:
    return [e for e in _AUDIT_LOG if e["org_id"] == org_id][-limit:]
