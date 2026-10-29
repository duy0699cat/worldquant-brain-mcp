"""Probe a few BRAIN API endpoints and print status codes and response snippets."""

import json
from datetime import datetime

from worldquant_mcp.client import WorldQuantClient
from worldquant_mcp.config import WorldQuantConfig

ENDPOINTS = [
    "/data-fields",
    "/data-fields/subindustry",
    "/universes",
    "/universes/TOP3000",
    "/instruments",
    "/assets",
]

PARAMS = {
    "region": "USA",
    "delay": "1",
    "universe": "TOP3000",
    "instrumentType": "EQUITY",
}


def probe() -> None:
    config = WorldQuantConfig.from_env()
    client = WorldQuantClient(config)
    try:
        client.authenticate()
        print("Timestamp: " + datetime.now().isoformat())
        for endpoint in ENDPOINTS:
            print(f"Probing {endpoint}...")
            try:
                # Use the raw session so non-2xx responses are printed instead of raised.
                response = client.http.get(endpoint, params=PARAMS)
                print(f"Status: {response.status_code}")
                if response.status_code == 200 and "json" in response.headers.get("content-type", ""):
                    data = response.json()
                    if isinstance(data, dict):
                        print(f"Keys: {list(data.keys())}")
                    print(f"Snippet: {json.dumps(data)[:200]}")
                else:
                    print(f"Response: {response.text[:200]}")
            except Exception as exc:
                print(f"Error probing {endpoint}: {exc}")
            print("-" * 20)
    finally:
        client.close()


if __name__ == "__main__":
    probe()
