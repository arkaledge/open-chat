"""Add message threading support

Revision ID: 002_message_threading
Revises: 001_initial_schema
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '002_message_threading'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add threading columns to messages table
    op.add_column('messages', sa.Column('parent_message_id', UUID(as_uuid=True), nullable=True))
    op.add_column('messages', sa.Column('thread_id', UUID(as_uuid=True), nullable=True))
    op.add_column('messages', sa.Column('is_thread_root', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('messages', sa.Column('branch_depth', sa.Integer(), nullable=False, server_default='0'))

    # Create foreign key constraint for parent message
    op.create_foreign_key(
        'fk_messages_parent_message',
        'messages', 'messages',
        ['parent_message_id'], ['id'],
        ondelete='SET NULL'
    )

    # Create index for thread queries
    op.create_index('ix_messages_thread_id', 'messages', ['thread_id'])
    op.create_index('ix_messages_parent_message_id', 'messages', ['parent_message_id'])

    # Add conversation metadata for branching
    op.add_column('conversations', sa.Column('parent_conversation_id', UUID(as_uuid=True), nullable=True))
    op.add_column('conversations', sa.Column('branched_at_message_id', UUID(as_uuid=True), nullable=True))
    op.add_column('conversations', sa.Column('branch_count', sa.Integer(), nullable=False, server_default='0'))

    # Create foreign key for parent conversation
    op.create_foreign_key(
        'fk_conversations_parent',
        'conversations', 'conversations',
        ['parent_conversation_id'], ['id'],
        ondelete='SET NULL'
    )

    # Create foreign key for branched message
    op.create_foreign_key(
        'fk_conversations_branched_message',
        'conversations', 'messages',
        ['branched_at_message_id'], ['id'],
        ondelete='SET NULL'
    )

    # Create index for branch queries
    op.create_index('ix_conversations_parent_conversation_id', 'conversations', ['parent_conversation_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_conversations_parent_conversation_id', table_name='conversations')
    op.drop_index('ix_messages_parent_message_id', table_name='messages')
    op.drop_index('ix_messages_thread_id', table_name='messages')

    # Drop foreign keys
    op.drop_constraint('fk_conversations_branched_message', 'conversations', type_='foreignkey')
    op.drop_constraint('fk_conversations_parent', 'conversations', type_='foreignkey')
    op.drop_constraint('fk_messages_parent_message', 'messages', type_='foreignkey')

    # Drop columns from conversations
    op.drop_column('conversations', 'branch_count')
    op.drop_column('conversations', 'branched_at_message_id')
    op.drop_column('conversations', 'parent_conversation_id')

    # Drop columns from messages
    op.drop_column('messages', 'branch_depth')
    op.drop_column('messages', 'is_thread_root')
    op.drop_column('messages', 'thread_id')
    op.drop_column('messages', 'parent_message_id')
