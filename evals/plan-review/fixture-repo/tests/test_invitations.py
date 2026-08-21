from app.services.invitations import invite_member


def test_invite_member_returns_pending_invitation():
    result = invite_member(org_id=1, email="a@example.com")
    assert result["status"] == "pending"
    assert "invitation_id" in result


def test_invite_member_accepts_role():
    result = invite_member(org_id=1, email="b@example.com", role="admin")
    assert result["status"] == "pending"
