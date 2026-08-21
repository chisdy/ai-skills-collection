"""已应用的最后一次迁移：给 organizations 加 plan_tier。

organizations 现有列：id, name, owner_id, max_members, plan_tier, created_at
"""

revision = "0003"
down_revision = "0002"


def upgrade(conn):
    conn.execute("ALTER TABLE organizations ADD COLUMN plan_tier TEXT NOT NULL DEFAULT 'free'")


def downgrade(conn):
    conn.execute("ALTER TABLE organizations DROP COLUMN plan_tier")
