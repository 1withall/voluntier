"""update_user_verification_to_scaled_score

Revision ID: a6e983422c84
Revises: 
Create Date: 2025-10-29 17:24:45.552297+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a6e983422c84'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Replace binary verification flags with scaled score system."""
    # Make email nullable (users can verify without email)
    op.alter_column('users', 'email',
                   existing_type=sa.String(255),
                   nullable=True)
    
    # Drop old binary verification columns
    op.drop_column('users', 'verification_status')
    op.drop_column('users', 'document_verified')
    op.drop_column('users', 'community_verified')
    op.drop_column('users', 'in_person_verified')
    
    # Add new scaled verification columns
    op.add_column('users', sa.Column('verification_score', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('users', sa.Column('verification_methods', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('verification_workflow_id', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('trust_network', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('activity_score', sa.Float(), nullable=False, server_default='0.0'))
    
    # Drop old verification_status index
    op.drop_index('ix_users_verification_status', table_name='users')
    
    # Add new verification indexes
    op.create_index('ix_users_verification_score', 'users', ['verification_score'])
    op.create_index('ix_users_workflow_id', 'users', ['verification_workflow_id'])


def downgrade() -> None:
    """Downgrade schema: Restore binary verification flags."""
    # Drop new columns
    op.drop_index('ix_users_verification_score', table_name='users')
    op.drop_index('ix_users_workflow_id', table_name='users')
    op.drop_column('users', 'activity_score')
    op.drop_column('users', 'trust_network')
    op.drop_column('users', 'verification_workflow_id')
    op.drop_column('users', 'verification_methods')
    op.drop_column('users', 'verification_score')
    
    # Restore old columns
    op.add_column('users', sa.Column('in_person_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('community_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('document_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('verification_status', sa.String(50), nullable=False, server_default='pending'))
    op.create_index('ix_users_verification_status', 'users', ['verification_status'])
    
    # Make email non-nullable again
    op.alter_column('users', 'email',
                   existing_type=sa.String(255),
                   nullable=False)
