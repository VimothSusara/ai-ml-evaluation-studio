"""evaluation profiles and evaluation json

Revision ID: 0003_evaluation
Revises: 0002_ml_catalog
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_evaluation"
down_revision = "0002_ml_catalog"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "evaluation_profiles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("problem_type_id", sa.UUID(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("required_metrics_json", sa.Text(), nullable=False),
        sa.Column("required_plots_json", sa.Text(), nullable=False),
        sa.Column("optional_plots_json", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.ForeignKeyConstraint(["problem_type_id"], ["problem_types.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("problem_type_id", "schema_version", name="uq_eval_profile_pt_version"),
    )
    op.create_index(
        "ix_evaluation_profiles_problem_type_id",
        "evaluation_profiles",
        ["problem_type_id"],
    )

    op.add_column("model_runs", sa.Column("evaluation_json", sa.Text(), nullable=True))
    op.add_column("experiments", sa.Column("evaluation_json", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("experiments", "evaluation_json")
    op.drop_column("model_runs", "evaluation_json")
    op.drop_index("ix_evaluation_profiles_problem_type_id", table_name="evaluation_profiles")
    op.drop_table("evaluation_profiles")