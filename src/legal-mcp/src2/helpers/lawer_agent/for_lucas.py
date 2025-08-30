import sys
import asyncio
import os
from types import SimpleNamespace
from typing import List, Any
from dotenv import load_dotenv

load_dotenv()
root_path = os.getenv("ROOT_PATH")


sys.path.insert(0, root_path)
from helpers.lawer_agent.get_regulation import get_region_regulation_details


def dicts_to_objects(data: List[dict]) -> List[Any]:
    return [SimpleNamespace(**item) for item in data]


async def regulation(region: str):
    # Await the async function correctly
    result = await get_region_regulation_details(region)
    
    if result.get("success") and "data" in result:
        laws = dicts_to_objects(result["data"])
        individual_jsons = []
        for law in laws:
            individual_json = {
                "region": region,
                "statute": law.statute,
                "law_id": getattr(law, "law_id", None),
                "regulations": getattr(law, "regulations", None)
            }
            individual_jsons.append(individual_json)
        return individual_jsons

    return f"Error getting regulation from {region}"


def get_regulation():
    if len(sys.argv) < 2:
        print("Please provide a region.")
        sys.exit(1)
    
    region = sys.argv[1]
    regulations = asyncio.run(regulation(region)) 
    print(regulations)


if __name__ == "__main__":
    get_regulation()
