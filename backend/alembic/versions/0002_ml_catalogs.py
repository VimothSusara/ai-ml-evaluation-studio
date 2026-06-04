"""ml catalog and model runs

Revision ID: 0002_ml_catalog
Revises: 0001_initial
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_ml_catalog"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "problem_types",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_problem_types_code", "problem_types", ["code"], unique=True)

    op.create_table(
        "model_definitions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("estimator_key", sa.String(80), nullable=False),
        sa.Column("default_params_json", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_model_definitions_code", "model_definitions", ["code"], unique=True)

    op.create_table(
        "problem_type_models",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("problem_type_id", sa.UUID(), nullable=False),
        sa.Column("model_id", sa.UUID(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["problem_type_id"], ["problem_types.id"]),
        sa.ForeignKeyConstraint(["model_id"], ["model_definitions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("problem_type_id", "model_id", name="uq_problem_model"),
    )

    op.create_table(
        "model_requirements",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("problem_type_id", sa.UUID(), nullable=False),
        sa.Column("min_rows", sa.Integer(), nullable=False),
        sa.Column("min_features", sa.Integer(), nullable=False),
        sa.Column("min_classes", sa.Integer(), nullable=True),
        sa.Column("max_classes", sa.Integer(), nullable=True),
        sa.Column("target_must_be_numeric", sa.Boolean(), nullable=False),
        sa.Column("max_missing_target_ratio", sa.Float(), nullable=False),
        sa.Column("rules_json", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["problem_type_id"], ["problem_types.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("problem_type_id"),
    )

    op.add_column("datasets", sa.Column("validation_json", sa.Text(), nullable=True))
    op.add_column("experiments", sa.Column("problem_type_override", sa.String(50), nullable=True))

    op.create_table(
        "model_runs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("experiment_id", sa.UUID(), nullable=False),
        sa.Column("model_id", sa.UUID(), nullable=False),
        sa.Column("model_code", sa.String(80), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("metrics_json", sa.Text(), nullable=True),
        sa.Column("model_s3_key", sa.String(512), nullable=True),
        sa.Column("error_text", sa.Text(), nullable=True),
        sa.Column("train_duration_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["experiment_id"], ["experiments.id"]),
        sa.ForeignKeyConstraint(["model_id"], ["model_definitions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_model_runs_experiment_id", "model_runs", ["experiment_id"])


def downgrade():
    op.drop_index("ix_model_runs_experiment_id", table_name="model_runs")
    op.drop_table("model_runs")
    op.drop_column("experiments", "problem_type_override")
    op.drop_column("datasets", "validation_json")
    op.drop_table("model_requirements")
    op.drop_table("problem_type_models")
    op.drop_index("ix_model_definitions_code", table_name="model_definitions")
    op.drop_table("model_definitions")
    op.drop_index("ix_problem_types_code", table_name="problem_types")
    op.drop_table("problem_types")