#!/usr/bin/env python3
import json, os, pathlib, sys

BASE = pathlib.Path(__file__).parent.resolve()
LOG = BASE / "changes_log.jsonl"
OUT = BASE / "data" / "changes.json"

def main(limit=500):
    rows = []
    if LOG.exists():
        for line in LOG.read_text(encoding="utf-8").splitlines():
            try:
                rows.append(json.loads(line))
            except:
                pass
    rows.sort(key=lambda r: r.get("ts", 0), reverse=True)
    rows = rows[:limit]
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(rows)} entries to {OUT}")

if __name__ == "__main__":
    lim = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    main(lim)
