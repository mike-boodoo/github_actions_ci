from fastapi import FastAPI
from pydantic import BaseModel
import os
import time

app = FastAPI(
    title="CI/CD Demo API",
    version="1.0.0",
)


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str


@app.get("/")
def root():
    return {
        "service": "ci-cd-demo",
        "message": "Hello from the CI/CD pipeline",
    }


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="healthy",
        version=os.getenv("APP_VERSION", "development"),
        environment=os.getenv("APP_ENV", "local"),
    )


@app.get("/ready")
def ready():
    return {
        "ready": True,
        "timestamp": time.time(),
    }
