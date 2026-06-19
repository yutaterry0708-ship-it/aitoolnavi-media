"""Expand seed topics into a prioritized article queue (data/keywords.csv).

Usage:
    python keyword_research.py --per-topic 15
"""
import os
import csv
import argparse

import yaml

from llm import call_llm_json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_config():
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def expand_topic(topic, niche, per_topic, model):
    prompt = f"""あなたは日本語SEOのキーワード設計の専門家です。
ニッチ: {niche}
シードトピック: {topic}

新規ドメインでも上位を狙える「ロングテール（検索意図が明確・競合が比較的弱い）」キーワードを
{per_topic}個提案してください。比較/おすすめ/料金系(commercial)と 使い方/とは系(informational)を
バランスよく。各KWに以下を付けてJSON配列だけで返す（前置き・説明文は書かない）:
- keyword: 実際の検索クエリ
- intent: "commercial" または "informational"
- affiliate_tag: 紐づけたいアフィリ案件のヒント（例: "Notion","転職エージェント","なし"）
- title: クリックされる記事タイトル（32文字前後・年号や数字OK）
"""
    return call_llm_json(prompt, model=model, max_tokens=4096)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-topic", type=int, default=12)
    args = ap.parse_args()

    cfg = load_config()
    niche = cfg["niche"]["primary"]
    model = cfg["llm"]["keyword_model"]

    seed_path = os.path.join(ROOT, "data", "keywords_seed.csv")
    out_path = os.path.join(ROOT, "data", "keywords.csv")

    existing, rows = set(), []
    if os.path.exists(out_path):
        with open(out_path, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                existing.add(r["keyword"])
                rows.append(r)

    with open(seed_path, encoding="utf-8") as f:
        seeds = [r["topic"].strip() for r in csv.DictReader(f) if r.get("topic", "").strip()]

    for topic in seeds:
        print(f"Expanding: {topic}")
        try:
            kws = expand_topic(topic, niche, args.per_topic, model)
        except Exception as e:  # noqa: BLE001
            print(f"  skip ({e})")
            continue
        for kw in kws:
            k = (kw.get("keyword") or "").strip()
            if not k or k in existing:
                continue
            existing.add(k)
            rows.append({
                "keyword": k,
                "intent": kw.get("intent", "informational"),
                "affiliate_tag": kw.get("affiliate_tag", "なし"),
                "title": kw.get("title", k),
                "status": "pending",
            })

    fieldnames = ["keyword", "intent", "affiliate_tag", "title", "status"]
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} keywords -> {out_path}")


if __name__ == "__main__":
    main()
