import os
from typing import List
from .common_queries import Definitions, CommonQueries
import asyncpg
from dotenv import load_dotenv

# Load .env file
load_dotenv()

async def upsert_definitions(definitions: List[Definitions], region: str) -> None:

    if not definitions:
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

    for definition in definitions:
        await queries.upsert_definitions(definition, region)

    await pool.close()
