"""note.com Auto Publisher: content/*.md -> note.com (Playwright headless)

Requires in .env:
    NOTE_EMAIL    = note.com login email
    NOTE_PASSWORD = note.com login password

Usage:
    python note_publisher.py             # publish 1 pending article
    python note_publisher.py --all       # publish all pending
    python note_publisher.py --dry-run   # preview only
"""
import os, re, sys, json, time, argparse
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent.parent
load_dotenv(ROOT / ".env", override=True)

NOTE_EMAIL    = os.getenv("NOTE_EMAIL", "")
NOTE_PASSWORD = os.getenv("NOTE_PASSWORD", "")
CONTENT_DIR   = ROOT / "content"
NOTE_LOG      = ROOT / "data" / "note_published.json"
DISCLOSURE    = "※本記事はアフィリエイト広告（PR）を含みます。"


def load_log():
    return json.loads(NOTE_LOG.read_text(encoding="utf-8")) if NOTE_LOG.exists() else {}

def save_log(data):
    NOTE_LOG.parent.mkdir(exist_ok=True)
    NOTE_LOG.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def md_to_text(md_path):
    text = md_path.read_text(encoding="utf-8")
    h1 = re.search(r"^# (.+)$", text, re.MULTILINE)
    title = h1.group(1).strip() if h1 else md_path.stem
    body = re.sub(r"^# .+\n", "", text, flags=re.MULTILINE)
    body = re.sub(r"#{1,4} (.+)", r"\1", body)
    body = re.sub(r"\*{1,2}(.+?)\*{1,2}", r"\1", body)
    body = re.sub(r"`(.+?)`", r"\1", body)
    body = re.sub(r"```[\s\S]*?```", "", body)
    body = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", body)
    body = re.sub(r"^[-*] ", "・", body, flags=re.MULTILINE)
    return {"title": title, "body": DISCLOSURE + "\n\n" + body.strip()}

def publish_to_note(md_path, dry_run=False):
    info = md_to_text(md_path)
    print(f"  タイトル: {info['title']}")
    if dry_run:
        print("  [DRY-RUN]")
        return "dry-run"
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        ctx = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
        page = ctx.new_page()
        page.goto("https://note.com/login", wait_until="domcontentloaded", timeout=60000)
        time.sleep(3)
        # メールアドレス入力 (複数セレクタ試行)
        for sel in ['input[name="email"]', 'input[type="email"]', 'input[placeholder*="メール"]', 'input[placeholder*="email"]']:
            try:
                page.fill(sel, NOTE_EMAIL, timeout=5000); break
            except: pass
        time.sleep(0.5)
        for sel in ['input[name="password"]', 'input[type="password"]']:
            try:
                page.fill(sel, NOTE_PASSWORD, timeout=5000); break
            except: pass
        time.sleep(0.5)
        for sel in ['button[type="submit"]', 'button:has-text("ログイン")', 'button:has-text("Login")']:
            try:
                page.click(sel, timeout=5000); break
            except: pass
        time.sleep(3)
        if "login" in page.url:
            print("  ERROR: ログイン失敗"); browser.close(); return ""
        page.goto("https://note.com/notes/new", wait_until="networkidle")
        time.sleep(2)
        page.locator('[placeholder*="タイトル"]').first.fill(info["title"])
        page.locator('[contenteditable="true"]').first.click()
        page.keyboard.type(info["body"][:5000])
        page.locator('button:has-text("公開"), button:has-text("投稿")').first.click()
        time.sleep(1)
        confirm = page.locator('button:has-text("公開する"), button:has-text("投稿する")')
        if confirm.count() > 0:
            confirm.first.click(); time.sleep(2)
        url = page.url
        browser.close()
    return url

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--file")
    args = ap.parse_args()
    if not NOTE_EMAIL or not NOTE_PASSWORD:
        print("ERROR: NOTE_EMAIL / NOTE_PASSWORD を .env に設定してください"); sys.exit(1)
    log = load_log()
    if args.file:
        targets = [Path(args.file)]
    else:
        all_files = sorted(CONTENT_DIR.glob("*.md"))
        targets = [f for f in all_files if f.name not in log]
        if not args.all and targets: targets = targets[:1]
    if not targets:
        print("公開待ち記事なし"); return
    print(f"note.com 投稿対象: {len(targets)} 件")
    for md_path in targets:
        print(f"\n→ {md_path.name}")
        url = publish_to_note(md_path, dry_run=args.dry_run)
        if url and url != "dry-run":
            log[md_path.name] = {"url": url}
            save_log(log)
            print(f"  公開済: {url}")

if __name__ == "__main__":
    main()
