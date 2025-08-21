#!/usr/bin/env python3
import csv, json, os, time, hashlib, pathlib, difflib, sys, textwrap, random
from typing import Dict, List
import requests
from bs4 import BeautifulSoup

BASE = pathlib.Path(__file__).parent.resolve()
DATA = BASE / "data"
SNAP = BASE / "snapshots"
LOG_JSONL = BASE / "changes_log.jsonl"
DATA.mkdir(exist_ok=True)
SNAP.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": "JohnPac-Competitive-Monitor/1.0 (+contact marketing)"
}

RATE_MIN, RATE_MAX = 2, 5  # seconds between requests

def load_targets(path="targets.csv"):
    targets = []
    with open(BASE / path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # normalize keys
            row = {k.strip(): (v or "").strip() for k,v in row.items()}
            if not row.get("competitor") or not row.get("url"): 
                continue
            targets.append(row)
    return targets

def fetch(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=45)
    r.raise_for_status()
    return r.text

def extract_field(html: str, selector: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    if not selector:
        return soup.get_text(separator=" ", strip=True)[:2000]
    nodes = soup.select(selector)
    if not nodes:
        # fallback: try headings
        nodes = soup.select("h1, h2, h3, h4, .title, .product-title, .post-title")
    text = " | ".join(n.get_text(separator=" ", strip=True) for n in nodes)[:4000]
    return text

def snap_path(competitor: str, url: str, field: str) -> pathlib.Path:
    key = f"{competitor}|{url}|{field}"
    h = hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]
    return SNAP / f"{h}.json"

def read_snapshot(p: pathlib.Path) -> Dict:
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}

def write_snapshot(p: pathlib.Path, data: Dict):
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def append_log(entry: Dict):
    with open(LOG_JSONL, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def post_to_slack(webhook: str, message: str):
    try:
        resp = requests.post(webhook, json={"text": message}, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"[warn] slack webhook failed: {e}", file=sys.stderr)

def main():
    targets = load_targets()
    changes = []
    for t in targets:
        comp = t.get("competitor")
        url = t.get("url")
        field = t.get("field", "content")
        selector = t.get("css_selector", "")
        try:
            html = fetch(url)
            cur_val = extract_field(html, selector)
            sp = snap_path(comp, url, field)
            prev = read_snapshot(sp)
            prev_val = prev.get("value", "")
            if cur_val != prev_val:
                entry = {
                    "ts": int(time.time()),
                    "competitor": comp,
                    "url": url,
                    "field": field,
                    "old": prev_val,
                    "new": cur_val
                }
                changes.append(entry)
                write_snapshot(sp, {"value": cur_val, "url": url, "competitor": comp, "field": field, "ts": entry["ts"]})
                append_log(entry)
            time.sleep(random.uniform(RATE_MIN, RATE_MAX))
        except Exception as e:
            entry = {
                "ts": int(time.time()),
                "competitor": comp,
                "url": url,
                "field": field,
                "old": "",
                "new": f"[ERROR] {e}"
            }
            changes.append(entry)
            append_log(entry)

    # Rebuild data/changes.json (show last 500 changes)
    build_changes_index(limit=500)

    # Optional Slack ping
    webhook = os.getenv("SLACK_WEBHOOK_URL", "").strip()
    if webhook and changes:
        lines = []
        for c in changes[:20]:
            lines.append(f"*{c['competitor']}* — {c['field']}\n{c['url']}\n• OLD: {c['old'][:200]}\n• NEW: {c['new'][:200]}")
        post_to_slack(webhook, "Competitive Watch — changes detected:\n\n" + "\n\n".join(lines))

    print(f"Done. Changes this run: {len(changes)}")

def build_changes_index(limit=500):
    rows = []
    if os.path.exists(LOG_JSONL):
        with open(LOG_JSONL, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    rows.append(json.loads(line))
                except:
                    pass
    rows.sort(key=lambda r: r.get("ts", 0), reverse=True)
    rows = rows[:limit]
    (BASE / "data" / "changes.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
