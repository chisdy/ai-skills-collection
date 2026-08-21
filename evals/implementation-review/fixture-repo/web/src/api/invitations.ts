export interface InvitationResult {
  status: string;
  invitation_id: number;
  email: string;
}

export async function createInvitation(
  orgId: number,
  body: { email: string; role?: string },
): Promise<InvitationResult> {
  const res = await fetch(`/api/orgs/${orgId}/invitations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return res.json();
}

export async function listMembers(orgId: number) {
  const res = await fetch(`/api/orgs/${orgId}/members`);
  return res.json();
}
