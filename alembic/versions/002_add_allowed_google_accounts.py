"""
Alembic migration for allowed_google_accounts table.
"""
from alembic import op
import sqlalchemy as sa
import uuid

revision = '002_add_allowed_google_accounts'
down_revision = '001_initial_schema_with_timezone'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'allowed_google_accounts',
        sa.Column('id', sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column('email', sa.String(255), unique=True, nullable=True, index=True),
        sa.Column('domain', sa.String(255), nullable=True, index=True),
        sa.Column('active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

def downgrade():
    op.drop_table('allowed_google_accounts')
