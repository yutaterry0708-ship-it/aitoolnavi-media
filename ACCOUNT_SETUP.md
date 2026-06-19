# アカウント開設ガイド（匿名・完全自動化前提）

> **すべて屋号・ペンネームで運営。実名は報酬受取（ASP・銀行）にだけ使い、世間には出さない。**

---

## 0. 全体の順番（この順でやると詰まらない）

```
ドメイン取得 → 法務ページ公開（Hugo+Cloudflare Pages）→ ASP登録
→ X アカウント → APIキー → Task Scheduler 設定
→ YouTube（オプション）→ Instagram（オプション）
```

---

## 1. ドメイン取得（¥1,500/年）

- **お名前.com / Cloudflare Registrar** で屋号ベースの `.com` or `.jp` を取得
- 例: `aitoolnavi.com` / `aisaas-navi.com` / `toolhack.jp`
- **個人情報保護（Whois代行）を必ず有効化**（無料でできる）
- 取得後 → `config.yaml` の `domain` を更新

---

## 2. Hugo サイト + Cloudflare Pages（無料）

```bash
# Hugo インストール (Windows)
winget install Hugo.Hugo.Extended

# サイト作成（プロジェクトルートで）
cd "C:\Users\yutat\OneDrive\デスクトップ\ai-auto-affiliate"
hugo new site site
cd site

# テーマ（PaperMod: SEO最適・シンプル・日本語対応）
git init
git submodule add https://github.com/adityatelange/hugo-PaperMod themes/PaperMod

# content/ に記事を配置して確認
hugo server
```

**Cloudflare Pages設定（push自動デプロイ）:**
1. GitHubリポジトリにプロジェクトをpush（プライベートで可）
2. Cloudflare Pages → 「Create a project」→ GitHub連携
3. Build command: `hugo --minify` / Output directory: `public`
4. 独自ドメインを接続（Cloudflare DNS → CNAME設定）
5. **毎日 `git push` するだけで自動デプロイ** → `run_all.ps1` の末尾コメントを解除

---

## 3. ASP 登録（アフィリエイトの要）

**全部無料。報酬受取に本人確認＋振込口座が必要（屋号で可）。**

| ASP | 特徴 | 登録URL |
|---|---|---|
| A8.net | 日本最大。案件数最多 | https://www.a8.net/ |
| もしもアフィリエイト | Amazon連携＋高単価あり | https://af.moshimo.com/ |
| afb | 美容・教育・SaaS案件豊富 | https://www.afi-b.com/ |
| アクセストレード | IT転職高単価（¥15,000〜）| https://www.accesstrade.ne.jp/ |

**登録時のポイント:**
- 運営者名: 屋号（例: AIツールナビ 編集部）
- サイトURL: 既に公開済みのドメインが必要（法務ページだけでもOK）
- 審査通過後 → 各案件の計測リンクを `config.yaml` の `affiliate.links` に追記

**高単価・おすすめ案件（審査後に申請）:**
- AIツール系: Notion / Canva Pro / Dropbox / Slack / Monday.com 等
- 転職系: レバテックキャリア（エンジニア転職、¥30,000〜）、マイナビIT（¥15,000〜）
- 教育系: Udemy / Schoo / 資格系通信講座

---

## 4. X (Twitter) アカウント

**匿名運用ルール:**
- アカウント名: ブランド名（例: @aitoolnavi）
- 表示名: 「AIツールナビ｜自動化・効率化のリアルな話」
- プロフ: 「AIツール・SaaSを実際に使って比較。AI × 業務自動化のリアルな話を発信。」
- アイコン: AI画像生成（Midjourney / DALL-E / Stable Diffusion）でロゴ作成

**API 設定（自動投稿に必須）:**
1. [developer.twitter.com](https://developer.twitter.com) → App作成（無料）
2. 「Read and Write」権限を付与
3. 生成された4つのキーを `.env` に設定:
   ```
   X_API_KEY=...
   X_API_SECRET=...
   X_ACCESS_TOKEN=...
   X_ACCESS_SECRET=...
   ```
4. テスト投稿: `cd src && python traffic/x_auto_poster.py --generate 3 --post --force`

**投稿戦略（自動化後）:**
- 1日3本（9時・12時・19時）→ `run_all.ps1` が自動実行
- 週次PDCAでバズった型を増やす（`pdca_engine.py` が自動分析）
- エンゲージメント高いアカウントのフォロワーをフォロー（手動 or Buffer等）

---

## 5. YouTube（フェーズ2・任意）

**完全匿名・顔出しなしの作り方:**
1. Googleアカウント（匿名メール）でチャンネル作成
2. チャンネル名: ブランド名
3. スクリプト生成: `python traffic/youtube_script.py --keyword "..." --length 8`
4. 音声化（2択）:
   - **VOICEVOX**（無料・日本語・高品質・ローカル実行）→ Docker or インストーラ
   - **ElevenLabs**（API・月50分まで無料・英語メイン）
5. 画面収録 + テロップ → OBS Studio（無料）or CapCut
6. アップロードは手動（YouTube Data APIは本番審査が複雑なため）

**CPMが高い理由:** AIツールレビューは商材が高額→広告CPM $14〜35。
登録1000人 + 視聴4000時間で YouTube パートナープログラム（広告収益）+アフィリの二重収益。

---

## 6. Instagram（フェーズ2・任意）

**Reels戦略（顔出しなし）:**
1. ビジネスアカウントで作成（統計が見られる）
2. Reels台本: `python traffic/instagram_reel.py --topic "..." --type both`
3. 動画作成（無料ツール）:
   - **CapCut PC** → テキスト・テロップ・BGM
   - **Canva** → スライド→動画書き出し
4. 投稿は手動 or **Meta Business Suite**（スケジュール投稿・無料）
5. 連携: 同じ動画をFacebook・Threadsにも同時投稿でリーチ拡大

---

## 7. Task Scheduler 登録（全自動化の完成）

```powershell
# 管理者PowerShellで実行
$action  = New-ScheduledTaskAction -Execute "powershell.exe" `
           -Argument "-NonInteractive -File `"C:\Users\yutat\OneDrive\デスクトップ\ai-auto-affiliate\src\run_all.ps1`""
$trigger = New-ScheduledTaskTrigger -Daily -At 7:30am
$set     = New-ScheduledTaskSettingsSet -WakeToRun -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "AIAffiliateAll" -Action $action -Trigger $trigger -Settings $set

# 確認
Get-ScheduledTask "AIAffiliateAll" | Get-ScheduledTaskInfo
```

---

## 8. コストまとめ

| 項目 | 費用 |
|---|---|
| ドメイン | ¥1,500/年（¥125/月） |
| Cloudflare Pages | **無料** |
| X API（Free） | **無料**（月500ツイートまで） |
| Claude API | ¥3,000〜5,000/月（記事90本/月） |
| VOICEVOX | **無料**（ローカル） |
| **合計** | **¥3,100〜5,100/月** |

---

## 9. ステマ規制チェックリスト（景表法 2023/10〜）

すべてのアフィリ記事・SNS投稿で確認：

- [ ] 記事冒頭に「PR」または「広告」表記がある
- [ ] アフィリリンクに `rel="sponsored"` が付いている（`affiliate_inject.py`が自動化）
- [ ] 「必ず稼げる/痩せる/治る」等の断定表現がない
- [ ] 投資・医療・金融の助言をしていない
- [ ] 実際に試した / 調査したコンテンツである

---

## 付録: バズる投稿の型（毎週PDCAで更新）

| 型 | 例 | 伸びやすいジャンル |
|---|---|---|
| 箇条書き | 「Notionでやってること10選↓」 | ツール活用 |
| 逆説 | 「無料で十分すぎる件について」 | 比較 |
| 数字 | 「3分でできる○○の設定」 | How-to |
| 比較 | 「ChatGPT vs Claude、正直な感想」 | レビュー |
| 問いかけ | 「AI使ってる人に聞きたい…」 | エンゲージメント |
| Before/After | 「AI導入前後の業務時間の変化」 | 実体験 |
