from app.models.organization import Organization

_ORGS: dict[int, Organization] = {}


def get_organization(org_id: int) -> Organization:
    if org_id not in _ORGS:
        _ORGS[org_id] = Organization(id=org_id, name=f"org-{org_id}", owner_id=1)
    return _ORGS[org_id]
