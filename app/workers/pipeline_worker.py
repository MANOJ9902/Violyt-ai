"""Celery tasks for the LangGraph intelligence pipeline."""

from __future__ import annotations

import asyncio

from celery import Celery

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

celery_app = Celery(
    "pipeline_worker",
    broker=get_settings().celery_broker_url,
    backend=get_settings().celery_broker_url,
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    track_started=True,
)


@celery_app.task(bind=True, name="pipeline.run_phase1", max_retries=1)
def run_phase1_task(self, run_id: str, payload: dict) -> dict:
    from app.services.pipeline.runner import execute_phase1

    logger.info("pipeline_worker.phase1", run_id=run_id)
    return asyncio.run(execute_phase1(run_id, payload))


@celery_app.task(bind=True, name="pipeline.run_phase2", max_retries=1)
def run_phase2_task(self, run_id: str, creative_blueprint: dict | None) -> dict:
    from app.services.pipeline.runner import execute_phase2

    logger.info("pipeline_worker.phase2", run_id=run_id)
    return asyncio.run(execute_phase2(run_id, creative_blueprint))
