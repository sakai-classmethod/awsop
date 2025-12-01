"""プロファイル管理"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ProfileConfig:
    """プロファイル設定"""

    name: str
    role_arn: Optional[str] = None
    region: Optional[str] = None
    source_profile: Optional[str] = None
    external_id: Optional[str] = None
    mfa_serial: Optional[str] = None


class ProfileManager:
    """プロファイル管理クラス"""

    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "~/.aws/config"

    def get_profile(self, profile_name: str) -> ProfileConfig:
        """プロファイル設定を取得"""
        # TODO: 実装は後続のタスクで行う
        raise NotImplementedError()

    def list_profiles(self) -> list[str]:
        """プロファイル一覧を取得"""
        # TODO: 実装は後続のタスクで行う
        raise NotImplementedError()
