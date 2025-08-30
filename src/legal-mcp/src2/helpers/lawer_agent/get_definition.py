# get definition by region and statute
import logging
import os
import asyncpg
from dotenv import load_dotenv
from helpers.db.common_queries import CommonQueries, DbQueryResult
logger = logging.getLogger(__name__)
load_dotenv()

async def get_definition(region: str, statute: str) -> DbQueryResult:
     # Get individual DB connection parameters
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "postgres")
    host = os.getenv("DB_HOST", "localhost")
    port = int(os.getenv("DB_PORT", 5432))
    database = os.getenv("DB_NAME", "postgres")

    # Validate required parameters
    if not all([host, user, password, database]):
        raise ValueError("One or more DB connection environment variables are missing")

    if not region:
        raise ValueError("Region is required")
    
    # Create a connection pool
    pool = await asyncpg.create_pool(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database
    )

    try:
        async with pool.acquire() as conn:
            queries = CommonQueries(conn)
            result = await queries.get_law_definition_by_statute(statute, region)
    finally:
        await pool.close()

    return result

