"""add document chunk full text index

Revision ID: 266abeb5c52c
Revises: c1f76979a4f1
Create Date: 2026-10-07 14:40:52.687868

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '266abeb5c52c'
down_revision: Union[str, Sequence[str], None] = 'c1f76979a4f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(

        """

        CREATE INDEX ix_document_chunks_content_fts

        ON document_chunks

        USING gin (to_tsvector('simple', content))

        """

    )


def downgrade() -> None:
    op.execute(

        """

        DROP INDEX IF EXISTS ix_document_chunks_content_fts

        """

    )
