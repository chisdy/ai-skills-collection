from app.repositories import membership as membership_repo
from app.services.invitations import invite_member


def test_invite_member_returns_pending_invitation():
    result = invite_member(org_id=1, email="a@example.com")
    assert result["status"] == "pending"
    assert "invitation_id" in result


def test_invite_member_accepts_role():
    result = invite_member(org_id=1, email="b@example.com", role="admin")
    assert result["status"] == "pending"


def test_duplicate_invitation_returns_failed_with_reason():
    invite_member(org_id=2, email="dup@example.com")
    before = membership_repo.count_pending_invitations(2)
    result = invite_member(org_id=2, email="dup@example.com")
    assert result["status"] == "failed"
    assert result["reason"] == "duplicate_invitation"
    assert membership_repo.count_pending_invitations(2) == before


def test_has_pending_invitation():
    invite_member(org_id=3, email="p@example.com")
    assert membership_repo.has_pending_invitation(3, "p@example.com")
    assert not membership_repo.has_pending_invitation(3, "absent@example.com")
