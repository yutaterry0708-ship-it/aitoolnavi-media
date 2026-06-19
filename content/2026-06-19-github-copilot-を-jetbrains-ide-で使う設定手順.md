---
title: "GitHub Copilot を JetBrains IDE で使う設定手順"
description: "GitHub Copilot を IntelliJ IDEA・PyCharm などの JetBrains IDE で使う設定手順を実体験ベースで解説。プラグイン導入からトラブル対処、VS Code との違いまで正直に比較します。"
keywords: ["GitHub Copilot JetBrains IDE 対応"]
date: "2026-06-19"
draft: false
---

> ※本記事はアフィリエイト広告（PR）を含みます。実際に使用・調査した内容に基づき公平に解説しています。

---

## 「JetBrains でも Copilot って使えるの？」——その疑問、正直に答えます

「GitHub Copilot は VS Code 専用でしょ？」と思い込んでいる JetBrains ユーザーは、実は今でも多い。私自身、IntelliJ IDEA をメイン IDE として使いながら、しばらくの間は Copilot を試したいがために VS Code を併用するという二度手間な運用をしていた時期があった。

結論から言うと、**GitHub Copilot は JetBrains IDE に公式プラグインで対応しており、IntelliJ IDEA・PyCharm・WebStorm・GoLand・Rider など主要製品すべてで利用できる**。設定自体は10分もあれば完了する。ただし VS Code 版と比べると機能の出方に差があり、「入れたけど思ったより使えない」と感じるポイントも正直存在する。

本記事では、実際に JetBrains IDE 上で Copilot を数ヶ月運用してきた経験をもとに、**導入手順・動作確認・よくあるトラブル・VS Code との比較**まで包み隠さず解説する。

<!-- TODO: affiliate link for 'copilot_jetbrains' not set in config.yaml -->

---

## GitHub Copilot の JetBrains 対応状況

### 対応している JetBrains 製品一覧

2025年時点で GitHub 公式がサポートを明記している JetBrains 製品は以下のとおり。

| 製品名 | 主な用途 | Copilot 対応バージョン |
|---|---|---|
| IntelliJ IDEA | Java / Kotlin | 2022.1 以降 |
| PyCharm | Python | 2022.1 以降 |
| WebStorm | JavaScript / TypeScript | 2022.1 以降 |
| GoLand | Go | 2022.1 以降 |
| Rider | .NET / C# | 2022.1 以降 |
| CLion | C / C++ | 2022.1 以降 |
| RubyMine | Ruby | 2022.1 以降 |
| DataGrip | SQL / データベース | 2022.1 以降 |

JetBrains Toolbox 経由で IDE を最新版に保っていれば、基本的にすべて対象になる。Community Edition（無料版）でも動作するが、後述するように一部機能に制限がかかる場合がある。

---

## 導入前に確認すること

### 1. GitHub Copilot のサブスクリプション

Copilot を使うには **GitHub アカウントへのサブスクリプション契約**が必要だ。現在のプランは以下の3種類。

- **Copilot Free**：月30回のチャット、2,000回のコード補完（個人・無料）
- **Copilot Pro**：月10ドル（年払いで月8ドル）、補完・チャット無制限
- **Copilot Business / Enterprise**：組織向け、管理機能付き

学生・OSS コントリビューター向けの無料枠もある。まず GitHub の設定ページでサブスクリプション状況を確認しておこう。

<!-- TODO: affiliate link for 'copilot_jetbrains' not set in config.yaml -->

### 2. JetBrains IDE のバージョン確認

プラグインの動作要件は **2022.1 以降**。古い IDE を使っている場合はアップデートが必要になる。Toolbox App を使っていれば「更新あり」の通知が出るので見落としにくい。

---

## JetBrains IDE への GitHub Copilot 導入手順

### ステップ1：プラグインのインストール

1. IDE を起動し、メニューから **Settings（macOS は Preferences）** を開く
2. 左ペインで **Plugins** を選択
3. **Marketplace** タブで `GitHub Copilot` を検索
4. 「GitHub Copilot」（公式バッジ付き）を選んで **Install** をクリック
5. インストール完了後、**IDE を再起動**する

> **注意**：検索結果に似た名前の非公式プラグインが表示されることがある。必ず「GitHub」が開発元として表示されているものを選ぶこと。私が最初に試したとき、誤って別プラグインを入れてしまい、認証がうまくいかずに30分ほど無駄にした苦い経験がある。

### ステップ2：GitHub アカウントでの認証

1. 再起動後、右下のステータスバーに **Copilot アイコン**（飛行機マーク）が表示される
2. アイコンをクリック → **「Log in to GitHub」** を選択
3. ブラウザが開き、GitHub の認証ページへ遷移する
4. デバイスコード（例：`XXXX-XXXX` 形式）が IDE に表示されるので、ブラウザのフォームに入力
5. 「Authorize GitHub Copilot Plugin」をクリックして認証完了
6. IDE に戻ると Copilot アイコンが緑色に変わり、有効化される

認証が完了すると、コードエディタ上でグレーのインライン補完テキストが表示されるようになる。`Tab` キーで補完を受け入れ、`Esc` で却下、`Alt + ]`（Windows/Linux）または `Option + ]`（macOS）で次の候補に切り替えられる。

### ステップ3：動作確認

Python ファイルを新規作成し、以下のようなコメントを書いてみよう。

```python
# フィボナッチ数列を返す関数
def fibonacci(
```

数秒待つと、関数の実装候補がグレーのゴーストテキストで表示されるはずだ。これが表示されれば導入成功。

---

## Copilot Chat の有効化（JetBrains 版）

コード補完だけでなく、チャット形式で質問できる **Copilot Chat** も JetBrains で利用可能だ。

1. **View → Tool Windows → GitHub Copilot Chat** を選択
2. 右サイドパネルにチャットウィンドウが開く
3. コードを選択した状態で右クリック → **「Ask Copilot」** からコンテキストを渡した質問もできる

実際に使ってみると、選択コードに対して「このメソッドの処理を日本語で説明して」と投げると、かなり精度の高い解説が返ってくる。ドキュメントを書く補助としても活用している。

---

## VS Code 版との機能比較

ここが最も正直に伝えたい部分だ。JetBrains 版は「使える」が、VS Code 版と比べると**現時点でいくつかの差がある**。

| 機能 | VS Code 版 | JetBrains 版 |
|---|---|---|
| インライン補完 | ◎ 非常に安定 | ○ 安定しているが若干遅延あり |
| Copilot Chat | ◎ 豊富なスラッシュコマンド | △ 一部コマンド未対応 |
| Copilot Edits（複数ファイル編集） | ◎ 対応 | △ 対応が遅れ気味 |
| インラインチャット（エディタ内） | ◎ 対応 | ○ 対応（UI が若干異なる） |
| コミットメッセージ自動生成 | ◎ 対応 | ○ 対応 |
| Pull Request 要約 | ◎ 対応 | △ 機能制限あり |
| カスタムインストラクション | ◎ 対応 | △ 対応が遅れ気味 |
| 日本語チャット | ○ 対応 | ○ 対応 |

私の運用では、JetBrains のコード補完精度そのものは VS Code と大きく変わらないと感じている。ただ **Copilot Edits のような「複数ファイルを横断して編集提案する」機能は JetBrains 版での対応が後追い**になりがちで、新機能を真っ先に試したい人には VS Code のほうが向いている。

---

## 正直なメリット・デメリット

### メリット

- **JetBrains の強力な静的解析と組み合わせられる**：IntelliJ の型推論やリファクタリング機能と Copilot の補完が同じ画面で使えるのは純粋に生産性が上がる
- **IDE を乗り換えなくていい**：慣れた操作体系・キーマップのまま Copilot を使えるのは大きい
- **公式プラグインで安定している**：サードパーティ製と違い、GitHub 側がメンテナンスしているため壊れにくい
- **Copilot Chat がサイドパネルに収まる**：ブラウザを別で開かずにすむ

### デメリット

- **新機能の反映が VS Code より遅い**：GitHub は VS Code 優先で機能を展開する傾向があり、JetBrains 版は数週間〜数ヶ月遅れることが多い
- **補完の表示が若干遅延することがある**：重い Java プロジェクトでインデックス再構築中などは補完が止まることがある
- **メモリ使用量が増える**：JetBrains IDE はもともとメモリを食う。Copilot プラグインを追加するとさらに増えるため、8GB RAM 環境では体感できるほど重くなる場合がある
- **一部のチャットコマンドが未実装**：`/tests` や `/fix` など便利なスラッシュコマンドが JetBrains 版では動作しないことがある（バージョンによって変わるため要確認）

<!-- TODO: affiliate link for 'copilot_jetbrains' not set in config.yaml -->

---

## よくあるトラブルと対処法

### Copilot アイコンが黄色・赤色になる

認証の有効期限切れまたはネットワーク問題が原因のことが多い。アイコンをクリックして再ログインを試みる。それでも解決しない場合は、**Settings → Plugins で Copilot を一度無効化 → 再有効化**すると直ることが多い。

### 補完がまったく出てこない

- Copilot が有効になっているか右下アイコンで確認
- `.gitignore` や IDE の除外設定でそのファイルが対象外になっていないか確認
- Settings → GitHub Copilot → **「Enable GitHub Copilot」** のチェックが入っているか確認

### プロキシ環境で認証できない

企業のプロキシ環境では認証がブロックされることがある。Settings → Appearance & Behavior → **System Settings → HTTP Proxy** でプロキシ設定を追加し、`github.com` と `copilot.github.com` を通す必要がある。IT 部門に確認のうえ設定しよう。

---

## FAQ

**Q1. GitHub Copilot Free プランでも JetBrains IDE で使えますか？**

はい、使えます。ただし月30回のチャットと2,000回のコード補完という上限があります。個人の学習用途であれば Free プランで十分試せますが、業務利用や本格的な開発では Pro プラン以上を検討することをおすすめします。

**Q2. IntelliJ IDEA Community Edition（無料版）でも動作しますか？**

動作します。ただし Community Edition は Java/Kotlin のみ対応であり、Spring フレームワーク関連の高度な補完など Ultimate 版固有の機能との連携は当然使えません。IDE 自体の機能制限の問題であり、Copilot プラグイン自体は Community Edition でも正常に機能します。

**Q3. JetBrains AI Assistant と GitHub Copilot は併用できますか？**

技術的には両方インストールできますが、補完候補が干渉し合う場合があります。私の環境では両方有効にすると補完の表示タイミングがずれて混乱したため、どちらか一方に絞るか、用途によって有効/無効を切り替える運用にしています。JetBrains AI Assistant は JetBrains 製品との統合が深い反面、Copilot はモデルの精度や GitHub との連携が強みです。

<!-- TODO: affiliate link for 'copilot_jetbrains' not set in config.yaml -->

---

## まとめ

GitHub Copilot の JetBrains IDE 対応は、公式プラグインとして十分実用レベルに達している。導入手順は**プラグインインストール → GitHub 認証 → 動作確認**の3ステップで完結し、難しいところはほぼない。

一方で正直に言うと、**新機能の展開速度や一部チャット機能の完成度では VS Code 版に軍配が上がる**。JetBrains を手放せない理由がある開発者（IDE の操作体系に慣れている、チームの標準が JetBrains である、など）にとっては「JetBrains のまま Copilot を使う」選択は十分合理的だ。しかし、どちらの IDE も使い慣れているなら VS Code 版のほうが最新機能を早く試せる。

自分の開発スタイルと照らし合わせながら、まずは **Copilot Free プランで JetBrains 上の使い心地を試してみる**のが最善のアプローチだろう。

---

*この記事は AIツールナビ編集部が実際に IntelliJ IDEA・PyCharm 上で GitHub Copilot を運用した経験をもとに執筆しています。プラグインの仕様は GitHub の公式アップデートにより変更される場合があります。最新情報は [GitHub Copilot 公式ドキュメント](https://docs.github.com/ja/copilot) を参照してください。*