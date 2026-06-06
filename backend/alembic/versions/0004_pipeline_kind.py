"""pipeline kind and model pipeline config

Revision ID: 0004_pipeline_kind
Revises: 0003_evaluation
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_pipeline_kind"
down_revision = "0003_evaluation"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "problem_types",
        sa.Column(
            "pipeline_kind",
            sa.String(50),
            nullable=False,
            server_default="tabular_sklearn",
        ),
    )
    op.add_column(
        "model_definitions",
        sa.Column("pipeline_config_json", sa.Text(), nullable=True),
    )
    op.add_column(
        "experiments",
        sa.Column("pipeline_kind", sa.String(50), nullable=True),
    )
    op.alter_column("problem_types", "pipeline_kind", server_default=None)


def downgrade():
    op.drop_column("experiments", "pipeline_kind")
    op.drop_column("model_definitions", "pipeline_config_json")
    op.drop_column("problem_types", "pipeline_kind")
