import asyncio

from arq.connections import RedisSettings
from arq.worker import create_worker

from app.config import get_settings
from app.tasks.enhance_task import process_enhance_page

settings = get_settings()


class WorkerSettings:
    functions = [process_enhance_page]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    on_startup = lambda ctx: None
    on_shutdown = lambda ctx: None


if __name__ == "__main__":
    worker = create_worker(WorkerSettings)
    asyncio.run(worker.run())
