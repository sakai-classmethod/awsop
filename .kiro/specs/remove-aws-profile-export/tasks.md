# 実装計画: AWS_PROFILE export 廃止

## 概要

awsop CLI ツールから `AWS_PROFILE` 環境変数の管理（export / unset / 環境変数クリア）を完全に除去する。変更は3つのメソッドに限定され、既存のプロパティベーステストとユニットテストを更新する。

## タスク

- [x] 1. format_export_commands() から AWS_PROFILE を除去
  - [x] 1.1 `src/awsop/app/credentials_manager.py` の `format_export_commands()` メソッドから `export AWS_PROFILE={profile}` 行を削除する
    - 出力が7行になることを確認する（8行から1行減）
    - `AWSOP_PROFILE` の export は維持する
    - _要件: 1.1, 1.2, 1.3_

  - [x] 1.2 `tests/property/test_export_commands.py` のプロパティテストを更新する
    - **Property 1: export コマンドの変数セットと値の正確性**
    - **検証: 要件 1.1, 1.2, 1.3**
    - `required_vars` リストから `AWS_PROFILE` を削除
    - `export AWS_PROFILE=` のアサーションを削除
    - `AWS_PROFILE` が出力に含まれないことのアサーションを追加
    - 行数の期待値を8から7に変更

- [x] 2. format_unset_commands() から AWS_PROFILE を除去
  - [x] 2.1 `src/awsop/app/credentials_manager.py` の `format_unset_commands()` メソッドから `unset AWS_PROFILE` 行を削除する
    - 出力が7行になることを確認する（8行から1行減）
    - _要件: 2.1, 2.2_

  - [x] 2.2 `tests/property/test_unset_commands.py` のプロパティテストを更新する
    - **Property 2: unset コマンドの変数セットの正確性**
    - **検証: 要件 2.1, 2.2**
    - `required_vars` リストから `AWS_PROFILE` を削除
    - `AWS_PROFILE` が出力に含まれないことのアサーションを追加
    - 行数の期待値を8から7に変更

- [x] 3. チェックポイント - export/unset の変更を確認
  - すべてのテストが通ることを確認し、不明点があればユーザーに質問する。

- [x] 4. run_aws_command() の環境変数クリアリストから AWS_PROFILE を除去
  - [x] 4.1 `src/awsop/services/onepassword.py` の `run_aws_command()` メソッドの `aws_env_vars` リストから `AWS_PROFILE` を削除する
    - クリア対象が7項目になることを確認する（8項目から1項目減）
    - _要件: 3.1, 3.2_

  - [x] 4.2 `tests/property/test_env_cleanup.py` を新規作成し、Property 3 のプロパティテストを実装する
    - **Property 3: 環境変数クリアの変数セットの正確性**
    - **検証: 要件 3.1, 3.2**
    - ランダムな環境変数辞書を生成し、対象7変数と `AWS_PROFILE` を含める
    - `run_aws_command()` 実行後の環境で対象7変数が除去され、`AWS_PROFILE` が保持されることを確認
    - `@settings(max_examples=100)` を設定

  - [x] 4.3 `tests/unit/test_onepassword.py` の既存ユニットテストを更新する
    - `test_run_aws_command_success` のアサーションを更新
    - `AWS_PROFILE` が環境に保持されることを確認するアサーションを追加
    - _要件: 3.1, 3.2_

- [x] 5. 最終チェックポイント - すべてのテストが通ることを確認
  - `uv run pytest tests/property/test_export_commands.py tests/property/test_unset_commands.py tests/property/test_env_cleanup.py tests/unit/test_onepassword.py -v` を実行
  - すべてのテストが通ることを確認し、不明点があればユーザーに質問する。

## 備考

- `*` マーク付きのタスクはオプションであり、MVP のためにスキップ可能
- 各タスクは具体的な要件を参照しトレーサビリティを確保
- チェックポイントで段階的な検証を実施
- プロパティテストは設計ドキュメントの正当性プロパティを検証する
