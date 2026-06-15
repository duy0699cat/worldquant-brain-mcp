import os
import json
import asyncio
from dotenv import load_dotenv
from worldquant_mcp.config import WorldQuantConfig
from worldquant_mcp.client import WorldQuantClient

async def probe():
    load_dotenv()
    config = WorldQuantConfig()
    # The client needs to be initialized. 
    # Looking at client.py, it likely manages its own session or needs to be used in a context manager.
    client = WorldQuantClient(config)
    
    # We need to authenticate. The client might have an authenticate method.
    # Looking at our previous read, we should check for login/auth.
    
    endpoints = [
        "/data-fields",
        "/data-fields/subindustry",
        "/universes",
        "/universes/TOP3000",
        "/instruments",
        "/assets"
    ]
    
    params = {
        "region": "USA",
        "delay": "1",
        "universe": "TOP3000",
        "instrumentType": "EQUITY"
    }

    print(f"Timestamp: {asyncio.get_event_loop().time()}")
    
    # Attempt to authenticate if needed
    # (Assuming basic session-based access for now or that the client handles it)
    
    async with client:
        for endpoint in endpoints:
            try:
                print(f"Probing {endpoint}...")
                url = f"{config.api_base_url}{endpoint}"
                async with client.session.get(url, params=params) as resp:
                    print(f"Status: {resp.status}")
                    if resp.status == 200:
                        data = await resp.json()
                        print(f"Keys: {list(data.keys())}")
                        print(f"Snippet: {json.dumps(data)[:200]}")
                    else:
                        text = await resp.text()
                        print(f"Response: {text[:200]}")
            except Exception as e:
                print(f"Error probing {endpoint}: {e}")
            print("-" * 20)

if __name__ == "__main__":
    asyncio.run(probe())
