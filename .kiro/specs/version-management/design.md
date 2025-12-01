# 設計ドキュメント

## 概要

awsop ツールのバージョン管理を改善し、Single Source of Truth (SSOT) の原則に従って`pyproject.toml`を唯一のバージョン情報源とする。現在、バージョン情報が`pyproject.toml`と`src/awsop/__init__.py`の両方にハードコードされており、手動同期が必要で同期忘れのリスクがある。

この設計では、Python 標準ライブラリの`importlib.metadata`を使用してバージョン情報を動的に取得し、パッケージ未インストール時のフォールバック処理を実装する。これにより、開発環境と本番環境の両方で一貫した動作を実現し、保守性と信頼性を向上させる。

## アーキテクチャ

### 現在のアーキテクチャ

```
pyproject.toml (version = "1.0.0")
    ↓ (手動同期が必要)
src/awsop/__init__.py (__version__ = "1.0.0")
    ↓
src/awsop/cli.py (from awsop import __version__)
    ↓
awsop -v コマンド
```

**問題点:**

- バージョン情報が 2 箇所に存在
- 手動同期が必要
- 同期忘れのリスク

### 新しいアーキテクチャ

```
pyproject.toml (version = "1.0.0") ← 唯一の情報源
    ↓
importlib.metadata.version("awsop")
    ↓
src/awsop/__init__.py (__version__ = 動的取得)
    ↓
src/awsop/cli.py (from awsop import __version__)
    ↓
awsop -v コマンド
```

**改善点:**

- バージョン情報は`pyproject.toml`のみに存在
- 自動的に同期される
- 同期忘れのリスクがゼロ

## コンポーネントとインターフェース

### 1. バージョン取得モジュール (`src/awsop/__init__.py`)

**責務:**

- `importlib.metadata`を使用してバージョン情報を動的に取得
- パッケージ未インストール時のフォールバック処理
- `__version__`変数の提供

**インターフェース:**

```python
# 公開API
__version__: str  # バージョン文字列（例: "1.0.0" または "unknown"）
```

**実装詳細:**

```python
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("awsop")
except PackageNotFoundError:
    __version__ = "unknown"
```

### 2. CLI モジュール (`src/awsop/cli.py`)

**責務:**

- `__version__`をインポートして使用
- `--version`/`-v`オプションの処理
- バージョン情報の表示

**変更点:**

- インポート部分は変更なし: `from awsop import __version__`
- バージョン表示ロジックは変更なし

## データモデル

### バージョン情報

**型:** `str`

**形式:**

- 通常時: セマンティックバージョニング形式（例: "1.0.0", "2.1.3"）
- フォールバック時: "unknown"

**制約:**

- `pyproject.toml`のバージョンは PEP 440 に準拠
- 空文字列は許可されない

## エラーハンドリング

### 1. パッケージ未インストールエラー

**シナリオ:** パッケージがインストールされていない状態で`importlib.metadata.version()`を呼び出す

**エラー:** `PackageNotFoundError`

**処理:**

```python
try:
    __version__ = version("awsop")
except PackageNotFoundError:
    __version__ = "unknown"
```

**結果:** "unknown"を返し、プログラムは正常に動作を継続

### 2. その他の例外

**シナリオ:** 予期しない例外が発生

**処理:** 基本的には`PackageNotFoundError`のみをキャッチするが、万が一の場合に備えて広範な例外処理も検討可能

**推奨:** 明示的に`PackageNotFoundError`のみをキャッチし、他の例外は伝播させる（デバッグのため）

## テスト戦略

### ユニットテスト

1. **インストール済み環境でのバージョン取得**

   - パッケージがインストールされている状態で`__version__`が正しい値を返すことを確認
   - `pyproject.toml`のバージョンと一致することを確認

2. **フォールバック動作**

   - `PackageNotFoundError`が発生した場合に"unknown"が返されることを確認
   - モックを使用して例外をシミュレート

3. **CLI バージョン表示**
   - `awsop -v`が正しい形式で出力することを確認
   - `awsop --version`が同じ出力をすることを確認

### プロパティベーステスト

このプロジェクトでは Hypothesis を使用してプロパティベーステストを実装します。各プロパティベーステストは最低 100 回の反復を実行します。

## 正確性プロパティ

_プロパティとは、システムのすべての有効な実行において真であるべき特性や動作のことです。本質的には、システムが何をすべきかについての形式的な記述です。プロパティは、人間が読める仕様と機械で検証可能な正確性保証との橋渡しとなります。_

### Property 1: バージョン文字列の型保証

*任意の*バージョン取得において、返される値は文字列型でなければならない

**検証: 要件 2.4**

**説明:** `__version__`変数は常に文字列型である必要があります。これにより、バージョン情報を使用するコード（CLI 表示、ログ出力など）が型エラーなく動作することが保証されます。

**テスト方法:**

- インストール済み環境とフォールバック環境の両方で`__version__`の型を確認
- `isinstance(__version__, str)`が常に`True`を返すことを検証

### 具体的なテストケース

以下は、プロパティではなく具体的な例やエッジケースとしてテストすべき項目です：

#### Example 1: インストール済み環境でのバージョン取得

パッケージがインストールされている状態で、`__version__`が`pyproject.toml`で定義されたバージョンと一致することを確認

**検証: 要件 2.2**

#### Example 2: CLI バージョン表示（-v）

`awsop -v`を実行した際に、"awsop X.Y.Z"形式で出力されることを確認

**検証: 要件 4.1**

#### Example 3: CLI バージョン表示（--version）

`awsop --version`を実行した際に、`-v`と同じ出力が得られることを確認

**検証: 要件 4.2**

#### Example 4: 編集可能モードでのインストール

`uv tool install -e .`でインストールした場合に、正しいバージョンが取得できることを確認

**検証: 要件 5.1**

#### Example 5: 通常モードでのインストール

通常のインストール方法で正しいバージョンが取得できることを確認

**検証: 要件 5.2**

#### Edge Case 1: パッケージ未インストール時のフォールバック

`PackageNotFoundError`が発生した場合に、"unknown"が返され、プログラムが正常に動作を継続することを確認

**検証: 要件 3.1, 3.2, 3.3, 3.4**

**テスト方法:**

- `importlib.metadata.version`をモックして`PackageNotFoundError`を発生させる
- `__version__`が"unknown"になることを確認
- 例外が伝播しないことを確認
