import logging
from typing import List, Optional, Any, Dict, Union
from datetime import datetime, timezone
from dataclasses import dataclass

logger = logging.getLogger(__name__)

DbQueryResult = Dict[str, Any]

@dataclass
class Definitions:
    file_location: str
    region: Union[str, int]
    statute: str
    definitions: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Regulations:
    file_location: str
    statute: str
    law_id: Union[str, int]
    regulations: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

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

    async def upsert_definitions(self, data: Definitions, region) -> DbQueryResult:
        try:
            query = f"""
            INSERT INTO techjam.t_law_{region}_definitions (
                
            ) VALUES (
                $1, $2, $3, $4::jsonb, $5, $6
            )
            ON CONFLICT (id) DO UPDATE SET
                file_location = EXCLUDED.file_location,
                statute = EXCLUDED.statute,
                region = EXCLUDED.region,
                definitions = EXCLUDED.definitions,                
                created_at = EXCLUDED.created_at,
                updated_at = EXCLUDED.updated_at

            RETURNING id;
            """
            params = [
                data.file_location,
                data.region or region,
                data.statute,
                data.definitions,
                data.created_at or datetime.now(timezone.utc),
                data.updated_at or datetime.now(timezone.utc),
            ]
            logger.debug(f"Query: {query}, Params: {params}")
            await self.db.execute(query, params)
            logger.debug(f"Upserted law definitions of region {region}")
            return {"success": True, "data": None}
        except Exception as e:
            logger.error(f"Failed to upsert law definitions of region {region}: {e}")
            return {"success": False, "error": str(e)}

    async def upsert_regulations(self, data: Regulations, region) -> DbQueryResult:
        try:
            query = f"""
            INSERT INTO techjam.t_law_{region}_regulations (
                
            ) VALUES (
                $1, $2, $3, $4::json, $5, $6
            )
            ON CONFLICT (id) DO UPDATE SET
                file_location = EXCLUDED.file_location,
                statute = EXCLUDED.statute,
                law_id = EXCLUDED.law_id,
                regulations = EXCLUDED.regulations,
                created_at = EXCLUDED.created_at,
                updated_at = EXCLUDED.updated_at
                
            RETURNING id;
            """
            params = [
                data.file_location,
                data.statute,
                data.law_id,
                data.regulations,
                data.created_at or datetime.now(timezone.utc),
                data.updated_at or datetime.now(timezone.utc),
            ]
            logger.debug(f"Query: {query}, Params: {params}")
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
                return {"success": False, "error": "Regulation not found"}
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

    async def get_law_definition_by_statute(self, statute: str, region: str) -> DbQueryResult:
        try:
            result = await self.db.fetchrow(f"SELECT * FROM techjam.t_law_{region}_definitions WHERE statute = $1", statute)
            if not result:
                return {"success": False, "error": "law definition not found"}
            return {"success": True, "data": dict(result)}
        except Exception as e:
            logger.error(f"Failed to retrieve definitions: {e}")
            return {"success": False, "error": str(e)}
