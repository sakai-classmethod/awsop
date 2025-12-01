"""認証情報ファイルへの書き込み"""

import os
from configparser import ConfigParser
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
        """プロファイルに認証情報を書き込む

        Args:
            profile_name: プロファイル名
            access_key_id: アクセスキーID
            secret_access_key: シークレットアクセスキー
            session_token: セッショントークン

        Raises:
            ValueError: プロファイルが既に存在し、awsop管理でない場合
        """
        # プロファイルが既に存在する場合、awsop管理かチェック
        if self.credentials_file.exists():
            parser = ConfigParser(interpolation=None)
            parser.read(self.credentials_file)

            if parser.has_section(profile_name):
                if not self.is_managed_by_awsop(profile_name):
                    raise ValueError(
                        f"プロファイル '{profile_name}' は既に存在し、"
                        "awsop管理ではありません。上書きできません。"
                    )

        # 認証情報を書き込む
        # ConfigParserの補間機能を無効化（%文字を正しく扱うため）
        parser = ConfigParser(interpolation=None)
        if self.credentials_file.exists():
            parser.read(self.credentials_file)

        # プロファイルセクションを作成または更新
        if not parser.has_section(profile_name):
            parser.add_section(profile_name)

        parser.set(profile_name, "aws_access_key_id", access_key_id)
        parser.set(profile_name, "aws_secret_access_key", secret_access_key)
        parser.set(profile_name, "aws_session_token", session_token)
        parser.set(profile_name, "manager", "awsop")

        # ディレクトリが存在しない場合は作成
        self.credentials_file.parent.mkdir(parents=True, exist_ok=True)

        # ファイルに書き込み
        with open(self.credentials_file, "w") as f:
            parser.write(f)

        # ファイルパーミッションを600に設定
        os.chmod(self.credentials_file, 0o600)

    def is_managed_by_awsop(self, profile_name: str) -> bool:
        """プロファイルがawsop管理かチェック

        Args:
            profile_name: プロファイル名

        Returns:
            awsop管理の場合True、それ以外False
        """
        if not self.credentials_file.exists():
            return False

        parser = ConfigParser(interpolation=None)
        parser.read(self.credentials_file)

        if not parser.has_section(profile_name):
            return False

        # manager = awsop プロパティが存在するかチェック
        return parser.get(profile_name, "manager", fallback=None) == "awsop"
