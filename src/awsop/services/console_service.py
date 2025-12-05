"""AWSコンソールURL生成サービス"""

import json
import logging
import urllib.parse
import urllib.request
from typing import Dict

logger = logging.getLogger(__name__)


class ConsoleService:
    """AWSコンソールURL生成サービス"""

    # サービスマッピング: 短縮名から完全なサービス名またはURLテンプレートへのマッピング
    SERVICE_MAPPING: Dict[str, str] = {
        # 一般的な短縮形
        "api": "apigateway",
        "c9": "cloud9",
        "cfn": "cloudformation",
        "cw": "cloudwatch",
        "ddb": "dynamodb",
        "eb": "elasticbeanstalk",
        "ec": "elasticache",
        "es": "elasticsearch",
        "gd": "guardduty",
        "k8s": "eks",
        "l": "lambda",
        "logs": "https://console.{amazon_domain}/cloudwatch/home?region={region}#logsV2:log-groups",
        "r53": "route53",
        "secret": "secretsmanager",
        "sfn": "states",
        "ssm": "systems-manager",
        # その他のマッピング
        "acm": "acm",
        "athena": "athena",
        "batch": "batch",
        "cloudfront": "cloudfront",
        "cloudtrail": "cloudtrail",
        "codebuild": "codebuild",
        "codecommit": "codecommit",
        "codedeploy": "codedeploy",
        "codepipeline": "codepipeline",
        "cognito": "cognito",
        "config": "config",
        "dynamodb": "dynamodb",
        "ec2": "ec2",
        "ecr": "ecr",
        "ecs": "ecs",
        "efs": "efs",
        "eks": "eks",
        "elasticache": "elasticache",
        "elasticbeanstalk": "elasticbeanstalk",
        "elb": "ec2/v2/home?region={region}#LoadBalancers:",
        "emr": "emr",
        "events": "events",
        "glue": "glue",
        "iam": "iam",
        "kinesis": "kinesis",
        "kms": "kms",
        "lambda": "lambda",
        "rds": "rds",
        "redshift": "redshift",
        "route53": "route53",
        "s3": "s3",
        "sagemaker": "sagemaker",
        "secretsmanager": "secretsmanager",
        "sns": "sns",
        "sqs": "sqs",
        "stepfunctions": "states",
        "vpc": "vpc",
        "waf": "wafv2",
    }

    def get_signin_token(
        self,
        access_key_id: str,
        secret_access_key: str,
        session_token: str,
        amazon_domain: str,
    ) -> str:
        """
        AWS Federation Endpointからサインイントークンを取得

        Args:
            access_key_id: アクセスキーID
            secret_access_key: シークレットアクセスキー
            session_token: セッショントークン
            amazon_domain: Amazonドメイン

        Returns:
            str: サインイントークン

        Raises:
            RuntimeError: トークン取得に失敗した場合
        """
        logger.info("サインイントークンを取得中...")

        # セッションJSONを作成
        session_data = {
            "sessionId": access_key_id,
            "sessionKey": secret_access_key,
            "sessionToken": session_token,
        }
        session_json = json.dumps(session_data)

        # Federation Endpoint URLを構築
        params = {
            "Action": "getSigninToken",
            "Session": session_json,
        }
        url = f"https://signin.{amazon_domain}/federation?{urllib.parse.urlencode(params)}"

        logger.debug(
            f"Federation Endpoint URL: https://signin.{amazon_domain}/federation"
        )

        try:
            # HTTPリクエストを送信
            with urllib.request.urlopen(url, timeout=30) as response:
                response_data = json.loads(response.read().decode("utf-8"))

            # サインイントークンを取得
            signin_token = response_data.get("SigninToken")
            if not signin_token:
                raise RuntimeError("サインイントークンがレスポンスに含まれていません")

            logger.info("サインイントークンの取得に成功しました")
            return signin_token

        except urllib.error.URLError as e:
            logger.error(f"Federation Endpointへの接続に失敗しました: {str(e)}")
            raise RuntimeError(
                f"AWS Federation Endpointへの接続に失敗しました: {str(e)}"
            ) from e
        except json.JSONDecodeError as e:
            logger.error(f"レスポンスのJSON解析に失敗しました: {str(e)}")
            raise RuntimeError(f"レスポンスの解析に失敗しました: {str(e)}") from e
        except Exception as e:
            logger.error(f"サインイントークンの取得に失敗しました: {str(e)}")
            raise RuntimeError(
                f"サインイントークンの取得に失敗しました: {str(e)}"
            ) from e

    def generate_console_url(
        self,
        signin_token: str,
        destination_url: str,
        amazon_domain: str,
    ) -> str:
        """
        コンソールURLを生成

        Args:
            signin_token: サインイントークン
            destination_url: デスティネーションURL
            amazon_domain: Amazonドメイン

        Returns:
            str: 完全なコンソールURL
        """
        logger.debug(f"コンソールURLを生成中: destination={destination_url}")

        # コンソールURLのパラメータを構築
        params = {
            "Action": "login",
            "Issuer": "",
            "Destination": destination_url,
            "SigninToken": signin_token,
        }

        # 完全なURLを生成
        console_url = f"https://signin.{amazon_domain}/federation?{urllib.parse.urlencode(params)}"

        logger.debug(f"生成されたコンソールURL: {console_url[:100]}...")
        return console_url

    def get_amazon_domain(self, region: str) -> str:
        """
        リージョンから適切なAmazonドメインを取得

        Args:
            region: AWSリージョン

        Returns:
            str: Amazonドメイン (aws.amazon.com, amazonaws-us-gov.com, amazonaws.cn)
        """
        # GovCloudリージョンの場合
        if region.startswith("us-gov-"):
            domain = "amazonaws-us-gov.com"
            logger.debug(f"GovCloudリージョン検出: {region} -> {domain}")
            return domain

        # 中国リージョンの場合
        if region.startswith("cn-"):
            domain = "amazonaws.cn"
            logger.debug(f"中国リージョン検出: {region} -> {domain}")
            return domain

        # 標準リージョンの場合
        domain = "aws.amazon.com"
        logger.debug(f"標準リージョン: {region} -> {domain}")
        return domain

    def build_destination_url(
        self,
        service: str,
        region: str,
        amazon_domain: str,
    ) -> str:
        """
        サービス名からデスティネーションURLを構築

        Args:
            service: サービス名または短縮名
            region: AWSリージョン
            amazon_domain: Amazonドメイン

        Returns:
            str: デスティネーションURL
        """
        logger.debug(
            f"デスティネーションURLを構築中: service={service}, region={region}"
        )

        # 完全なURL（http://またはhttps://で始まる）の場合はそのまま使用
        if service.startswith("http://") or service.startswith("https://"):
            logger.debug("完全なURLが指定されました")
            return service

        # サービスマッピングを確認
        mapped_service = self.SERVICE_MAPPING.get(service, service)
        logger.debug(f"サービスマッピング: {service} -> {mapped_service}")

        # マッピング結果が完全なURLテンプレートの場合
        if mapped_service.startswith("http://") or mapped_service.startswith(
            "https://"
        ):
            # テンプレート変数を置換
            destination_url = mapped_service.format(
                region=region,
                amazon_domain=amazon_domain,
            )
            logger.debug(f"テンプレートURLを展開: {destination_url}")
            return destination_url

        # サービス名からURLを構築
        # "console"の場合はコンソールホームページ
        if mapped_service == "console":
            destination_url = (
                f"https://console.{amazon_domain}/console/home?region={region}"
            )
        else:
            destination_url = (
                f"https://console.{amazon_domain}/{mapped_service}/home?region={region}"
            )

        logger.debug(f"構築されたデスティネーションURL: {destination_url}")
        return destination_url
