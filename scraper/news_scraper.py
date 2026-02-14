import csv
import os
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from readability import Document

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
}


def fetch_html(url):
    try:
        res = requests.get(url, headers=DEFAULT_HEADERS, timeout=20)
        res.raise_for_status()
        return res.text
    except requests.RequestException as exc:
        print(f"Warning: failed to fetch {url}: {exc}")
        return None


def source_label(url):
    netloc = urlparse(url).netloc
    return netloc.replace("www.", "") if netloc else url


def discover_feed_url(page_url):
    html = fetch_html(page_url)
    if not html:
        return None, None

    soup = BeautifulSoup(html, "html.parser")
    feed_links = []

    for link in soup.find_all("link"):
        rel = link.get("rel")
        if isinstance(rel, list):
            rel = " ".join(rel)
        rel = (rel or "").lower()
        link_type = (link.get("type") or "").lower()
        href = link.get("href")
        if not href:
            continue
        if "alternate" in rel and any(x in link_type for x in ("rss", "atom", "xml")):
            feed_links.append(urljoin(page_url, href))

    if not feed_links:
        for link in soup.find_all("a", href=True):
            href = link["href"].lower()
            if "rss" in href or "feed" in href:
                feed_links.append(urljoin(page_url, link["href"]))

    return (feed_links[0] if feed_links else None), html


def parse_feed(xml_text):
    soup = BeautifulSoup(xml_text, "xml")
    items = []

    if soup.find("rss") or soup.find("channel"):
        for item in soup.find_all("item"):
            title = (item.find("title") or {}).get_text(strip=True) if item.find("title") else ""
            link = (item.find("link") or {}).get_text(strip=True) if item.find("link") else ""
            if not link and item.find("guid"):
                link = (item.find("guid") or {}).get_text(strip=True)
            pub_date = (
                (item.find("pubDate") or {}).get_text(strip=True)
                if item.find("pubDate")
                else (item.find("date") or {}).get_text(strip=True) if item.find("date") else ""
            )
            summary = (
                (item.find("description") or {}).get_text(" ", strip=True)
                if item.find("description")
                else ""
            )
            items.append({"title": title, "url": link, "date": pub_date, "summary": summary})

    if not items and soup.find("feed"):
        for entry in soup.find_all("entry"):
            title = (entry.find("title") or {}).get_text(strip=True) if entry.find("title") else ""
            link_tag = entry.find("link", href=True)
            link = link_tag["href"] if link_tag else ""
            published = (
                (entry.find("published") or {}).get_text(strip=True)
                if entry.find("published")
                else (entry.find("updated") or {}).get_text(strip=True) if entry.find("updated") else ""
            )
            summary = (
                (entry.find("summary") or {}).get_text(" ", strip=True)
                if entry.find("summary")
                else (entry.find("content") or {}).get_text(" ", strip=True) if entry.find("content") else ""
            )
            items.append({"title": title, "url": link, "date": published, "summary": summary})

    return items


def parse_article_listing(html_text, base_url):
    soup = BeautifulSoup(html_text, "html.parser")
    articles = []
    for art in soup.find_all("article"):
        title_tag = art.find("h2") or art.find("h3")
        title = title_tag.get_text(strip=True) if title_tag else "No Title"

        date_tag = art.find("time")
        date = date_tag.get_text(strip=True) if date_tag else ""

        content = " ".join([p.get_text(strip=True) for p in art.find_all("p")])

        link_tag = art.find("a", href=True)
        article_url = urljoin(base_url, link_tag["href"]) if link_tag else base_url

        articles.append(
            {"title": title, "url": article_url, "date": date, "summary": content}
        )
    return articles


def extract_article_text(html_text):
    try:
        doc = Document(html_text)
        summary_html = doc.summary(html_partial=True)
    except Exception:
        summary_html = html_text
    soup = BeautifulSoup(summary_html, "html.parser")
    return " ".join(soup.stripped_strings)

def scrape_ai_news(urls, max_per_source=20):
    # Scrapes a list of news section URLs, discovers RSS/Atom when possible,
    # and saves results to CSV with extracted article text.
    os.makedirs("output/datasets", exist_ok=True)
    with open("output/datasets/news.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["source", "title", "date", "url", "content"])

        seen_urls = set()
        for source_url in urls:
            source = source_label(source_url)
            feed_url, html = discover_feed_url(source_url)

            items = []
            if feed_url:
                feed_xml = fetch_html(feed_url)
                if feed_xml:
                    items = parse_feed(feed_xml)

            if not items and html:
                items = parse_article_listing(html, source_url)

            if not items:
                print(f"Warning: no items found for {source_url}")
                continue

            for item in items[:max_per_source]:
                article_url = item.get("url") or source_url
                if article_url:
                    article_url = urljoin(source_url, article_url)
                if not article_url or article_url in seen_urls:
                    continue
                seen_urls.add(article_url)

                article_html = fetch_html(article_url)
                content = extract_article_text(article_html) if article_html else ""
                if not content:
                    content = item.get("summary", "")

                writer.writerow(
                    [
                        source,
                        item.get("title") or "No Title",
                        item.get("date") or "",
                        article_url,
                        content,
                    ]
                )
