from __future__ import annotations

import os
from pathlib import Path

import psycopg2


def load_env(path: Path) -> None:
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ[key.strip()] = value.strip()


if __name__ == "__main__":
    backend = Path(__file__).resolve().parents[1]
    load_env(backend / ".env")
    dsn = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://")

    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            for table in ["behavior_events", "user_segments", "products", "personalization_decisions"]:
                cur.execute(f"select count(*) from {table}")
                count = cur.fetchone()[0]
                print(f"{table}:{count}")
