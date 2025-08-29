# get definition by region and statute
import logging
import os
from src2.helpers.db.common_queries import CommonQueries, DbQueryResult
import asyncpg
from dotenv import load_dotenv
logger = logging.getLogger(__name__)
load_dotenv()

async def get_definition(region: str, statute: str) -> DbQueryResult:
    
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL is not set in .env")
    
    if not region:
        logger.error("missing region")
        return 
    if not statute:
        logger.error("missing statute")        
        return

    pool = await asyncpg.create_pool(db_url)
    try:
        async with pool.acquire() as conn:
            queries = CommonQueries(conn)
            result = await queries.get_law_definition_by_statute(statute, region)
    finally:
        await pool.close()
    
    return result

