"""add shipment_id to notifications"""

revision = 'c9d2e8f1a3b4'
down_revision = 'b7c1d9e84a52'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.add_column('notifications', sa.Column('shipment_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(None, 'notifications', 'shipments', ['shipment_id'], ['id'], ondelete='CASCADE')

def downgrade():
    op.drop_constraint(None, 'notifications', type_='foreignkey')
    op.drop_column('notifications', 'shipment_id')