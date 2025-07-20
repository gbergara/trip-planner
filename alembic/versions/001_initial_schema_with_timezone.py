"""Initial schema with timezone support

Revision ID: 001_initial_schema_with_timezone
Revises: 
Create Date: 2025-01-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
import sys
import os

# Add the app directory to path so we can import the models
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.models.booking import TripStatus, BookingType, BookingStatus, TodoCategory

# revision identifiers, used by Alembic.
revision = '001_initial_schema_with_timezone'
down_revision = None
branch_labels = None
depends_on = None


def get_datetime_type():
    """Get timezone-aware datetime type for the current database."""
    bind = op.get_bind()
    if bind.dialect.name in ('postgresql', 'cockroachdb'):
        return TIMESTAMP(timezone=True)
    else:
        return sa.DateTime


def get_uuid_type():
    """Get appropriate UUID type for the current database."""
    bind = op.get_bind()
    if bind.dialect.name in ('postgresql', 'cockroachdb'):
        return UUID(as_uuid=True)
    else:
        return sa.String(36)


def upgrade() -> None:
    """Create all tables with proper timezone support from the beginning."""
    
    datetime_type = get_datetime_type()
    uuid_type = get_uuid_type()
    
    print("🚀 Creating fresh database schema with timezone support...")
    
    # Create users table
    op.create_table('users',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('google_id', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('given_name', sa.String(255), nullable=True),
        sa.Column('family_name', sa.String(255), nullable=True),
        sa.Column('picture', sa.Text, nullable=True),
        sa.Column('preferred_language', sa.String(10), default='en'),
        sa.Column('preferred_currency', sa.String(10), default='USD'),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', datetime_type, nullable=False),
        sa.Column('updated_at', datetime_type, nullable=False),
        sa.Column('last_login', datetime_type, nullable=True),
    )
    
    # Create indexes for users
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_google_id', 'users', ['google_id'], unique=True)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    
    # Create trips table
    op.create_table('trips',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('status', sa.Enum(TripStatus), default=TripStatus.PLANNING),
        sa.Column('user_id', uuid_type, sa.ForeignKey('users.id'), nullable=True),
        sa.Column('guest_session_id', sa.String(255), nullable=True),
        sa.Column('start_date', datetime_type, nullable=False),
        sa.Column('end_date', datetime_type, nullable=True),
        sa.Column('primary_destination', sa.String(200), nullable=True),
        sa.Column('destinations', sa.Text, nullable=True),
        sa.Column('budget', sa.Float, nullable=True),
        sa.Column('currency', sa.String(3), default='USD'),
        sa.Column('traveler_count', sa.Integer, default=1),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', datetime_type, nullable=False),
        sa.Column('updated_at', datetime_type, nullable=False),
    )
    
    # Create indexes for trips
    op.create_index('ix_trips_id', 'trips', ['id'])
    op.create_index('ix_trips_user_id', 'trips', ['user_id'])
    op.create_index('ix_trips_guest_session_id', 'trips', ['guest_session_id'])
    
    # Create bookings table
    op.create_table('bookings',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('trip_id', uuid_type, sa.ForeignKey('trips.id'), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('booking_type', sa.Enum(BookingType), nullable=False),
        sa.Column('status', sa.Enum(BookingStatus), default=BookingStatus.PENDING),
        sa.Column('booking_date', datetime_type, nullable=False),
        sa.Column('start_date', datetime_type, nullable=False),
        sa.Column('end_date', datetime_type, nullable=True),
        sa.Column('departure_location', sa.String(200), nullable=True),
        sa.Column('arrival_location', sa.String(200), nullable=True),
        sa.Column('address', sa.String(500), nullable=True),
        sa.Column('price', sa.Float, nullable=True),
        sa.Column('currency', sa.String(3), default='USD'),
        sa.Column('confirmation_number', sa.String(100), nullable=True),
        sa.Column('provider', sa.String(200), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('contact_email', sa.String(200), nullable=True),
        sa.Column('contact_phone', sa.String(50), nullable=True),
        # Flight specific fields
        sa.Column('flight_number', sa.String(20), nullable=True),
        sa.Column('airline', sa.String(100), nullable=True),
        sa.Column('departure_terminal', sa.String(10), nullable=True),
        sa.Column('arrival_terminal', sa.String(10), nullable=True),
        sa.Column('seat_number', sa.String(10), nullable=True),
        # Accommodation specific fields
        sa.Column('room_type', sa.String(100), nullable=True),
        sa.Column('guests_count', sa.Integer, nullable=True),
        sa.Column('check_in_time', sa.String(10), nullable=True),
        sa.Column('check_out_time', sa.String(10), nullable=True),
        # Car rental specific fields
        sa.Column('car_model', sa.String(100), nullable=True),
        sa.Column('pickup_location', sa.String(200), nullable=True),
        sa.Column('return_location', sa.String(200), nullable=True),
        sa.Column('created_at', datetime_type, nullable=False),
        sa.Column('updated_at', datetime_type, nullable=False),
    )
    
    # Create indexes for bookings
    op.create_index('ix_bookings_id', 'bookings', ['id'])
    op.create_index('ix_bookings_trip_id', 'bookings', ['trip_id'])
    
    # Create todos table
    op.create_table('todos',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('trip_id', uuid_type, sa.ForeignKey('trips.id'), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('category', sa.Enum(TodoCategory), default=TodoCategory.OTHER),
        sa.Column('completed', sa.Boolean, default=False),
        sa.Column('completed_at', datetime_type, nullable=True),
        sa.Column('priority', sa.Integer, default=2),
        sa.Column('due_date', datetime_type, nullable=True),
        sa.Column('created_at', datetime_type, nullable=False),
        sa.Column('updated_at', datetime_type, nullable=False),
    )
    
    # Create indexes for todos
    op.create_index('ix_todos_id', 'todos', ['id'])
    op.create_index('ix_todos_trip_id', 'todos', ['trip_id'])
    
    print("✅ Fresh database schema created successfully with timezone support!")


def downgrade() -> None:
    """Drop all tables."""
    print("🗑️  Dropping all tables...")
    
    op.drop_table('todos')
    op.drop_table('bookings')
    op.drop_table('trips')
    op.drop_table('users')
    
    # Drop enums if they exist (PostgreSQL/CockroachDB)
    bind = op.get_bind()
    if bind.dialect.name in ('postgresql', 'cockroachdb'):
        try:
            # Drop the enum types that were created by SQLAlchemy
            for enum_name in ['tripstatus', 'bookingtype', 'bookingstatus', 'todocategory']:
                op.execute(f'DROP TYPE IF EXISTS {enum_name}')
        except Exception as e:
            print(f"Note: Could not drop enums: {e}")
    
    print("✅ All tables dropped successfully!") 