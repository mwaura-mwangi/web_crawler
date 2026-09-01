import json
import logging
import sqlite3
from urllib.parse import urljoin, urlparse
import bs4
import pandas as pd
import requests

# configure logging to display real time status updates in the terminal
# helps track which URLs are being fetched and when matches are found
logging.basicConfig(
    level = logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

class ElementCrawler:

    def __init__(self, target_elements=None, max_depth=1, timeout=5):
        """
        Initializes crawler settings, target criteria, and tracking states.
        :param target_elements: Dict defining scripts, selectors, or keywords
        to search for.
        :param max_depth: How many link clicks deep to crawl away from seed URLs
        (0 = seed page only).
        :param timeout: Seconds to wait for a website to respond before
        giving up.
        """
        # Store criteria (fallback to empty dict if None is passed)
        self.target_elements = target_elements or {}
        self.max_depth = max_depth
        self.timeout = timeout

        # Maintain a set of visited URLs to avoid infinite loops across duplicate links
        self.visited = set()

        # Modern User-Agent header makes the crawler look like a standard web browser
        # instead of a basic script (which many sites block immediately)
        self.headers = {
            "User-Agent":(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                "AppleWebKit/537.36 (KHTML, like Gecko)"
                "Chrome/120.0.0 Safari/537.36"
            )
        }


    def fetch_page(self, url):
        """
        Sends an HTTP GET request to retrieve the raw HTML code of a webpage.

        Returns string HTML on success, or None on error.
        """
        try:
            # Issue request using custom headers and set a strict timeout limit
            response = requests.get(
                url, headers = self.headers, timeout = self.timeout
            )

            # HTTP 200 OK indicates the request succeeded and content was returned
            if response.status_code == 200:
                return response.text
        except requests.RequestException as e:
            # Catch network errors (DNS issues, timeouts, connection drops) gracefully
            logging.warning(f"failed to fetch {url}: {e}")
        return None


    def inspect_page(self, html, url):
        """
        Parses HTML DOM tree using BeautifulSoup and checks for target

        signatures: keywords, CSS selectors, and script references.
        """
        # Parse raw HTML text into a searchable Document Object Model (DOM) tree
        soup = bs4.BeautifulSoup(html, "html.parser")
        matches = []

        # 1. Check for Keywords
        if "keywords" in self.target_elements:
            # Extract pure visible text from the page and convert to lowercase for case-insensitive matching
            page_text = soup.get_text().lower()

            # Find which of the user-provided target keywords exist in the page body
            found_words = [
                word
                for word in self.target_elements["keywords"]
                if word.lower() in page_text
            ]

            if found_words:
                matches.append(f"keywords found: {', '.join(found_words)}")


        # 2. Check for CSS Selectors / Tags
        if "selectors" in self.target_elements:
            for selector in self.target_elements["selectors"]:
                # soup.select() runs a standard CSS selector query against the DOM structure.
                # If matching elements are returned, the feature exists on this page.
                if soup.select(selector):
                    matches.append(f"selector found: '{selector}'")

        # 3. Check for Scripts / Services
        if "scripts" in self.target_elements:
            # Gather all external script URLs (<script src="...">)
            scripts = [
                s.get("src", "")
                for s in soup.find_all("scripts")
                if s.get("src")
            ]
            # Gather all inline script content (<script>/* code */</script>)
            script_text = "".join([s.text for s in soup.find_all("scripts")])

            for script_pattern in self.target_elements["scripts"]:
                # Check if target pattern matches any external script URL OR inline code snippet
                if any(
                    script_pattern in src for src in scripts
                ) or(script_pattern in script_text):
                    matches.append(f"Script detected: '{script_pattern}'")

        # Return both the matched criteria list and the parsed DOM tree (used for link extraction)
        return matches, soup


    def crawl(self, start_urls):
        """
        Controls the crawl workflow: processes queue items, fetches content,

        runs inspection checks, and discovers new links.
        """
        results = []

        for start_url in start_urls:
            # Breadth-First Search (BFS) Queue storing tuples of: (URL_to_visit, current_depth)
            queue = [(start_url, 0)]

            while queue:
                # Pop the first element from the front of the queue
                url, depth = queue.pop(0)

                # Skip URLs that have already been crawled or exceed configured depth limits
                if url in self.visited or depth > self.max_depth:
                    continue

                # Record URL as visited immediately to prevent duplicate work
                self.visited.add(url)
                logging.info(f"Crawling [Depth {depth}]: {url}")

                # Download the target page HTML
                html = self.fetch_page(url)
                if not html:
                    continue

                # Run feature detection rules against downloaded page content
                matches, soup = self.inspect_page(html, url)

                # Save metadata record if any specified criteria matched on this page
                if matches:
                    results.append(
                        {
                            "url":url,
                            "depth": depth,
                            "matched_features": "; ".join(matches),
                        }
                    )

                    logging.info(f"Match identified on {url}")

                # Find child links to extend crawl traversal
                if depth < self.max_depth:
                    # Look for all anchor tags with valid href targets (<a href="...">)
                    for tag in soup.find_all("a", href=True):
                        # Resolve relative paths ('/about') into absolute links ('https://domain.com/about')
                        link = urljoin(url, tag["href"])
                        parsed_link = urlparse(link)

                        # Enforce standard web protocols (http/https) and skip previously processed URLs
                        if (
                            parsed_link.scheme in ["http", "https"]
                            and link not in self.visited

                        ):
                            
                            # Append discovered link onto crawl queue incrementing current depth
                            queue.append((link, depth + 1))

        return results

# Export csv using pandas
def export_to_csv(results, filename="crawl_results.csv"):
    """Save structured crawl results to a csv file"""
    if not results:
        logging.info("No crawl results to export to csv.")
        return
    df = pd.DataFrame(results)
    df.to_csv(filename, index=False)
    logging.info(f"Successfully exported {len(results)} records to {filename}")


# Export sqlite database using sqlite3
def export_to_sqlite(results, db_name="crawl_results.db", table_name="crawled_sites"):
    """Saves structured crawl results to a SQLite database table."""
    if not results:
        logging.info("No crawl results to export to SQLite.")
        return

    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # create target table if it doesnt already exist
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE,
        depth INTEGER,
        matched_features TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
""")

    # insert new rows, updates existing ones if url exists
    for record in results:
        cursor.execute(f"""
            INSERT INTO {table_name}(url, depth, matched_features)
            VALUES (?, ?, ?)
            ON CONFLICT (url) DO UPDATE SET
                depth = excluded.depth,
                matched_features = excluded.matched_features
        """, 
            (record["url"], record["depth"], record["matched_features"]))

    conn.commit()
    conn.close()
    logging.info(f"Successfully saved {len(results)} records to SQLite database {db_name} (Table: '{table_name}')")


# Main script entry point
if __name__ == "__main__":

    # Define target search criteria for site inspection
    targets = {
        # Scripts to look for (Google Tag Manager, Shopify assets, etc.)
        "scripts": ["googletagmanager.com", "cdn.shopify.com"],
        # CSS selectors to search for (contact forms, email input fields, class names)
        "selectors": [
            "form[action*='subscribe']", 
            "input[type='email']",
            ".contact-form",
            ],
        # Keywords to locate anywhere in plain page body text    
        "keywords": ["data engineering", "python"],
    }

    # Seed list of domains where crawling begins
    seed_urls = [
        "https://quotes.toscrape.com"
    ]

    # Initialize crawler with defined target elements and set depth traversal limit
    crawler = ElementCrawler(target_elements=targets, max_depth=1)
    found_sites = crawler.crawl(seed_urls)


    # export crawl findings to both destinations
    export_to_csv(found_sites, filename="crawl_results.csv")
    export_to_sqlite(found_sites, db_name="crawl_results.db")