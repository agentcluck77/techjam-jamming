import sys
import asyncio
import os 
from dotenv import load_dotenv

load_dotenv()
root_path = os.getenv("ROOT_PATH")

# Add the project root directory to Python path
sys.path.insert(0, root_path)

from postgres.src2.helpers.db.pdf_path_getter import get_pdf_path
from postgres.src2.helpers.db.pdf_parser import parse_pdf
from postgres.src2.helpers.db.chunker import conditional_chunk
from postgres.src2.helpers.db.upsert_definitions import upsert_definitions
from postgres.src2.helpers.db.upsert_regulations import upsert_regulations
from postgres.src2.helpers.db.fetch_pdf import clean, split_into_json_for_step2
from postgres.scripts.table_setup import setup_table
from postgres.src2.helpers.db.common_queries import Definitions, Regulations


async def upsert_law(region: str, pdf_path: str, statute: str) -> None:
    text = parse_pdf(pdf_path)
    chunks = conditional_chunk(text)
    for c in chunks:
        definition, json_str2 = await clean(c)
        print(f"json: {json_str2}")
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
                regulations=i["regulation"]
            )
            await upsert_regulations([data], region)

import asyncio

if __name__ == "__main__":
    root_path = os.getenv("ROOT_PATH")
    print(root_path)
    pdf_paths = get_pdf_path("EU_DSA.pdf", root_path)
    print(pdf_paths)
    if not pdf_paths:
        raise FileNotFoundError("PDF not found")
    pdf_path = pdf_paths[0]  # take the first match
    region = "EU"
    statute = "EU_DSA"
    asyncio.run(upsert_law(region, pdf_path, statute))
