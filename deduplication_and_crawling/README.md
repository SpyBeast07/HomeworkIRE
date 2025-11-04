# 🧩 Deduplication and Crawling Assignment

This assignment is divided into two activities:

---

## **Activity 2.1 — Deduplication**

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

---

## **Activity 2.2 — Crawling**

You are given a **web-server** you can run locally that you can ping to get a page reporting:

- A unique identifier for that page (**page_id**)  
- A **node_id** that updates at unknown time intervals  
- All the previous node IDs and update timestamps for that page  
- A list of all outgoing links from that page  

**Task:**  
Crawl the website, estimate the **page rank** of each of the pages, and **update node IDs** for all pages efficiently, **minimising the number of page visits.**

---

### **Additional Details**

We will be incrementally rolling out updated versions of the web-server and instructions to use the web server.  

As a test, we have attached a **Docker image (.tar file)** for amd64 systems that you can load and run to launch a web server at **port 3000**.  
We have also attached a **README.md** that contains commands for launching the server.  

> ⚠️ This is not the final version of the web server and may have bugs.  
> Please reach out to the TAs by replying to the announcement thread on **Moodle** in case of any issues.

---

## **Instructions on Running the Server**

Run the following commands to launch the webserver at:

🔗 **http://localhost:3000**

---

### **1. Verify The Image Contents (One Time Operation — Optional, but Recommended)**

```bash
sha256sum -c crawling_assignment-1.0-amd64.tar.sha256
```

### **2. Load the Image (One Time Operation)

```bash
docker load -i crawling_assignment-1.0-amd64.tar
```

### **3. Run the Image (Every Time You Restart the Server)

```bash
docker run --rm -p 3000:3000 --read-only --tmpfs /tmp:rw,noexec,nosuid --cap-drop ALL --security-opt no-new-privileges --pids-limit 128 --memory 256m crawling_assignment:1.0
```

### **4. To Stop the Server

```bash
docker stop <container-id-or-name>
```
