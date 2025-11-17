# crawler/parser.py

from bs4 import BeautifulSoup
from typing import Dict, List, Optional

def parse_page(html_content: str) -> Optional[Dict[str, str | List[str]]]:
    """
    Parses the HTML content of a v1.2 crawler page.
    This version looks for the new tags found in the server HTML.

    Args:
        html_content: The raw HTML text.

    Returns:
        A dictionary containing parsed data or None if parsing fails.
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')

        # --- Extract Page ID ---
        # Find: <div class="page-id">Page ID: page_gnb58c5k</div>
        page_id_tag = soup.find('div', class_='page-id')
        if not page_id_tag:
            print("Error: Could not find 'div.page-id' tag.")
            return None
        page_id = page_id_tag.text.split(':')[-1].strip()

        # --- Extract Node ID ---
        # Find: <span class="node-id">Node ID: <b>d65qjg5idtzb</b></span>
        node_id_tag = soup.find('span', class_='node-id')
        # We must also find the <b> tag *inside* it
        if not node_id_tag or not node_id_tag.b:
            print("Error: Could not find 'span.node-id' or 'b' tag inside it.")
            return None
        node_id = node_id_tag.b.text.strip()

        # --- Extract Outgoing Links ---
        # Find: <table class="files-table"> ... <a href="/page_...">
        links_list = []
        links_table = soup.find('table', class_='files-table')
        
        if links_table:
            # Find all <a> tags that have an 'href' attribute
            all_a_tags = links_table.find_all('a', href=True)
            for a_tag in all_a_tags:
                href = a_tag['href']
                # Clean the link: strip all whitespace, then strip leading/trailing slashes
                cleaned_link = href.strip().strip('/')
                if cleaned_link: # Ensure it's not an empty string
                    links_list.append(cleaned_link)
        
        # All data has been found
        return {
            'page_id': page_id,
            'node_id': node_id,
            'links': links_list
        }

    except Exception as e:
        print(f"An error occurred during parsing: {e}")
        return None