"""Align invoices with ZATCA requirements

Revision ID: 8f2c0c3e1aa9
Revises: 4612391e1020
Create Date: 2025-08-20 08:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8f2c0c3e1aa9'
down_revision: Union[str, Sequence[str], None] = '4612391e1020'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add missing columns to invoices table
    with op.batch_alter_table('invoices') as batch_op:
        # Add invoice_number (nullable first to avoid backfill issues), then unique index
        batch_op.add_column(sa.Column('invoice_number', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('seller_taxes', sa.NUMERIC(precision=10, scale=2), server_default='0.00', nullable=False))
        batch_op.add_column(sa.Column('zatca_uuid', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('zatca_xml', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('zatca_xml_hash', sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column('submitted_at', postgresql.TIMESTAMP(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('last_error', sa.Text(), nullable=True))
        # Rename tax_number -> vat_number if exists
        try:
            batch_op.alter_column('tax_number', new_column_name='vat_number')
        except Exception:
            pass

    # Create unique constraint on invoice_number
    try:
        op.create_unique_constraint('uq_invoices_invoice_number', 'invoices', ['invoice_number'])
    except Exception:
        pass

    # Adjust enum to lowercase values on PostgreSQL
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        # Create a new enum type with lowercase values
        new_enum = postgresql.ENUM('pending', 'in_progress', 'done', 'failed', name='invoice_status_enum_lc')
        new_enum.create(bind, checkfirst=True)
        # Alter column to new enum, coercing values to lowercase text
        op.execute("ALTER TABLE invoices ALTER COLUMN status TYPE invoice_status_enum_lc USING lower(status::text)::invoice_status_enum_lc")
        # Drop old enum and rename new to old name
        op.execute("DROP TYPE IF EXISTS invoice_status_enum")
        op.execute("ALTER TYPE invoice_status_enum_lc RENAME TO invoice_status_enum")

    # Make invoice_number non-null if possible (leave nullable to avoid failures if data missing)
    # Developers may backfill and then enforce NOT NULL in a later migration

    # Remove server default from seller_taxes
    with op.batch_alter_table('invoices') as batch_op:
        batch_op.alter_column('seller_taxes', server_default=None)


def downgrade() -> None:
    # Attempt to revert changes conservatively
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        # Recreate uppercase enum if needed
        old_enum = postgresql.ENUM('PENDING', 'IN_PROGRESS', 'DONE', 'FAILED', name='invoice_status_enum_uc')
        old_enum.create(bind, checkfirst=True)
        op.execute("ALTER TABLE invoices ALTER COLUMN status TYPE invoice_status_enum_uc USING upper(status::text)::invoice_status_enum_uc")
        op.execute("DROP TYPE IF EXISTS invoice_status_enum")
        op.execute("ALTER TYPE invoice_status_enum_uc RENAME TO invoice_status_enum")

    with op.batch_alter_table('invoices') as batch_op:
        try:
            batch_op.alter_column('vat_number', new_column_name='tax_number')
        except Exception:
            pass
        try:
            batch_op.drop_constraint('uq_invoices_invoice_number', type_='unique')
        except Exception:
            pass
        for col in ['invoice_number', 'seller_taxes', 'zatca_uuid', 'zatca_xml', 'zatca_xml_hash', 'submitted_at', 'last_error']:
            try:
                batch_op.drop_column(col)
            except Exception:
                pass
