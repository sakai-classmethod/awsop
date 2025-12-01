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
        full_command = ["op", "plugin", "run", "--", "aws"] + command
        result = subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
