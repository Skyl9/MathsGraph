"""fix_sequences

Revision ID: f79dc7489ad5
Revises: 0e03cd313afa
Create Date: 2026-06-16 20:45:13.227514

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f79dc7489ad5"
down_revision: Union[str, Sequence[str], None] = "0e03cd313afa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Sources table sequence fix
    op.execute("CREATE SEQUENCE IF NOT EXISTS sources_id_seq OWNED BY sources.id;")
    op.execute("SELECT setval('sources_id_seq', coalesce(max(id), 0) + 1, false) FROM sources;")
    op.execute("ALTER TABLE sources ALTER COLUMN id SET DEFAULT nextval('sources_id_seq');")

    # 2. Foreign_name table sequence fix
    op.execute("CREATE SEQUENCE IF NOT EXISTS foreign_name_id_seq OWNED BY foreign_name.id;")
    op.execute("SELECT setval('foreign_name_id_seq', coalesce(max(id), 0) + 1, false) FROM foreign_name;")
    op.execute("ALTER TABLE foreign_name ALTER COLUMN id SET DEFAULT nextval('foreign_name_id_seq');")


def downgrade() -> None:
    # Restoring old (incorrect) defaults is not fully necessary, but we can attempt to reverse if absolutely needed.
    op.execute("ALTER TABLE sources ALTER COLUMN id SET DEFAULT nextval('relations_id_seq');")
    op.execute("ALTER TABLE foreign_name ALTER COLUMN id SET DEFAULT nextval('concepts_id_seq');")
