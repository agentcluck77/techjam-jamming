import sys
print(sys.path)
import asyncio
from pathlib import Path
import json


import sys
import os
# Add the project root directory to Python path
sys.path.insert(0, r'C:\Users\xinti\OneDrive\Desktop\techjam-jamming')

from postgres.src2.helpers.db.upsert_definitions import upsert_definitions
from postgres.src2.helpers.db.upsert_regulations import upsert_regulations
from postgres.src2.helpers.db.fetch_pdf import parse_and_clean, split_into_json_for_step2
from postgres.scripts.table_setup import setup_table
from postgres.src2.helpers.db.common_queries import Definitions, Regulations


async def upsert_law(region: str, pdf_path: str, statute: str) -> None:
    definition, json_str2 = await parse_and_clean(pdf_path)
    setup_table(region)
    for term, meaning in definition.items():
        data = Definitions(
            file_location=pdf_path,
            region=region,
            statute=statute,
            definitions=f"{term}: {meaning}"
        )
        print(data)
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

