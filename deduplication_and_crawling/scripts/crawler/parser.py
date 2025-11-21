# crawler/parser.py

from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import re
from datetime import datetime, timezone

def parse_page(html_content: str) -> Optional[Dict]:
    """
    Parses HTML to extract page_id, node_id, links, AND update history.
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')

        # 1. Page ID
        page_id_tag = soup.find('div', class_='page-id')
        if not page_id_tag: return None
        page_id = page_id_tag.text.split(':')[-1].strip()

        # 2. Node ID
        node_id_tag = soup.find('span', class_='node-id')
        if not node_id_tag or not node_id_tag.b: return None
        node_id = node_id_tag.b.text.strip()

        # 3. Links
        links_list = []
        links_table = soup.find('table', class_='files-table')
        if links_table:
            all_a_tags = links_table.find_all('a', href=True)
            for a_tag in all_a_tags:
                href = a_tag['href'].strip().strip('/')
                if href: links_list.append(href)

        # 4. History (Timestamps) - CRITICAL FOR NEW METRIC
        history_timestamps = []
        
        # A. Current timestamp
        last_updated_span = soup.find('span', class_='last-updated')
        if last_updated_span:
            text = last_updated_span.text
            # Regex to find YYYY-MM-DD HH:MM:SS
            match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', text)
            if match:
                dt = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
                history_timestamps.append(dt.replace(tzinfo=timezone.utc).timestamp())

        # B. Past history
        details = soup.find('details')
        if details:
            history_divs = details.find_all('div')
            for div in history_divs:
                match = re.search(r'\((\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) UTC\)', div.text)
                if match:
                    dt = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
                    history_timestamps.append(dt.replace(tzinfo=timezone.utc).timestamp())

        history_timestamps.sort() # Oldest first

        return {
            'page_id': page_id,
            'node_id': node_id,
            'links': links_list,
            'history': history_timestamps 
        }

    except Exception as e:
        print(f"Error parsing HTML: {e}")
        return None