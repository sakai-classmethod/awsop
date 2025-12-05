"""UIフィードバックのユニットテスト

要件8.1, 8.2, 8.3, 8.4, 8.5を検証
"""

import sys
from io import StringIO
import pytest
from awsop.ui.console import ConsoleUI


class TestUIFeedback:
    """UIフィードバックのテスト"""

    def test_spinner_display(self):
        """スピナー表示のテスト（要件8.1）"""
        # 標準エラー出力をキャプチャ
        old_stderr = sys.stderr
        sys.stderr = StringIO()

        try:
            ui = ConsoleUI()

            # スピナーを表示
            with ui.spinner("処理中..."):
                pass

            # エラーが発生しないことを確認
            # スピナーは標準エラー出力に表示される
            stderr_output = sys.stderr.getvalue()
            # スピナーは動的に表示されるため、具体的な内容は確認しない
            # エラーが発生しなければOK

        finally:
            sys.stderr = old_stderr

    def test_success_message(self):
        """成功メッセージのテスト（要件8.2）"""
        # 標準エラー出力をキャプチャ
        old_stderr = sys.stderr
        sys.stderr = StringIO()

        try:
            ui = ConsoleUI()
            test_message = "操作が成功しました"

            ui.success(test_message)

            # 標準エラー出力に出力されていることを確認
            stderr_output = sys.stderr.getvalue()
            assert len(stderr_output) > 0, "標準エラー出力に何も出力されていません"

            # メッセージが含まれていることを確認
            assert test_message in stderr_output, (
                f"メッセージ '{test_message}' が標準エラー出力に含まれていません"
            )

            # 成功を示すマーク（✓）が含まれていることを確認
            assert "✓" in stderr_output, "成功マークが含まれていません"

        finally:
            sys.stderr = old_stderr

    def test_info_message_stderr(self):
        """情報メッセージの標準エラー出力テスト（要件8.3）"""
        # 標準エラー出力をキャプチャ
        old_stderr = sys.stderr
        sys.stderr = StringIO()

        try:
            ui = ConsoleUI()
            test_message = "情報メッセージです"

            ui.info(test_message)

            # 標準エラー出力に出力されていることを確認
            stderr_output = sys.stderr.getvalue()
            assert len(stderr_output) > 0, "標準エラー出力に何も出力されていません"

            # メッセージが含まれていることを確認
            assert test_message in stderr_output, (
                f"メッセージ '{test_message}' が標準エラー出力に含まれていません"
            )

            # 情報を示すマーク（ℹ）が含まれていることを確認
            assert "ℹ" in stderr_output, "情報マークが含まれていません"

        finally:
            sys.stderr = old_stderr

    def test_error_message(self):
        """エラーメッセージのテスト（要件8.4）"""
        # 標準エラー出力をキャプチャ
        old_stderr = sys.stderr
        sys.stderr = StringIO()

        try:
            ui = ConsoleUI()
            test_message = "エラーが発生しました"

            ui.error(test_message)

            # 標準エラー出力に出力されていることを確認
            stderr_output = sys.stderr.getvalue()
            assert len(stderr_output) > 0, "標準エラー出力に何も出力されていません"

            # メッセージが含まれていることを確認
            assert test_message in stderr_output, (
                f"メッセージ '{test_message}' が標準エラー出力に含まれていません"
            )

            # エラーを示すマーク（✗）が含まれていることを確認
            assert "✗" in stderr_output, "エラーマークが含まれていません"

        finally:
            sys.stderr = old_stderr

    def test_spinner_context_manager(self):
        """スピナーのコンテキストマネージャーテスト（要件8.5）"""
        # 標準エラー出力をキャプチャ
        old_stderr = sys.stderr
        sys.stderr = StringIO()

        try:
            ui = ConsoleUI()

            # スピナーがコンテキストマネージャーとして機能することを確認
            with ui.spinner("処理中..."):
                # 処理中の状態
                pass

            # コンテキストを抜けた後、スピナーが自動的に停止されることを確認
            # （エラーが発生しなければOK）

        finally:
            sys.stderr = old_stderr

    def test_multiple_messages(self):
        """複数のメッセージを連続して表示するテスト"""
        # 標準エラー出力をキャプチャ
        old_stderr = sys.stderr
        sys.stderr = StringIO()

        try:
            ui = ConsoleUI()

            # 複数のメッセージを表示
            ui.info("情報1")
            ui.success("成功1")
            ui.error("エラー1")
            ui.info("情報2")

            # すべてのメッセージが標準エラー出力に含まれることを確認
            stderr_output = sys.stderr.getvalue()
            assert "情報1" in stderr_output
            assert "成功1" in stderr_output
            assert "エラー1" in stderr_output
            assert "情報2" in stderr_output

        finally:
            sys.stderr = old_stderr

    def test_debug_message(self):
        """デバッグメッセージのテスト"""
        # 標準エラー出力をキャプチャ
        old_stderr = sys.stderr
        sys.stderr = StringIO()

        try:
            ui = ConsoleUI()
            test_message = "デバッグ情報"

            ui.debug(test_message)

            # 標準エラー出力に出力されていることを確認
            stderr_output = sys.stderr.getvalue()
            assert len(stderr_output) > 0, "標準エラー出力に何も出力されていません"

            # メッセージが含まれていることを確認
            assert test_message in stderr_output, (
                f"メッセージ '{test_message}' が標準エラー出力に含まれていません"
            )

            # デバッグを示すマーク（🔍）が含まれていることを確認
            assert "🔍" in stderr_output, "デバッグマークが含まれていません"

        finally:
            sys.stderr = old_stderr

    def test_empty_message(self):
        """空のメッセージのテスト"""
        # 標準エラー出力をキャプチャ
        old_stderr = sys.stderr
        sys.stderr = StringIO()

        try:
            ui = ConsoleUI()

            # 空のメッセージでもエラーが発生しないことを確認
            ui.info("")
            ui.success("")
            ui.error("")
            ui.debug("")

            # エラーが発生しなければOK

        finally:
            sys.stderr = old_stderr

    def test_long_message(self):
        """長いメッセージのテスト"""
        # 標準エラー出力をキャプチャ
        old_stderr = sys.stderr
        sys.stderr = StringIO()

        try:
            ui = ConsoleUI()

            # 長いメッセージを作成
            long_message = "これは非常に長いメッセージです。" * 20

            # 長いメッセージでもエラーが発生しないことを確認
            ui.info(long_message)

            # メッセージが標準エラー出力に含まれることを確認
            stderr_output = sys.stderr.getvalue()
            assert "これは非常に長いメッセージです。" in stderr_output

        finally:
            sys.stderr = old_stderr

    def test_special_characters_in_message(self):
        """特殊文字を含むメッセージのテスト"""
        # 標準エラー出力をキャプチャ
        old_stderr = sys.stderr
        sys.stderr = StringIO()

        try:
            ui = ConsoleUI()

            # 特殊文字を含むメッセージ
            special_message = "エラー: ファイル 'test.txt' が見つかりません (404)"

            ui.error(special_message)

            # メッセージが標準エラー出力に含まれることを確認
            stderr_output = sys.stderr.getvalue()
            assert "test.txt" in stderr_output
            assert "404" in stderr_output

        finally:
            sys.stderr = old_stderr
