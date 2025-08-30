import os
from typing import List
from .common_queries import Regulations, CommonQueries
import asyncpg
from dotenv import load_dotenv

load_dotenv()

async def upsert_regulations(regulations: List[Regulations], region: str) -> None:
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL is not set in .env")

    if not regulations:
        return

    pool = await asyncpg.create_pool(db_url)
    queries = CommonQueries(pool)

    for regulation in regulations:
        await queries.upsert_regulations(regulation, region)

    await pool.close()

