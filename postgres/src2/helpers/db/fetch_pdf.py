import sys
import os
from dotenv import load_dotenv

load_dotenv()

root_path = os.getenv("ROOT_PATH")
# Add the project root directory to Python path
sys.path.insert(0, root_path)

from postgres.src2.helpers.db.pdf_parser import parse_pdf
from postgres.src2.helpers.laws.llm_service import cleaner_llm
import json

async def clean(text: str) -> str:
    definitions, step2 = await cleaner_llm(text)
    return definitions, step2


async def split_into_json_for_step2(json_str: str):
    data = json.loads(json_str)
    
    # data is already a list of regulation dicts
    regulations = []
    for reg in data:
        law_id = reg.get("law_id", "")
        details = reg.get("regulation", "")
        regulations.append({"law_id": law_id, "regulation": details})
    
    print(regulations)
    return regulations