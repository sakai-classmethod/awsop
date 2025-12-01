"""AWS設定ファイルの読み取り"""

from configparser import ConfigParser
from pathlib import Path
from typing import Optional


class AWSConfigParser:
    """AWS設定ファイルパーサー"""

    def __init__(self, config_file: Optional[str] = None):
        self.config_file = Path(config_file or "~/.aws/config").expanduser()

    def read_profile(self, profile_name: str) -> dict:
        """プロファイル設定を読み取る

        Args:
            profile_name: プロファイル名

        Returns:
            プロファイル設定の辞書

        Raises:
            FileNotFoundError: 設定ファイルが存在しない場合
            KeyError: プロファイルが見つからない場合
        """
        if not self.config_file.exists():
            raise FileNotFoundError(f"設定ファイルが見つかりません: {self.config_file}")

        parser = ConfigParser()
        parser.read(self.config_file)

        # AWS設定ファイルでは、プロファイル名は "profile <name>" の形式
        # ただし、"default" プロファイルは例外で "default" のまま
        section_name = (
            profile_name if profile_name == "default" else f"profile {profile_name}"
        )

        if not parser.has_section(section_name):
            raise KeyError(f"プロファイルが見つかりません: {profile_name}")

        # セクションの内容を辞書として返す
        return dict(parser.items(section_name))

    def list_profiles(self) -> list[str]:
        """プロファイル一覧を取得

        Returns:
            プロファイル名のリスト

        Raises:
            FileNotFoundError: 設定ファイルが存在しない場合
        """
        if not self.config_file.exists():
            raise FileNotFoundError(f"設定ファイルが見つかりません: {self.config_file}")

        parser = ConfigParser()
        parser.read(self.config_file)

        profiles = []
        for section in parser.sections():
            if section == "default":
                profiles.append("default")
            elif section.startswith("profile "):
                # "profile " プレフィックスを削除
                profiles.append(section[8:])

        return profiles
