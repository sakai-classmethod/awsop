"""認証情報の取得と管理"""

import logging
import subprocess
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from awsop.services.onepassword import OnePasswordClient
from awsop.services.aws_sts import STSClient

logger = logging.getLogger(__name__)


@dataclass
class Credentials:
    """AWS認証情報"""

    access_key_id: str
    secret_access_key: str
    session_token: str
    expiration: datetime
    region: str
    profile: str


class CredentialsManager:
    """認証情報管理クラス"""

    def __init__(
        self,
        onepassword_client: Optional[OnePasswordClient] = None,
        sts_client: Optional[STSClient] = None,
    ):
        """
        認証情報マネージャーを初期化

        Args:
            onepassword_client: 1Password CLIクライアント（テスト用）
            sts_client: AWS STSクライアント（テスト用）
        """
        self.onepassword_client = onepassword_client or OnePasswordClient()
        self.sts_client = sts_client or STSClient()

    def assume_role(
        self,
        role_arn: str,
        session_name: str,
        duration: int,
        region: str,
        profile: str,
        external_id: Optional[str] = None,
        mfa_token: Optional[str] = None,
    ) -> Credentials:
        """
        ロールを引き受けて認証情報を取得

        Args:
            role_arn: 引き受けるロールのARN
            session_name: セッション名
            duration: セッションの有効期間（秒）
            region: AWSリージョン
            profile: プロファイル名
            external_id: 外部ID（オプション）
            mfa_token: MFAトークン（オプション）

        Returns:
            Credentials: 取得した認証情報

        Raises:
            RuntimeError: 認証情報の取得に失敗した場合
        """
        logger.info(f"ロールを引き受けます: {role_arn}")

        try:
            # 1Password CLI経由でAssumeRoleを実行
            # mfa_tokenが指定されている場合は、直接STSClientを使用
            # 指定されていない場合は、1Password CLI経由で実行
            if mfa_token:
                logger.debug(
                    "MFAトークンが指定されているため、直接STSClientを使用します"
                )
                response = self.sts_client.assume_role(
                    role_arn=role_arn,
                    role_session_name=session_name,
                    duration_seconds=duration,
                    external_id=external_id,
                )
            else:
                logger.debug("1Password CLI経由でAssumeRoleを実行します")
                # 1Password CLIの利用可能性をチェック
                if not self.onepassword_client.check_availability():
                    raise RuntimeError(
                        "1Password CLIが利用できません。opコマンドをインストールしてください。"
                    )

                # op plugin run経由でAssumeRoleを実行
                command = [
                    "sts",
                    "assume-role",
                    "--role-arn",
                    role_arn,
                    "--role-session-name",
                    session_name,
                    "--duration-seconds",
                    str(duration),
                ]

                if external_id:
                    command.extend(["--external-id", external_id])

                response = self.onepassword_client.run_aws_command(command)

            # レスポンスから認証情報を抽出
            credentials_data = response["Credentials"]

            # Expirationをdatetimeオブジェクトに変換
            expiration = credentials_data["Expiration"]
            if isinstance(expiration, str):
                # ISO 8601形式の文字列をdatetimeに変換
                from dateutil import parser as date_parser

                expiration = date_parser.isoparse(expiration)

            # Credentialsオブジェクトを作成
            credentials = Credentials(
                access_key_id=credentials_data["AccessKeyId"],
                secret_access_key=credentials_data["SecretAccessKey"],
                session_token=credentials_data["SessionToken"],
                expiration=expiration,
                region=region,
                profile=profile,
            )

            logger.info("認証情報の取得に成功しました")
            return credentials

        except subprocess.CalledProcessError as e:
            logger.error(f"1Password CLIの実行に失敗しました: {str(e)}")
            raise RuntimeError("1Password での認証に失敗しました") from e
        except json.JSONDecodeError as e:
            logger.error(f"1Password CLIの出力解析に失敗しました: {str(e)}")
            raise RuntimeError("1Password の出力を解析できませんでした") from e
        except KeyError as e:
            logger.error(
                f"AssumeRoleのレスポンスに必要なフィールドがありません: {str(e)}"
            )
            raise RuntimeError("ロールの引き受けに失敗しました") from e
        except Exception as e:
            logger.error(f"認証情報の取得に失敗しました: {str(e)}")
            raise RuntimeError(f"認証情報の取得に失敗しました: {str(e)}") from e

    def format_export_commands(self, credentials: Credentials) -> str:
        """
        export コマンド形式で出力

        Args:
            credentials: 認証情報

        Returns:
            str: export コマンド形式の文字列
        """
        # 有効期限をISO 8601形式に変換
        if isinstance(credentials.expiration, datetime):
            expiration_str = credentials.expiration.isoformat()
        else:
            expiration_str = str(credentials.expiration)

        # export コマンドを生成（要件1.1, 1.2, 1.3）
        # AWS_PROFILE は awsop が管理しないため除外
        commands = [
            f"export AWS_ACCESS_KEY_ID={credentials.access_key_id}",
            f"export AWS_SECRET_ACCESS_KEY={credentials.secret_access_key}",
            f"export AWS_SESSION_TOKEN={credentials.session_token}",
            f"export AWS_REGION={credentials.region}",
            f"export AWS_DEFAULT_REGION={credentials.region}",
            f"export AWSOP_PROFILE={credentials.profile}",
            f"export AWSOP_EXPIRATION={expiration_str}",
        ]

        return "\n".join(commands)

    def format_unset_commands(self) -> str:
        """
        unset コマンド形式で出力

        Returns:
            str: unset コマンド形式の文字列
        """
        # unset コマンドを生成（要件2.1, 2.2）
        # AWS_PROFILE は awsop が管理しないため除外
        commands = [
            "unset AWS_ACCESS_KEY_ID",
            "unset AWS_SECRET_ACCESS_KEY",
            "unset AWS_SESSION_TOKEN",
            "unset AWS_REGION",
            "unset AWS_DEFAULT_REGION",
            "unset AWSOP_PROFILE",
            "unset AWSOP_EXPIRATION",
        ]

        return "\n".join(commands)
