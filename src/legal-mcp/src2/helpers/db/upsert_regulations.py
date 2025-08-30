import os
from typing import List
from .common_queries import Regulations, CommonQueries
from .embedding_operations import auto_generate_embeddings_on_insert
import asyncpg
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

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

    try:
        queries = CommonQueries(pool)

        for regulation in regulations:
            # Upsert the regulation
            result = await queries.upsert_regulations(regulation, region)
            
            # Auto-generate embeddings for the inserted/updated regulation
            if result.get("success") and regulation.regulations:
                async with pool.acquire() as conn:
                    await auto_generate_embeddings_on_insert(conn, region, law_id=regulation.law_id)
                    logger.info(f"Generated embedding for regulation {regulation.law_id} in {region}")

    finally:
        await pool.close()
