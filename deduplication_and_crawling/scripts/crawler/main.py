import asyncio
import aiohttp
import time
import json
from .crawler import Crawler
from .pagerank import calculate_pagerank
from .evaluator import format_payload, submit_evaluation
from .utils import BASE_URL, EVALUATION_WINDOW_SECONDS, SUBMISSION_INTERVAL_SECONDS

class Bot:
    """
    The main bot orchestrator.
    v1.2: Optimized for low staleness. Sleeps *first*, then
    re-crawls *just before* submitting.
    """
    def __init__(self, start_page="/"):
        self.start_url = f"{BASE_URL}{start_page}"
        self.start_time = 0.0
        
        self.crawler = Crawler(start_page=start_page)
        self.pagerank_scores = {}

    async def run(self):
        print(f"--- 🤖 CRAWLING BOT ACTIVATED (v1.2 - Optimal Staleness) ---")
        print(f"Target: {BASE_URL}")
        print(f"Submitting every {SUBMISSION_INTERVAL_SECONDS}s until server cutoff.")
        print("="*40)
        
        async with aiohttp.ClientSession() as session:
            # --- START THE TIMER ---
            try:
                print("Probing server to start 60s timer...")
                async with session.get(self.start_url, timeout=5) as response:
                    response.raise_for_status()
                self.start_time = time.time()
                self.crawler.start_time = self.start_time 
                self.crawler.session = session # Give session to crawler
                print(f"Timer started at {time.strftime('%H:%M:%S')}. Window ends at t+60s.")
            except Exception as e:
                print(f"❌ CRITICAL ERROR: Could not connect to {self.start_url}.")
                return

            # --- 1. INITIAL FULL CRAWL ---
            print("\n--- [PHASE 1] Starting initial full graph crawl... ---")
            await self.crawler.crawl()
            print(f"--- [PHASE 1] Initial crawl complete. Found {len(self.crawler.graph)} pages.")
            
            # --- 2. MAIN EVALUATION LOOP ---
            print("\n--- [PHASE 2] Entering main evaluation loop... ---")
            submission_count = 0
            
            while True:
                submission_count += 1
                elapsed = time.time() - self.start_time
                
                print(f"\n--- Running Submission {submission_count} (t={elapsed:.2f}s) ---")
                
                # --- THIS IS THE NEW LOGIC (Staleness Fix) ---
                if submission_count > 1:
                    # This is not the first submission, so we need to re-crawl
                    # to get fresh data *before* this submission.
                    
                    # We'll aim to finish re-crawling just before submission
                    # A full re-crawl takes ~1.5-2.0s.
                    
                    print(f"  Re-crawling all {len(self.crawler.graph)} pages for fresh nodes...")
                    
                    all_pages = list(self.crawler.graph.keys())
                    for page_path in all_pages:
                        await self.crawler.refetch(page_path)
                        # Add a tiny sleep to be nice to the server
                        await asyncio.sleep(0.01)
                    
                    print(f"  Re-crawl complete. New visit count (bot-side): {self.crawler.total_visits}")

                # 1. (Re)Calculate PageRank
                print("  [1/3] Calculating PageRank...")
                self.pagerank_scores = calculate_pagerank(self.crawler.graph)
                
                # 2. Format Payload
                print("  [2/3] Formatting payload...")
                payload = format_payload(self.crawler.node_data, self.pagerank_scores)
                
                # 3. Submit Evaluation
                print("  [3/3] Submitting to /evaluate...")
                response = await submit_evaluation(session, payload)
                
                print("\n  --- Server Response ---")
                print(f"  MSE:      {response.get('mse')}")
                print(f"  Coverage: {response.get('coverage')}")
                print(f"  Staleness: {response.get('avg_staleness')}")
                print(f"  Visits:   {response.get('visit_count')}")
                
                if 'error' in response:
                    print(f"  Error: {response.get('error')}")
                    error_str = str(response.get('error')).lower()
                    if "too late" in error_str or "ended" in error_str:
                        print("  Evaluation window closed by server. Exiting.")
                        break
                
                # --- 3. SLEEP (THE NEW LOGIC) ---
                # Sleep *after* submitting, until it's time to re-crawl
                # for the *next* submission.
                
                next_submission_time = (submission_count * SUBMISSION_INTERVAL_SECONDS)
                
                # We need ~2.0s for the re-crawl + submission
                # So, we'll sleep until (next_submission_time - 2.0s)
                RECRAWL_BUFFER_SECONDS = 2.0
                
                current_elapsed = time.time() - self.start_time
                time_to_wait = (next_submission_time - RECRAWL_BUFFER_SECONDS) - current_elapsed
                
                if time_to_wait > 0:
                    print(f"\n  Sleeping for {time_to_wait:.2f}s...")
                    await asyncio.sleep(time_to_wait)

        print("\n="*40)
        print("--- 🤖 BOT SHUTDOWN COMPLETE ---")
        print(f"Total submissions: {submission_count}")
        print("Your 'evaluation.bin' file should be in the '/data' folder.")


async def main():
    bot = Bot()
    await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown signal received. Exiting.")