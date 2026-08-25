import asyncio
import httpx
import time
import statistics


async def fetch(client, url):
    start = time.perf_counter()
    try:
        response = await client.get(url, follow_redirects=True)
        duration = time.perf_counter() - start
        return duration, response.status_code
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None, None


async def run_load_test(url, name, num_requests=100, concurrency=10):
    print(f"Testing {name} ({url})...")
    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        tasks = []
        sem = asyncio.Semaphore(concurrency)

        async def sem_fetch():
            async with sem:
                return await fetch(client, url)

        for _ in range(num_requests):
            tasks.append(sem_fetch())

        results = await asyncio.gather(*tasks)
        if results:
            print(f"  Sample Status Code: {results[0][1]}")

    durations = [r[0] for r in results if r[0] is not None]
    status_codes = [r[1] for r in results if r[1] is not None]

    if not durations:
        print(f"No successful requests for {name}")
        return

    avg = statistics.mean(durations) * 1000
    p95 = statistics.quantiles(durations, n=20)[18] * 1000
    p99 = statistics.quantiles(durations, n=100)[98] * 1000
    success_rate = (status_codes.count(200) / num_requests) * 100

    print(f"  Total Requests: {num_requests}")
    print(f"  Concurrency: {concurrency}")
    print(f"  Success Rate: {success_rate:.1f}%")
    print(f"  Avg Latency: {avg:.2f}ms")
    print(f"  P95 Latency: {p95:.2f}ms")
    print(f"  P99 Latency: {p99:.2f}ms")
    print("-" * 20)


async def main():
    base_url = "http://localhost:8000"
    tests = [
        ("/api/health/live", "Liveness Check"),
        ("/api/health/ready", "Readiness Check"),
        ("/api/recommendations/", "Recommendations (Guest)"),
    ]

    for path, name in tests:
        await run_load_test(base_url + path, name, num_requests=100, concurrency=20)


if __name__ == "__main__":
    asyncio.run(main())
