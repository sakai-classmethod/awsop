"""シェルラッパー関数の生成"""


def generate_shell_wrapper() -> str:
    """
    zsh用のシェルラッパー関数と補完スクリプトを生成

    Returns:
        str: シェルスクリプト文字列
    """
    return """# awsop シェルラッパー関数
function awsop() {
  # ヘルプ、バージョン、リストなどの情報表示オプションをチェック
  local info_option=false
  for arg in "$@"; do
    case "$arg" in
      -h|--help|-v|--version|-l|--list-profiles|--init-shell|-s|--show-commands|-c|--console|--console-service|--console-link)
        info_option=true
        break
        ;;
    esac
  done

  if [[ "$info_option" == "true" ]]; then
    # 情報表示オプションの場合は eval せずに直接実行
    command awsop "$@"
    return $?
  fi

  # 通常の認証情報取得の場合は eval
  local output
  # stdout のみをキャプチャ（stderr はそのままターミナルに表示）
  output=$(command awsop "$@")
  local exit_code=$?

  if [[ $exit_code -eq 0 ]]; then
    # export コマンドを eval
    eval "$output"
  fi
  return $exit_code
}

# zsh 補完（正規表現による部分一致）
_awsop() {
  local -a profiles options
  local prev_word="${words[CURRENT-1]}"
  local current_word="${words[CURRENT]}"
  
  # オプションリストの定義
  options=(
    '-h:ヘルプを表示'
    '--help:ヘルプを表示'
    '-s:exportコマンドを表示'
    '--show-commands:exportコマンドを表示'
    '-u:環境変数をクリア'
    '--unset:環境変数をクリア'
    '-l:プロファイル一覧を表示'
    '--list-profiles:プロファイル一覧を表示'
    '--init-shell:シェルラッパー関数を出力'
    '-c:AWSコンソールをブラウザで開く'
    '--console:AWSコンソールをブラウザで開く'
    '--console-service:開くサービスを指定'
    '--console-link:コンソールURLのみを出力'
    '-r:AWSリージョンを指定'
    '--region:AWSリージョンを指定'
    '-n:セッション名を指定'
    '--session-name:セッション名を指定'
    '-d:ロール期間を指定（秒）'
    '--role-duration:ロール期間を指定（秒）'
    '-m:MFAトークンを指定'
    '--mfa-token:MFAトークンを指定'
    '-o:出力プロファイル名を指定'
    '--output-profile:出力プロファイル名を指定'
    '-a:ロールARNを指定'
    '--role-arn:ロールARNを指定'
    '-p:ソースプロファイルを指定'
    '--source-profile:ソースプロファイルを指定'
    '-e:外部IDを指定'
    '--external-id:外部IDを指定'
    '--config-file:設定ファイルパスを指定'
    '--credentials-file:認証情報ファイルパスを指定'
    '-i:INFOレベルのログを表示'
    '--info:INFOレベルのログを表示'
    '--debug:DEBUGレベルのログを表示'
    '-v:バージョンを表示'
    '--version:バージョンを表示'
  )

  # AWSサービス一覧（--console-service用）
  services=(
    'acm:AWS Certificate Manager'
    'api:API Gateway (短縮形)'
    'apigateway:API Gateway'
    'athena:Amazon Athena'
    'batch:AWS Batch'
    'c9:Cloud9 (短縮形)'
    'cfn:CloudFormation (短縮形)'
    'cloud9:AWS Cloud9'
    'cloudformation:AWS CloudFormation'
    'cloudfront:Amazon CloudFront'
    'cloudtrail:AWS CloudTrail'
    'cloudwatch:Amazon CloudWatch'
    'codebuild:AWS CodeBuild'
    'codecommit:AWS CodeCommit'
    'codedeploy:AWS CodeDeploy'
    'codepipeline:AWS CodePipeline'
    'cognito:Amazon Cognito'
    'config:AWS Config'
    'cw:CloudWatch (短縮形)'
    'ddb:DynamoDB (短縮形)'
    'dynamodb:Amazon DynamoDB'
    'eb:Elastic Beanstalk (短縮形)'
    'ec:ElastiCache (短縮形)'
    'ec2:Amazon EC2'
    'ecr:Amazon ECR'
    'ecs:Amazon ECS'
    'efs:Amazon EFS'
    'eks:Amazon EKS'
    'elasticache:Amazon ElastiCache'
    'elasticbeanstalk:AWS Elastic Beanstalk'
    'elb:Elastic Load Balancing'
    'emr:Amazon EMR'
    'es:Elasticsearch (短縮形)'
    'events:Amazon EventBridge'
    'glue:AWS Glue'
    'gd:GuardDuty (短縮形)'
    'guardduty:Amazon GuardDuty'
    'iam:AWS IAM'
    'k8s:EKS (短縮形)'
    'kinesis:Amazon Kinesis'
    'kms:AWS KMS'
    'l:Lambda (短縮形)'
    'lambda:AWS Lambda'
    'logs:CloudWatch Logs'
    'r53:Route 53 (短縮形)'
    'rds:Amazon RDS'
    'redshift:Amazon Redshift'
    'route53:Amazon Route 53'
    's3:Amazon S3'
    'sagemaker:Amazon SageMaker'
    'secret:Secrets Manager (短縮形)'
    'secretsmanager:AWS Secrets Manager'
    'sfn:Step Functions (短縮形)'
    'sns:Amazon SNS'
    'sqs:Amazon SQS'
    'ssm:Systems Manager (短縮形)'
    'states:AWS Step Functions'
    'stepfunctions:AWS Step Functions'
    'systems-manager:AWS Systems Manager'
    'vpc:Amazon VPC'
    'waf:AWS WAF'
    'wafv2:AWS WAFv2'
  )
  
  # プロファイルリストを取得
  if [[ -f ~/.aws/config ]]; then
    profiles=($(sed -nE 's/^\\[(profile )?([^]]+)\\]/\\2/p' ~/.aws/config))
  fi

  # 文脈に応じて補完タイプを決定
  if [[ "$prev_word" == "--source-profile" ]] || [[ "$prev_word" == "--output-profile" ]] || [[ "$prev_word" == "-p" ]] || [[ "$prev_word" == "-o" ]]; then
    # プロファイル名を必要とするオプションの後
    _describe 'profile' profiles
  elif [[ "$prev_word" == "--console-service" ]]; then
    # サービス名を必要とするオプションの後
    _describe 'service' services
  elif [[ "$current_word" == -* ]]; then
    # 現在の単語が - で始まる場合はオプション補完
    _describe 'option' options
  else
    # それ以外はプロファイル補完
    _describe 'profile' profiles
  fi
}
compdef _awsop awsop

# zsh の matcher-list 設定で部分一致を有効化
# ユーザーは .zshrc に以下を追加することを推奨:
# zstyle ':completion:*' matcher-list 'm:{a-z}={A-Z}' 'r:|[._-]=* r:|=*' 'l:|=* r:|=*'
"""
