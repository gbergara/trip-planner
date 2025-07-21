"""
Alembic migration for shared_trips table.
"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg

revision = '003_add_shared_trips'
down_revision = '002_add_allowed_google_accounts'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'shared_trips',
        sa.Column('id', pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('trip_id', pg.UUID(as_uuid=True), sa.ForeignKey('trips.id', ondelete='CASCADE'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('invited_by', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_shared_trips_email', 'shared_trips', ['email'])

def downgrade():
    op.drop_index('ix_shared_trips_email', table_name='shared_trips')
    op.drop_table('shared_trips')
