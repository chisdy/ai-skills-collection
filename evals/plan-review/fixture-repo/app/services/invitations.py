from app.repositories import membership as membership_repo
from app.services import audit
from app.tasks import notifications


def invite_member(org_id: int, email: str, role: str = "member") -> dict:
    """邀请成员。

    返回的是 dict，不是 bool —— 调用方依赖 invitation_id 字段。
    目前没有任何席位数量校验。
    """
    invitation = membership_repo.create_invitation(org_id, email, role)
    notifications.notify_org_owner(org_id, event="member_invited", email=email)
    audit.record(org_id=org_id, action="invitation.created", target=email)
    return {"status": "pending", "invitation_id": invitation.id, "email": email}


def revoke_invitation(org_id: int, invitation_id: int) -> dict:
    audit.record(org_id=org_id, action="invitation.revoked", target=str(invitation_id))
    return {"status": "revoked", "invitation_id": invitation_id}
