"""AWS STS APIとの統合"""

import logging
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

import boto3
from botocore.exceptions import ClientError, BotoCoreError

logger = logging.getLogger(__name__)


@dataclass
class AssumeRoleRequest:
    """AssumeRoleリクエストパラメータ"""

    role_arn: str
    role_session_name: str
    duration_seconds: int = 3600
    external_id: Optional[str] = None
    mfa_token: Optional[str] = None


class STSClient:
    """AWS STSクライアント"""

    def __init__(self):
        """STSクライアントを初期化"""
        self.client = boto3.client("sts")

    def assume_role(
        self,
        role_arn: str,
        role_session_name: str,
        duration_seconds: int = 3600,
        external_id: Optional[str] = None,
    ) -> dict:
        """
        AssumeRoleを実行

        Args:
            role_arn: 引き受けるロールのARN
            role_session_name: セッション名
            duration_seconds: セッションの有効期間（秒）
            external_id: 外部ID（オプション）

        Returns:
            AssumeRoleレスポンス

        Raises:
            ValueError: role_arnが無効な場合、またはduration_secondsが範囲外の場合
            RuntimeError: AssumeRoleの実行に失敗した場合
        """
        # role_arnの検証
        if not role_arn:
            raise ValueError("role_arnは必須です")

        if not role_arn.startswith("arn:aws:iam::"):
            raise ValueError(f"無効なrole_arn形式です: {role_arn}")

        # duration_secondsの検証（要件4.4.1, 4.4.3）
        if duration_seconds < 900:
            raise ValueError("ロール期間は900秒以上である必要があります")

        if duration_seconds > 43200:
            raise ValueError("ロール期間は43200秒以下である必要があります")

        logger.info(
            f"AssumeRoleを実行: role_arn={role_arn}, session={role_session_name}"
        )

        try:
            # AssumeRoleリクエストのパラメータを構築
            params = {
                "RoleArn": role_arn,
                "RoleSessionName": role_session_name,
                "DurationSeconds": duration_seconds,
            }

            # 外部IDが指定されている場合は追加
            if external_id:
                params["ExternalId"] = external_id
                logger.debug(f"外部IDを使用: {external_id}")

            # AssumeRoleを実行
            response = self.client.assume_role(**params)

            logger.info("AssumeRoleが成功しました")
            logger.debug(f"有効期限: {response['Credentials']['Expiration']}")

            return response

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))

            logger.error(f"AssumeRoleが失敗しました: {error_code} - {error_message}")

            # エラーメッセージを日本語化
            if error_code == "AccessDenied":
                raise RuntimeError(
                    f"ロールの引き受けに失敗しました: アクセスが拒否されました ({error_message})"
                ) from e
            elif error_code == "InvalidParameterValue":
                raise RuntimeError(
                    f"ロールの引き受けに失敗しました: 無効なパラメータです ({error_message})"
                ) from e
            else:
                raise RuntimeError(
                    f"ロールの引き受けに失敗しました: {error_message}"
                ) from e

        except BotoCoreError as e:
            logger.error(f"boto3エラー: {str(e)}")
            raise RuntimeError(f"AWS APIの呼び出しに失敗しました: {str(e)}") from e
        except Exception as e:
            logger.error(f"予期しないエラー: {str(e)}")
            raise RuntimeError(
                f"AssumeRoleの実行中にエラーが発生しました: {str(e)}"
            ) from e
