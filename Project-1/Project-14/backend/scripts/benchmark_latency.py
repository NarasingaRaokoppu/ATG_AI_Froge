from __future__ import annotations

import statistics
import time

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def run_benchmark(request_count: int = 100) -> None:
    latencies_ms: list[float] = []

    for idx in range(request_count):
        payload = {
            "user_id": f"u_bench_{idx % 10}",
            "session_id": f"s_bench_{idx}",
            "page_type": "home" if idx % 2 == 0 else "plp",
            "context": {"device": "web"},
        }

        start = time.perf_counter()
        response = client.post("/api/v1/personalization/decide", json=payload)
        elapsed = (time.perf_counter() - start) * 1000
        if response.status_code != 200:
            raise RuntimeError(f"request failed at index {idx}: {response.status_code}")
        latencies_ms.append(elapsed)

    p95 = statistics.quantiles(latencies_ms, n=100)[94]
    print(f"requests={request_count}")
    print(f"avg_ms={statistics.mean(latencies_ms):.2f}")
    print(f"p95_ms={p95:.2f}")


if __name__ == "__main__":
    run_benchmark(100)
