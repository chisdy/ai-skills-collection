from app.models.membership import Invitation, Membership

_MEMBERSHIPS: list[Membership] = []
_INVITATIONS: list[Invitation] = []


def count_active_members(org_id: int) -> int:
    return len([m for m in _MEMBERSHIPS if m.org_id == org_id and m.status == "active"])


def count_pending_invitations(org_id: int) -> int:
    return len([i for i in _INVITATIONS if i.org_id == org_id and i.status == "pending"])


def create_invitation(org_id: int, email: str, role: str) -> Invitation:
    invitation = Invitation(id=len(_INVITATIONS) + 1, org_id=org_id, email=email, role=role)
    _INVITATIONS.append(invitation)
    return invitation


def accept_invitation(invitation_id: int, user_id: int) -> Membership:
    invitation = next(i for i in _INVITATIONS if i.id == invitation_id)
    invitation.status = "accepted"
    membership = Membership(
        id=len(_MEMBERSHIPS) + 1,
        org_id=invitation.org_id,
        user_id=user_id,
    )
    _MEMBERSHIPS.append(membership)
    return membership
