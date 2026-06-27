---
name: awsop
description: |
  awsop CLI の使い方ガイド。1Password 連携による AWS 認証情報の取得、プロファイル切り替え、AWS マネジメントコンソールの起動方法を案内する。
  ユーザーが「AWS の認証情報を設定したい」「プロファイルを切り替えたい」「コンソールを開きたい」「awsop の使い方を教えて」と言ったとき、
  または awsop コマンドのオプションやトラブルシューティングについて質問があるときに使用する。
---

# awsop CLI 使い方ガイド

awsop は 1Password CLI (`op`) と Touch ID を使って、AWS の一時認証情報を安全に取得する CLI ツール。長期認証情報を平文ファイルに保存せず、必要なときにだけ STS AssumeRole で一時認証情報を取得する。Touch ID による対話認証が必要なため、ローカル開発環境専用であり、CI/CD パイプラインなどのヘッドレス環境では使用できない。

## 前提条件

- 1Password CLI (`op`) がインストール済みで、サインイン済みであること
- `~/.aws/config` に `role_arn` を含むプロファイルが定義されていること
- AWS 認証情報が 1Password に保存されていること

## インストール

Homebrew:

```bash
brew install sakai-classmethod/tap/awsop
```

Go で直接:

```bash
go install github.com/sakai-classmethod/awsop/cmd/awsop@latest
```

## 初期設定

シェルラッパー関数を `.zshrc` に追加する。これにより `awsop` の出力（export コマンド）が自動で `eval` され、環境変数が設定される。zsh 補完も同時に有効化される。

```bash
echo 'eval "$(awsop --init-shell)"' >> ~/.zshrc
source ~/.zshrc
```

`~/.aws/config` にプロファイルを定義する:

```ini
[profile production]
role_arn = arn:aws:iam::123456789012:role/MyRole
region = ap-northeast-1

[profile staging]
role_arn = arn:aws:iam::987654321098:role/MyRole
region = ap-northeast-1
```

## 基本操作

### プロファイル一覧

```bash
awsop --list-profiles    # or -l
```

### 認証情報の取得

```bash
awsop production
```

Touch ID 認証後、以下の環境変数が設定される:
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`
- `AWS_REGION`, `AWS_DEFAULT_REGION`
- `AWSOP_PROFILE`, `AWSOP_EXPIRATION`

同じプロファイルの認証情報がまだ有効（残り5分以上）なら、キャッシュが再利用されて Touch ID は求められない。

### プロファイルの切り替え

別のプロファイルを実行すると、同じ環境変数（`AWS_ACCESS_KEY_ID` など）が新しい認証情報で上書きされる。事前に `--unset` する必要はない。

```bash
# production から staging に切り替え
awsop staging
```

`AWSOP_PROFILE` を確認すれば、現在どのプロファイルの認証情報が設定されているかがわかる:

```bash
echo $AWSOP_PROFILE
```

### 認証情報のクリア

```bash
awsop --unset    # or -u
```

### export コマンドの確認（eval せずに表示）

```bash
awsop production --show-commands    # or -s
```

## AWS マネジメントコンソールの起動

```bash
awsop production -c                          # コンソールホームを開く
awsop production --console-service s3        # 特定サービスを開く
awsop production --console-service lambda    # Lambda を開く
awsop production --console-link              # URL のみ出力（ブラウザを開かない）
```

`-c`、`--console-service`、`--console-link` はそれぞれ単独で使用可能。`--console-service` を指定すると `-c` なしでもブラウザが開く。`-c` と `--console-link` は同時に使用できない。

### サービス短縮名

| 短縮名 | サービス | 短縮名 | サービス |
|:---|:---|:---|:---|
| `l` | Lambda | `cfn` | CloudFormation |
| `ddb` | DynamoDB | `cw` | CloudWatch |
| `logs` | CloudWatch Logs | `ssm` | Systems Manager |
| `r53` | Route 53 | `sfn` | Step Functions |
| `secret` | Secrets Manager | `k8s` | EKS |
| `api` | API Gateway | `gd` | GuardDuty |
| `c9` | Cloud9 | `eb` | Elastic Beanstalk |
| `ec` | ElastiCache | `es` | Elasticsearch |

完全なサービス名（`s3`, `ec2`, `lambda`, `iam` など）もそのまま使える。

## オプション一覧

| オプション | 短縮形 | 説明 |
|:---|:---|:---|
| `--list-profiles` | `-l` | プロファイル一覧を表示 |
| `--show-commands` | `-s` | export コマンドを表示 |
| `--unset` | `-u` | 環境変数をクリア |
| `--init-shell` | | シェルラッパー関数を出力 |
| `--console` | `-c` | AWS コンソールをブラウザで開く |
| `--console-service` | | 開くサービスを指定 |
| `--console-link` | | コンソール URL のみを出力 |
| `--force-refresh` | | キャッシュを無視して再取得 |
| `--region` | `-r` | AWS リージョンを指定 |
| `--session-name` | `-n` | AssumeRole のセッション名 |
| `--role-duration` | `-d` | ロール有効期間（秒、デフォルト 3600、最大 43200） |
| `--mfa-token` | `-m` | MFA トークンを指定 |
| `--output-profile` | `-o` | `~/.aws/credentials` に書き込むプロファイル名 |
| `--role-arn` | `-a` | プロファイルを使わず直接ロール ARN を指定 |
| `--source-profile` | `-p` | ソースプロファイル（`--role-arn` と併用） |
| `--external-id` | `-e` | 外部 ID |
| `--config-file` | | カスタム設定ファイルパス |
| `--credentials-file` | | カスタム認証情報ファイルパス |
| `--info` | `-i` | INFO ログを表示 |
| `--debug` | | DEBUG ログを表示 |
| `--version` | `-v` | バージョンを表示 |

## 高度な使い方

### 直接ロール ARN を指定

```bash
awsop --role-arn arn:aws:iam::123456789012:role/MyRole
awsop --role-arn arn:aws:iam::123456789012:role/MyRole --source-profile base
```

### 認証情報をファイルに書き込む

```bash
awsop production --output-profile prod-temp
# 他のツールから: export AWS_PROFILE=prod-temp
```

`~/.aws/credentials` に既存のプロファイルがある場合、そのセクションに `manager = awsop` が設定されている場合のみ上書きされる。それ以外の既存プロファイルは保護され、上書きされない。

### リージョン / セッション名 / ロール期間の指定

```bash
awsop production --region us-west-2
awsop production --session-name "deploy-v1.2.3"
awsop production --role-duration 7200
```

### キャッシュを無視して再取得

```bash
awsop production --force-refresh
```

### 外部 ID を使用

```bash
awsop --role-arn arn:aws:iam::999999999999:role/ThirdPartyRole --external-id "my-external-id"
```

## 出力の仕組み

- `stdout`: export / unset コマンドのみ（シェルの `eval` 用）
- `stderr`: スピナー、成功/エラーメッセージなどのユーザーフィードバック

シェルラッパー関数がこの分離を利用して、stdout を `eval` しつつ stderr をそのままターミナルに表示する。

## 環境変数

awsop が設定する環境変数:

| 変数 | 用途 |
|:---|:---|
| `AWS_ACCESS_KEY_ID` | 一時アクセスキー |
| `AWS_SECRET_ACCESS_KEY` | 一時シークレットキー |
| `AWS_SESSION_TOKEN` | セッショントークン |
| `AWS_REGION` | リージョン |
| `AWS_DEFAULT_REGION` | リージョン（レガシー互換） |
| `AWSOP_PROFILE` | 現在のプロファイル名（キャッシュ判定に使用） |
| `AWSOP_EXPIRATION` | 認証情報の有効期限（RFC3339 形式） |

## トラブルシューティング

### 1Password CLI が見つからない

```bash
which op          # パスを確認
op --version      # バージョンを確認
op account list   # サインイン状態を確認
brew install 1password-cli   # macOS でインストール
```

### プロファイルが見つからない

```bash
awsop --list-profiles                          # 一覧を確認
grep -A 5 "profile production" ~/.aws/config   # 設定を確認
```

プロファイル名は大文字小文字を区別する。`role_arn` が定義されていないプロファイルは使用できない。

### AssumeRole が失敗する

```bash
awsop production --debug   # 詳細ログで原因を確認
```

よくある原因:
- ロールの信頼ポリシーが正しくない
- MFA が必要だが設定されていない
- ロール ARN のタイプミス

### 認証情報の期限切れ

```bash
echo $AWSOP_EXPIRATION     # 有効期限を確認
awsop production           # 再取得（キャッシュが切れていれば自動で再認証）
```

### コンソールが開かない

```bash
awsop production --console-link   # URL のみ取得して手動でブラウザに貼り付け
awsop production -c --debug       # デバッグログで原因を確認
```
