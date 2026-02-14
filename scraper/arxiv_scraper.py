import csv
import os
import xml.etree.ElementTree as ET

import requests

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
}

def scrape_arxiv(category="cs.AI", max_results=50):
    # scrapes arXiv papers from a given category
    url = (
        "https://export.arxiv.org/api/query"
        f"?search_query=cat:{category}&start=0&max_results={max_results}"
    )

    os.makedirs("output/datasets", exist_ok=True)
    with open("output/datasets/arxiv.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["title", "authors", "summary", "published", "link"])

        try:
            res = requests.get(url, headers=DEFAULT_HEADERS, timeout=20)
            res.raise_for_status()
            root = ET.fromstring(res.text)
        except requests.RequestException as exc:
            print(f"Warning: failed to fetch arXiv feed: {exc}")
            return
        except ET.ParseError as exc:
            print(f"Warning: failed to parse arXiv feed: {exc}")
            return

        for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
            title = entry.find("{http://www.w3.org/2005/Atom}title").text.strip()
            authors = ", ".join([a.find("{http://www.w3.org/2005/Atom}name").text for a in entry.findall("{http://www.w3.org/2005/Atom}author")])
            summary = entry.find("{http://www.w3.org/2005/Atom}summary").text.strip()
            published = entry.find("{http://www.w3.org/2005/Atom}published").text
            link = entry.find("{http://www.w3.org/2005/Atom}id").text
            writer.writerow([title, authors, summary, published, link])
