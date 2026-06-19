# AI自動アフィリエイト・メディア（匿名・完全自動運用）

匿名ブランドで「AIツール/SaaS の比較・レビュー記事」をAIが毎日自動生成し、SaaSアフィリエイトで収益化する仕組み。
顔出し・実名・人脈ゼロ。初期投資 月¥5,000以下。Windows Task Scheduler で無人運用する。

> このプロジェクトは C04（メタオーケストレーター）で設計・実行された。
> 主軸=C03意思決定 / 推論強化=なぜなぜ＋全否定（楽観バイアス除去）/ 品質=Q11ハルシネーション抑制＋Q08ソース明記 / 節約=E13サブエージェント並列。

---

## 0. 最初に正直な前提（ここを誤解すると失敗する）

- **「数週間で月30万」は不可能。** アフィリは検索流入が育つのに **6〜12ヶ月**かかる。これは仕組みの問題で、誰がやっても同じ。
- **AIに丸投げで放置＝ゼロ。** 2026年のGoogleは「薄いAI量産」を順位付けしない。**E-E-A-T（実体験・比較・正直なデメリット）が入った記事だけ**が勝つ。このエンジンはそれを生成する設計だが、ニッチ選定と初期の品質チェックは人間が握る。
- **AIが回せるのは「制作」。** ドメイン購入・ASP審査（本人確認＋振込口座が必要）・APIキー・公開GO は人間がやる。それ以外（記事生成・SNS整形・内部リンク）は全自動。
- **月30万の中身（ユニットエコノミクス）**:
  - SaaSアフィリの実質単価 ≒ ¥4,000/成約（保守値）
  - 月30万 = **75成約/月**
  - 必要な月間セッション ≒ **3〜8万**（商業意図ページのCVRを1〜2%と仮定）
  - → 記事200〜400本＋上位案件への絞り込みで6〜12ヶ月後に射程
  - **加速レバー**: 転職(IT/AI人材)案件は1成約¥15,000〜30,000 → 月10〜20成約で届く。高単価案件を1〜2本混ぜると到達が早まる。

**結論: これは「夜の間にAIが資産を積み上げ続け、半年〜1年で月30万に育てる装置」。即金ではない。即金が要るなら別途クラウドソーシング受託を並走（README末尾）。**

---

## 1. なぜこの事業か（C04の結論）

あなたの新条件＝「人脈不使用・完全自動・匿名・低投資・SNS/アフィリOK」を満たす交点は実質ここ1つ。
さらにあなたの既存資産（Gemini→Claude→Notion→note→X の自動投稿パイプライン）が**そのまま転用できる**唯一の領域。

| 検討案 | 匿名 | 完全自動 | 低投資 | 30万現実性 | 判定 |
|---|---|---|---|---|---|
| **AIツール比較メディア×SaaSアフィリ** | ◎ | ◎ | ◎ | ★★★ | **採用** |
| 顔出しなしSNS（YouTube/TikTok）+広告 | ◎ | △(動画品質) | ◎ | ★★ | 補助(集客)に採用 |
| デジタル商品販売(Gumroad/BOOTH) | ◎ | ○ | ◎ | ★★ | 第2収益源に追加 |
| せどり/転売 | ○ | ✗(物流手作業) | ✗(在庫資金+古物商許可) | ★★ | 完全自動と非両立→除外 |

**金融・投資テーマは全案で禁止**（トレイダーズHD内定者＋金商法・投資助言業＝違法/内定取消リスク。匿名でも金商法は金商法）。

---

## 2. アーキテクチャ

```
[seed topics] data/keywords_seed.csv
      │  keyword_research.py（Claude/Gemini）
      ▼
[記事キュー] data/keywords.csv（pending/published）
      │  run_daily.py（毎日3本・Task Scheduler）
      ├─ generate_article.py  → content/*.md（E-E-A-T記事＋[[AFF:案件名]]）
      ├─ affiliate_inject.py  → アフィリンク置換（rel=sponsored・広告表記）
      └─ sns_repurpose.py     → 顔出しなしXスレッド（集客）
      ▼
[静的サイト] Hugo/Astro → Cloudflare Pages（無料・git push自動デプロイ）
      ▼
[収益] SaaS/AIツール/転職アフィリ（A8・もしも・afb・アクセストレード）
```

---

## 3. 法務・匿名運用（必読）

- **匿名は「読者・世間に対して」OK。ASP・税務には実名＋口座が必要**（報酬振込のため）。サイトはペンネーム/屋号で運営し、ASP登録だけ本名で行う。これで世間的には完全匿名を保てる。
- **ステマ規制（景表法・2023/10〜）**: アフィリ記事には必ず「広告」表記。→ `config.yaml` の `disclosure` を全記事冒頭に自動挿入済み。
- **特商法**: 純粋なアフィリ（自分で物を売らない）は原則 表記義務なし。ただし**プライバシーポリシー＋免責＋アフィリ開示**は必須。Amazon/楽天を使うなら各規約の表記を入れる。
- **景表法/薬機法**: 「必ず稼げる/治る/痩せる」等の断定禁止 → 生成プロンプトで禁止済み。
- **屋号・開業届**: 年20万超の所得は確定申告。屋号で開業届を出すと匿名運用しやすい（任意）。
- **インボイス**: 当面は免税事業者で可。ASPからの報酬は基本影響小。売上が育ったら検討。
- **【並行タスク】トレイダーズHDへ「入社前の非金融の個人事業/副業の可否」を文面で確認**（あなたの選択＝これから確認）。下にテンプレあり。

---

## 4. クイックスタート（runbook）

```bash
# 0) 依存インストール（このフォルダで。Desktop直下では実行しない＝pwd確認）
cd "C:/Users/yutat/OneDrive/デスクトップ/ai-auto-affiliate"
python -m venv .venv && .venv/Scripts/activate
pip install -r requirements.txt

# 1) APIキー設定（financial_bot と同じキーが使える）
cp .env.example .env   # .env を編集して ANTHROPIC_API_KEY / GEMINI_API_KEY を入れる

# 2) ブランド・ニッチ設定
#   config.yaml の brand.name / domain を決める（例: AIツールナビ）

# 3) キーワード設計（記事キューを生成）
cd src && python keyword_research.py --per-topic 15

# 4) まず1本テスト生成
python generate_article.py --keyword "Notion AI 使い方" --title "Notion AIの使い方を実際に試して解説【2026年版】" --intent commercial --affiliate-tag "Notion"

# 5) 毎日バッチ（3本生成→アフィリ置換）
python run_daily.py --count 3

# 6) SNS用スレッド生成（投稿は --post を付けた時だけ。まずはdry-run）
python sns_repurpose.py --file ../content/2026-06-19-notion-ai.md
```

### 公開（静的サイト・無料）
```bash
# Hugo例（最軽量）
hugo new site site && cd site
# テーマ導入後、../content/*.md を content/posts/ に配置 → git push
# Cloudflare Pages にリポジトリ連携すると push毎に自動デプロイ（無料）
```

---

## 5. 完全自動化（Windows Task Scheduler）

`run_report.ps1` の教訓（UTF-8 BOMなし・cmd /c 迂回・WakeToRun）に倣う。
毎朝 記事生成→アフィリ置換→（任意で）git push までを1タスク化する `run_daily.ps1` を `src/` に同梱。

```powershell
# 管理者PowerShellで（毎日 7:30 実行・スリープ復帰）
$action  = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-File `"C:\Users\yutat\OneDrive\デスクトップ\ai-auto-affiliate\src\run_daily.ps1`""
$trigger = New-ScheduledTaskTrigger -Daily -At 7:30am
$set     = New-ScheduledTaskSettingsSet -WakeToRun -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "AIAffiliateDaily" -Action $action -Trigger $trigger -Settings $set
```

---

## 6. ロードマップ（30万までの道筋）

### Phase 0 — 立ち上げ（Week 1）
- [ ] `config.yaml` のブランド名・ニッチ確定
- [ ] ドメイン取得（¥1,500/年・お名前.com等／屋号で）
- [ ] ASP登録（A8.net・もしもアフィリエイト・afb・アクセストレード）※本人確認＋口座
- [ ] APIキー設定・`keyword_research.py` で記事キュー150本生成
- [ ] 看板記事（cornerstone）を手直し込みで10本公開
- [ ] Cloudflare Pages デプロイ／Search Console 登録
- [ ] トレイダーズHDへ副業可否を確認（テンプレ下記）

### Phase 1 — 量と権威の構築（Month 1-3）目標 ¥1〜5万/月
- [ ] `run_daily.py` を Task Scheduler で毎日3本・自動公開
- [ ] 顔出しなしXアカウントで毎日スレッド自動投稿（集客）
- [ ] 内部リンク・トピッククラスター化／記事100本到達
- [ ] 最初の成約を確認

### Phase 2 — 最適化と高単価化（Month 3-6）目標 ¥5〜15万/月
- [ ] 上位表示記事に高単価案件（転職IT/AI人材 ¥15,000〜）を差し込み
- [ ] 勝ち記事のリライト・CVR改善／記事250本
- [ ] 第2収益源: 比較表をまとめた有料Notionテンプレ等をGumroad/BOOTHで匿名販売

### Phase 3 — 複利スケール（Month 6-12）目標 ¥15〜30万+/月
- [ ] 流入の複利化＋勝ちジャンルに集中投下
- [ ] 2サイト目（横展開）or YouTube faceless 追加

---

## 7. あなた / AI の分担

| あなた（人間が必須） | AI（このエンジンが自動） |
|---|---|
| ドメイン購入・ASP審査・APIキー | キーワード設計・記事生成 |
| ニッチ最終確定・初期10本の品質チェック | アフィリンク置換・広告表記 |
| 公開GO（git push）/ 副業確認 | SNSスレッド整形・内部リンク |
| 月1の数値確認・勝ち案件の選定 | 毎日のバッチ運用（無人） |

---

## 付録A: トレイダーズHD 副業確認メール（テンプレ）
```
件名: 入社前の個人事業（副業）の可否についてのご確認

人事ご担当者様
お世話になっております。内定者の野々口裕大です。
入社前の期間に、個人で「IT/Webメディア運営（アフィリエイト広告収入）」を
始めたいと考えております。金融・投資に関する情報発信や助言は一切行わず、
AIツール紹介など非金融分野に限定する想定です。
つきましては、(1)入社前の当該副業の可否 (2)入社後に継続する場合の申請手続き
(3)禁止される業務範囲 についてご教示いただけますでしょうか。
何卒よろしくお願いいたします。
```

## 付録B: 即金が必要な場合の並走策（任意）
アフィリが育つまでの数ヶ月、同じ記事生成エンジンの出力をクラウドワークス/ランサーズで
「AI記事作成代行（非金融）」として匿名販売すれば即現金化できる（1記事¥1,500〜7,000）。
本体メディアと違い人手が要るが、Phase 0-1の資金繰りに有効。
