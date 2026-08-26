import asyncio
import time

import aiohttp

# Target API endpoint that hits the database
URL = "http://127.0.0.1:8000/api/health/ready"
CONCURRENCY = 1000


async def fetch(session, url, task_id):
    start_time = time.time()
    try:
        async with session.get(url, timeout=30) as response:
            status = response.status
            # Read the payload but we don't strictly need to parse it for load testing
            await response.text()
            elapsed = time.time() - start_time
            return status, elapsed, None
    except Exception as e:
        elapsed = time.time() - start_time
        return None, elapsed, str(e)


async def main():
    print(f"Starting load test with {CONCURRENCY} concurrent requests to {URL}...")

    # Custom TCP connector to allow 1000 simultaneous connections
    connector = aiohttp.TCPConnector(limit=CONCURRENCY)

    start_time = time.time()
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        for i in range(CONCURRENCY):
            tasks.append(fetch(session, URL, i))

        print("Firing requests...")
        results = await asyncio.gather(*tasks)

    total_time = time.time() - start_time

    # Analyze results
    success_count = 0
    failure_count = 0
    total_response_time = 0

    errors = {}
    status_codes = {}

    for status, elapsed, err in results:
        total_response_time += elapsed
        if status == 200:
            success_count += 1
        else:
            failure_count += 1

        if status:
            status_codes[status] = status_codes.get(status, 0) + 1

        if err:
            errors[err] = errors.get(err, 0) + 1

    # Calculate percentiles
    response_times = [elapsed for status, elapsed, err in results]
    response_times.sort()

    p50 = response_times[int(len(response_times) * 0.50)] * 1000
    p90 = response_times[int(len(response_times) * 0.90)] * 1000
    p99 = response_times[int(len(response_times) * 0.99)] * 1000

    print("\n" + "=" * 40)
    print("LOAD TEST RESULTS")
    print("=" * 40)
    print(f"Total Requests:      {CONCURRENCY}")
    print(f"Total Time Taken:    {total_time:.2f} seconds")
    print(f"Requests/Second:     {CONCURRENCY / total_time:.2f}")
    print(f"Average Response:    {(total_response_time / CONCURRENCY) * 1000:.2f} ms")
    print(f"p50 Response Time:   {p50:.2f} ms")
    print(f"p90 Response Time:   {p90:.2f} ms")
    print(f"p99 Response Time:   {p99:.2f} ms")
    print(f"Successful (200 OK): {success_count}")
    print(f"Failed:              {failure_count}")

    if status_codes:
        print("\nStatus Codes Breakdown:")
        for code, count in status_codes.items():
            print(f"  {code}: {count}")

    if errors:
        print("\nError Breakdown:")
        for err, count in errors.items():
            print(f"  {count}x {err}")

    if success_count == CONCURRENCY:
        print("\n[SUCCESS] PERFECT RUN! The database successfully handled 1,000 concurrent queries.")
    elif success_count > 0:
        print("\n[WARNING] PARTIAL SUCCESS. Some requests timed out or failed due to pool limits.")
    else:
        print("\n[ERROR] COMPLETE FAILURE. The database rejected or timed out all requests.")


if __name__ == "__main__":
    asyncio.run(main())
