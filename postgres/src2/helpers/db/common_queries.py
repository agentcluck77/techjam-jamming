import logging
from typing import List, Optional, Any, Dict, Union
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)

# Type aliases
DbQueryResult = Dict[str, Any]

class Definitions:
    file_location: str
    region: Union[str, int]
    statute: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    definitions: Optional[str] = None

class Regulations:
    file_location: str
    statute: str
    law_id: Union[str, int]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    regulations: Optional[str] = None

class Prd:
    file_location: str 
    feature: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    relevant_laws: Optional[str] = None


# Common queries
class CommonQueries:
    def __init__(self, db):
        self.db = db

    async def upsert_definitions(self, definition: Definitions, region) -> DbQueryResult:
        try:
            query = """
            INSERT INTO techjam.t_law_{region}_definitions (
                
            ) VALUES (
                $1, $2, $3, $4, $5
            )
            ON CONFLICT (id) DO UPDATE SET
                file_location = EXCLUDED.file_location,
                statute = EXCLUDED.statute,
                region = EXCLUDED.region,
                created_at = EXCLUDED.created_at,
                updated_at = EXCLUDED.updated_at,
                definitions = EXCLUDED.definitions
            RETURNING id;
            """
            params = [
                definition.file_location,
                definition.region,
                definition.statute,
                definition.created_at or datetime.now(timezone.utc),
                definition.updated_at or datetime.now(timezone.utc),
                definition.definitions,
            ]
            await self.db.execute(query, params)
            logger.debug(f"Upserted law definitions of region {region}")
            return {"success": True, "data": None}
        except Exception as e:
            logger.error(f"Failed to upsert law definitions of region {region}: {e}")
            return {"success": False, "error": str(e)}

    async def upsert_regulations(self, regulations: Regulations, region) -> DbQueryResult:
        try:
            query = """
            INSERT INTO techjam.t_law_{region}_regulations (
                
            ) VALUES (
                $1, $2, $3, $4, $5
            )
            ON CONFLICT (id) DO UPDATE SET
                file_location = EXCLUDED.file_location,
                statute = EXCLUDED.statute,
                region = EXCLUDED.region,
                created_at = EXCLUDED.created_at,
                updated_at = EXCLUDED.updated_at,
                definitions = EXCLUDED.definitions
            RETURNING id;
            """
            params = [
                regulations.file_location,
                regulations.statute,
                regulations.law_id,
                regulations.created_at or datetime.now(timezone.utc),
                regulations.updated_at or datetime.now(timezone.utc),
                regulations.regulations
            ]
            await self.db.execute(query, params)
            logger.debug(f"Upserted law regulations of region {region}")
            return {"success": True, "data": None}
        except Exception as e:
            logger.error(f"Failed to upsert law regulations of region {region}: {e}")
            return {"success": False, "error": str(e)}

    async def get_law_regulation_by_id(self, law_id: Union[str, int], region) -> DbQueryResult:
        try:
            result = await self.db.fetchrow(f"SELECT * FROM techjam.t_law_{region}_regulations WHERE law_id = $1", law_id)
            if not result:
                return {"success": False, "error": "Ticket not found"}
            return {"success": True, "data": dict(result)}
        except Exception as e:
            logger.error(f"Failed to retrieve law {law_id}: {e}")
            return {"success": False, "error": str(e)}

    async def get_all_law_regulations(self, region) -> DbQueryResult:
        try:
            rows = await self.db.fetch(f"SELECT * FROM techjam.t_law_{region}_regulations ORDER BY updated_at DESC")
            return {"success": True, "data": [dict(row) for row in rows]}
        except Exception as e:
            logger.error(f"Failed to retrieve law regulations for {region}: {e}")
            return {"success": False, "error": str(e)}

