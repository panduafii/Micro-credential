from __future__ import annotations

import asyncio
from collections.abc import Sequence

import structlog
from redis import Redis
from rq import Connection, Queue, Worker
from src.core.config import get_settings
from src.workers import jobs

logger = structlog.get_logger()

QUEUE_NAMES: Sequence[str] = ("default", "high")
REGISTERED_JOBS = {
    "score_essay": jobs.score_essay_job,
    "generate_recommendations": jobs.generate_recommendations_job,
}


async def main() -> None:
    """Bootstrap the async worker, wiring queues and job handlers."""
    settings = get_settings()
    redis_connection = Redis.from_url(settings.redis_url)
    logger.info(
        "worker_bootstrap",
        queues=list(QUEUE_NAMES),
        redis_url=settings.redis_url,
        jobs=list(REGISTERED_JOBS.keys()),
    )

    await asyncio.to_thread(_run_worker, redis_connection, QUEUE_NAMES)


def _run_worker(connection: Redis, queue_names: Sequence[str]) -> None:
    """Run the RQ worker in a background thread."""
    with Connection(connection=connection):
        queues = [Queue(name, connection=connection) for name in queue_names]
        worker = Worker(queues, name="microcred-worker")
        worker.work(with_scheduler=True)


if __name__ == "__main__":
    asyncio.run(main())
