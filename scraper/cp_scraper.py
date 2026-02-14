import csv
import os

import requests

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
}

API_URL = "https://codeforces.com/api/problemset.problems"


def scrape_cp_problems(url=None, max_results=500):
    # Scrapes competitive programming problems via the Codeforces API
    try:
        res = requests.get(API_URL, headers=DEFAULT_HEADERS, timeout=20)
        res.raise_for_status()
    except requests.RequestException as exc:
        print(f"Warning: failed to fetch Codeforces problemset API: {exc}")
        return

    try:
        payload = res.json()
    except ValueError as exc:
        print(f"Warning: failed to parse Codeforces API response: {exc}")
        return

    if payload.get("status") != "OK":
        print(f"Warning: Codeforces API error: {payload.get('comment')}")
        return

    problems = payload.get("result", {}).get("problems", [])
    if max_results:
        problems = problems[:max_results]

    os.makedirs("output/datasets", exist_ok=True)
    with open("output/datasets/cp_problems.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["problem_id", "title", "tags", "rating", "url"])

        for problem in problems:
            title = problem.get("name") or "Unknown"
            tags = ", ".join(problem.get("tags", []))
            rating = problem.get("rating", "")
            contest_id = problem.get("contestId")
            index = problem.get("index")
            problem_id = f"{contest_id}{index}" if contest_id and index else title
            problem_url = (
                f"https://codeforces.com/problemset/problem/{contest_id}/{index}"
                if contest_id and index
                else ""
            )
            writer.writerow([problem_id, title, tags, rating, problem_url])
