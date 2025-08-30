import chromadb
import json
from typing import List, Dict, Any

def embed(list_of_jsons: List[Dict[str, Any]]):
    """
    Embed legal regulations from vivian_list into ChromaDB
    
    Expected format for each item in vivian_list:
    {
        "region": "EU" | "Utah" | "California" | "Florida",
        "statute": "EU_DSA" | "UTAH_SB976" | etc.,
        "law_id": "Article_28" | "Section_27000" | etc.,
        "text": "Full text of the regulation..."
    }
    """
    
    # Input validation
    if not list_of_jsons or not isinstance(list_of_jsons, list):
        raise ValueError("vivian_list must be a non-empty list")
    
    # Initialize ChromaDB client
    client = chromadb.PersistentClient()
    
    # Handle existing collection
    collection_name = "legal_regulations"
    try:
        collection = client.get_collection(collection_name)
        print(f"Using existing collection: {collection_name}")
    except:
        collection = client.create_collection(collection_name)
        print(f"Created new collection: {collection_name}")

    documents = []
    metadatas = []
    ids = []

    for i, each_json in enumerate(list_of_jsons):
        # Validate required fields
        required_fields = ["region", "statute", "law_id", "regulations"]
        for field in required_fields:
            if field not in each_json:
                print(f"Warning: Missing field '{field}' in item {i}, skipping...")
                continue
        
        region = each_json["region"]
        statute = each_json["statute"]
        law_id = each_json["law_id"]
        regulation = each_json["regulations"]
        
        # Create document text (statute + law_id + text)
        document_text = f"{statute} {law_id}: {regulation}"
        documents.append(document_text)
        
        # Create metadata
        metadata = {
            "region": region,
            "statute": statute,
            "law_id": law_id,
            # "source": "vivian_processing"
        }
        metadatas.append(metadata)
        
        # Generate unique ID
        doc_id = f"{statute}_{law_id}_{i}".replace(" ", "_").replace("/", "_")
        ids.append(doc_id)
    
    if not documents:
        raise ValueError("No valid documents")
    
    # Add documents to collection
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    
    print(f"Successfully embedded {len(documents)} legal regulations into ChromaDB")
    return collection

def load_list_of_jsons_from_file(file_path: str) -> List[Dict[str, Any]]:
    """Helper function to load vivian_list from a JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Example usage for when vivian_list arrives:
# list_of_jsons = load_list_of_jsons_from_file("vivian_regulations.json")
# collection = embed(list_of_jsons)