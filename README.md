# Web Crawler

A lightweight, configurable Python web crawler built to discover and inspect websites for specific design elements, embedded tracking/script footprints, and keyword patterns. 

This project was built to automate site classification and extract targeted metadata efficiently, supporting exports to both structured CSV files and a localized SQLite database.

---

## Features

- **Custom Signature Matching:** Search for pages containing specific text keywords, HTML tags/CSS selectors, or third-party JavaScript files (e.g., Google Tag Manager, Shopify assets).
- **Depth-Controlled BFS Crawling:** Uses a Breadth-First Search (BFS) queue to navigate external and internal links up to a configured maximum depth limit.
- **Robust Network Error Handling:** Configured with custom browser headers, strict request timeouts, and error catching for network timeouts or DNS resolution failures.
- **Dual Export Pipeline:** Automatically formats crawl findings and exports records to:
  - **CSV (`crawl_results.csv`)**: For quick inspection and lightweight tabular analysis.
  - **SQLite (`crawl_results.db`)**: For persistent storage with built-in `ON CONFLICT` upsert logic to avoid duplicate URL entries.

---

## Tech Stack

- **Python 3.12+**
- **Dependency Management:** `uv`
- **Networking & Parsing:** `requests`, `BeautifulSoup4` (`bs4`)
- **Data & Storage:** `pandas`, `sqlite3`

---

## Installation & Setup

### 1. Prerequisites
Ensure you have Python 3.12+ and `uv` installed on your machine.

### 2. Clone & Environment Setup
Clone the repository and create a virtual environment:

```bash
git clone https://github.com/your-username/web_crawler.git
cd web_crawler

# Create virtual environment using uv
uv init
uv venv

# Activate virtual environment
source .venv/bin/activate
```

### 3. Install Dependencies
Install the package locally in editable mode:

```bash
uv add pandas
uv add beautifulsoup4
uv pip install -e .
```

---

## Usage

### 1. Configuration
Open `app/element_crawler.py` to define your target signatures and seed URLs:

```python
targets = {
    # Detect specific script footprints
    "scripts": ["googletagmanager.com", "cdn.shopify.com"],
    
    # Target specific UI components or form elements via CSS selectors
    "selectors": ["form[action*='subscribe']", "input[type='email']", ".contact-form"],
    
    # Search for visible page text
    "keywords": ["data engineering", "python"],
}

seed_urls = [
    "https://quotes.toscrape.com/",
]
```

### 2. Run the Crawler
Execute the main crawler script from your terminal:

```bash
python app/element_crawler.py
```

---

## Database Schema (SQLite)

Matches are stored in `crawl_results.db` under the `crawled_sites` table with the following schema:

| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `id` | `INTEGER` | Auto incrementing primary key |
| `url` | `TEXT` | Unique target URL (used for upserts) |
| `depth` | `INTEGER` | Crawl depth level where match was found |
| `matched_features` | `TEXT` | Semicolon separated list of identified targets |
| `timestamp` | `DATETIME` | Auto generated UTC timestamp of insertion |

---

## Project Structure

```text
web_crawler/
├── app/
│   └── element_crawler.py   # Main crawler class, inspection logic, and export routines
├── pyproject.toml           # Project configuration & dependencies
├── README.md                # Project documentation
├── crawl_results.csv        # (Generated) Exported CSV dataset
└── crawl_results.db         # (Generated) Exported SQLite database