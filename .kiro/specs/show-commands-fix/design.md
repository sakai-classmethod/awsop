# 設計書

## 概要

`-s`/`--show-commands`オプションの動作を修正し、AWSume と同様の動作を実現します。具体的には：

- `-s`オプションなし：有効期限情報のみを標準エラー出力に表示
- `-s`オプションあり：有効期限情報を標準エラー出力に表示した後、export コマンドを標準出力に表示

この変更により、シェルスクリプトでの利用が容易になり、かつ対話的な利用時にも適切な情報が表示されます。

## アーキテクチャ

現在の実装では、`cli.py`の`main()`関数内で以下の処理が行われています：

1. 認証情報の取得
2. export コマンドの生成と標準出力への出力
3. 有効期限情報の表示（ConsoleUI 経由）

この設計では、以下の問題があります：

- `show_commands`フラグが実際の動作に影響を与えていない
- export コマンドが常に標準出力に出力される
- 有効期限情報が ConsoleUI 経由で出力されるため、標準エラー出力に出力される

### 修正後のアーキテクチャ

1. 認証情報の取得
2. 有効期限情報の表示（ConsoleUI 経由、標準エラー出力）
3. `show_commands`フラグが True の場合のみ、export コマンドを標準出力に出力

## コンポーネントとインターフェース

### 影響を受けるコンポーネント

#### cli.py の main() 関数

現在の実装：

```python
# export コマンドを標準出力に出力（要件 1.4, 5.4）
export_commands = credentials_manager.format_export_commands(credentials)
print(export_commands)

# --show-commands オプションがない場合は、有効期限も表示
if not show_commands:
    # 有効期限情報を表示
    ui.info(f"\\[{effective_profile}] Credentials will expire {expiration_str}")
```

修正後の実装：

```python
# 有効期限情報を常に表示（標準エラー出力）
ui.info(f"\\[{effective_profile}] Credentials will expire {expiration_str}")

# --show-commands オプションが指定された場合のみ、export コマンドを標準出力に出力
if show_commands:
    export_commands = credentials_manager.format_export_commands(credentials)
    print(export_commands)
```

### データモデル

既存のデータモデルに変更はありません。

## 正確性プロパティ

_プロパティとは、システムのすべての有効な実行において真であるべき特性や動作のことです。これは、人間が読める仕様と機械で検証可能な正確性保証の橋渡しとなります。_

### プロパティ 1: show-commands フラグが True の場合の完全な動作

*任意の*有効なプロファイルと認証情報に対して、`show_commands=True`で実行した場合、標準エラー出力に有効期限情報が含まれ、かつ標準出力に export コマンド（AWS_ACCESS_KEY_ID、AWS_SECRET_ACCESS_KEY、AWS_SESSION_TOKEN、AWS_REGION、AWS_DEFAULT_REGION を含む）が含まれる必要があります。

**検証: 要件 1.1, 1.2, 1.3, 2.1, 2.3**

### プロパティ 2: show-commands フラグが False の場合の完全な動作

*任意の*有効なプロファイルと認証情報に対して、`show_commands=False`で実行した場合、標準エラー出力に有効期限情報が含まれ、かつ標準出力に export コマンドが含まれない必要があります。

**検証: 要件 1.4, 1.5, 2.2, 2.4**

## エラーハンドリング

既存のエラーハンドリングに変更はありません。

## テスト戦略

### ユニットテスト

既存のユニットテストに変更はありません。

### プロパティベーステスト

Hypothesis を使用してプロパティベーステストを実装します。各プロパティベーステストは最低 100 回の反復を実行します。

#### テスト 1: show-commands フラグが True の場合の完全な動作

**Feature: show-commands-fix, Property 1: show-commands フラグが True の場合の完全な動作**

ランダムなプロファイル名と認証情報を生成し、`-s`オプション付きで CLI を実行します。以下を検証します：

- 標準エラー出力に有効期限情報（`Credentials will expire`を含む文字列）が含まれる
- 標準出力に以下の export コマンドが含まれる：
  - `export AWS_ACCESS_KEY_ID=...`
  - `export AWS_SECRET_ACCESS_KEY=...`
  - `export AWS_SESSION_TOKEN=...`
  - `export AWS_REGION=...`
  - `export AWS_DEFAULT_REGION=...`

#### テスト 2: show-commands フラグが False の場合の完全な動作

**Feature: show-commands-fix, Property 2: show-commands フラグが False の場合の完全な動作**

ランダムなプロファイル名と認証情報を生成し、`-s`オプションなしで CLI を実行します。以下を検証します：

- 標準エラー出力に有効期限情報（`Credentials will expire`を含む文字列）が含まれる
- 標準出力に export コマンドが含まれない

### 統合テスト

既存の統合テストを更新し、`-s`オプションの動作を検証します。

## 実装の詳細

### cli.py の変更

1. export コマンドの出力位置を変更
2. `show_commands`フラグの条件分岐を反転
3. 有効期限情報の表示を常に実行

### テストの追加

1. `tests/property/test_show_commands.py`を新規作成
2. 上記のプロパティベーステストを実装
3. 既存の統合テストを更新

## セキュリティ考慮事項

- export コマンドには機密情報（認証情報）が含まれるため、標準出力への出力は慎重に扱う必要があります
- 既存の実装と同様、認証情報は標準出力に出力されますが、これはシェルスクリプトでの利用を想定した設計です

## パフォーマンス考慮事項

パフォーマンスへの影響はありません。
