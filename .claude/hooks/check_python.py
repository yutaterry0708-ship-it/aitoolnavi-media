"""PostToolUse hook: Claude が編集した .py を構文チェック＋致命的バグのみ lint する。

- ファイルは一切書き換えない（自動フォーマットはしない）
- 問題があれば exit 2 + stderr → Claude に差し戻されて自動修正される
- ruff 未インストール環境（Windows 等）では構文チェックのみ
"""
import ast
import json
import shutil
import subprocess
import sys

try:
    payload = json.loads(sys.stdin.buffer.read().decode("utf-8"))
except Exception:  # noqa: BLE001 - 入力が想定外なら何もしない
    sys.exit(0)

path = (payload.get("tool_input") or {}).get("file_path") or ""
if not path.endswith(".py"):
    sys.exit(0)

try:
    with open(path, encoding="utf-8") as f:
        ast.parse(f.read(), filename=path)
except FileNotFoundError:
    sys.exit(0)
except SyntaxError as e:
    print(f"SyntaxError: {path}:{e.lineno}: {e.msg}", file=sys.stderr)
    sys.exit(2)

ruff = shutil.which("ruff")
if ruff:
    # E9/F63/F7/F82 = 構文・未定義名など「実行時に落ちる」系だけ。スタイルは見ない。
    r = subprocess.run(
        [ruff, "check", "--no-cache", "--select", "E9,F63,F7,F82",
         "--output-format", "concise", path],
        capture_output=True, text=True, encoding="utf-8",
    )
    if r.returncode == 1:
        print(r.stdout.strip(), file=sys.stderr)
        sys.exit(2)
sys.exit(0)
