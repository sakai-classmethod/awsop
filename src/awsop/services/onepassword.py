"""1Password CLIとの統合"""

import subprocess
import json
from typing import Optional


class OnePasswordClient:
    """1Password CLIクライアント"""

    def check_availability(self) -> bool:
        """opコマンドの存在確認"""
        # TODO: 実装は後続のタスクで行う
        raise NotImplementedError()

    def run_aws_command(self, command: list[str]) -> dict:
        """op plugin run経由でAWSコマンドを実行"""
        # TODO: 実装は後続のタスクで行う
        raise NotImplementedError()
