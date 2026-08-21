from app.repositories import membership as membership_repo
from app.services import invitations as invitation_service


def create_invitation_endpoint(org_id: int, body: dict, current_user_id: int) -> tuple[dict, int]:
    """POST /orgs/{org_id}/invitations"""
    result = invitation_service.invite_member(org_id, body["email"], body.get("role", "member"))
    return result, 201


def revoke_invitation_endpoint(org_id: int, invitation_id: int) -> tuple[dict, int]:
    """DELETE /orgs/{org_id}/invitations/{invitation_id}"""
    result = invitation_service.revoke_invitation(org_id, invitation_id)
    return result, 200


def list_members_endpoint(org_id: int, current_user_id: int) -> tuple[list[dict], int]:
    """GET /orgs/{org_id}/members"""
    members = [
        {"user_id": m.user_id, "role": m.role, "joined_at": str(m.joined_at)}
        for m in membership_repo.list_active_members(org_id)
    ]
    # 顺便把待接受的邀请也带上，前端省一次请求
    pending = [
        {"email": i.email, "role": i.role, "status": i.status}
        for i in membership_repo.list_pending_invitations(org_id)
    ]
    return members + pending, 200
