"""1Password CLIとの統合"""

import subprocess
import json
import shutil


class OnePasswordClient:
    """1Password CLIクライアント"""

    def check_availability(self) -> bool:
        """opコマンドの存在確認

        Returns:
            bool: opコマンドが利用可能な場合True
        """
        return shutil.which("op") is not None

    def run_aws_command(self, command: list[str]) -> dict:
        """op plugin run経由でAWSコマンドを実行

        Args:
            command: 実行するAWSコマンド（例: ["sts", "assume-role", ...]）

        Returns:
            dict: コマンドの実行結果（JSON形式）

        Raises:
            subprocess.CalledProcessError: コマンド実行が失敗した場合
            json.JSONDecodeError: 出力のJSON解析が失敗した場合
        """
        import os

        # 環境変数をコピーして、AWS関連の環境変数をクリア
        env = os.environ.copy()
        aws_env_vars = [
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "AWS_SESSION_TOKEN",
            "AWS_DEFAULT_REGION",
            "AWS_REGION",
            "AWSOP_PROFILE",
            "AWSOP_EXPIRATION",
        ]
        for var in aws_env_vars:
            env.pop(var, None)

        full_command = ["op", "plugin", "run", "--", "aws"] + command
        result = subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )
        return json.loads(result.stdout)
