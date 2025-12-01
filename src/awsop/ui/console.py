"""Rich を使用したコンソールUI"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from contextlib import contextmanager
from typing import List


class ConsoleUI:
    """コンソールUI

    標準エラー出力にステータスメッセージを表示する。
    要件8.1, 8.2, 8.3に準拠。
    """

    def __init__(self):
        # 標準エラー出力に出力（要件5.4, 8.2, 8.3）
        self.console = Console(stderr=True)

    @contextmanager
    def spinner(self, text: str):
        """スピナー表示

        Args:
            text: スピナーに表示するテキスト

        要件8.1: 1Password経由で認証情報を取得している間、
        スピナーアニメーションを標準エラー出力に表示する
        """
        with self.console.status(text, spinner="dots"):
            yield

    def success(self, message: str):
        """成功メッセージ表示

        Args:
            message: 成功メッセージ

        要件8.2: 認証情報の取得が完了したら、
        プロファイル名と有効期限を色付きで標準エラー出力に表示する
        """
        self.console.print(f"[green]✓[/green] {message}")

    def error(self, message: str):
        """エラーメッセージ表示

        Args:
            message: エラーメッセージ

        要件8.3: エラーが発生したら、
        エラーメッセージを赤色で標準エラー出力に表示する
        """
        self.console.print(f"[red]✗[/red] {message}")

    def info(self, message: str):
        """情報メッセージ表示

        Args:
            message: 情報メッセージ
        """
        self.console.print(f"[blue]ℹ[/blue] {message}")

    def debug(self, message: str):
        """デバッグメッセージ表示

        Args:
            message: デバッグメッセージ
        """
        self.console.print(f"[dim]🔍 {message}[/dim]")

    def print_profiles(self, profiles: List[str]):
        """プロファイル一覧を表示

        Args:
            profiles: プロファイル名のリスト

        要件3.1, 3.2: プロファイル一覧を見やすく表示する
        """
        if not profiles:
            self.info("利用可能なプロファイルがありません")
            return

        # テーブルを作成
        table = Table(
            title="利用可能なプロファイル", show_header=True, header_style="bold cyan"
        )
        table.add_column("プロファイル名", style="green")

        for profile in profiles:
            table.add_row(profile)

        # Panelで囲んで表示
        panel = Panel(table, border_style="blue")
        self.console.print(panel)
