
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import html
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "data" / "state.json"

QUERIES = [
    "specialty coffee shop operations problems",
    "coffee shop opening closing checklist template",
    "specialty cafe staff training operations",
    "cafe shift handover software",
    "restaurant shift handover app",
    "hospitality staff communication shift log",
]

def clean_text(value):
    value = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", html.unescape(value)).strip()

def collect_news(query):
    params = urlencode({
        "q": query,
        "hl": "en-US",
        "gl": "US",
        "ceid": "US:en",
    })
    url = "https://news.google.com/rss/search?" + params
    request = Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 DigitalIncomeAgent/1.0"}
    )

    with urlopen(request, timeout=20) as response:
        root = ET.fromstring(response.read())

    results = []
    for item in root.findall(".//item")[:5]:
        results.append({
            "title": clean_text(item.findtext("title")),
            "link": item.findtext("link"),
            "published": item.findtext("pubDate"),
            "description": clean_text(item.findtext("description")),
            "query": query,
        })
    return results

def main():
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)

    if STATE_PATH.exists():
        state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    else:
        state = {"agent_name": "Digital Income Agent", "run_count": 0}

    now = datetime.now(timezone.utc).isoformat()
    collected = []
    errors = []

    for query in QUERIES:
        try:
            collected.extend(collect_news(query))
            print("Collected:", query)
        except Exception as error:
            errors.append({"query": query, "error": str(error)})
            print("Search failed:", query, str(error))

    existing = state.get("research_items", [])
    known_links = {item.get("link") for item in existing}

    new_items = []
    for item in collected:
        if item.get("link") and item["link"] not in known_links:
            new_items.append(item)
            known_links.add(item["link"])

    state["run_count"] = state.get("run_count", 0) + 1
    state["status"] = "research_ok" if collected else "research_partial"
    state["last_run_utc"] = now
    state["research_last_run_utc"] = now
    state["research_queries"] = QUERIES
    state["research_new_items"] = len(new_items)
    state["research_errors"] = errors
    state["research_items"] = (new_items + existing)[:100]

    STATE_PATH.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )

    print("Digital Income Agent: research run complete")
    print("New articles:", len(new_items))
    print("Total stored:", len(state["research_items"]))
    print("Errors:", len(errors))

if __name__ == "__main__":
    main()
