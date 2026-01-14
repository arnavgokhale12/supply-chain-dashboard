"""add market and indicator tables

Revision ID: a1b2c3d4e5f6
Revises: f8a76eccf23c
Create Date: 2026-01-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f8a76eccf23c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # IndicatorConfig table
    op.create_table('indicator_configs',
        sa.Column('series_id', sa.String(length=50), nullable=False),
        sa.Column('include_in_composite', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('weight', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('invert_sign', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['series_id'], ['series.id']),
        sa.PrimaryKeyConstraint('series_id')
    )

    # MarketSeries table
    op.create_table('market_series',
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('series_type', sa.String(length=50), nullable=False),
        sa.Column('theme', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('symbol')
    )

    # MarketPrice table
    op.create_table('market_prices',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('close', sa.Float(), nullable=False),
        sa.Column('adjusted_close', sa.Float(), nullable=False),
        sa.Column('volume', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['symbol'], ['market_series.symbol']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol', 'date', name='uq_market_prices_symbol_date')
    )
    op.create_index(op.f('ix_market_prices_symbol'), 'market_prices', ['symbol'], unique=False)
    op.create_index(op.f('ix_market_prices_date'), 'market_prices', ['date'], unique=False)

    # RegimeReturn table
    op.create_table('regime_returns',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('regime', sa.String(length=20), nullable=False),
        sa.Column('avg_monthly_return', sa.Float(), nullable=False),
        sa.Column('std_monthly_return', sa.Float(), nullable=True),
        sa.Column('sample_count', sa.Integer(), nullable=False),
        sa.Column('computed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['symbol'], ['market_series.symbol']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_regime_returns_symbol'), 'regime_returns', ['symbol'], unique=False)
    op.create_index(op.f('ix_regime_returns_regime'), 'regime_returns', ['regime'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_regime_returns_regime'), table_name='regime_returns')
    op.drop_index(op.f('ix_regime_returns_symbol'), table_name='regime_returns')
    op.drop_table('regime_returns')
    op.drop_index(op.f('ix_market_prices_date'), table_name='market_prices')
    op.drop_index(op.f('ix_market_prices_symbol'), table_name='market_prices')
    op.drop_table('market_prices')
    op.drop_table('market_series')
    op.drop_table('indicator_configs')
