"""add_api_logs_table

Revision ID: 364ea9785782
Revises: 7323d2c13e11
Create Date: 2026-05-15 13:15:59.155870

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "364ea9785782"
down_revision: Union[str, Sequence[str], None] = "7323d2c13e11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
               CREATE TABLE api_logs
               (
                   id          SERIAL PRIMARY KEY,
                   endpoint    VARCHAR(255) NOT NULL,
                   method      VARCHAR(10)  NOT NULL,
                   status_code INTEGER      NOT NULL,
                   duration_ms FLOAT        NOT NULL,
                   created_at  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
               );

               -- Un index pour que les requêtes de l'admin soient ultra-rapides
               CREATE INDEX idx_api_logs_created_at ON api_logs (created_at);
               CREATE INDEX idx_api_logs_endpoint ON api_logs (endpoint);
               """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE IF EXISTS api_logs CASCADE;")
