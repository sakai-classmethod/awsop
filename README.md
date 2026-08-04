# awsop

[![Go](https://img.shields.io/badge/Go-1.24+-00ADD8.svg)](https://go.dev/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 目次

- [プロジェクト概要](#プロジェクト概要)
- [対象ユーザー](#対象ユーザー)
- [前提条件](#前提条件)
- [使い方](#使い方)
  - [インストール](#インストール)
  - [設定](#設定)
  - [実行](#実行)
  - [コンソール起動](#コンソール起動)
  - [高度な使用方法](#高度な使用方法)
  - [利用可能なオプション](#利用可能なオプション)
- [関連ドキュメント](#関連ドキュメント)

## プロジェクト概要

`awsop` を使うと、1Password に保存された AWS 認証情報を使って、安全かつ簡単に AWS アカウント間を切り替えられます。

従来の AWS 認証情報管理ツールとは異なり、`awsop` は長期認証情報を平文ファイルに保存しません。代わりに 1Password CLI と Touch ID を使用して、必要な時にだけ一時認証情報を取得します。シェル統合により、`awsop production` と入力するだけで本番環境の認証情報が環境変数に設定されます。

主な特徴:

- 1Password と Touch ID によるセキュアな認証（長期認証情報を平文で保存しない）
- `awsop profile-name` だけで認証情報を設定
- `-c` オプションで AWS マネジメントコンソールをブラウザで直接起動
- 有効な認証情報のキャッシュ再利用（不要な Touch ID 認証を回避）
- 豊富なオプション（リージョン、セッション名、ロール期間など）
- zsh 補完（プロファイル名、オプション、サービス名の補完）

## 対象ユーザー

このプロジェクトは、複数の AWS アカウント間を頻繁に切り替える開発者で、1Password を使用して認証情報を管理している方を対象としています。特に、長期認証情報の平文保存を禁止しているセキュリティポリシー環境や、MFA 必須のジャンプアカウント運用をしている方に最適です。

## 前提条件

`awsop` を使用するには、以下が必要です:

- Go 1.24 以上（ビルドする場合）
- [1Password CLI](https://developer.1password.com/docs/cli/)（`op` コマンド）がインストールされ、サインイン済みであること
- `~/.aws/config` に `role_arn` を含むプロファイルが定義されていること
- AWS 認証情報が 1Password に保存されていること

1Password CLI のインストール（macOS）:

```bash
brew install 1password-cli
op signin
```

## 使い方

### インストール

Homebrew（macOS / Linux）:

```bash
brew install sakai-classmethod/tap/awsop
```

ソースからビルドする場合（Go 1.24 以上が必要）:

```bash
go install github.com/sakai-classmethod/awsop/cmd/awsop@latest
```

### 設定

1. シェルラッパー関数を `.zshrc` に追加する

    ```bash
    echo 'eval "$(awsop --init-shell)"' >> ~/.zshrc
    source ~/.zshrc
    ```

    これにより `awsop` コマンドの出力が自動的に `eval` され、環境変数が設定されます。zsh 補完も同時に有効化されます。

2. `~/.aws/config` にプロファイルを定義する

    ```ini
    [profile production]
    role_arn = arn:aws:iam::123456789012:role/MyRole
    region = ap-northeast-1

    [profile staging]
    role_arn = arn:aws:iam::987654321098:role/MyRole
    region = ap-northeast-1
    ```

### 実行

1. 利用可能なプロファイルを確認する

    ```bash
    awsop --list-profiles
    ```

2. プロファイルを指定して認証情報を取得する

    ```bash
    awsop production
    ```

    1Password で Touch ID 認証が求められます。認証が成功すると、以下の環境変数が設定されます:

    - `AWS_ACCESS_KEY_ID`
    - `AWS_SECRET_ACCESS_KEY`
    - `AWS_SESSION_TOKEN`
    - `AWS_REGION` / `AWS_DEFAULT_REGION`
    - `AWSOP_PROFILE`
    - `AWSOP_EXPIRATION`

    同じプロファイルの認証情報がまだ有効な場合（残り5分以上）、キャッシュが再利用され 1Password CLI を呼び出しません。

3. 認証情報をクリアする

    ```bash
    awsop --unset
    ```

### コンソール起動

認証情報を使って AWS マネジメントコンソールをブラウザで開きます:

```bash
# コンソールホームを開く
awsop production -c

# 特定のサービスを開く
awsop production --console-service s3
awsop production --console-service lambda

# URL のみを取得（ブラウザを開かない）
awsop production --console-link
```

短縮名も使用できます（`l` → Lambda、`cfn` → CloudFormation、`ddb` → DynamoDB など）。

### 高度な使用方法

リージョンを指定:

```bash
awsop production --region us-west-2
```

ロール期間を指定:

```bash
awsop production --role-duration 7200
```

1 時間を超えるロール期間を指定する（`mfa_serial` があるプロファイル）:

プロファイルに `mfa_serial` が定義されている場合、通常の 1Password shell plugin 経由のパスは MFA セッションを経由するため、AWS の role chaining の仕様により 3600 秒が上限になります。3600 秒を超える期間（ロール側の MaxSessionDuration 以内）を指定するには、以下のいずれかを使用します。

1. `awsop_op_item` を設定して 1Password から直接取得する（推奨）

    ```ini
    [profile production]
    role_arn = arn:aws:iam::123456789012:role/MyRole
    region = ap-northeast-1
    mfa_serial = arn:aws:iam::111111111111:mfa/user
    awsop_op_item = AWS
    awsop_op_vault = Private
    ```

    `awsop_op_item` には長期認証情報と TOTP を保存している 1Password アイテム名（または ID）を指定します。`awsop_op_vault` は任意で、アイテムが属する vault を指定します。この設定がある状態で `awsop production -d 43200` のように 3600 秒超を指定すると、`op item get` で長期キーと TOTP を取得し、GetSessionToken セッションを挟まずに AssumeRole を実行します。長期キーはメモリ内のみで保持され、ディスクへは書き込まれません。

2. `--mfa-token` で MFA トークンを手入力する

    ```bash
    awsop production -d 43200 -m 123456
    ```

    source credentials は `--source-profile`（またはプロファイルの `source_profile`）で指定した `~/.aws/credentials` のセクションから解決されます。

どちらの手段も使えない状態で 3600 秒超を指定した場合は、AssumeRole を呼ぶ前にエラーで即終了します。

認証情報を `~/.aws/credentials` に書き込む:

```bash
awsop production --output-profile prod-temp
```

直接ロール ARN を指定:

```bash
awsop --role-arn arn:aws:iam::123456789012:role/MyRole
```

キャッシュを無視して再取得:

```bash
awsop production --force-refresh
```

### 利用可能なオプション

| オプション | 短縮形 | 説明 |
| :--- | :--- | :--- |
| `--list-profiles` | `-l` | 利用可能なプロファイル一覧を表示 |
| `--show-commands` | `-s` | export コマンドを表示（eval せずに確認） |
| `--unset` | `-u` | 環境変数をクリア |
| `--init-shell` | - | シェルラッパー関数を出力 |
| `--console` | `-c` | AWS コンソールをブラウザで開く |
| `--console-service` | - | 開くサービスを指定（例: s3, lambda） |
| `--console-link` | - | コンソール URL のみを出力 |
| `--force-refresh` | - | 有効な認証情報があっても再取得 |
| `--region` | `-r` | AWS リージョンを指定 |
| `--session-name` | `-n` | AssumeRole のセッション名を指定 |
| `--role-duration` | `-d` | ロールの有効期間（秒）を指定 |
| `--mfa-token` | `-m` | MFA トークンを指定 |
| `--output-profile` | `-o` | 認証情報を `~/.aws/credentials` に書き込む |
| `--role-arn` | `-a` | 直接ロール ARN を指定 |
| `--source-profile` | `-p` | ソースプロファイルを指定 |
| `--external-id` | `-e` | 外部 ID を指定 |
| `--config-file` | - | カスタム設定ファイルを指定 |
| `--credentials-file` | - | カスタム認証情報ファイルを指定 |
| `--info` | `-i` | INFO レベルのログを表示 |
| `--debug` | - | DEBUG レベルのログを表示 |
| `--version` | `-v` | バージョン情報を表示 |
| `--help` | `-h` | ヘルプを表示 |

## 関連ドキュメント

- [EXAMPLES.md](EXAMPLES.md) - 様々なシナリオでの使用例
- [CONTRIBUTING.md](CONTRIBUTING.md) - 開発環境のセットアップとテスト方法
- [CHANGELOG.md](CHANGELOG.md) - バージョンごとの変更内容
