# run_all.ps1 — 全自動フルパイプライン (UTF-8 BOMなし)
# Task Schedulerに登録して毎日実行
# 実行順: トレンド分析 → 記事3本生成 → Xスレッド5本生成+投稿 → Reels台本生成
$ErrorActionPreference = 'Stop'
$proj = "C:\Users\yutat\OneDrive\デスクトップ\ai-auto-affiliate"
$src  = Join-Path $proj "src"
$log  = Join-Path $proj "run.log"

$py = Join-Path $proj ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

Set-Location $src

function Run($script, $args_str) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    cmd /c "`"$py`" $script $args_str >> `"$log`" 2>&1"
    Add-Content $log "$ts [$script $args_str] exit=$LASTEXITCODE"
}

# 1. トレンド分析（今日のコンテンツ方針を決める）
Run "traffic\trend_analyzer.py" "--save"

# 2. ブログ記事 3本生成
Run "run_daily.py" "--count 3"

# 2b. WordPress に記事公開（WP_APP_PASSWORD が設定済みなら）
$wpPass = (& cmd /c "set WP_APP_PASSWORD" 2>$null)
if ($env:WP_APP_PASSWORD -or (Select-String "WP_APP_PASSWORD=." "$proj\.env")) {
    Run "wp_publisher.py" ""
}

# 2c. note.com に1記事公開（NOTE_PASSWORD が設定済みなら）
if ($env:NOTE_PASSWORD -or (Select-String "NOTE_PASSWORD=." "$proj\.env")) {
    Run "traffic\note_publisher.py" ""
}

# 3. Xスレッド5本生成 → キューへ（即投稿は1本）
Run "traffic\x_auto_poster.py" "--generate 5"
Run "traffic\x_auto_poster.py" "--post"

# 4. YouTube スクリプト（週3本: 月水金）
$dayOfWeek = (Get-Date).DayOfWeek
if ($dayOfWeek -in @('Monday','Wednesday','Friday')) {
    Run "traffic\youtube_script.py" "--keyword 'AIツール最新比較 2026' --length 8"
    # VOICEVOX が起動中なら音声も自動生成
    try {
        $vv = Invoke-WebRequest "http://127.0.0.1:50021/version" -TimeoutSec 2 -ErrorAction Stop
        Run "traffic\voicevox_tts.py" "--speaker 11"
    # 音声生成後に動画も自動生成
    Run "traffic\youtube_video_maker.py" ""
    } catch { Add-Content $log "$(Get-Date -Format 'HH:mm:ss') VOICEVOX not running - skip TTS/video" }
}

# 5. Instagram Reels台本（月水のみ）
if ($dayOfWeek -in @('Monday','Wednesday')) {
    Run "traffic\instagram_reel.py" "--topic 'AIツール活用術' --type both"
}

# 週次PDCA（日曜のみ）
$today = (Get-Date).DayOfWeek
if ($today -eq 'Sunday') {
    Run "traffic\pdca_engine.py" ""
}

# git push（Cloudflare Pages 自動デプロイ）
# ドメイン・Pages設定後にコメントアウト解除
# cmd /c "git -C `"$proj`" add content/ data/ && git -C `"$proj`" commit -m `"auto: $(Get-Date -Format 'yyyy-MM-dd')`" && git -C `"$proj`" push >> `"$log`" 2>&1"
