"""压测基准脚本 — 使用 asyncio + httpx 并发测试关键 API。

使用方法::

    # 确保后端运行在 http://localhost:8000
    cd backend
    uv run python -m tests.load.locustfile

    # 如果安装了 locust，也可直接用:
    # uv run locust -f tests/load/locustfile.py --headless -u 20 -r 5 -t 60s
"""

from __future__ import annotations

import asyncio
import statistics
import time

import httpx

# ── 配置 ──────────────────────────────────────────────────────────
BASE_URL = "http://localhost:8000"
CONCURRENCY = 20
TOTAL_REQUESTS = 100

ENDPOINTS = [
    ("GET", "/health", "Health Check"),
    ("GET", "/api/products", "Product List"),
    ("GET", "/api/search?q=test&types=requirement", "Global Search"),
    ("GET", "/api/analytics/overview", "Analytics Overview"),
]


async def _request(
    client: httpx.AsyncClient,
    method: str,
    path: str,
) -> tuple[int, float]:
    """发送单个请求，返回 (status_code, elapsed_seconds)。"""
    start = time.perf_counter()
    try:
        response = await client.request(method, f"{BASE_URL}{path}", timeout=30)
        elapsed = time.perf_counter() - start
        return response.status_code, elapsed
    except Exception:
        elapsed = time.perf_counter() - start
        return 0, elapsed


async def _run_endpoint(method: str, path: str, label: str) -> dict:
    """对单个端点进行并发压测。"""
    latencies: list[float] = []
    errors = 0
    sem = asyncio.Semaphore(CONCURRENCY)

    async with httpx.AsyncClient() as client:

        async def _task():
            nonlocal errors
            async with sem:
                status, elapsed = await _request(client, method, path)
                latencies.append(elapsed)
                if status < 200 or status >= 400:
                    errors += 1

        tasks = [_task() for _ in range(TOTAL_REQUESTS)]
        await asyncio.gather(*tasks)

    latencies.sort()
    return {
        "endpoint": f"{method} {path}",
        "label": label,
        "total": TOTAL_REQUESTS,
        "errors": errors,
        "p50": round(latencies[int(len(latencies) * 0.50)] * 1000, 1),
        "p95": round(latencies[int(len(latencies) * 0.95)] * 1000, 1),
        "p99": round(latencies[int(len(latencies) * 0.99)] * 1000, 1),
        "avg": round(statistics.mean(latencies) * 1000, 1),
    }


async def main() -> None:
    print(f"\n{'=' * 70}")
    print(f" Sisyphus-Y 压测基准  |  并发={CONCURRENCY}  请求数={TOTAL_REQUESTS}")
    print(f"{'=' * 70}\n")

    for method, path, label in ENDPOINTS:
        try:
            result = await _run_endpoint(method, path, label)
            print(
                f"  {result['label']:20s} | "
                f"p50={result['p50']:>7.1f}ms  "
                f"p95={result['p95']:>7.1f}ms  "
                f"p99={result['p99']:>7.1f}ms  "
                f"avg={result['avg']:>7.1f}ms  "
                f"err={result['errors']}/{result['total']}"
            )
        except Exception as e:
            print(f"  {label:20s} | ❌ 测试失败: {e}")

    print(f"\n{'=' * 70}\n")


# ── Locust 定义（可选，需要安装 locust）────────────────────────────
try:
    from locust import HttpUser, between, task

    class SisyphusUser(HttpUser):
        wait_time = between(0.5, 2)

        @task(3)
        def list_products(self):
            self.client.get("/api/products")

        @task(2)
        def search(self):
            self.client.get("/api/search?q=test&types=requirement")

        @task(1)
        def health(self):
            self.client.get("/health")

        @task(1)
        def analytics_overview(self):
            self.client.get("/api/analytics/overview")

except ImportError:
    pass


if __name__ == "__main__":
    asyncio.run(main())
