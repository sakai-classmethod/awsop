"""プロファイル管理"""

from dataclasses import dataclass
from typing import Optional

from awsop.services.aws_config import AWSConfigParser


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
        self.parser = AWSConfigParser(config_file)

    def get_profile(self, profile_name: str) -> ProfileConfig:
        """プロファイル設定を取得

        Args:
            profile_name: プロファイル名

        Returns:
            ProfileConfig: プロファイル設定

        Raises:
            FileNotFoundError: 設定ファイルが存在しない場合
            KeyError: プロファイルが見つからない場合
        """
        # AWSConfigParserを使用してプロファイル設定を読み取る
        config_dict = self.parser.read_profile(profile_name)

        # 辞書からProfileConfigオブジェクトを作成
        return ProfileConfig(
            name=profile_name,
            role_arn=config_dict.get("role_arn"),
            region=config_dict.get("region"),
            source_profile=config_dict.get("source_profile"),
            external_id=config_dict.get("external_id"),
            mfa_serial=config_dict.get("mfa_serial"),
        )

    def list_profiles(self) -> list[str]:
        """プロファイル一覧を取得

        Returns:
            list[str]: プロファイル名のリスト

        Raises:
            FileNotFoundError: 設定ファイルが存在しない場合
        """
        # AWSConfigParserを使用してプロファイル一覧を取得
        return self.parser.list_profiles()
