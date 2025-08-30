import sys
print(sys.path)
import asyncio

import importlib.util
import sys
from pathlib import Path


from upsert_definitions import upsert_definitions
from upsert_regulations import upsert_regulations
from fetch_pdf import parse_and_clean, split_into_json_for_step2
# from scripts.table_setup import setup_table
from common_queries import Definitions, Regulations


async def upsert_law(region: str, pdf_path: str, statute: str) -> None:
    definition, json_str2 = await parse_and_clean(pdf_path)
    setup_table(region)
    for i in definition:
        data = Definitions(
            file_location=pdf_path,
            region=region,
            statute=statute,
            definitions=i
        )
        await upsert_definitions([data], region)
    
    regulation = await split_into_json_for_step2(json_str2)
    for i in regulation:
        data = Regulations(
            file_location=pdf_path,
            statute=statute,
            law_id=i["law_id"],
            regulations=i["details"]
        )
        await upsert_regulations([data], region)

import asyncio

if __name__ == "__main__":
    pdf_path = r"C:\Users\xinti\OneDrive\Desktop\techjam-jamming\postgres\infodump\Florida State Law.pdf"
    region = "Florida"
    statute = "Florida Stuff"
    asyncio.run(upsert_law(region, pdf_path, statute))

