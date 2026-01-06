from alembic import op
import sqlalchemy as sa

revision = "0897940a6520"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column(
        "series",
        sa.Column("external_id", sa.String(length=255), nullable=True)
    )

def downgrade() -> None:
    op.drop_column("series", "external_id")
