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


def accept_invitation_endpoint(org_id: int, invitation_id: int, current_user_id: int) -> tuple[dict, int]:
    """POST /orgs/{org_id}/invitations/{invitation_id}/accept"""
    membership = membership_repo.accept_invitation(invitation_id, current_user_id)
    return {"status": "active", "membership_id": membership.id}, 200
