# crawler/crawler.py

import asyncio
import aiohttp
import time
from typing import Dict, Set, Tuple, List
from .parser import parse_page

class Crawler:
    def __init__(self, start_page: str = "/"):
        self.start_page = start_page
        self.base_url = "http://localhost:3000"
        
        self.graph: Dict[str, list] = {}
        self.node_data: Dict[str, Tuple[str, float]] = {}
        
        # Stores the update history for every node
        self.server_update_history: Dict[str, List[float]] = {}
        
        self.queue = asyncio.Queue()
        self.seen: Set[str] = set()
        self.session: aiohttp.ClientSession = None
        self.total_visits = 0
        self.start_time = 0.0

    async def fetch(self, page_path: str) -> None:
        if page_path in self.seen: return
        self.seen.add(page_path)
        await self._perform_request(page_path)

    async def refetch(self, page_path: str) -> None:
        await self._perform_request(page_path)

    async def _perform_request(self, page_path: str):
        url = f"{self.base_url}/{page_path}"
        self.total_visits += 1
        
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status != 200: return
                html_content = await response.text()
                parsed_data = parse_page(html_content)
                
                if parsed_data:
                    p_id = parsed_data['page_id']
                    
                    # Store Graph Data
                    self.graph[p_id] = parsed_data['links']
                    self.node_data[p_id] = (parsed_data['node_id'], time.time())
                    
                    # Store History Data (For Prediction)
                    self.server_update_history[p_id] = parsed_data['history']

                    # Add new links
                    for link in parsed_data['links']:
                        if link not in self.seen:
                            await self.queue.put(link)
        except Exception as e:
            print(f"Error fetching {url}: {e}")

    async def crawl(self) -> None:
        self.start_time = time.time()
        print(f"--- 🚀 Starting crawl from {self.start_page} ---")
        try:
            await self.queue.put(self.start_page.lstrip('/'))
            while not self.queue.empty():
                page = await self.queue.get()
                await self.fetch(page)
                await asyncio.sleep(0.01)
        except Exception as e:
            print(f"Crawl error: {e}")