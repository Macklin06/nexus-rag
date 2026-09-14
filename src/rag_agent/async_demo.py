import time
import logging
import asyncio


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def timing(func):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.info("run() completed in %.4f seconds", elapsed)
        return result

    return wrapper


def fetch_one():
    time.sleep(1)

async def fetch_one_async():
    await asyncio.sleep(1)

@timing
def run():
    for i in range(5):
        fetch_one()


run()

async def run_async():
    await asyncio.gather(
        fetch_one_async(),
        fetch_one_async(),
        fetch_one_async(),
        fetch_one_async(),
        fetch_one_async()
    )

async def timed_run_async():
    start = time.perf_counter()

    await run_async()

    elapsed = time.perf_counter() - start
    logger.info("run_async() completed in %.4f seconds", elapsed)

asyncio.run(timed_run_async())

