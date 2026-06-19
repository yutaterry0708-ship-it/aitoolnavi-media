# AIAffiliateDaily - daily content generation (save as UTF-8, NO BOM)
# Routes through cmd /c with redirection to avoid PowerShell NativeCommandError
# when stderr is written (see global CLAUDE.md note).
$ErrorActionPreference = 'Stop'
$proj = "C:\Users\yutat\OneDrive\デスクトップ\ai-auto-affiliate"
$py = Join-Path $proj ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }
$log = Join-Path $proj "run.log"
Set-Location (Join-Path $proj "src")
cmd /c "`"$py`" run_daily.py --count 3 >> `"$log`" 2>&1"
# Optional: auto-deploy (uncomment after git + Cloudflare Pages are set up)
# cmd /c "git -C `"$proj`" add -A && git -C `"$proj`" commit -m auto && git -C `"$proj`" push >> `"$log`" 2>&1"
