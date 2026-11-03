---
description: プロジェクトを再解析して CLAUDE.md / .claude/settings.json の改善案を出す（承認まで変更しない）
---
ultrathink を適用し、このプロジェクトの CLAUDE.md と .claude/settings.json を見直すための環境解析を行ってください。

重要事項:
- まずは Plan Mode として振る舞い、コードや設定ファイルを一切変更しないでください。
- ディレクトリ構造、使用技術（`requirements.txt` など）、Lint/Test の設定、CI（`.github/workflows/`）、アーキテクチャのパターンを調査してください。
- 既存の CLAUDE.md と .claude/settings.json を読んだうえで、次の2つを提案してください。
  - CLAUDE.md の更新案（200行未満。ビルド/テストコマンドと重要なアーキテクチャ上の決定事項だけを書き、Linter で代替できるスタイル規則は除く）
  - 安全性を高め、自動チェックなどの hooks を提供する .claude/settings.json の更新案
- 私が「適用して」と許可を出した後にのみ、実際にファイルを作成・保存してください。
