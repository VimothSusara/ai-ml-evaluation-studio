import io
import json
import uuid

import pandas as pd
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.core.config import get_settings
from app.db.models import Dataset, Experiment, Job, ModelDefinition, ModelRun
from app.services.explanation_service import explain_metrics
from app.services.profiling_service import build_profile, read_csv_bytes, sanitize_dataframe
from app.services.recommendation_service import resolve_model_codes
from app.services.storage_service import StorageService
from app.services.training_service import pick_best_run, train_single_model
from app.services.validation_service import infer_problem_type_from_profile, validate_target
from app.services.evaluation_profile_service import get_evaluation_profile
from app.services.explanation_service import explain_evaluation

settings = get_settings()
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, future=True)
storage = StorageService()


@celery_app.task(name="tasks.run_dataset_profile")
def run_dataset_profile(job_id: str, dataset_id: str):
    with Session(engine) as db:
        job = db.get(Job, uuid.UUID(job_id))
        dataset = db.get(Dataset, uuid.UUID(dataset_id))

        if not job:
            raise ValueError(f"Job not found: {job_id}")
        if not dataset:
            raise ValueError(f"Dataset not found: {dataset_id}")

        try:
            job.status = "running"
            db.commit()

            raw = storage.download_bytes(settings.S3_BUCKET_DATASETS, dataset.s3_key)
            df_raw = read_csv_bytes(raw)
            df, dropped = sanitize_dataframe(df_raw)
            profile = build_profile(df, dropped_columns=dropped)
            
            dataset.profile_json = json.dumps(profile)
            dataset.status = "profiled"
            job.status = "completed"
            job.result_json = json.dumps({"dataset_id": dataset_id, "profile_ready": True})
            db.commit()
        except Exception as exc:
            job.status = "failed"
            job.error_text = str(exc)
            if dataset:
                dataset.status = "failed"
            db.commit()
            raise


@celery_app.task(name="tasks.train_experiment")
def train_experiment(
    job_id: str,
    experiment_id: str,
    model_codes: list[str] | None = None,
):
    with Session(engine) as db:
        job = db.get(Job, uuid.UUID(job_id))
        exp = db.get(Experiment, uuid.UUID(experiment_id))

        if not job:
            raise ValueError(f"Job not found: {job_id}")
        if not exp:
            raise ValueError(f"Experiment not found: {experiment_id}")

        dataset = db.get(Dataset, exp.dataset_id)
        if not dataset:
            raise ValueError("Dataset not found for experiment")

        try:
            if dataset.status != "profiled":
                raise ValueError("Dataset profiling is not complete yet")

            profile = json.loads(dataset.profile_json)
            inferred = infer_problem_type_from_profile(profile, exp.target_column)
            problem_type = exp.problem_type_override or inferred

            profile_config = get_evaluation_profile(db, problem_type)

            validation = validate_target(profile, exp.target_column, problem_type, db)
            if not validation["is_valid"]:
                raise ValueError("; ".join(validation["errors"]))

            job.status = "running"
            exp.status = "running"
            exp.problem_type = problem_type
            db.commit()

            storage.ensure_bucket(settings.S3_BUCKET_ARTIFACTS)
            csv_bytes = storage.download_bytes(settings.S3_BUCKET_DATASETS, dataset.s3_key)

            models_to_train = resolve_model_codes(db, problem_type, model_codes)
            run_summaries: list[dict] = []

            for model_code, estimator_key, params_json in models_to_train:
                model_def = db.scalar(
                    select(ModelDefinition).where(ModelDefinition.code == model_code)
                )
                if not model_def:
                    continue

                run = ModelRun(
                    experiment_id=exp.id,
                    model_id=model_def.id,
                    model_code=model_code,
                    status="running",
                )
                db.add(run)
                db.commit()
                db.refresh(run)

                try:
                    metrics, artifact_bytes, evaluation = train_single_model(
                        csv_bytes,
                        exp.target_column,
                        problem_type,
                        estimator_key,
                        params_json,
                        profile_config,
                    )
                    model_key = f"{exp.owner_id}/{exp.id}/{model_code}.joblib"
                    storage.upload_bytes(
                        settings.S3_BUCKET_ARTIFACTS,
                        model_key,
                        artifact_bytes,
                        "application/octet-stream",
                    )
                    run.status = "completed"
                    run.metrics_json = json.dumps(metrics)
                    run.evaluation_json = json.dumps(evaluation)
                    run.model_s3_key = model_key
                    run.train_duration_ms = int(metrics.get("train_duration_ms", 0))
                    run_summaries.append({
                        "model_code": model_code,
                        "status": "completed",
                        "metrics": metrics,
                        "evaluation": evaluation,
                        "model_run_id": str(run.id),
                    })
                except Exception as model_exc:
                    run.status = "failed"
                    run.error_text = str(model_exc)
                    run_summaries.append({
                        "model_code": model_code,
                        "status": "failed",
                        "error": str(model_exc),
                    })

                db.commit()

            best = pick_best_run(run_summaries, problem_type)
            if best:
                best_run = db.get(ModelRun, uuid.UUID(best["model_run_id"]))
                exp.status = "completed"
                exp.metrics_json = json.dumps(best["metrics"])
                exp.evaluation_json = json.dumps(best.get("evaluation", {}))
                exp.explanation_text = explain_evaluation(best.get("evaluation", {}))
                exp.model_s3_key = best_run.model_s3_key if best_run else None
                job.status = "completed"
                job.result_json = json.dumps({
                    "experiment_id": experiment_id,
                    "problem_type": problem_type,
                    "best_model": best["model_code"],
                    "model_runs": run_summaries,
                })
            else:
                exp.status = "failed"
                job.status = "failed"
                job.error_text = "All model training runs failed"
                job.result_json = json.dumps({"model_runs": run_summaries})
            db.commit()
        except Exception as exc:
            exp.status = "failed"
            job.status = "failed"
            job.error_text = str(exc)
            db.commit()
            raise