# crawler/pagerank.py

import networkx as nx
from typing import Dict

def calculate_pagerank(graph: Dict[str, list]) -> Dict[str, float]:
    """
    Calculates PageRank for a graph using the networkx library.

    Args:
        graph: A dictionary where keys are page_ids and values are
            lists of outgoing page_ids.
            e.g., {'page_A': ['page_B'], 'page_B': ['page_A']}

    Returns:
        A dictionary where keys are page_ids and values are their
        computed PageRank scores.
        e.g., {'page_A': 0.5, 'page_B': 0.5}
    """
    if not graph:
        print("PageRank Warning: Graph is empty.")
        return {}

    # 1. Create a directed graph object
    G = nx.DiGraph()

    # 2. Add all pages (nodes) to the graph.
    # We must add all nodes first, even those with no outgoing links.
    all_pages = set(graph.keys())
    for page_list in graph.values():
        all_pages.update(page_list)
    
    G.add_nodes_from(all_pages)

    # 3. Add all links (edges) to the graph
    for page_id, links in graph.items():
        for link in links:
            if link in all_pages: # Ensure the link is a valid page
                G.add_edge(page_id, link)

    # 4. Calculate PageRank
    #    - alpha is the damping factor (0.85 is standard)
    #    - max_iter stops if it doesn't converge
    #    - tol is the convergence tolerance
    try:
        pagerank_scores = nx.pagerank(G, alpha=0.85, max_iter=100, tol=1.0e-6)
        return pagerank_scores
        
    except nx.exception.NetworkXError as e:
        print(f"PageRank Error: {e}")
        # This can happen if the graph has issues (e.g., all nodes are sinks)
        # In this case, we'll return a uniform distribution.
        if not all_pages:
            return {}
        uniform_score = 1.0 / len(all_pages)
        return {page: uniform_score for page in all_pages}