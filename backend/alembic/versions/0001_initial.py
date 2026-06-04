"""initial

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-02
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=True),
        sa.Column("oauth_provider", sa.String(length=50), nullable=True),
        sa.Column("oauth_sub", sa.String(length=255), nullable=True),
        sa.Column(
            "role",
            sa.Enum("superadmin", "user", name="role"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "datasets",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("s3_key", sa.String(length=512), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("profile_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("s3_key"),
    )
    op.create_index(op.f("ix_datasets_owner_id"), "datasets", ["owner_id"], unique=False)

    op.create_table(
        "experiments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column("dataset_id", sa.UUID(), nullable=False),
        sa.Column("target_column", sa.String(length=255), nullable=False),
        sa.Column("problem_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("metrics_json", sa.Text(), nullable=True),
        sa.Column("explanation_text", sa.Text(), nullable=True),
        sa.Column("model_s3_key", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"]),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_experiments_owner_id"), "experiments", ["owner_id"], unique=False)
    op.create_index(op.f("ix_experiments_dataset_id"), "experiments", ["dataset_id"], unique=False)

    op.create_table(
        "jobs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column("job_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("celery_task_id", sa.String(length=255), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=True),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("error_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("celery_task_id"),
    )
    op.create_index(op.f("ix_jobs_owner_id"), "jobs", ["owner_id"], unique=False)
    op.create_index(op.f("ix_jobs_celery_task_id"), "jobs", ["celery_task_id"], unique=False)

def downgrade():
    op.drop_index(op.f("ix_jobs_celery_task_id"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_owner_id"), table_name="jobs")
    op.drop_table("jobs")
    op.drop_index(op.f("ix_experiments_dataset_id"), table_name="experiments")
    op.drop_index(op.f("ix_experiments_owner_id"), table_name="experiments")
    op.drop_table("experiments")
    op.drop_index(op.f("ix_datasets_owner_id"), table_name="datasets")
    op.drop_table("datasets")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    sa.Enum(name="role").drop(op.get_bind(), checkfirst=True)