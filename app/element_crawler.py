import json
import logging
import sqlite3
from urllib.parse import urljoin, urlparse
import bs4
import pandas as pd
import requests

logging.basicConfig(
    level = logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

class ElementCrawler:

    def __init__(self):
        pass