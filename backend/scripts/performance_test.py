import asyncio
import httpx
import time
import statistics
import sys

BASE_URL = "http://localhost:8000"


async def fetch(client, url):
    start = time.perf_counter()
    try:
        response = await client.get(url, follow_redirects=True)
        duration = time.perf_counter() - start
        return duration, response.status_code
    except Exception as e:
        duration = time.perf_counter() - start
        return duration, str(e)


async def run_load_test(url, name, num_requests=100, concurrency=10):
    print(f"Testing {name} ({url})...")
    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        tasks = []
        # Create a semaphore to control concurrency
        sem = asyncio.Semaphore(concurrency)

        async def sem_fetch(url):
            async with sem:
                return await fetch(client, url)

        start_time = time.perf_counter()
        results = await asyncio.gather(*[sem_fetch(url) for _ in range(num_requests)])
        total_time = time.perf_counter() - start_time

        durations = [r[0] for r in results if isinstance(r[1], int) and r[1] == 200]
        errors = [r[1] for r in results if not (isinstance(r[1], int) and r[1] == 200)]

        print(f"  Total Requests: {num_requests}")
        print(f"  Concurrency: {concurrency}")
        print(f"  Total Time: {total_time:.2f}s")
        print(f"  Success Rate: {len(durations) / num_requests * 100:.1f}%")
        if durations:
            print(f"  Avg Latency: {statistics.mean(durations) * 1000:.2f}ms")
            print(f"  P95 Latency: {statistics.quantiles(durations, n=20)[18] * 1000:.2f}ms")
            print(f"  P99 Latency: {statistics.quantiles(durations, n=100)[98] * 1000:.2f}ms")
        if errors:
            from collections import Counter

            error_counts = Counter(errors)
            print(f"  Errors: {dict(error_counts)}")
        print("-" * 20)


async def main():
    # Warm up
    print("Warming up...")
    async with httpx.AsyncClient() as client:
        await client.get(f"{BASE_URL}/api/health")

    tests = [
        ("/api/health", "Health Check"),
        ("/api/products/public", "Public Products (Default)"),
        ("/api/categories", "Categories"),
        ("/api/banners/public", "Public Banners"),
        ("/api/products/public?limit=50", "Products (Limit 50)"),
        ("/api/products/public?search=pen", "Search 'pen'"),
        ("/api/products/public?category=Stationery", "Category 'Stationery'"),
    ]

    # Baseline: Low concurrency
    print("\n--- Baseline Test (Concurrency: 5) ---")
    for path, name in tests:
        await run_load_test(BASE_URL + path, name, num_requests=50, concurrency=5)

    # Load: Higher concurrency
    print("\n--- Load Test (Concurrency: 20) ---")
    for path, name in tests:
        await run_load_test(BASE_URL + path, name, num_requests=100, concurrency=20)


if __name__ == "__main__":
    asyncio.run(main())
