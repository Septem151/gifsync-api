# pylint: disable=invalid-name,missing-function-docstring
"""Initial migration.

Revision ID: dde669ba8d23
Revises:
Create Date: 2021-06-28 15:59:40.013514

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "dde669ba8d23"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(  # pylint: disable=no-member
        "GifSyncUser",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("TIMEZONE('utc', CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    role_table = op.create_table(  # pylint: disable=no-member
        "Role",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.bulk_insert(  # pylint: disable=no-member
        role_table, [{"name": "admin"}, {"name": "spotify"}]
    )
    op.create_table(  # pylint: disable=no-member
        "AssignedRole",
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["Role.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["GifSyncUser.id"],
        ),
        sa.PrimaryKeyConstraint("role_id", "user_id"),
    )
    op.create_table(  # pylint: disable=no-member
        "Gif",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("image", sa.String(length=256), nullable=False),
        sa.Column("thumbnail", sa.String(length=256), nullable=False),
        sa.Column("beats_per_loop", sa.Float(), nullable=False),
        sa.Column("custom_tempo", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("TIMEZONE('utc', CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["GifSyncUser.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", "user_id"),
    )


def downgrade():
    op.drop_table("Gif")  # pylint: disable=no-member
    op.drop_table("AssignedRole")  # pylint: disable=no-member
    op.drop_table("Role")  # pylint: disable=no-member
    op.drop_table("GifSyncUser")  # pylint: disable=no-member
