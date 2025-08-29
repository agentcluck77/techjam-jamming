from src2.helpers.db.pdf_parser import parse_pdf
from src2.helpers.laws.clean_law import clean_law_llm
import json

async def parse_and_clean(pdf_path: str) -> str:
    text = parse_pdf(pdf_path)
    cleaned = await clean_law_llm(text)
    return cleaned

async def split_into_json(json_str: str):
    data = json.loads(json_str)

    definitions = data.get("definitions", [])
    regu = data.get("regulations", [])
    regulations = []
    for reg in regu:
        number = reg.get("number", "")
        details = reg.get("details", "")
        regulations.append({"number": number, "details": details})
    
    return [definitions, regulations]

