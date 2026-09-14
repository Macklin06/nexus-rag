import asyncio
import time
import httpx


async def test_endpoint(url):
    async with httpx.AsyncClient() as client:
        start = time.perf_counter()

        tasks = [
            client.get(url),
            client.get(url),
            client.get(url),
            client.get(url),
            client.get(url),
        ]

        responses = await asyncio.gather(*tasks)

        elapsed = time.perf_counter() - start

        print(f"{url}: {elapsed:.2f} seconds")
        print([response.status_code for response in responses])


async def main():
    await test_endpoint("http://127.0.0.1:8000/sync-sleep")
    await test_endpoint("http://127.0.0.1:8000/async-sleep")


asyncio.run(main())