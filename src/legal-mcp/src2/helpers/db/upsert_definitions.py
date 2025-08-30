import os
from typing import List
from .common_queries import Definitions, CommonQueries
from .embedding_operations import auto_generate_embeddings_on_insert
import asyncpg
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

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

    try:
        queries = CommonQueries(pool)

        for definition in definitions:
            # Upsert the definition
            result = await queries.upsert_definitions(definition, region)
            
            # Auto-generate embeddings for the inserted/updated definition
            if result.get("success") and definition.definitions:
                async with pool.acquire() as conn:
                    await auto_generate_embeddings_on_insert(conn, region, statute=definition.statute)
                    logger.info(f"Generated embedding for definition {definition.statute} in {region}")

    finally:
        await pool.close()
