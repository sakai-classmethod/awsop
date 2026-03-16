# 要件ドキュメント

## はじめに

awsop CLIツールにおいて、`AWS_PROFILE` 環境変数の export/unset を廃止する。現在、`format_export_commands()` で `export AWS_PROFILE={profile}` を出力し、`format_unset_commands()` で `unset AWS_PROFILE` を出力し、`run_aws_command()` で環境変数から `AWS_PROFILE` を削除しているが、これらの処理をすべて除去する。

`AWS_PROFILE` は AWS CLI/SDK がプロファイルベースの認証情報を参照するために使用する環境変数であり、awsop が STS で取得した一時認証情報（`AWS_ACCESS_KEY_ID` 等）と競合する可能性がある。awsop は独自の `AWSOP_PROFILE` でプロファイル名を管理しているため、`AWS_PROFILE` の設定は不要である。

## 用語集

- **Credentials_Manager**: 認証情報の取得・管理・フォーマットを担当するモジュール（`credentials_manager.py`）
- **OnePassword_Client**: 1Password CLI との統合を担当するクライアント（`onepassword.py`）
- **Export_Formatter**: `Credentials_Manager` 内の `format_export_commands()` メソッド。認証情報を `export` コマンド形式に変換する
- **Unset_Formatter**: `Credentials_Manager` 内の `format_unset_commands()` メソッド。環境変数の `unset` コマンドを生成する
- **AWS_Command_Runner**: `OnePassword_Client` 内の `run_aws_command()` メソッド。AWS コマンド実行時の環境変数を管理する
- **AWSOP_PROFILE**: awsop 独自のプロファイル名管理用環境変数

## 要件

### 要件 1: export コマンドから AWS_PROFILE を除去

**ユーザーストーリー:** 開発者として、awsop が `AWS_PROFILE` を export しないようにしたい。STS で取得した一時認証情報と `AWS_PROFILE` が競合するのを防ぐためである。

#### 受け入れ基準

1. WHEN 認証情報を export コマンド形式にフォーマットするとき、THE Export_Formatter SHALL `AWS_ACCESS_KEY_ID`、`AWS_SECRET_ACCESS_KEY`、`AWS_SESSION_TOKEN`、`AWS_REGION`、`AWS_DEFAULT_REGION`、`AWSOP_PROFILE`、`AWSOP_EXPIRATION` の export コマンドを出力する
2. WHEN 認証情報を export コマンド形式にフォーマットするとき、THE Export_Formatter SHALL `AWS_PROFILE` の export コマンドを出力に含めない
3. THE Export_Formatter SHALL プロファイル名を `AWSOP_PROFILE` 環境変数のみで管理する

### 要件 2: unset コマンドから AWS_PROFILE を除去

**ユーザーストーリー:** 開発者として、awsop の unset コマンドから `AWS_PROFILE` を除去したい。awsop が設定していない環境変数を unset する必要がないためである。

#### 受け入れ基準

1. WHEN 環境変数の unset コマンドを生成するとき、THE Unset_Formatter SHALL `AWS_ACCESS_KEY_ID`、`AWS_SECRET_ACCESS_KEY`、`AWS_SESSION_TOKEN`、`AWS_REGION`、`AWS_DEFAULT_REGION`、`AWSOP_PROFILE`、`AWSOP_EXPIRATION` の unset コマンドを出力する
2. WHEN 環境変数の unset コマンドを生成するとき、THE Unset_Formatter SHALL `AWS_PROFILE` の unset コマンドを出力に含めない

### 要件 3: AWS コマンド実行時の環境変数クリアから AWS_PROFILE を除去

**ユーザーストーリー:** 開発者として、`run_aws_command()` の環境変数クリアリストから `AWS_PROFILE` を除去したい。awsop が `AWS_PROFILE` を管理しなくなるため、クリア対象からも外す必要があるためである。

#### 受け入れ基準

1. WHEN AWS コマンドを実行するとき、THE AWS_Command_Runner SHALL `AWS_ACCESS_KEY_ID`、`AWS_SECRET_ACCESS_KEY`、`AWS_SESSION_TOKEN`、`AWS_DEFAULT_REGION`、`AWS_REGION`、`AWSOP_PROFILE`、`AWSOP_EXPIRATION` を環境変数から除去する
2. WHEN AWS コマンドを実行するとき、THE AWS_Command_Runner SHALL `AWS_PROFILE` を環境変数のクリア対象に含めない
