"""Rich を使用したコンソールUI"""

from rich.console import Console
from rich.spinner import Spinner
from contextlib import contextmanager


class ConsoleUI:
    """コンソールUI"""

    def __init__(self):
        self.console = Console(stderr=True)

    @contextmanager
    def spinner(self, text: str):
        """スピナー表示"""
        # TODO: 実装は後続のタスクで行う
        yield

    def success(self, message: str):
        """成功メッセージ表示"""
        # TODO: 実装は後続のタスクで行う
        pass

    def error(self, message: str):
        """エラーメッセージ表示"""
        # TODO: 実装は後続のタスクで行う
        pass

    def info(self, message: str):
        """情報メッセージ表示"""
        # TODO: 実装は後続のタスクで行う
        pass

    def debug(self, message: str):
        """デバッグメッセージ表示"""
        # TODO: 実装は後続のタスクで行う
        pass
