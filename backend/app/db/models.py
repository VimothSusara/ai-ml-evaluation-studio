import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Text,
    Enum,
    Boolean,
    Integer,
    Float,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.core.roles import Role


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    oauth_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    oauth_sub: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[Role] = mapped_column(
        Enum(Role, name="role", values_callable=lambda x: [e.value for e in x]),
        default=Role.USER,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class ProblemType(Base):
    __tablename__ = "problem_types"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    models: Mapped[list["ProblemTypeModel"]] = relationship(back_populates="problem_type")
    requirements: Mapped["ModelRequirement | None"] = relationship(back_populates="problem_type")


class ModelDefinition(Base):
    __tablename__ = "model_definitions"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(120))
    estimator_key: Mapped[str] = mapped_column(String(80))
    default_params_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    problem_links: Mapped[list["ProblemTypeModel"]] = relationship(back_populates="model")


class ProblemTypeModel(Base):
    __tablename__ = "problem_type_models"
    __table_args__ = (UniqueConstraint("problem_type_id", "model_id", name="uq_problem_model"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    problem_type_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("problem_types.id"), index=True)
    model_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("model_definitions.id"), index=True)
    priority: Mapped[int] = mapped_column(Integer, default=1)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    problem_type: Mapped["ProblemType"] = relationship(back_populates="models")
    model: Mapped["ModelDefinition"] = relationship(back_populates="problem_links")


class ModelRequirement(Base):
    __tablename__ = "model_requirements"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    problem_type_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("problem_types.id"), unique=True)
    min_rows: Mapped[int] = mapped_column(Integer, default=10)
    min_features: Mapped[int] = mapped_column(Integer, default=1)
    min_classes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_classes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_must_be_numeric: Mapped[bool] = mapped_column(Boolean, default=False)
    max_missing_target_ratio: Mapped[float] = mapped_column(Float, default=0.0)
    rules_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    problem_type: Mapped["ProblemType"] = relationship(back_populates="requirements")


class EvaluationProfile(Base):
    __tablename__ = "evaluation_profiles"
    __table_args__ = (
        UniqueConstraint("problem_type_id", "schema_version", name="uq_eval_profile_pt_version"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    problem_type_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("problem_types.id"), index=True)
    schema_version: Mapped[int] = mapped_column(Integer, default=1)
    required_metrics_json: Mapped[str] = mapped_column(Text)
    required_plots_json: Mapped[str] = mapped_column(Text)
    optional_plots_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    problem_type: Mapped["ProblemType"] = relationship()


class Dataset(Base):
    __tablename__ = "datasets"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    s3_key: Mapped[str] = mapped_column(String(512), unique=True)
    status: Mapped[str] = mapped_column(String(50), default="uploaded")
    profile_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    validation_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Experiment(Base):
    __tablename__ = "experiments"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    dataset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("datasets.id"), index=True)
    target_column: Mapped[str] = mapped_column(String(255))
    problem_type: Mapped[str] = mapped_column(String(50), default="unknown")
    problem_type_override: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="queued")
    metrics_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_s3_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    evaluation_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    dataset = relationship("Dataset")
    model_runs: Mapped[list["ModelRun"]] = relationship(
        back_populates="experiment",
        foreign_keys="ModelRun.experiment_id",
    )


class ModelRun(Base):
    __tablename__ = "model_runs"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    experiment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("experiments.id"), index=True)
    model_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("model_definitions.id"), index=True)
    model_code: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(50), default="queued")
    metrics_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_s3_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    error_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    train_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    evaluation_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    experiment: Mapped["Experiment"] = relationship(
        back_populates="model_runs",
        foreign_keys=[experiment_id],
    )
    model_definition: Mapped["ModelDefinition"] = relationship()


class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    job_type: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), default="queued")
    celery_task_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)