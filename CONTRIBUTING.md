# 開発者ガイド

awsop プロジェクトへの貢献に興味を持っていただき、ありがとうございます！

## 目次

- [開発環境のセットアップ](#開発環境のセットアップ)
- [開発ワークフロー](#開発ワークフロー)
- [テスト](#テスト)
- [コーディング規約](#コーディング規約)
- [コミットメッセージ](#コミットメッセージ)
- [プルリクエスト](#プルリクエスト)

## 開発環境のセットアップ

### 前提条件

- Python 3.11 以上
- [uv](https://github.com/astral-sh/uv) パッケージマネージャー
- [1Password CLI](https://developer.1password.com/docs/cli/)
- Git

### セットアップ手順

1. **リポジトリをフォーク・クローン**

```bash
git clone <your-fork-url>
cd awsop
```

2. **依存関係をインストール**

```bash
# 開発依存関係を含めてインストール
uv sync

# 開発モードでツールとしてインストール
uv tool install -e .
```

3. **動作確認**

```bash
# バージョン情報を表示
awsop --version

# テストを実行
uv run pytest
```

## 開発ワークフロー

### ブランチ戦略

- `main`: 安定版
- `develop`: 開発版
- `feature/*`: 新機能
- `bugfix/*`: バグ修正
- `hotfix/*`: 緊急修正

### 開発の流れ

1. **Issue を作成**

新機能やバグ修正を始める前に、Issue を作成して議論してください。

2. **ブランチを作成**

```bash
# 新機能の場合
git checkout -b feature/my-new-feature

# バグ修正の場合
git checkout -b bugfix/fix-something
```

3. **コードを書く**

- テストを先に書く（TDD）
- コードを実装
- テストが通ることを確認

4. **コミット**

```bash
git add .
git commit -m "feat: 新機能の説明"
```

5. **プッシュしてプルリクエストを作成**

```bash
git push origin feature/my-new-feature
```

## テスト

### テストの種類

awsop では 3 種類のテストを実装しています：

1. **ユニットテスト** (`tests/unit/`): 個別のコンポーネントをテスト
2. **プロパティベーステスト** (`tests/property/`): Hypothesis を使用した網羅的なテスト
3. **統合テスト** (`tests/integration/`): エンドツーエンドのフローをテスト

### テストの実行

```bash
# すべてのテストを実行
uv run pytest

# 特定のディレクトリのテストを実行
uv run pytest tests/unit/
uv run pytest tests/property/
uv run pytest tests/integration/

# 特定のテストファイルを実行
uv run pytest tests/unit/test_onepassword.py

# 特定のテスト関数を実行
uv run pytest tests/unit/test_onepassword.py::test_check_availability

# カバレッジ付きで実行
uv run pytest --cov=src --cov-report=html

# 詳細な出力
uv run pytest -v

# 失敗したテストのみ再実行
uv run pytest --lf
```

### テストの書き方

#### ユニットテスト

```python
def test_profile_manager_get_profile():
    """プロファイル取得のテスト"""
    manager = ProfileManager()
    profile = manager.get_profile("test-profile")
    assert profile.name == "test-profile"
```

#### プロパティベーステスト

```python
from hypothesis import given, strategies as st

@given(st.text(min_size=1))
def test_property_profile_reading(profile_name: str):
    """Feature: awsop-cli-migration, Property 1: プロファイル設定の読み取り"""
    # プロパティのテスト実装
    pass
```

### テストカバレッジ

- 目標: 80% 以上
- カバレッジレポートは `htmlcov/index.html` で確認できます

```bash
# カバレッジレポートを生成
uv run pytest --cov=src --cov-report=html

# ブラウザで開く
open htmlcov/index.html
```

## コーディング規約

### Python スタイルガイド

- [PEP 8](https://pep8-ja.readthedocs.io/ja/latest/) に準拠
- 型ヒントを使用
- docstring を記述（Google スタイル）

### コードフォーマット

```bash
# Ruff でフォーマット
uv run ruff format src tests

# リント
uv run ruff check src tests

# 自動修正
uv run ruff check --fix src tests
```

### 命名規則

- **変数・関数**: `snake_case`
- **クラス**: `PascalCase`
- **定数**: `UPPER_SNAKE_CASE`
- **プライベート**: `_leading_underscore`

### docstring の例

```python
def assume_role(
    role_arn: str,
    session_name: str,
    duration: int = 3600,
) -> Credentials:
    """ロールを引き受けて認証情報を取得する

    Args:
        role_arn: 引き受けるロールの ARN
        session_name: セッション名
        duration: 有効期間（秒）

    Returns:
        取得した認証情報

    Raises:
        AssumeRoleError: ロールの引き受けに失敗した場合
    """
    pass
```

## コミットメッセージ

### フォーマット

```
<type>: <subject>

<body>

<footer>
```

### Type

- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメントのみの変更
- `style`: コードの意味に影響しない変更（空白、フォーマットなど）
- `refactor`: バグ修正や機能追加を伴わないコード変更
- `perf`: パフォーマンス改善
- `test`: テストの追加・修正
- `chore`: ビルドプロセスやツールの変更

### 例

```bash
feat: リージョン指定オプションを追加

--region オプションでAWSリージョンを指定できるようにした。
プロファイルの設定よりも優先される。

Closes #123
```

## プルリクエスト

### チェックリスト

プルリクエストを作成する前に、以下を確認してください：

- [ ] テストが通る
- [ ] 新しいコードにテストを追加した
- [ ] ドキュメントを更新した
- [ ] コードがフォーマットされている
- [ ] コミットメッセージが規約に従っている

### プルリクエストのテンプレート

```markdown
## 概要

このプルリクエストの目的を簡潔に説明してください。

## 変更内容

- 変更点 1
- 変更点 2

## 関連 Issue

Closes #123

## テスト

テスト方法を記述してください。

## スクリーンショット（該当する場合）

UI の変更がある場合は、スクリーンショットを添付してください。
```

## デバッグ

### ログの有効化

```bash
# INFO レベルのログ
awsop production --info

# DEBUG レベルのログ
awsop production --debug
```

### Python デバッガー

```python
# コードにブレークポイントを設定
import pdb; pdb.set_trace()

# または Python 3.7+
breakpoint()
```

### テストのデバッグ

```bash
# 詳細な出力
uv run pytest -vv

# 標準出力を表示
uv run pytest -s

# 失敗時に pdb を起動
uv run pytest --pdb
```

## リリースプロセス

1. バージョン番号を更新（`pyproject.toml`）
2. CHANGELOG.md を更新
3. タグを作成

```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

## 質問・サポート

- Issue を作成
- ディスカッションで質問

---

貢献していただき、ありがとうございます！
