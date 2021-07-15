# pylint: disable=invalid-name,missing-function-docstring
"""Remove thumbnail column

Revision ID: d909b9718869
Revises: dde669ba8d23
Create Date: 2021-07-07 18:47:20.844991

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d909b9718869"
down_revision = "dde669ba8d23"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("Gif", "thumbnail")  # pylint: disable=no-member


def downgrade():
    op.add_column(  # pylint: disable=no-member
        "Gif",
        sa.Column(
            "thumbnail", sa.VARCHAR(length=256), autoincrement=False, nullable=False
        ),
    )
