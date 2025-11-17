# crawler/evaluator.py

import aiohttp
import time
from typing import Dict, Tuple, Any

BASE_URL = "http://localhost:3000"

def format_payload(
    node_data: Dict[str, Tuple[str, float]], 
    pagerank_scores: Dict[str, float]
) -> Dict[str, Any]:
    """
    Formats the crawler data and PageRank scores into the JSON
    payload required by the /evaluate endpoint.
    """
    entries = []
    
    # Use pagerank_scores keys as the master list of all pages
    for page_id, score in pagerank_scores.items():
        # Get the node_id from node_data.
        # Default to a placeholder if page is in PR but not node_data
        # (this shouldn't happen with our current crawler, but it's safe)
        node_id = node_data.get(page_id, ("UNKNOWN_NODE_ID", 0))[0]
        
        entries.append({
            "page_id": page_id,
            "latest_node_id": node_id,
            "score": score
        })
        
    return {"entries": entries}


async def submit_evaluation(
    session: aiohttp.ClientSession, 
    payload: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Submits the formatted payload to the /evaluate endpoint
    and returns the server's JSON response.
    """
    evaluate_url = f"{BASE_URL}/evaluate"
    
    try:
        async with session.post(evaluate_url, json=payload, timeout=10) as response:
            if response.status == 200:
                print("Submit successful (HTTP 200).")
                return await response.json()
            else:
                print(f"Submit failed. HTTP Status: {response.status}")
                error_text = await response.text()
                print(f"Server error: {error_text}")
                return {"error": error_text, "status": response.status}
                
    except Exception as e:
        print(f"An error occurred during submission: {e}")
        return {"error": str(e)}