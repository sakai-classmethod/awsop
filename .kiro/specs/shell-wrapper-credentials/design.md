# 設計ドキュメント

## 概要

本設計は、awsop コマンドが AWSume と同様の動作を実現するための変更を定義する。主な変更点は以下の通り：

1. デフォルト動作で常に export コマンドを標準出力に出力
2. `--show-commands`オプション使用時は標準エラー出力に export コマンドを表示
3. シェルラッパー関数が`--show-commands`を情報表示オプションとして扱う

## アーキテクチャ

### 現在のアーキテクチャ

```
ユーザー → シェルラッパー関数 → Python CLI
                ↓                    ↓
              eval                stdout: (なし)
                                  stderr: 有効期限情報
```

### 新しいアーキテクチャ

**デフォルト動作（`-s`なし）:**

```
ユーザー → シェルラッパー関数 → Python CLI
                ↓                    ↓
              eval                stdout: exportコマンド
                                  stderr: 有効期限情報
```

**`--show-commands`オプション:**

```
ユーザー → シェルラッパー関数 → Python CLI
                ↓                    ↓
           (evalしない)          stdout: (なし)
                                  stderr: 有効期限情報 + exportコマンド
```

## コンポーネントとインターフェース

### 1. CLI 層（cli.py）

**変更点:**

- デフォルトで常に export コマンドを標準出力に出力
- `--show-commands`オプション使用時は標準エラー出力にも export コマンドを表示

**インターフェース:**

```python
def main(
    ...
    show_commands: bool = False,
    ...
) -> None:
    # 認証情報取得後

    # 常にexportコマンドを標準出力に出力（要件1.1）
    export_commands = credentials_manager.format_export_commands(credentials)
    print(export_commands)  # stdout

    # --show-commandsオプション使用時は標準エラー出力にも表示（要件2.1）
    if show_commands:
        ui.info(export_commands)  # stderr
```

### 2. シェルラッパー関数（wrapper.py）

**変更点:**

- `--show-commands`（`-s`）を情報表示オプションとして扱う
- 情報表示オプション使用時は eval しない

**インターフェース:**

```bash
function awsop() {
  # 情報表示オプションをチェック（-s を追加）
  local info_option=false
  for arg in "$@"; do
    case "$arg" in
      -h|--help|-v|--version|-l|--list-profiles|--init-shell|-s|--show-commands)
        info_option=true
        break
        ;;
    esac
  done

  if [[ "$info_option" == "true" ]]; then
    # 情報表示オプションの場合はevalせずに直接実行
    command awsop "$@"
    return $?
  fi

  # 通常の認証情報取得の場合はeval
  local output
  output=$(command awsop "$@")
  local exit_code=$?

  if [[ $exit_code -eq 0 ]]; then
    eval "$output"
  fi
  return $exit_code
}
```

### 3. CredentialsManager（app/credentials_manager.py）

**変更なし:**

- `format_export_commands()`メソッドは既に存在
- export コマンドの形式は変更なし

### 4. ConsoleUI（ui/console.py）

**変更なし:**

- `info()`メソッドで標準エラー出力に表示
- 既存の実装で対応可能

## データモデル

変更なし。既存の Credentials モデルを使用。

## 正しさのプロパティ

_プロパティは、システムのすべての有効な実行において真であるべき特性や動作の形式的な記述です。プロパティは、人間が読める仕様と機械で検証可能な正しさの保証との橋渡しとなります。_

### Property 1: デフォルト動作での export コマンド出力

*任意の*有効なプロファイルと認証情報に対して、`--show-commands`オプションなしで実行した場合、標準出力に export コマンドが含まれ、標準エラー出力には有効期限情報のみが含まれる必要があります。

**検証: 要件 1.1, 1.4, 1.5**

### Property 2: show-commands オプション使用時の動作

*任意の*有効なプロファイルと認証情報に対して、`--show-commands`オプションを指定した場合、標準出力に export コマンドが含まれず、標準エラー出力に有効期限情報と export コマンドの両方が含まれる必要があります。

**検証: 要件 2.1, 2.2**

### Property 3: シェルラッパー関数の eval 動作

*任意の*コマンドライン引数に対して、`-s`または`--show-commands`が含まれる場合、シェルラッパー関数は eval を実行せず、含まれない場合は eval を実行する必要があります。

**検証: 要件 3.1, 3.2, 3.3, 3.4**

### Property 4: 環境変数の設定

*任意の*有効なプロファイルと認証情報に対して、シェルラッパー関数経由で`--show-commands`なしで実行した場合、AWS_ACCESS_KEY_ID、AWS_SECRET_ACCESS_KEY、AWS_SESSION_TOKEN、AWS_REGION、AWS_DEFAULT_REGION が環境変数に設定される必要があります。

**検証: 要件 1.2, 1.3**

## エラーハンドリング

既存のエラーハンドリングを維持：

- 認証失敗時は標準エラー出力にエラーメッセージを表示
- 終了コード 1 で終了
- export コマンドは出力しない

## テスト戦略

### ユニットテスト

1. **CLI 層のテスト**

   - デフォルト動作で export コマンドが標準出力に出力されることを確認
   - `--show-commands`使用時に標準エラー出力にも export コマンドが表示されることを確認

2. **シェルラッパー関数のテスト**
   - `-s`が情報表示オプションとして認識されることを確認
   - 情報表示オプション使用時に eval が実行されないことを確認

### プロパティベーステスト

1. **Property 1 のテスト**

   - Hypothesis を使用してランダムなプロファイルと認証情報を生成
   - デフォルト動作で標準出力に export コマンドが含まれることを検証
   - 標準エラー出力に export コマンドが含まれないことを検証

2. **Property 2 のテスト**

   - Hypothesis を使用してランダムなプロファイルと認証情報を生成
   - `--show-commands`使用時に標準エラー出力に export コマンドが含まれることを検証
   - 標準出力に export コマンドが含まれないことを検証

3. **Property 3 のテスト**

   - シェルスクリプトのテストフレームワークを使用
   - `-s`オプションの有無でシェルラッパー関数の動作が変わることを検証

4. **Property 4 のテスト**
   - 統合テストとして実装
   - シェルラッパー関数経由で実行後、環境変数が設定されていることを検証

### 統合テスト

1. **エンドツーエンドテスト**

   - 実際のシェル環境でシェルラッパー関数を実行
   - AWS CLI が認証情報を使用できることを確認

2. **後方互換性テスト**
   - 既存のテストを更新して実行
   - すべてのテストが通ることを確認

## 実装の注意点

### 1. 標準出力と標準エラー出力の使い分け

- **標準出力**: シェルラッパー関数がキャプチャして eval する内容

  - デフォルト: export コマンド
  - `--show-commands`: 何も出力しない

- **標準エラー出力**: ユーザーへの情報表示
  - デフォルト: 有効期限情報のみ
  - `--show-commands`: 有効期限情報 + export コマンド

### 2. シェルラッパー関数の更新

`--init-shell`コマンドで生成されるシェルラッパー関数を更新する必要がある。既存ユーザーは`--init-shell`を再実行して更新する必要がある。

### 3. テストの更新

既存の`test_show_commands.py`のテストを更新する必要がある：

- Property 1: 標準出力に export コマンドが含まれることを検証（現在は含まれないことを検証している）
- Property 2: 標準エラー出力に export コマンドが含まれることを検証（現在は標準出力を検証している）

### 4. ドキュメントの更新

- README.md の使用例を更新
- `--show-commands`オプションの説明を更新

## 移行計画

1. **Phase 1: CLI 層の変更**

   - `cli.py`を更新してデフォルトで export コマンドを出力
   - `--show-commands`使用時に標準エラー出力にも表示

2. **Phase 2: シェルラッパー関数の更新**

   - `wrapper.py`を更新して`-s`を情報表示オプションとして扱う
   - `--init-shell`で新しいシェルラッパー関数を生成

3. **Phase 3: テストの更新**

   - 既存のテストを新しい動作に合わせて更新
   - 新しいプロパティベーステストを追加

4. **Phase 4: ドキュメントの更新**
   - README.md を更新
   - CHANGELOG に変更内容を記載

## パフォーマンスへの影響

- 標準出力への export コマンド出力は既存の処理と同等
- パフォーマンスへの影響はほぼなし

## セキュリティへの影響

- 認証情報の取り扱いは変更なし
- 標準出力に認証情報が含まれるが、これは既存の動作と同じ
- セキュリティへの影響はなし
