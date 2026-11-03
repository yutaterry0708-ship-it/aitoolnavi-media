# AIツールナビ（aitoolnavi-media）

AIツール/SaaS の比較記事を LLM で毎日自動生成し、静的サイトとして公開するアフィリエイトメディア。
Python（CI は 3.11）。ビルドツール・テストスイートなし。設定は `config.yaml`、秘密情報は `.env`（コミット禁止）。

## コマンド

スクリプトは **`src/` をカレントにして実行**する（`from llm import ...` が解決できなくなるため）。

```bash
pip install -r requirements.txt markdown    # markdown は static_publisher に必要だが requirements.txt に未記載
cd src
python setup_check.py                        # APIキー・依存の確認（ネットワーク不要）
python static_publisher.py                   # content/*.md → docs/ を再生成（ローカル完結・無料）
python static_publisher.py --serve           # http://localhost:8080 でプレビュー
python run_daily.py --count 3                # ⚠ API課金: キューから記事生成＋アフィリ置換
python keyword_research.py --per-topic 15    # ⚠ API課金: keywords_seed.csv → keywords.csv を拡張
```

テストは無い。変更後の確認は「構文チェック（PostToolUse hook で自動）」＋「`static_publisher.py` を実行して `git diff docs/` を確認」。

## IMPORTANT: 外部に副作用があるコマンド（実行前に必ずユーザー確認）

| コマンド | 副作用 |
|---|---|
| `run_daily.py` / `generate_article.py` / `keyword_research.py` / `traffic/*.py` の生成系 | Anthropic API 課金 |
| `traffic/x_auto_poster.py --post`, `sns_repurpose.py --post` | X に実投稿 |
| `wp_publisher.py`（`--dry-run` なし） | WordPress に公開 |
| `traffic/note_publisher.py`（`--dry-run` なし） | note.com に公開 |
| `master` への push | 本番サイトに反映 |

試すだけなら `--dry-run` / `--post` なしで実行する。

## 作業の進め方

- 新機能・バグ修正は、コードを書く前に影響範囲を調べて計画を示す（数行で済む修正は除く）。
- 設計判断を伴うタスクは複数案を比較してから実装する。
- 破壊的な変更（ファイル・データの削除、`keywords.csv` の一括書き換えなど）は事前に承認を得る。

## パイプライン（本番 = GitHub Actions）

`.github/workflows/daily.yml` が毎日 22:30 UTC（7:30 JST）に実行し、`master` に直接コミットする。

1. `run_daily.py --count 3` — `data/keywords.csv` の `status=pending` を上から N 件生成 → `content/YYYY-MM-DD-<slug>.md`。行を `published` / `error` に更新
2. `affiliate_inject.py` — `[[AFF:案件名]]` を `config.yaml` の `affiliate.links` で置換
3. `static_publisher.py` — `content/*.md` → `docs/<slug>/index.html`、`index.html` / `sitemap.xml` / `robots.txt`
4. `traffic/x_auto_poster.py`（失敗しても続行）
5. `content/ docs/ data/keywords.csv data/sns_queue.csv` をコミット & push

`src/run_all.ps1` / `src/run_daily.ps1` はローカル Windows Task Scheduler 用の経路（パスは `C:\Users\yutat\...` 固定）。

## 設計上の決定・落とし穴

- IMPORTANT: **`docs/` は生成物。直接編集しない**（毎回上書きされる）。例外は手管理の `docs/CNAME`。見た目を変えるときは `src/static_publisher.py` のテンプレート（`HTML_TEMPLATE` など）を編集して再生成する。
- **`keyword_research.py` は CI に入っていない**。キューが全件 `published` になると記事生成が止まり、差分がないのでコミットも発生しない。
- **アフィリ置換は破壊的**: URL 未設定の `[[AFF:x]]` は `<!-- TODO: affiliate link for 'x' ... -->` に置き換わり、元のプレースホルダーは消える。後から `config.yaml` に URL を入れても既存記事には自動反映されない。
- ブランド名・ドメイン・広告表記は `config.yaml` と `static_publisher.py`（ハードコード）の二重管理。片方を変えたらもう片方も直す。
- LLM 呼び出しは必ず `src/llm.py`（`call_claude` / `call_llm_json`、リトライ付き）を経由する。モデル名は `config.yaml` の `llm.*` で管理。
- `.env` は `load_dotenv(override=True)` で読む（空のシステム環境変数を上書きするための意図的な指定）。
- IMPORTANT: `.env` の値（APIキー・パスワード）をコード・ログ・コミット・チャットに出さない。
- 依存を追加するときは `requirements.txt` と `daily.yml` の `pip install` 行の**両方**を更新する（CI は requirements.txt を使っていない）。
- `data/keywords.csv` のスキーマ: `keyword,intent,affiliate_tag,title,status`（status: `pending` / `published` / `error`）。

## コンテンツ上の制約（プロンプト・記事を編集するとき）

- IMPORTANT: 金融・投資・医療の情報や助言は**一切扱わない**（法務・就業上の理由で全面禁止）。
- 「必ず稼げる / 治る / 痩せる」等の断定表現は禁止（景表法・薬機法）。
- 広告表記（`content.disclosure`）は景表法のステマ規制上必須。削除しない。
- アフィリリンクは `rel="sponsored nofollow noopener"` を維持する。
- 実体験を装った虚偽の固有数値を書かない。

## Windows 用スクリプト

- `.ps1` は **UTF-8（BOMなし）**で保存する。
- PowerShell から Python を呼ぶときは `cmd /c "... >> log 2>&1"` 経由にする（stderr 出力で NativeCommandError になるのを回避）。
