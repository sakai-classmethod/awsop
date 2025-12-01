# awsop

1Password 連携による AWS 認証情報管理ツール

## 概要

awsop は、1Password CLI を使用して AWS 認証情報を安全に管理し、AssumeRole による一時認証情報の取得を行う Python 製 CLI ツールです。

## 特徴

- 1Password 連携による安全な認証情報管理
- AWS STS AssumeRole のサポート
- シェル統合による簡単な環境変数設定
- Rich UI による視覚的なフィードバック

## インストール

```bash
# uvを使用してインストール
uv tool install awsop

# または、ローカルから開発版をインストール
uv tool install -e .
```

## 使用方法

### シェル統合のセットアップ

```bash
# .zshrcに追加
eval "$(awsop --init-shell)"
```

### プロファイルの切り替え

```bash
# プロファイルを指定して認証情報を取得
awsop my-profile

# リージョンを指定
awsop my-profile --region us-west-2

# ロール期間を指定
awsop my-profile --role-duration 7200
```

### その他のコマンド

```bash
# プロファイル一覧を表示
awsop --list-profiles

# 認証情報をクリア
awsop --unset

# バージョン情報を表示
awsop --version

# ヘルプを表示
awsop --help
```

## 開発

### 開発環境のセットアップ

```bash
# 依存関係をインストール
uv sync

# テストを実行
uv run pytest

# カバレッジ付きでテストを実行
uv run pytest --cov=src --cov-report=html
```

## ライセンス

MIT License
