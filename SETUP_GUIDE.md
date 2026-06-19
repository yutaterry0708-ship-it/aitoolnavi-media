# セットアップ完全ガイド（匿名・X・Instagram・note.com）

**先に実行して現状確認:**
```
cd "C:\Users\yutat\OneDrive\デスクトップ\ai-auto-affiliate\src"
python setup_check.py
```

---

## 1. ドメイン取得（¥1,100〜/年・所要10分）

**Cloudflare Registrar を使う理由**: 業界最安値（卸値そのまま）＋Whois自動非公開（匿名確保）＋Cloudflare Pages（無料ホスト）と一体管理

### 手順
1. **https://dash.cloudflare.com** を開く
2. アカウントがなければ無料登録（メールアドレスのみ）
3. 左サイドバー → **「Domain Registration」** → **「Register Domain」**
4. 検索ボックスにドメイン名を入力

   **おすすめ候補（先着順・今すぐ確認）:**
   - `aitoolnavi.com`（AIツールナビ）
   - `aisaasnavi.com`
   - `toolhack.jp`
   - `ai-tool-lab.com`
   - `saas-matome.com`

5. `.com` は年 ¥1,100〜 / `.jp` は年 ¥2,200〜 → `.com` で十分
6. カートに入れる → 支払い（クレジットカード1枚で完了）
7. **Whois Privacy はデフォルトで有効** → 個人情報は自動保護されている

### 取得後にやること
```yaml
# config.yaml の domain を更新
brand:
  domain: "取得したドメイン.com"   # ← ここを変える
```

---

## 2. `.env` を作る（④ APIキーの設定）

### 手順
```powershell
# ai-auto-affiliate フォルダで
Copy-Item .env.example .env
```

メモ帳や VSCode で `.env` を開く:
```
ANTHROPIC_API_KEY=     ← ここに入れる（下記参照）
GEMINI_API_KEY=        ← financial_bot の .env からコピー
X_API_KEY=             ← 後述
X_API_SECRET=          ← 後述
X_ACCESS_TOKEN=        ← 後述
X_ACCESS_SECRET=       ← 後述
```

### Anthropic API Key の取得（ANTHROPIC_API_KEY）

1. **https://console.anthropic.com** を開く
2. Googleアカウントでサインイン（匿名メールでも可）
3. 左サイドバー → **「API Keys」**
4. **「Create Key」** ボタン → 名前は何でもOK（例: `ai-affiliate`）
5. `sk-ant-api03-...` という文字列が表示される → **今だけしか見えないのでコピー**
6. `.env` に貼る:
   ```
   ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxx
   ```

**料金**: 従量課金（記事1本≒¥5〜15）。月100本生成しても¥500〜1,500。  
`claude-haiku`（KW・SNS用）は激安。`claude-sonnet`（記事本文）は少し高め。

---

## 3. X（Twitter）API キー取得

### アカウント作成（匿名）
1. https://x.com で新規アカウント作成
   - メール: 専用の Gmail（匿名メールアドレス推奨）
   - 電話: 最初は不要なこともあるが要求されたら格安SIMでも可
   - ユーザー名: `@aitoolnavi` など（ブランド名ベース）
   - 表示名: `AIツールナビ`
   - プロフ: 「AIツール・SaaSを実際に試して比較。業務効率化のリアルな話。」
   - アイコン: DALL-E / Canva でロゴ画像を生成して設定

2. しばらく普通に使う（凍結回避のため数日間は手動投稿を数件）

### Developer Portal で API キーを取得
1. **https://developer.twitter.com/en/portal/dashboard** を開く
   （X にログインした状態で）
2. 右上 **「+ Create Project」**
3. プロジェクト名: 任意（例: `AIAffiliateBot`）
4. ユースケース: `Making a bot` または `Organic social growth`
5. アプリ作成 → アプリ名: 任意
6. **権限設定（重要）**:
   - 左サイドバー → Settings → User authentication settings
   - App permissions: **「Read and Write」** を選択
   - Type of App: **「Web App, Automated App or Bot」**
   - Callback URL: `http://localhost` （使わないが入力必須）
   - Save
7. **「Keys and tokens」** タブ
   - **API Key and Secret**: `Regenerate` → 2つをコピー
   - **Access Token and Secret**: `Generate` → 2つをコピー
8. `.env` に4つを貼り付け

**無料枠（Basic, $0）**: 月500ツイートまで書き込み可 → 1日16本まで。  
毎日3本なら無料枠で十分。

### 動作テスト
```powershell
cd "C:\Users\yutat\OneDrive\デスクトップ\ai-auto-affiliate\src"
python traffic\x_auto_poster.py --generate 3
python traffic\x_auto_poster.py --post --force   # dry-runなら投稿しない（キー設定後は実投稿）
```

---

## 4. Instagram（顔出しなし）

**APIは不要。Meta Business Suite で無料スケジュール投稿できる。**

### アカウント作成（匿名）
1. https://www.instagram.com → 新規登録
   - メール: 専用のメールアドレス
   - ユーザー名: `@aitoolnavi` など
   - **プロアカウントに切り替え** → プロフィール → 「プロアカウントへ切り替え」→ クリエイター
   - カテゴリ: 「ブロガー」or「デジタルクリエイター」

2. プロフ文:
   ```
   AIツール・SaaSを本音レビュー📊
   業務効率化のリアルな話を投稿
   ブログ → リンク欄
   ```

### 投稿ワークフロー（半自動）
```powershell
# リール台本 + カルーセル原稿を自動生成
cd src
python traffic\instagram_reel.py --topic "ChatGPT vs Claude 比較" --type both
# → data/instagram/YYYY-MM-DD-....json に保存される
```

生成されたJSONを見て:
- **Reels**: CapCut PC / Canva でテキスト動画を作成（10分/本）
- **カルーセル**: Canva で各スライドを作成（15分/本）
- **Meta Business Suite** (https://business.facebook.com) でスケジュール投稿

**完全自動化のタイミング**: フォロワー1,000人超えたら Meta Graph API のトークンを取得して自動化を検討（それまでは週2〜3本手動でOK）

---

## 5. note.com

**アカウント作成（匿名）**:
1. https://note.com → 新規登録
   - メール: 専用メールアドレス
   - クリエイター名（ニックネーム）: 「AIツールナビ」
   - URL: `note.com/@aitoolnavi`（取得できたら）
   - プロフ: 「AIツール・SaaSを実際に使って比較。業務効率化のリアルな話。」

**記事投稿ワークフロー**:
```powershell
# ブログ記事からnote用に変換（自動生成）
cd src
python traffic\note_publisher.py --from-article ..\content\2026-06-19-notion-ai.md

# または直接キーワードから生成
python traffic\note_publisher.py --keyword "Notion AIの使い方" --affiliate-tag "Notion"

# → data/note_ready/YYYY-MM-DD-....txt にコピペ用テキストが保存される
```

保存されたtxtを開いて → note.com の「新しい記事」にコピペ → タグ設定 → 公開（30秒）

**note.com でアフィリできるか?**  
→ 外部リンクは貼れる。「PR」「広告」の表記を冒頭に入れればOK（自動挿入済み）。  
→ 有料note（100〜500円）を作って記事自体を販売することも可能（別収益）。

---

## 6. ⑤ Task Scheduler 設定（全自動化・1回だけ）

**管理者 PowerShell** で実行（スタートメニュー → 「PowerShell」右クリック → 「管理者として実行」）:

```powershell
# 毎朝 7:30 に全自動実行するタスクを登録
$proj    = "C:\Users\yutat\OneDrive\デスクトップ\ai-auto-affiliate"
$script  = Join-Path $proj "src\run_all.ps1"
$action  = New-ScheduledTaskAction -Execute "powershell.exe" `
           -Argument "-NonInteractive -ExecutionPolicy Bypass -File `"$script`""
$trigger = New-ScheduledTaskTrigger -Daily -At 7:30am
$set     = New-ScheduledTaskSettingsSet `
           -WakeToRun `
           -AllowStartIfOnBatteries `
           -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "AIAffiliateAll" `
                       -Action $action -Trigger $trigger -Settings $set
```

**Xの最適時間（追加トリガー）** — 9時・12時・19時に個別投稿:
```powershell
$post_script = Join-Path $proj "src\traffic\x_auto_poster.py"
$py = Join-Path $proj ".venv\Scripts\python.exe"
foreach ($hour in @(9, 12, 19)) {
    $trigger2 = New-ScheduledTaskTrigger -Daily -At "$($hour):00"
    $action2  = New-ScheduledTaskAction -Execute $py `
                -Argument "`"$post_script`" --post" `
                -WorkingDirectory (Join-Path $proj "src")
    Register-ScheduledTask -TaskName "AIAffiliateX_$hour" `
                           -Action $action2 -Trigger $trigger2 -Settings $set
}
```

**確認**:
```powershell
Get-ScheduledTask | Where-Object { $_.TaskName -like "AIAffiliate*" }
```

**GUI で確認したい場合**: `Win + R` → `taskschd.msc` → 左ペインの「タスクスケジューラライブラリ」→ `AIAffiliateAll` が表示されていればOK

---

## 7. 今日やること（チェックリスト）

```
[ ] 1. ドメイン取得（Cloudflare Registrar・10分）
[ ] 2. .env 作成（.env.example をコピー）
[ ] 3. Anthropic API Key 取得 → .env に設定
[ ] 4. Gemini API Key を .env にコピー（financial_botと同じ）
[ ] 5. X アカウント作成（匿名）+ API キー取得 → .env に設定
[ ] 6. Instagram アカウント作成（匿名・プロアカ）
[ ] 7. note.com アカウント作成（匿名）
[ ] 8. pip install feedparser
[ ] 9. python src/setup_check.py → 全 [OK] になることを確認
[ ] 10. python src/run_daily.py --count 1 → 記事1本生成テスト
[ ] 11. python src/traffic/x_auto_poster.py --generate 3 --post --force
[ ] 12. Task Scheduler 登録 → 翌朝から完全自動
```

---

## 8. 月次コスト（全部込み）

| 項目 | 費用 |
|---|---|
| ドメイン | ¥92/月（¥1,100/年） |
| Cloudflare Pages | 無料 |
| Anthropic API（記事90本/月） | ¥3,000〜5,000 |
| X API（Basic無料） | 無料 |
| Instagram・note.com | 無料 |
| **合計** | **¥3,100〜5,100/月** |
