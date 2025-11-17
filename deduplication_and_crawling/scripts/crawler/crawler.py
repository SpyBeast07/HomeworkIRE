import asyncio
import aiohttp
import time
from typing import Dict, Set, Tuple
from .parser import parse_page

# The server you started is running here
BASE_URL = "http://localhost:3000"

class Crawler:
    """
    Asynchronous crawler to discover the entire page graph.
    """
    def __init__(self, start_page: str = "/"):
        self.start_page = start_page
        self.base_url = BASE_URL
        
        # --- Crawl State ---
        # Stores the graph structure: {'page_id': ['link1', 'link2']}
        self.graph: Dict[str, list] = {}
        
        # Stores the latest node data: {'page_id': ('node_id', timestamp)}
        self.node_data: Dict[str, Tuple[str, float]] = {}
        
        # --- Internal State ---
        self.queue = asyncio.Queue()
        self.seen: Set[str] = set()
        self.session: aiohttp.ClientSession = None
        
        # --- Stats ---
        self.total_visits = 0
        self.start_time = 0.0

    async def fetch(self, page_path: str) -> None:
        """
        Fetches and parses a single page, adding new links to the queue.
        """
        if page_path in self.seen:
            return
        
        self.seen.add(page_path)
        url = f"{self.base_url}/{page_path}"

        try:
            async with self.session.get(url, timeout=10) as response:
                self.total_visits += 1
                if response.status != 200:
                    print(f"Error fetching {url}: Status {response.status}")
                    return
                
                html_content = await response.text()
                parsed_data = parse_page(html_content)
                
                if not parsed_data:
                    print(f"Error parsing {url}")
                    return

                page_id = parsed_data['page_id']
                node_id = parsed_data['node_id']
                links = parsed_data['links']
                
                # Store the discovered data
                self.graph[page_id] = links
                self.node_data[page_id] = (node_id, time.time())
                
                # Add new, unseen links to the queue
                for link in links:
                    if link not in self.seen:
                        await self.queue.put(link)
                        
        except Exception as e:
            print(f"Error during fetch for {url}: {e}")

    async def refetch(self, page_path: str) -> None:
        """
        Re-fetches a page *known* to be in the graph to update its node_id.
        This bypasses the 'seen' check.
        
        FIXED in v1.2: Correctly increments visit count and reports errors.
        """
        url = f"{self.base_url}/{page_path}"
        
        # Increment visit count *before* the network call
        # This fixes the bug where visits weren't being counted.
        self.total_visits += 1 
        
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status != 200:
                    # print(f"  Refetch warning: HTTP {response.status} for {page_path}")
                    return  # Don't parse errors
                
                html_content = await response.text()
                parsed_data = parse_page(html_content)
                
                if parsed_data:
                    # Update node_data with fresh timestamp
                    self.node_data[parsed_data['page_id']] = (parsed_data['node_id'], time.time())
                # else:
                    # print(f"  Refetch warning: Could not parse {page_path}")

        except Exception as e:
            # THIS IS THE FIX: Print the error instead of 'pass'
            print(f"  Refetch CRITICAL error: {e} on page {page_path}")

    async def crawl(self) -> None:
        """
        Runs the full crawl until the queue is empty.
        
        FIXED in v1.3: This function no longer creates its own session.
        It uses self.session (which was set by main.py) for all operations.
        """
        self.start_time = time.time()
        print(f"--- 🚀 Starting crawl from {self.start_page} ---")

        # self.session is ALREADY SET by main.py. We just use it.
        # The 'async with' block has been removed.
        
        try:
            # Start with the root page
            await self.queue.put(self.start_page.lstrip('/'))
            
            while not self.queue.empty():
                page_to_fetch = await self.queue.get()
                # The self.fetch() function will use self.session
                await self.fetch(page_to_fetch)
                await asyncio.sleep(0.01) # Give event loop a chance to breathe
            
            elapsed = time.time() - self.start_time
            print("\n--- ✅ Crawl Finished ---")
            print(f"  Total pages found: {len(self.graph)}")
            print(f"  Total visits made: {self.total_visits}")
            print(f"  Time taken:        {elapsed:.2f} seconds")
            print("\n--- Node Data (Sample) ---")
            # Print first 5 nodes found
            for i, (page, (node, _)) in enumerate(self.node_data.items()):
                if i >= 5:
                    break
                print(f"  {page}: {node}")
            print("...")
        
        except Exception as e:
            print(f"An error occurred during initial crawl: {e}")
            # This can happen if the session was closed unexpectedly
            print("Please ensure main.py is managing the session correctly.")

# This allows the file to be run directly for testing, though we'll use the notebook
if __name__ == "__main__":
    
    async def main_test():
        crawler = Crawler()
        await crawler.crawl()
    
    asyncio.run(main_test())