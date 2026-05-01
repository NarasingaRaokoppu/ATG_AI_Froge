"""Quick DB connectivity check."""

import asyncio

from sqlalchemy import text

from app.db import engine


async def main() -> None:
    async with engine.connect() as conn:
        result = await conn.execute(text("select 1"))
        print("DB OK:", result.scalar())
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
