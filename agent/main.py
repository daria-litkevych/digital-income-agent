from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import html
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "data" / "state.json"
REPORT_PATH = ROOT / "reports" / "latest.md"

SEARCHES = [
    {
        "hypothesis": "cafe_starter_kit",
        "name": "Small Café Manager Starter Kit",
        "query": '"specialty coffee" cafe operations staff training',
        "terms": ["specialty coffee", "coffee shop", "cafe", "barista", "opening checklist", "closing checklist", "staff training", "workflow", "inventory", "waste", "operations", "standard operating procedure", "sop"],
    },
    {
        "hypothesis": "cafe_starter_kit",
        "name": "Small Café Manager Starter Kit",
        "query": '"coffee shop" "daily checklist" OR "opening checklist" OR "closing checklist"',
        "terms": ["coffee shop", "cafe", "checklist", "opening", "closing", "cleaning", "daily", "routine", "manager"],
    },
    {
        "hypothesis": "cafe_starter_kit",
        "name": "Small Café Manager Starter Kit",
        "query": '"specialty cafe" staff retention OR training OR workflow OR inventory',
        "terms": ["specialty cafe", "coffee shop", "barista", "staff", "training", "retention", "workflow", "inventory", "waste", "manager"],
    },
    {
        "hypothesis": "cafe_starter_kit",
        "name": "Small Café Manager Starter Kit",
        "query": 'independent coffee shop owner operational challenges costs labor',
        "terms": ["independent coffee", "coffee shop", "cafe", "owner", "labor", "cost", "margin", "operations", "challenge", "profit"],
    },
    {
        "hypothesis": "shiftbrief_ai",
        "name": "ShiftBrief AI",
        "query": 'restaurant hospitality shift handover log communication software',
        "terms": ["shift handover", "handover", "shift log", "restaurant", "hospitality", "communication", "staff", "logbook", "task"],
    },
    {
        "hypothesis": "shiftbrief_ai",
        "name": "ShiftBrief AI",
        "query": 'hotel restaurant staff shift notes task handoff app',
        "terms": ["shift", "handoff", "handover", "restaurant", "hotel", "staff", "notes", "task", "app", "communication"],
    },
    {
        "hypothesis": "shiftbrief_ai",
        "name": "ShiftBrief AI",
        "query": '"restaurant shift report" OR "daily shift report" software',
        "terms": ["restaurant", "shift report", "daily report", "software", "manager", "team", "task", "communication"],
    },
    {
        "hypothesis": "shiftbrief_ai",
        "name": "ShiftBrief AI",
        "query": 'hospitality operations frontline employee communication shift change problems',
        "terms": ["hospitality", "frontline", "employee", "communication", "shift change", "shift", "restaurant", "hotel", "operations", "problem"],
    },
]

def clean_text(value):
    value = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", html.unescape(value)).strip()

def parse_date(value):
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None

def collect_news(search):
    cutoff = (datetime.now(timezone.utc) - timedelta(days=365)).date().isoformat()
    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).date().isoformat()
    query = f'{search["query"]} after:{cutoff} before:{tomorrow}'
    params = urlencode({"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"})
    url = "https://news.google.com/rss/search?" + params
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 DigitalIncomeAgent/2.0"})
    with urlopen(request, timeout=25) as response:
        root = ET.fromstring(response.read())

    results = []
    cutoff_date = datetime.now(timezone.utc).date() - timedelta(days=365)
    for item in root.findall(".//item")[:12]:
        title = clean_text(item.findtext("title"))
        description = clean_text(item.findtext("description"))
        published = item.findtext("pubDate")
        text = (title + " " + description).lower()
        matched = [term for term in search["terms"] if term.lower() in text]
        score = len(matched)
        date = parse_date(published)
        # RSS search operators are not a hard guarantee: enforce the date window locally.
        if not date or date.date() < cutoff_date:
            continue
        if score < 2 or not item.findtext("link"):
            continue
        results.append({
            "title": title,
            "link": item.findtext("link"),
            "published": published,
            "description": description,
            "query": search["query"],
            "hypothesis": search["hypothesis"],
            "relevance_score": score,
            "matched_terms": matched[:8],
            "published_date": date.date().isoformat() if date else None,
        })
    return results

def make_report(state, run_time):
    items = state.get("research_items", [])
    sections = [
        "# Digital Income Agent — Research Report",
        "",
        f"Generated: {run_time}",
        "",
        "## Executive snapshot",
        "",
        f"- New articles this run: {state.get('research_new_items', 0)}",
        f"- Relevant articles stored: {len(items)}",
        f"- Collection errors: {len(state.get('research_errors', []))}",
        "- Research window: approximately the last 12 months",
        "",
        "> Important: news coverage is a discovery signal, not proof of customer demand or willingness to pay. The next validation step is competitor/pricing research and direct conversations with café owners or managers.",
        "",
    ]
    for key, name in [
        ("cafe_starter_kit", "1. Small Café Manager Starter Kit"),
        ("shiftbrief_ai", "2. ShiftBrief AI"),
    ]:
        selected = [x for x in items if x.get("hypothesis") == key]
        selected.sort(key=lambda x: (x.get("relevance_score", 0), x.get("published_date") or ""), reverse=True)
        sections.extend(["## " + name, "", f"Relevant items found: {len(selected)}", ""])
        if not selected:
            sections.extend(["No sufficiently relevant articles found in this run.", ""])
        for item in selected[:15]:
            date = item.get("published_date") or item.get("published") or "Date unknown"
            sections.extend([
                f"### {item.get('title', 'Untitled')}",
                f"- Date: {date}",
                f"- Relevance score: {item.get('relevance_score', 0)}",
                f"- Matched topics: {', '.join(item.get('matched_terms', []))}",
                f"- Search: {item.get('query', '')}",
                f"- Source: {item.get('link', '')}",
                "",
            ])
    sections.extend([
        "## Collection limitations",
        "",
        "- Google News RSS is broad and may return duplicates, weak matches, or publisher summaries.",
        "- Relevance scoring is a lightweight keyword filter, not semantic AI analysis.",
        "- Articles do not establish market size, competitor quality, or purchase intent.",
        "- No products have been published and no customers have been contacted.",
        "",
        "## Next research priorities",
        "",
        "1. Identify direct competitors and substitute products for each hypothesis.",
        "2. Compare real prices, target customers, core features, and onboarding friction.",
        "3. Find recurring complaints in owner/operator communities and reviews.",
        "4. Design a low-cost demand test before building a full product.",
        "",
    ])
    return "\n".join(sections)

def main():
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if STATE_PATH.exists():
        state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    else:
        state = {"agent_name": "Digital Income Agent", "run_count": 0}

    now = datetime.now(timezone.utc).isoformat()
    collected, errors = [], []
    for search in SEARCHES:
        try:
            batch = collect_news(search)
            collected.extend(batch)
            print("Collected", len(batch), "relevant items for", search["hypothesis"])
        except Exception as error:
            errors.append({"query": search["query"], "error": str(error)[:500]})
            print("Search failed:", search["query"], str(error))

    existing = state.get("research_items", [])
    by_link = {item.get("link"): item for item in existing if item.get("link")}
    new_items = []
    for item in collected:
        link = item.get("link")
        if link and link not in by_link:
            new_items.append(item)
        if link:
            by_link[link] = item

    merged = list(by_link.values())
    merged.sort(key=lambda x: (x.get("published_date") or "", x.get("relevance_score", 0)), reverse=True)
    state["run_count"] = state.get("run_count", 0) + 1
    state["status"] = "research_ok" if collected and not errors else ("research_partial" if collected else "research_failed")
    state["last_run_utc"] = now
    state["research_last_run_utc"] = now
    state["research_queries"] = [x["query"] for x in SEARCHES]
    state["research_new_items"] = len(new_items)
    state["research_errors"] = errors
    state["research_items"] = merged[:200]
    state["research_hypotheses"] = {
        "cafe_starter_kit": "Small Café Manager Starter Kit",
        "shiftbrief_ai": "ShiftBrief AI",
    }
    state["research_method"] = "Google News RSS, last 365 days, keyword relevance score >= 2"
    REPORT_PATH.write_text(make_report(state, now), encoding="utf-8")
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Research complete. New:", len(new_items), "Stored:", len(state["research_items"]), "Errors:", len(errors))
    print("Report written to reports/latest.md")

if __name__ == "__main__":
    main()
