"""Daily orchestrator: pull N pending keywords -> generate -> inject affiliate links.

Designed for Windows Task Scheduler (see README section 5).

Usage:
    python run_daily.py --count 3
"""
import os
import csv
import glob
import argparse

import yaml

import generate_article as ga
import affiliate_inject as ai

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_config():
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=None)
    args = ap.parse_args()

    cfg = load_config()
    n = args.count or cfg["publishing"]["articles_per_day"]
    queue_path = os.path.join(ROOT, "data", "keywords.csv")
    if not os.path.exists(queue_path):
        raise SystemExit("data/keywords.csv not found. Run keyword_research.py first.")

    with open(queue_path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    done = 0
    for r in rows:
        if done >= n:
            break
        if r.get("status") != "pending":
            continue
        print(f"Generating: {r['keyword']}")
        try:
            md = ga.generate(r["keyword"], r.get("title") or r["keyword"],
                             r.get("intent", "informational"),
                             r.get("affiliate_tag", "なし"), cfg)
            path = ga.save(md, r.get("title") or r["keyword"], cfg)
            r["status"] = "published"
            done += 1
            print(f"  -> {path}")
        except Exception as e:  # noqa: BLE001
            r["status"] = "error"
            print(f"  ERROR: {e}")

    with open(queue_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # inject affiliate links into all content
    links = (cfg.get("affiliate", {}) or {}).get("links", {}) or {}
    for p in glob.glob(os.path.join(ROOT, cfg["content"]["output_dir"], "*.md")):
        with open(p, encoding="utf-8") as f:
            t = f.read()
        nt = ai.inject(t, links)
        if nt != t:
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write(nt)

    print(f"Done. Generated {done} article(s).")


if __name__ == "__main__":
    main()
