from get_regulation import get_region_regulation_details
from types import SimpleNamespace
from typing import List, Any

def dicts_to_objects(data: List[dict]) -> List[Any]:
    """
    Converts a list of dictionaries into a list of objects 
    so you can access keys as attributes.
    """
    return [SimpleNamespace(**item) for item in data]

def regulation(region):
    result = get_region_regulation_details(region)
    
    if result.get("success") and "data" in result:
        laws = dicts_to_objects(result["data"])
        
        individual_jsons = []
        for law in laws:
            individual_json = {
                "region": region,
                "statute": law.statute,
                "law_id": law.law_id,
                "regulations": law.regulations
            }
            individual_jsons.append(individual_json)
        
        return individual_jsons

    return []