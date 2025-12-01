"""AWS設定ファイルの読み取り"""

from configparser import ConfigParser
from pathlib import Path
from typing import Optional


class AWSConfigParser:
    """AWS設定ファイルパーサー"""

    def __init__(self, config_file: Optional[str] = None):
        self.config_file = Path(config_file or "~/.aws/config").expanduser()

    def read_profile(self, profile_name: str) -> dict:
        """プロファイル設定を読み取る"""
        # TODO: 実装は後続のタスクで行う
        raise NotImplementedError()

    def list_profiles(self) -> list[str]:
        """プロファイル一覧を取得"""
        # TODO: 実装は後続のタスクで行う
        raise NotImplementedError()
