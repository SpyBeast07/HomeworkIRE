# crawler/main.py

import asyncio
import aiohttp
import time
import statistics
from .crawler import Crawler
from .pagerank import calculate_pagerank
from .evaluator import format_payload, submit_evaluation
from .utils import BASE_URL, EVALUATION_WINDOW_SECONDS, SUBMISSION_INTERVAL_SECONDS
from .metric import calculate_streak_metric  # Import your custom metric logic

class Bot:
    def __init__(self, start_page="/"):
        self.start_url = f"{BASE_URL}{start_page}"
        self.start_time = 0.0
        self.crawler = Crawler(start_page=start_page)
        # Track when WE visited specific pages
        self.visit_log = {} 

    async def run(self):
        print(f"--- 🤖 SMART BOT ACTIVATED (Metric: Synced Updates) ---")
        print(f"Window: {EVALUATION_WINDOW_SECONDS}s | Interval: {SUBMISSION_INTERVAL_SECONDS}s")
        
        async with aiohttp.ClientSession() as session:
            # Start Timer
            try:
                await session.get(self.start_url)
                self.start_time = time.time()
                self.crawler.start_time = self.start_time 
                self.crawler.session = session
                print(f"Timer started. Running for {EVALUATION_WINDOW_SECONDS}s.")
            except:
                print("❌ Error: Is server running?")
                return

            # 1. Initial Crawl
            print("\n--- [PHASE 1] Discovering Graph... ---")
            await self.crawler.crawl()
            
            # Initialize visit logs for discovered pages
            for page in self.crawler.graph:
                self.visit_log[page] = [time.time()]

            # 2. Main Loop
            submission_count = 0
            while True:
                elapsed = time.time() - self.start_time
                if elapsed > EVALUATION_WINDOW_SECONDS:
                    break

                submission_count += 1
                print(f"\n--- Submission {submission_count} (t={elapsed:.1f}s) ---")

                # A. SMART RE-CRAWL LOGIC
                pages_to_visit = []
                current_time = time.time()

                for page, history in self.crawler.server_update_history.items():
                    my_last_visit = self.visit_log.get(page, [0])[-1]
                    
                    # Strategy: If we don't have enough history, DON'T SPAM.
                    # Visiting too often hurts the score (v,v,v,v -> 4^2=16 penalty).
                    # We assume a safe default update interval (e.g., 45s) if unknown.
                    
                    if len(history) < 2:
                        # Heuristic: Only visit if we haven't visited in 45 seconds
                        if (current_time - my_last_visit) > 45.0:
                            pages_to_visit.append(page)
                        continue

                    # We have history! Predict next update.
                    intervals = [history[i+1] - history[i] for i in range(len(history)-1)]
                    avg_interval = statistics.mean(intervals)
                    
                    last_known_update = history[-1]
                    predicted_next_update = last_known_update + avg_interval
                    
                    # LOGIC: Only visit if we predict a NEW update has happened since our last visit
                    if my_last_visit > last_known_update:
                        # We are current. Has enough time passed for a NEW update?
                        if current_time > predicted_next_update:
                            pages_to_visit.append(page)
                    else:
                        # We are definitely stale! Visit immediately.
                        pages_to_visit.append(page)

                print(f"  Predicting updates... Visiting {len(pages_to_visit)} / {len(self.crawler.graph)} pages.")
                
                # Execute Visits
                for page in pages_to_visit:
                    await self.crawler.refetch(page)
                    if page not in self.visit_log: self.visit_log[page] = []
                    self.visit_log[page].append(time.time())
                    await asyncio.sleep(0.01)

                # B. SUBMIT
                pr_scores = calculate_pagerank(self.crawler.graph)
                payload = format_payload(self.crawler.node_data, pr_scores)
                resp = await submit_evaluation(session, payload)
                
                # Check for Server Stop Signal
                if 'error' in resp and 'ended' in str(resp.get('error')):
                    print("  🛑 Server signal: Window ended.")
                    break

                # C. SLEEP
                next_time = (submission_count * SUBMISSION_INTERVAL_SECONDS)
                sleep_time = next_time - (time.time() - self.start_time)
                if sleep_time > 0:
                    print(f"  Sleeping {sleep_time:.2f}s...")
                    await asyncio.sleep(sleep_time)

        # --- 3. CALCULATE FINAL METRIC ---
        print("\n" + "="*40)
        print("📊 FINAL CUSTOM METRIC REPORT")
        print("="*40)
        
        total_score = 0.0
        node_count = 0
        
        for page in self.crawler.graph:
            u_times = self.crawler.server_update_history.get(page, [])
            v_times = self.visit_log.get(page, [])
            
            # Use your custom metric function
            score = calculate_streak_metric(u_times, v_times)
            total_score += score
            node_count += 1
            
            # Print sample for first few nodes
            if node_count <= 3:
                print(f"Node {page}: Score = {score:.4f} (Updates: {len(u_times)}, Visits: {len(v_times)})")

        if node_count > 0:
            avg_metric = total_score / node_count
            print("-" * 40)
            print(f"⭐ AVERAGE METRIC SCORE: {avg_metric:.4f}")
            print("(Target: As close to 1.0 as possible)")
        else:
            print("No nodes found to calculate metric.")

async def main():
    bot = Bot()
    await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass