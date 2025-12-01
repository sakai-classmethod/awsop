"""認証情報ファイルへの書き込み"""

from pathlib import Path
from typing import Optional


class CredentialsWriter:
    """認証情報ファイルライター"""

    def __init__(self, credentials_file: Optional[str] = None):
        self.credentials_file = Path(
            credentials_file or "~/.aws/credentials"
        ).expanduser()

    def write_profile(
        self,
        profile_name: str,
        access_key_id: str,
        secret_access_key: str,
        session_token: str,
    ) -> None:
        """プロファイルに認証情報を書き込む"""
        # TODO: 実装は後続のタスクで行う
        raise NotImplementedError()

    def is_managed_by_awsop(self, profile_name: str) -> bool:
        """プロファイルがawsop管理かチェック"""
        # TODO: 実装は後続のタスクで行う
        raise NotImplementedError()
