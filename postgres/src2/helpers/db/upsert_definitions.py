
# get definition, make into Definition, put into this

from .common_queries import Definitions, CommonQueries

# create or inject your db connection (example with asyncpg)
import asyncpg

async def upsert_definitions(definitions: list[Definitions], region: str) -> None:
    if not definitions:
        return

    # Create a DB connection
    db = await asyncpg.connect("postgresql://user:password@localhost:5432/mydb")

    # Wrap it with CommonQueries
    queries = CommonQueries(db)

    for definition in definitions:
        await queries.upsert_definitions(definition, region)

    await db.close()
