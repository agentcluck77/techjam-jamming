import sys
# Add the project root directory to Python path
sys.path.insert(0, r'C:\Users\xinti\OneDrive\Desktop\techjam-jamming')

from postgres.src2.helpers.db.pdf_parser import parse_pdf
from postgres.src2.helpers.laws.llm_service import cleaner_llm
import json

async def parse_and_clean(pdf_path: str) -> str:
    text = parse_pdf(pdf_path)
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