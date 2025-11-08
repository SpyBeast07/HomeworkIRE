import asyncio
import aiohttp
import time
import networkx as nx
from bs4 import BeautifulSoup
import re # Your parser will still need this

# --- Global State: Your bot's "brain" ---
# All async tasks will read/write from here
page_graph = {} # Stores all info: {page_path: {page_id, node_id, links, history}}
crawl_queue = asyncio.Queue() # Queue of page_paths to visit
visited_pages = set() # To avoid duplicate work
start_time = None
total_visits = 0

# Parser function
def parse_page(html_content):
    """
    Parses the HTML of a page and extracts all required data.
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 1. Find Page ID
        page_id_tag = soup.find('div', class_='page-id')
        page_id = page_id_tag.text.split(':')[-1].strip()
        
        # 2. Find Node ID
        node_id_tag = soup.find('span', class_='node-id')
        node_id = node_id_tag.find('b').text.strip()
        
        # 3. Find Outgoing Links
        outgoing_links = []
        link_tags = soup.find_all('a', class_='file-link')
        for tag in link_tags:
            outgoing_links.append(tag['href'])
            
        # 4. Find Node ID History
        history = []
        details_tag = soup.find('details')
        if details_tag:
            # Find all <div>s with the style 'margin-left: 1rem...'
            history_divs = details_tag.find_all('div', style=re.compile(r'margin-left'))
            for div in history_divs:
                # Text is '• p5zg2ka84j0e (2025-11-07 16:48:53 UTC)'
                text = div.text.strip('• ')
                match = re.search(r'^(.*?) \((.*? UTC)\)$', text)
                if match:
                    prev_node_id = match.group(1).strip()
                    timestamp = match.group(2).strip()
                    history.append({'node_id': prev_node_id, 'timestamp': timestamp})

        return {
            'page_id': page_id,
            'node_id': node_id,
            'outgoing_links': outgoing_links,
            'history': history
        }
        
    except Exception as e:
        print(f"Error parsing page: {e}")
        return None

# --- TASK A: The Crawler ---
async def crawler_task(session):
    global total_visits, page_graph, visited_pages
    
    while time.time() - start_time < 60: # Run for 60 seconds
        try:
            # 1. Get a page to crawl
            try:
                page_path = await asyncio.wait_for(crawl_queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue # Queue is empty, just loop again

            # 2. Fetch it
            total_visits += 1
            async with session.get(f"http://localhost:3000{page_path}") as response:
                if response.status != 200:
                    crawl_queue.task_done()
                    continue
                html = await response.text()
            
            # 3. Parse it
            page_data = parse_page(html) # Use your existing parser
            if not page_data:
                crawl_queue.task_done()
                continue

            # 4. Update the "brain" with the fresh data
            page_graph[page_path] = page_data
            
            # 5. Add new links *only if this page is new*
            if page_path not in visited_pages:
                visited_pages.add(page_path) # Mark as discovered
                for link in page_data['outgoing_links']:
                    if link not in visited_pages: 
                        await crawl_queue.put(link)
            
            # 6. (SIMPLE RE-VISIT)
            # ALWAYS re-add this page to the queue to be crawled again.
            # This keeps its node_id fresh.
            await crawl_queue.put(page_path) 
            
            crawl_queue.task_done()
            await asyncio.sleep(0.1) # Be a little more polite

        except Exception as e:
            print(f"Crawler error: {e}")

# --- TASK B: The Evaluator ---
async def evaluator_task(session):
    global page_graph, total_visits
    
    while time.time() - start_time < 60:
        # Wait for the next 15-second interval
        # We sleep for 14.5s to be safe
        await asyncio.sleep(14.5) 

        print("\n--- EVALUATING ---")

        # 1. Build the graph from the *current* state
        G = nx.DiGraph()
        current_graph_data = page_graph.copy() # Copy it so it doesn't change
        
        for page_path, data in current_graph_data.items():
            G.add_node(page_path)
            for link in data['outgoing_links']:
                if link not in G: G.add_node(link)
                G.add_edge(page_path, link)
        
        # 2. Calculate PageRank
        try:
            pagerank_scores = nx.pagerank(G)
        except:
            pagerank_scores = {} # Handle empty graph at start

        # 3. Format the data for submission
        entries = []
        for page_path, data in current_graph_data.items():
            entries.append({
                "page_id": data['page_id'],
                "latest_node_id": data['node_id'],
                "score": pagerank_scores.get(page_path, 0)
            })

        # 4. POST to the evaluation endpoint
        try:
            payload = {"entries": entries}
            async with session.post("http://localhost:3000/evaluate", json=payload) as response:
                result = await response.json()
                print(f"EVALUATION RESULT (at {time.time() - start_time:.2f}s):")
                print(result)
        except Exception as e:
            print(f"Evaluator error: {e}")


# --- Main Function to Start Everything ---
async def main():
    global start_time
    
    async with aiohttp.ClientSession() as session:
        # 1. Make the VERY FIRST visit to start the 60s timer
        print("Making first visit to start 60s window...")
        try:
            async with session.get("http://localhost:3000/") as response:
                html = await response.text()
                start_time = time.time() # Timer starts NOW
                total_visits = 1

                # Parse this first page
                page_data = parse_page(html)
                page_graph['/'] = page_data
                visited_pages.add('/')
                for link in page_data['outgoing_links']:
                    await crawl_queue.put(link)

        except Exception as e:
            print(f"Failed to start: {e}")
            return
            
        print("--- Bot Started. Running for 60 seconds... ---")
        
        # 2. Start the two tasks
        crawler = asyncio.create_task(crawler_task(session))
        evaluator = asyncio.create_task(evaluator_task(session))
        
        # 3. Wait for them to finish
        await asyncio.gather(crawler, evaluator)

if __name__ == "__main__":
    asyncio.run(main())