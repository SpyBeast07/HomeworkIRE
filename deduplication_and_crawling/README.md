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

### **Activity 2.2 — Crawling (v1.2 - Update Synchronization)**

You are given a **web-server** running locally. Each page reports a unique `page_id`, a `node_id` that updates at specific intervals, and a full history of previous updates.

**Task:**
Crawl the website and implement a "Smart Crawler" that models the update frequency of each node. The goal is **synchronization**: visiting a node immediately after it updates.

**Evaluation Criteria:**
1.  **5-Minute Window:** The bot must run for 300 seconds.
2.  **Custom Metric:** Instead of simple staleness, you must minimize the **Sum of Squared Lengths** of contiguous events.
    * *Ideal:* Update ($u$), Visit ($v$), Update ($u$), Visit ($v$). Streak lengths are 1. Score = $1.0$.
    * *Bad:* Update ($u$), Visit ($v$), Visit ($v$), Visit ($v$). Streak of 3 visits ($3^2 = 9$ penalty).
3.  **Constraint:** Minimize the metric by avoiding redundant visits ("spamming") and avoiding missed updates ("lazy").

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

## Activity 2.2: Crawling Summary (Metric: Update Synchronization)

### Goal
The assignment criteria shifted from maximizing freshness to **synchronizing visits with node updates**. The goal was to minimize a custom metric: the **Sum of Squared Lengths** of contiguous update ($u$) and visit ($v$) events.
* *Ideal Scenario:* $u, v, u, v$ (Streak lengths of 1). Metric = $1.0$.
* *Bad Scenario:* $u, u, u, v, v$ (Streaks of 3 and 2). Metric increases exponentially ($3^2 + 2^2$).

### Approach: The "Smart Predictive" Bot
To minimize this metric, I moved away from simple looping strategies. I built a **Predictive Bot** using `asyncio` and `aiohttp` that models the behavior of each node.

1.  **Data Gathering:** The bot parses the full HTML history of every node to extract timestamps of all previous updates.
2.  **Modeling:** For each node, it calculates the **Average Update Interval** based on its history.
3.  **Prediction:** It calculates a `Predicted Next Update` time ($T_{last} + Interval_{avg}$).
4.  **Execution:** The bot sits in a loop. It only triggers a visit (`refetch`) if the current time has passed the predicted update time. This ensures we visit *immediately* after an update, breaking the $u$ streak without creating a $v$ streak.
5.  **Safety Net:** If a node has insufficient history, the bot applies a heuristic (max wait time) to ensure data flow isn't completely stalled.

### Key Results
The "Smart Predictive" strategy was highly effective compared to a naive looping strategy.

* **Metric Score:** The bot achieved an average custom metric score of **4.1862**.
    * This indicates that on average, the "streaks" of missed updates or redundant visits were very short (length $\approx \sqrt{4.18} \approx 2$), proving the prediction logic was synchronized with the server's update frequency.
* **Behavior:** The logs showed the bot selectively visiting only 2-4 pages during quiet periods and ramping up activity only when specific update intervals were reached.
* **Final Outcome:** The bot successfully modeled the hidden update parameters of the server nodes, minimized the error metric over the full 5-minute window, and gracefully handled the server shutdown signal.