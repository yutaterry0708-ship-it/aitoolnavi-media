"""Setup verification tool — checks all required API keys and dependencies.

Run this first to see exactly what's missing.

Usage:
    python setup_check.py
"""
import os
import sys
import importlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(ROOT, ".env"), override=True)
except ImportError:
    pass

CHECKS = [
    # (label, check_fn, fix_message)
]

OK   = "[OK]"
WARN = "[--]"
FAIL = "[NG]"


def check_package(name):
    try:
        importlib.import_module(name)
        return True
    except ImportError:
        return False


def check_env(key):
    return bool(os.getenv(key, "").strip())


def check_file(rel_path):
    return os.path.exists(os.path.join(ROOT, rel_path))


def main():
    print("\n" + "=" * 55)
    print("  AI自動アフィリエイト セットアップ確認")
    print("=" * 55)

    issues = []

    # --- Python packages ---
    print("\n【Pythonパッケージ】")
    pkgs = {
        "anthropic":           "pip install anthropic",
        "google.generativeai": "pip install google-generativeai",
        "dotenv":              "pip install python-dotenv",
        "yaml":                "pip install PyYAML",
        "tweepy":              "pip install tweepy",
        "feedparser":          "pip install feedparser",
    }
    for pkg, fix in pkgs.items():
        ok = check_package(pkg.split(".")[0] if "." in pkg else pkg)
        sym = OK if ok else FAIL
        print(f"  {sym} {pkg:<30} {'OK' if ok else fix}")
        if not ok:
            issues.append(f"pip install: {fix.split()[-1]}")

    # --- APIキー ---
    print("\n【APIキー (.env)】")
    keys = {
        "ANTHROPIC_API_KEY": "④ セットアップガイドの手順で取得",
        "GEMINI_API_KEY":    "financial_botと同じキーを流用可",
        "X_API_KEY":         "③ X Developer Portalで取得",
        "X_API_SECRET":      "③ X Developer Portalで取得",
        "X_ACCESS_TOKEN":    "③ X Developer Portalで取得",
        "X_ACCESS_SECRET":   "③ X Developer Portalで取得",
    }
    for key, fix in keys.items():
        ok = check_env(key)
        sym = OK if ok else (WARN if "GEMINI" in key or "X_" in key else FAIL)
        print(f"  {sym} {key:<30} {'設定済み' if ok else f'未設定 → {fix}'}")
        if not ok and "ANTHROPIC" in key:
            issues.append(f"必須: {key} を .env に設定してください")

    # --- ファイル ---
    print("\n【設定ファイル】")
    files = {
        "config.yaml":              "brand.domain を実際のドメインに更新してください",
        ".env":                     ".env.example をコピーして .env を作成してください",
        "data/keywords.csv":        "python src/keyword_research.py を実行してください",
    }
    for rel, fix in files.items():
        ok = check_file(rel)
        sym = OK if ok else WARN
        extra = ""
        if ok and rel == "config.yaml":
            try:
                import yaml
                cfg = yaml.safe_load(open(os.path.join(ROOT, rel), encoding="utf-8"))
                if cfg["brand"]["domain"] == "example.com":
                    sym = WARN
                    extra = " → domain が example.com のまま（取得後に更新）"
            except Exception:
                pass
        print(f"  {sym} {rel:<35} {'OK' + extra if ok else f'なし → {fix}'}")

    # --- ディレクトリ作成 ---
    print("\n【データディレクトリ作成】")
    dirs = ["data/pdca", "data/note_ready", "data/youtube_scripts", "data/instagram", "content"]
    for d in dirs:
        path = os.path.join(ROOT, d)
        os.makedirs(path, exist_ok=True)
        print(f"  [OK] {d}")

    # --- サマリ ---
    print("\n" + "=" * 55)
    if not issues:
        print("  [OK] 全チェック通過！ `python src/run_daily.py` で動作確認できます。")
    else:
        print(f"  [NG] {len(issues)}件の必須設定が未完了:")
        for i in issues:
            print(f"     -> {i}")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    main()
