"""認証情報の取得と管理"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


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

    def assume_role(
        self,
        role_arn: str,
        session_name: str,
        duration: int,
        external_id: Optional[str] = None,
        mfa_token: Optional[str] = None,
    ) -> Credentials:
        """ロールを引き受けて認証情報を取得"""
        # TODO: 実装は後続のタスクで行う
        raise NotImplementedError()

    def format_export_commands(self, credentials: Credentials) -> str:
        """exportコマンド形式で出力"""
        # TODO: 実装は後続のタスクで行う
        raise NotImplementedError()

    def format_unset_commands(self) -> str:
        """unsetコマンド形式で出力"""
        # TODO: 実装は後続のタスクで行う
        raise NotImplementedError()
