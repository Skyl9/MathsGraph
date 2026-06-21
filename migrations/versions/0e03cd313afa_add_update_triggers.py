"""add_update_triggers

Revision ID: 0e03cd313afa
Revises: 81f2a16161e5
Create Date: 2026-06-16 20:41:45.495177

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "0e03cd313afa"
down_revision: Union[str, Sequence[str], None] = "81f2a16161e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        CREATE TRIGGER trg_update_concepts_timestamp
        BEFORE UPDATE ON concepts
        FOR EACH ROW
        EXECUTE FUNCTION update_timestamp_modification();
    """
    )
    op.execute(
        """
        CREATE TRIGGER trg_update_comments_timestamp
        BEFORE UPDATE ON comments
        FOR EACH ROW
        EXECUTE FUNCTION trigger_set_updated_at();
    """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TRIGGER IF EXISTS trg_update_concepts_timestamp ON concepts;")
    op.execute("DROP TRIGGER IF EXISTS trg_update_comments_timestamp ON comments;")
