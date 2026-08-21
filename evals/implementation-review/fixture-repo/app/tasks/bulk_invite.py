import csv

from app.services.invitations import invite_member


def import_invites_from_csv(org_id: int, csv_path: str) -> list[int]:
    """批量导入邀请。这是 invite_member 的第二个调用方，容易被漏掉。"""
    created = []
    with open(csv_path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            result = invite_member(org_id, row["email"], row.get("role", "member"))
            created.append(result["invitation_id"])
    return created
