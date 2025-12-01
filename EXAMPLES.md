# 使用例

このドキュメントでは、awsop の様々な使用例を紹介します。

## 目次

- [基本的な使い方](#基本的な使い方)
- [プロファイル管理](#プロファイル管理)
- [リージョンとセッション設定](#リージョンとセッション設定)
- [高度な使用例](#高度な使用例)
- [マルチアカウント運用](#マルチアカウント運用)
- [トラブルシューティング](#トラブルシューティング)

## 基本的な使い方

### プロファイルの切り替え

```bash
# プロファイルを指定して認証情報を取得
awsop production

# 成功すると以下のような出力が表示されます
# ✓ プロファイル 'production' の認証情報を取得しました
# 有効期限: 2025-12-01 15:30:00 JST
```

### 現在の認証状態を確認

```bash
# 環境変数を確認
echo $AWS_PROFILE
# => production

echo $AWSOP_EXPIRATION
# => 2025-12-01T15:30:00+09:00

# AWS CLI で確認
aws sts get-caller-identity
```

### 認証情報をクリア

```bash
# 環境変数をクリア
awsop --unset

# 確認
echo $AWS_PROFILE
# => (空)
```

## プロファイル管理

### プロファイル一覧を表示

```bash
# すべてのプロファイルを表示
awsop --list-profiles

# 出力例:
# production
# staging
# development
# sandbox
```

### export コマンドを確認

```bash
# eval せずに export コマンドを表示
awsop production --show-commands

# 出力例:
# export AWS_ACCESS_KEY_ID=ASIA...
# export AWS_SECRET_ACCESS_KEY=...
# export AWS_SESSION_TOKEN=...
# export AWS_REGION=ap-northeast-1
# export AWS_DEFAULT_REGION=ap-northeast-1
# export AWS_PROFILE=production
# export AWSOP_PROFILE=production
# export AWSOP_EXPIRATION=2025-12-01T15:30:00+09:00
```

## リージョンとセッション設定

### リージョンを指定

```bash
# 東京リージョン（デフォルト）
awsop production

# 米国西部リージョン
awsop production --region us-west-2

# 欧州リージョン
awsop production --region eu-west-1
```

### セッション名をカスタマイズ

```bash
# デフォルトのセッション名（awsop-<timestamp>）
awsop production

# カスタムセッション名
awsop production --session-name "deploy-v1.2.3"

# CloudTrail で確認すると、セッション名が表示されます
```

### ロール期間を指定

```bash
# デフォルト（1時間）
awsop production

# 2時間
awsop production --role-duration 7200

# 12時間（最大）
awsop production --role-duration 43200
```

## 高度な使用例

### 認証情報をファイルに書き込む

```bash
# ~/.aws/credentials に書き込む
awsop production --output-profile prod-temp

# 他のツールから使用
export AWS_PROFILE=prod-temp
terraform plan
```

### 直接ロール ARN を指定

```bash
# プロファイルを使わずにロールを引き受ける
awsop --role-arn arn:aws:iam::123456789012:role/MyRole

# ソースプロファイルを指定
awsop --role-arn arn:aws:iam::123456789012:role/MyRole \
      --source-profile base-profile

# セッション名とリージョンも指定
awsop --role-arn arn:aws:iam::123456789012:role/MyRole \
      --session-name "emergency-access" \
      --region us-east-1
```

### 外部 ID を使用

```bash
# サードパーティアカウントのロールを引き受ける
awsop --role-arn arn:aws:iam::999999999999:role/ThirdPartyRole \
      --external-id "my-unique-external-id"
```

### カスタム設定ファイルを使用

```bash
# 別の設定ファイルを使用
awsop production \
      --config-file ~/my-aws-configs/config \
      --credentials-file ~/my-aws-configs/credentials
```

## マルチアカウント運用

### ジャンプアカウント経由のアクセス

```bash
# ~/.aws/config の設定例
# [profile base]
# region = ap-northeast-1
#
# [profile production]
# role_arn = arn:aws:iam::111111111111:role/ProductionRole
# source_profile = base
# region = ap-northeast-1
#
# [profile staging]
# role_arn = arn:aws:iam::222222222222:role/StagingRole
# source_profile = base
# region = ap-northeast-1

# 本番環境にアクセス
awsop production

# ステージング環境にアクセス
awsop staging
```

### 複数のプロファイルを切り替える

```bash
# 本番環境で作業
awsop production
aws s3 ls

# ステージング環境に切り替え
awsop staging
aws s3 ls

# 開発環境に切り替え
awsop development
aws s3 ls
```

### 並行して複数のセッションを使用

```bash
# ターミナル1: 本番環境
awsop production
aws cloudformation describe-stacks

# ターミナル2: ステージング環境
awsop staging
aws cloudformation describe-stacks

# 各ターミナルで独立した認証情報が使用されます
```

## トラブルシューティング

### デバッグログを有効にする

```bash
# INFO レベルのログ
awsop production --info

# DEBUG レベルのログ（詳細）
awsop production --debug
```

### 1Password の認証に失敗する

```bash
# 1Password CLI が正しくインストールされているか確認
which op
op --version

# 1Password にサインインしているか確認
op account list

# サインインしていない場合
op signin
```

### プロファイルが見つからない

```bash
# プロファイル一覧を確認
awsop --list-profiles

# AWS 設定ファイルを確認
cat ~/.aws/config

# プロファイル名が正しいか確認（大文字小文字を区別）
```

### AssumeRole が失敗する

```bash
# デバッグログで詳細を確認
awsop production --debug

# role_arn が正しく設定されているか確認
grep -A 5 "profile production" ~/.aws/config

# IAM ポリシーを確認
# - ロールの信頼ポリシーが正しいか
# - MFA が必要な場合、設定されているか
```

### 認証情報の有効期限が切れた

```bash
# 現在の有効期限を確認
echo $AWSOP_EXPIRATION

# 認証情報を再取得
awsop production

# 長時間の作業には --role-duration を使用
awsop production --role-duration 7200
```

## ワークフロー例

### デプロイワークフロー

```bash
#!/bin/bash
# deploy.sh

# 本番環境の認証情報を取得
eval "$(awsop production --session-name "deploy-$(date +%Y%m%d-%H%M%S)")"

# デプロイ実行
echo "Deploying to production..."
aws cloudformation deploy \
  --template-file template.yaml \
  --stack-name my-stack \
  --capabilities CAPABILITY_IAM

# 完了後、認証情報をクリア
eval "$(awsop --unset)"
```

### マルチリージョンデプロイ

```bash
#!/bin/bash
# multi-region-deploy.sh

REGIONS=("ap-northeast-1" "us-west-2" "eu-west-1")

for region in "${REGIONS[@]}"; do
  echo "Deploying to $region..."
  eval "$(awsop production --region $region)"

  aws cloudformation deploy \
    --template-file template.yaml \
    --stack-name my-stack \
    --region $region
done

# 完了後、認証情報をクリア
eval "$(awsop --unset)"
```

### 定期的な認証情報の更新

```bash
#!/bin/bash
# refresh-credentials.sh

# 12時間ごとに認証情報を更新
while true; do
  echo "Refreshing credentials..."
  eval "$(awsop production --role-duration 43200)"

  # 12時間待機
  sleep 43200
done
```

## ベストプラクティス

### 1. セッション名を意味のあるものにする

```bash
# 悪い例
awsop production

# 良い例
awsop production --session-name "deploy-api-v2.1.0"
awsop production --session-name "debug-issue-123"
```

### 2. 長時間の作業には適切なロール期間を設定

```bash
# 短時間の作業（デフォルト1時間）
awsop production

# 長時間の作業（2-4時間）
awsop production --role-duration 7200

# 終日の作業（最大12時間）
awsop production --role-duration 43200
```

### 3. 作業終了後は認証情報をクリア

```bash
# 作業開始
awsop production

# 作業実行
aws s3 sync ./dist s3://my-bucket/

# 作業終了後、必ずクリア
awsop --unset
```

### 4. デバッグ時は詳細ログを有効にする

```bash
# 問題が発生した場合
awsop production --debug 2>&1 | tee awsop-debug.log

# ログファイルを確認
cat awsop-debug.log
```

### 5. スクリプトではエラーハンドリングを実装

```bash
#!/bin/bash
set -e  # エラー時に終了

# 認証情報を取得
if ! eval "$(awsop production)"; then
  echo "Failed to get credentials"
  exit 1
fi

# 作業実行
aws s3 ls

# クリーンアップ
eval "$(awsop --unset)"
```

---

その他の質問や使用例については、Issue を作成してください。
