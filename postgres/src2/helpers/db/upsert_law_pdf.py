from src2.helpers.db.upsert_definitions import upsert_definitions
from src2.helpers.db.upsert_regulations import upsert_regulations
from src2.helpers.db.fetch_pdf import parse_and_clean, split_into_json
from scripts.table_setup import setup_table

def upsert_law(region = str, pdf_path = str) -> None:
    json_str = parse_and_clean(pdf_path)
    [defin, regu] = split_into_json(json_str)
    for i in defin:
        definition = [i,]
        upsert_definitions( definition, region)
    upsert_regulations


