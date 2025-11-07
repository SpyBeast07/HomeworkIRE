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

### **Activity 2.2 — Crawling**

You are given a **web-server** you can run locally that you can ping to get a page reporting:

- A unique identifier for that page (**page_id**)  
- A **node_id** that updates at unknown time intervals  
- All the previous node IDs and update timestamps for that page  
- A list of all outgoing links from that page  

**Task:**  
Crawl the website, estimate the **page rank** of each of the pages, and **update node IDs** for all pages efficiently, **minimising the number of page visits.**

### **Instructions on Running the Server**

Run the following commands to launch the webserver at:

🔗 **http://localhost:3000**

---

**1. Verify The Image Contents (One Time Operation — Optional, but Recommended)**

```bash
sha256sum -c crawling_assignment-1.0-amd64.tar.sha256
```

**2. Load the Image (One Time Operation)**

```bash
docker load -i crawling_assignment-1.0-amd64.tar
```

**3. Run the Image (Every Time You Restart the Server)**

```bash
docker run --rm -p 3000:3000 --read-only --tmpfs /tmp:rw,noexec,nosuid --cap-drop ALL --security-opt no-new-privileges --pids-limit 128 --memory 256m crawling_assignment:1.0
```

**4. To Stop the Server**

```bash
docker stop <container-id-or-name>
```

## File Structure
```bash
.
├── crawling_server/
│   ├── crawling_assignment-1.0-amd64.tar
│   ├── crawling_assignment-1.0-amd64.tar.sha256
│   └── start_crawler.sh
├── data/
│   └── dedup_data.csv
├── scripts/
│   ├── crawling.ipynb
│   └── dedup_pipeline.ipynb
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

This script will check if the Docker container is running, stopped, or needs to be loaded from the `.tar` file, and will act accordingly.

### 3. Run the Analyses

The main logic for both activities is contained in Jupyter Notebooks (`.ipynb`) inside the `scripts/` folder.

- Run Deduplication:
    - Open `scripts/dedup_pipeline.ipynb`.
    - Run all cells from top to bottom to perform the full analysis, clustering, and evaluation.
- Run Crawling:
    - Open scripts/crawling.ipynb.
    - Ensure the Docker server is running (from Step 2).
    - Run all cells from top to bottom to crawl the site, calculate PageRank, and generate the final revisit priority table.

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

## Activity 2.2: Crawling Summary

### Goal
To crawl the local web server, calculate PageRank, and create an efficient update strategy.

### Approach

* **Discovery & Parsing:** Found that the server only responds with HTML. Used `BeautifulSoup` to parse the HTML and scrape the `page_id`, `node_id`, and outgoing links.
* **Crawling:** Wrote a crawler (using a Breadth-First Search) to visit every page, discovering a total of **14 unique pages**.
* **PageRank:** Used `networkx` to build a directed graph of the 14 pages and calculated the PageRank score for each.
* **Efficient Updates:** Analyzed the `history` of node ID changes for each page to calculate the average time between updates. Combined this "change frequency" score with the PageRank score to create a final `revisit_priority` score.

### Key Results

* **PageRank:** Successfully calculated the importance of all 14 pages.
* **Final Strategy:** Produced a prioritized table of all pages. Pages that are **both important (high PageRank) and change often (high "freshness")** are at the top. This table provides the exact strategy to update node IDs efficiently while minimizing server visits.