import sys
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()
root_path = os.getenv("ROOT_PATH")

sys.path.insert(0, root_path)
from helpers.lawer_agent.get_definition import get_definition


async def definitions(region: str, statute: str):
    result = await get_definition(region, statute)  # await the coroutine
    
    if result.get("success") and "data" in result:
        return result["data"]  # return as dict directly
    
    return f"Error getting definitions from {region}, {statute}"



def main():
    if len(sys.argv) < 3:
        print("Please provide a region and statute")
        sys.exit(1)
    
    region = sys.argv[1].capitalize()  
    statute = " ".join(sys.argv[2:]).title() 
    
    defin = asyncio.run(definitions(region, statute)) 
    print(defin)

if __name__ == "__main__":
    main()
