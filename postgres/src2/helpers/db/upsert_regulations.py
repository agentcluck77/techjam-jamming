import os
from typing import List
from .common_queries import Regulations, CommonQueries
import asyncpg
from dotenv import load_dotenv

# Load .env file
load_dotenv()

async def upsert_regulations(regulations: List[Regulations], region: str) -> None:

    if not regulations:
        return

    # Read connection details from env
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "postgres")
    host = os.getenv("DB_HOST", "localhost")
    port = int(os.getenv("DB_PORT", 5432))
    database = os.getenv("DB_NAME", "postgres")

    # Create asyncpg pool with explicit params
    pool = await asyncpg.create_pool(
        user=user,
        password=password,
        host=host,
        port=port,
        database=database
    )

    queries = CommonQueries(pool)

    for regulation in regulations:
        await queries.upsert_regulations(regulation, region)

    await pool.close()
