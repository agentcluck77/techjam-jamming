from src2.helpers.db.upsert_definitions import upsert_definitions
from src2.helpers.db.upsert_regulations import upsert_regulations
from src2.helpers.db.fetch_pdf import parse_and_clean, split_into_json
from scripts.table_setup import setup_table
from src2.helpers.db.common_queries import Definitions, Regulations


async def upsert_law(region: str, pdf_path: str, statute: str) -> None:
    json_str = await parse_and_clean(pdf_path)
    definition, regulation = await split_into_json(json_str)
    setup_table()
    for i in definition:
        data = Definitions(
            file_location=pdf_path,
            region=region,
            statute=statute,
            definitions=i
        )
        await upsert_definitions([data], region)
        
    for i in regulation:
        data = Regulations(
            file_location=pdf_path,
            statute=statute,
            law_id=i["number"],
            regulations=i["details"]
        )
        await upsert_regulations([data], region)


