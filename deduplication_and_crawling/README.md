# Assignment 2: Deduplication and Crawling

This project contains the complete solution for the two-part assignment:
* **Deduplication:** Identifying and grouping duplicate records from a noisy CSV file.
* **Crawling:** Crawling a local web server, calculating PageRank, and developing an efficient update strategy.

---

## 🧩 About Assignment

This assignment is divided into two activities:

### **Activity 2.1 — Deduplication**

Attached is a small data set (**dedup_data.csv**) with about **5K entries**, each of which contains details of synthetically generated persons:

- `given_name`  
- `surname`  
- `street_number`  
- `address_1`  
- `address_2`  
- `suburb`  
- `postcode`  
- `state`  
- `date_of_birth`  
- `soc_sec_id`  

Each entry is uniquely identified by the **id** column.  
There are potentially multiple entries of the same (generated) person, each with some variations in the entered details due to reporting noise and errors.  

**Task:**  
Identify all the different records of the same person and group all those records.

### **Activity 2.2 — Crawling (v1.2)**

You are given a **web-server (v1.2)** you can run locally that you can ping to get a page reporting:

* A unique identifier for that page (**page\_id**)
* A **node\_id** that updates at unknown time intervals
* All the previous node IDs and update timestamps for that page
* A list of all outgoing links from that page

**Task:**
Crawl the website, estimate the **page rank** of each of the pages, and **update node IDs** for all pages efficiently, **minimising the number of page visits** and **node staleness**.

This new version (v1.2) has strict evaluation criteria:
1.  **60-Second Window:** A timer starts on the first-ever visit to the server.
2.  **15-Second Submissions:** You must `POST` an evaluation to `/evaluate` within the first 15 seconds, and then again at least every 15 seconds.
3.  **New Metrics:** You are graded on a balance of:
    * `mse` (PageRank accuracy)
    * `coverage` (Percentage of graph discovered)
    * `avg_staleness` (How old your `node_id`s are)
    * `visit_count` (How many pages you hit)
4.  **Final Output:** The bot must run until the server returns an "evaluation ended" error, which triggers the server to generate a final `evaluation.bin` file for submission.

---

## Instructions on Running the Server (v1.2)

Run the following commands to launch the webserver at:

🔗 **http://localhost:3000**

**1. Verify The Image Contents (One Time Operation — Optional, but Recommended)**

```bash
sha256sum -c crawling_assignment-1.2-amd64.tar.sha256
```

**2. Load the Image (One Time Operation)**

```bash
docker load -i crawling_assignment-1.2-amd64.tar
```

**3. Run the Image (Every Time You Restart the Server)**

```bash
# This command must be run from the project's root directory
# to mount the './data' folder correctly.
docker run --rm -p 3000:3000 -v "$(pwd)/data:/data" --tmpfs /tmp:rw,noexec,nosuid --cap-drop ALL --security-opt no-new-privileges --pids-limit 128 --memory 256m crawling_assignment:1.2
```

**4. To Stop the Server**

```bash
docker stop <container-id-or-name>
# Or use the name from the 'start_crawler.sh' script:
docker stop crawling_server
```

## File Structure
```bash
.
├── crawling_server/
│   ├── crawling_assignment-1.0-amd64.tar
│   ├── crawling_assignment-1.0-amd64.tar.sha256
│   ├── crawling_assignment-1.2-amd64.tar
│   ├── crawling_assignment-1.2-amd64.tar.sha256
│   └── start_crawler.sh
├── data/
│   ├── dedup_data.csv
│   └── evaluation.bin      <-- CRAWLER OUTPUT APPEARS HERE
├── scripts/
│   ├── bot
│   ├── crawling_1.0.ipynb
│   ├── dedup_pipeline.ipynb
│   └── crawler/
│       ├── __init__.py
│       ├── main.py         <-- THE MAIN BOT RUNNER
│       ├── crawler.py      <-- Async crawler class
│       ├── parser.py       <-- HTML parser
│       ├── pagerank.py     <-- PageRank calculator
│       ├── evaluator.py    <-- /evaluate submission logic
│       └── utils.py        <-- Constants
├── .gitignore
├── Report.pdf
└── requirements.txt
```

## How to Run

### 1. Requirements

Install the required Python libraries. It's recommended to create a `requirements.txt` file with the following content and run `pip install -r requirements.txt`.

**`requirements.txt`:**
```bash
pandas
recordlinkage
jellyfish
networkx
scikit-learn
requests
beautifulsoup4
jupyter
aiohttp
nest_asyncio
```

Run:
```bash
pip install -r requirements.txt
```

### 2. Start the Crawling Server

The crawling server must be running to execute the second part of the assignment.

```bash
# Navigate to the server directory
cd crawling_server

# Make the script executable
chmod +x start_crawler.sh

# Run the script to start the server
./start_crawler.sh
```

This script handles all Docker operations for you.

### 3. Run the Analyses

- Run Deduplication (Activity 2.1):
    - Open `scripts/dedup_pipeline.ipynb`.
    - Run all cells from top to bottom to perform the full analysis, clustering, and evaluation.
- Run Crawling (Activity 2.2):
    - CRITICAL: You must restart the crawling server (Step 2) every time you want to run the bot. The server's 60-second timer starts on the first visit and does not reset.
    - From the project's root directory (e.g., `deduplication_and_crawling/`), run the main bot:
    ```bash
    python3 -m scripts.crawler.main
    ```
    - The bot will run for ~87 seconds, printing its status for each 14.5-second submission, until the server cuts it off.
    - Once finished, the final `evaluation.bin` file will be in the `data/` folder.

---

## Activity 2.1: Deduplication Summary

### Goal
To find and group all records belonging to the same person from `dedup_data.csv`.

### Approach
Pipeline used:

* **EDA:** Inspected the data to find missing values, incorrect types (`date_of_birth` as a float), and typos (e.g., 'nsw' vs 'nws').
* **Preprocessing:** Cleaned and standardized the data. Fixed typos, converted dates to 'YYYY-MM-DD' strings, and padded postcodes with zeros.
* **Blocking:** Grouped records by `postcode` to reduce the 12.5 million potential comparisons.
* **Comparison:** Used `recordlinkage` to score the similarity of names, addresses, and dates for all pairs within a block.
* **Decision & Clustering:** Set a threshold (score >= 4.0 out of 5.0) to classify a pair as a "match." Used `networkx` to group all matches into clusters.
* **Evaluation:** Used the `soc_sec_id` column as the "answer key" to validate the results.

### Key Results

* **Blocking:** Reduced comparisons by **99.87%**, from 12.5 million to just 16,115.
* **Accuracy:** The algorithm's 1,059 clusters were compared against the 2,291 true clusters, achieving an **Adjusted Rand Score (ARS) of 0.7307**, indicating a strong and successful result.

---

## Activity 2.2: Crawling Summary (v1.2)

### Goal
To build a bot that runs for a 60-second window, submits its findings every ~14.5 seconds, and generates a final `evaluation.bin` file. The bot was optimized to achieve high `coverage`, low PageRank `mse`, and low `avg_staleness` without an excessive `visit_count`.

### Approach: The "Optimal Staleness" Bot
The final bot (`v1.2 - Optimal Staleness`) was built using `asyncio` and `aiohttp` and follows a precise strategy:

1.  **Phase 1: Initial Fast Crawl (t=0s to t=1.2s)**
    * The bot starts its 60-second timer by probing the server.
    * It immediately performs a high-speed asynchronous **Breadth-First Search (BFS)** to discover the entire 50+ page graph in **~1.22 seconds**.
    * This initial crawl gathers the graph structure and the first set of `node_id`s.

2.  **Phase 2: First Submission (t=1.22s)**
    * Immediately after the crawl, the bot calculates PageRank on the discovered graph.
    * It submits the first evaluation, achieving near-perfect `mse` and `coverage`.

3.  **Phase 3: Main Evaluation Loop (t=1.22s to t=85s)**
    * The bot enters a `while True` loop that orchestrates a "sleep-then-crawl" cycle.
    * **Sleep:** After submitting, the bot sleeps for ~11-13 seconds.
    * **Re-crawl:** It wakes up *just before* the next 14.5s deadline and performs a **full re-crawl** of all 50+ pages. This takes ~1.5-2.0 seconds.
    * **Submit:** With brand-new `node_id`s, it calculates PageRank and submits the evaluation right on time.
    * **Repeat:** This cycle repeats, ensuring that every submission's `node_id`s are only ~1.5-2.0 seconds old, keeping staleness exceptionally low.

4.  **Phase 4: Shutdown (t=85s)**
    * The bot continues this loop, submitting 6 valid evaluations.
    * On the 7th attempt (at `t=85.00s`), the server responds with `"Evaluation window has ended."`
    * The bot catches this error, shuts down gracefully, and the server generates the `evaluation.bin` file.

### Key Results
The bot ran perfectly, achieving excellent and well-balanced scores. The log from the final run shows the strategy was successful:

* **MSE (Accuracy):** `1.12e-07` (Near-perfect PageRank calculation).
* **Coverage:** `96.2%` (Discovered 50 out of 52 pages on the first pass).
* **Staleness:** The "Optimal Staleness" strategy worked perfectly.
    * *Submission 1 (t=1.22s):* `1430 ms`
    * *Submission 2 (t=12.50s):* `6451 ms`
    * *Submission 3 (t=27.00s):* `10703 ms`
    * The staleness remained low and stable, proving the "sleep-then-crawl" logic was far superior to the "crawl-then-sleep" logic which resulted in staleness exploding to 58,000+ ms.
* **Visits:** The bot made a total of `252` valid visits by the final valid submission (t=56.00s), demonstrating an efficient balance between visit count and staleness.
* **Final Outcome:** The bot successfully completed its full lifecycle and triggered the generation of the `evaluation.bin` file for submission.