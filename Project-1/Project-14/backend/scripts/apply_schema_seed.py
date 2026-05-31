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


def main() -> None:
    backend_root = Path(__file__).resolve().parents[1]
    load_env(backend_root / ".env")

    dsn = os.environ.get("DATABASE_URL", "").replace("postgresql+asyncpg://", "postgresql://")
    if not dsn:
        raise RuntimeError("DATABASE_URL missing in backend/.env")

    schema_sql = (backend_root / "sql" / "schema.sql").read_text(encoding="utf-8")
    seed_sql = (backend_root / "sql" / "seed_products.sql").read_text(encoding="utf-8")

    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(schema_sql)
            cur.execute(seed_sql)

    print("SCHEMA_AND_SEED_APPLIED")


if __name__ == "__main__":
    main()
