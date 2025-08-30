import os
from typing import List
from .common_queries import Definitions, CommonQueries
import asyncpg
from dotenv import load_dotenv

load_dotenv()

async def upsert_definitions(definitions: List[Definitions], region: str) -> None:

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL is not set in .env")

    if not definitions:
        return

    pool = await asyncpg.create_pool(db_url)
    queries = CommonQueries(pool)

    for definition in definitions:
        await queries.upsert_definitions(definition, region)

    await pool.close()

