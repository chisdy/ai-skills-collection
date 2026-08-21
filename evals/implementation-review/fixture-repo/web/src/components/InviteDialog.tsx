import { useState } from "react";

import { createInvitation } from "../api/invitations";

export function InviteDialog({ orgId }: { orgId: number }) {
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    setError(null);
    const result = await createInvitation(orgId, { email });
    if (result.status !== "pending") {
      setError("邀请失败");
    }
  }

  return (
    <div className="invite-dialog">
      <input value={email} onChange={(e) => setEmail(e.target.value)} />
      {error ? <p className="error">{error}</p> : null}
      <button onClick={submit}>发送邀请</button>
    </div>
  );
}
