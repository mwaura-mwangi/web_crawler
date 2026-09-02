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
├── LICENSE                  # Project license
├── README.md                # Project documentation
├── crawl_results.csv        # (Generated) Exported CSV dataset
└── crawl_results.db         # (Generated) Exported SQLite database
```

# Building a Standalone Executable with PyInstaller

You can bundle your desktop GUI application into a single standalone executable file using **PyInstaller**. This allows anyone to run your application without needing Python installed on their system.

---

## 1. Install PyInstaller

Ensure your virtual environment is activated, then install `pyinstaller` using `uv`:

```bash
uv pip install pyinstaller
```

---

## 2. Generate the Standalone Executable

Run PyInstaller targeting your `gui.py` entry point:

```bash
pyinstaller --noconfirm --onedir --windowed --name "WebCrawlerApp" app/gui.py
```

### Options Explained:
- `--windowed` (`-w`): Hides the black terminal/console window so only the Tkinter window appears.
- `--onedir` (`-D`): Packages the app into a clean directory structure (faster startup time). If you prefer a **single file**, replace `--onedir` with `--onefile` (`-F`).
- `--name "WebCrawlerApp"`: Sets the executable binary name.

---

## 3. Include Dependencies & Files

If PyInstaller needs explicit module hints or if you want to include default configuration files, you can build using PyInstaller's spec file.

Generate and run with a spec file:

```bash
pyi-makespec --windowed --name "WebCrawlerApp" app/gui.py
pyinstaller WebCrawlerApp.spec
```

---

## 4. Output Location

Once compilation finishes, your executable will be located in the `dist/` directory:

```text
web_crawler/
├── dist/
│   └── WebCrawlerApp/       <-- Executable package folder
│       └── WebCrawlerApp    <-- Binary executable file
├── build/                   <-- Temporary build artifacts (can be deleted)
└── WebCrawlerApp.spec       <-- PyInstaller build configuration
```

To test running your compiled GUI executable from terminal:

```bash
./dist/WebCrawlerApp/WebCrawlerApp
```


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.