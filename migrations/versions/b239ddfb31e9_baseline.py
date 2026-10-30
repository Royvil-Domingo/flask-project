"""baseline

Revision ID: b239ddfb31e9
Revises: 
Create Date: 2026-10-30 09:15:03.454551

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b239ddfb31e9'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('borrowers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.create_unique_constraint('uq_borrowers_user_id', ['user_id'])
        batch_op.create_foreign_key('fk_borrowers_user_id_users', 'users', ['user_id'], ['id'])

    with op.batch_alter_table('borrowings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('requested_on', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('rejection_reason', sa.String(length=255), nullable=True))
        batch_op.alter_column('borrowed_on', existing_type=sa.DATE(), nullable=True)

    # Backfill requested_on for the 2 existing rows before locking it to NOT NULL.
    op.execute("UPDATE borrowings SET requested_on = borrowed_on WHERE requested_on IS NULL")

    with op.batch_alter_table('borrowings', schema=None) as batch_op:
        batch_op.alter_column('requested_on', existing_type=sa.Date(), nullable=False)


def downgrade():
    with op.batch_alter_table('borrowings', schema=None) as batch_op:
        batch_op.alter_column('borrowed_on', existing_type=sa.DATE(), nullable=False)
        batch_op.drop_column('rejection_reason')
        batch_op.drop_column('requested_on')

    with op.batch_alter_table('borrowers', schema=None) as batch_op:
        batch_op.drop_constraint('fk_borrowers_user_id_users', type_='foreignkey')
        batch_op.drop_constraint('uq_borrowers_user_id', type_='unique')
        batch_op.drop_column('user_id')