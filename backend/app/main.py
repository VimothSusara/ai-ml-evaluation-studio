from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.v1 import admin, auth, datasets, experiments, jobs, catalog, model_runs
from app.core.config import get_settings
from app.services.storage_service import StorageService

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    storage = StorageService()
    storage.ensure_bucket(settings.S3_BUCKET_DATASETS)
    storage.ensure_bucket(settings.S3_BUCKET_ARTIFACTS)
    yield


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.BACKEND_CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["auth"])
app.include_router(datasets.router, prefix=f"{settings.API_V1_PREFIX}/datasets", tags=["datasets"])
app.include_router(experiments.router, prefix=f"{settings.API_V1_PREFIX}/experiments", tags=["experiments"])
app.include_router(jobs.router, prefix=f"{settings.API_V1_PREFIX}/jobs", tags=["jobs"])
app.include_router(admin.router, prefix=f"{settings.API_V1_PREFIX}/admin", tags=["admin"])
app.include_router(catalog.router, prefix=f"{settings.API_V1_PREFIX}/catalog", tags=["catalog"])
app.include_router(
    model_runs.router,
    prefix=f"{settings.API_V1_PREFIX}/model-runs",
    tags=["model-runs"],
)

@app.get("/health")
def health():
    return {"status": "ok"}