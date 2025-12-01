"""UI出力先のプロパティテスト

Property 10: 出力先の分離
要件5.4, 8.2, 8.3を検証
"""

import sys
from io import StringIO
from hypothesis import given, strategies as st
from awsop.ui.console import ConsoleUI


# 印字可能な文字列のみを生成する戦略
# 制御文字はRichライブラリが処理する際に変換されるため除外
printable_text = st.text(
    alphabet=st.characters(
        blacklist_categories=("Cc", "Cs"),  # 制御文字とサロゲートを除外
        min_codepoint=32,  # スペース以上
    ),
    min_size=1,
)


@given(printable_text)
def test_property_10_output_separation_success(message: str):
    """Feature: awsop-cli-migration, Property 10: 出力先の分離

    任意の実行に対して、ステータスメッセージは標準エラー出力に出力される。

    検証: 要件5.4, 8.2, 8.3
    """
    # 標準エラー出力をキャプチャ
    old_stderr = sys.stderr
    sys.stderr = StringIO()

    try:
        ui = ConsoleUI()
        ui.success(message)

        # 標準エラー出力に出力されていることを確認
        stderr_output = sys.stderr.getvalue()
        assert len(stderr_output) > 0, "標準エラー出力に何も出力されていません"

        # Richは長い行を折り返すため、空白を正規化して比較
        normalized_output = "".join(stderr_output.split())
        normalized_message = "".join(message.split())
        assert normalized_message in normalized_output, (
            f"メッセージ '{message}' が標準エラー出力に含まれていません"
        )
    finally:
        sys.stderr = old_stderr


@given(printable_text)
def test_property_10_output_separation_error(message: str):
    """Feature: awsop-cli-migration, Property 10: 出力先の分離

    任意のエラーメッセージは標準エラー出力に出力される。

    検証: 要件5.4, 8.2, 8.3
    """
    # 標準エラー出力をキャプチャ
    old_stderr = sys.stderr
    sys.stderr = StringIO()

    try:
        ui = ConsoleUI()
        ui.error(message)

        # 標準エラー出力に出力されていることを確認
        stderr_output = sys.stderr.getvalue()
        assert len(stderr_output) > 0, "標準エラー出力に何も出力されていません"

        # Richは長い行を折り返すため、空白を正規化して比較
        # メッセージの本質的な内容が含まれていることを確認
        normalized_output = "".join(stderr_output.split())
        normalized_message = "".join(message.split())
        assert normalized_message in normalized_output, (
            f"メッセージ '{message}' が標準エラー出力に含まれていません"
        )
    finally:
        sys.stderr = old_stderr


@given(printable_text)
def test_property_10_output_separation_info(message: str):
    """Feature: awsop-cli-migration, Property 10: 出力先の分離

    任意の情報メッセージは標準エラー出力に出力される。

    検証: 要件5.4, 8.2, 8.3
    """
    # 標準エラー出力をキャプチャ
    old_stderr = sys.stderr
    sys.stderr = StringIO()

    try:
        ui = ConsoleUI()
        ui.info(message)

        # 標準エラー出力に出力されていることを確認
        stderr_output = sys.stderr.getvalue()
        assert len(stderr_output) > 0, "標準エラー出力に何も出力されていません"

        # Richは長い行を折り返すため、空白を正規化して比較
        normalized_output = "".join(stderr_output.split())
        normalized_message = "".join(message.split())
        assert normalized_message in normalized_output, (
            f"メッセージ '{message}' が標準エラー出力に含まれていません"
        )
    finally:
        sys.stderr = old_stderr


@given(printable_text)
def test_property_10_output_separation_debug(message: str):
    """Feature: awsop-cli-migration, Property 10: 出力先の分離

    任意のデバッグメッセージは標準エラー出力に出力される。

    検証: 要件5.4, 8.2, 8.3
    """
    # 標準エラー出力をキャプチャ
    old_stderr = sys.stderr
    sys.stderr = StringIO()

    try:
        ui = ConsoleUI()
        ui.debug(message)

        # 標準エラー出力に出力されていることを確認
        stderr_output = sys.stderr.getvalue()
        assert len(stderr_output) > 0, "標準エラー出力に何も出力されていません"

        # Richは長い行を折り返すため、空白を正規化して比較
        normalized_output = "".join(stderr_output.split())
        normalized_message = "".join(message.split())
        assert normalized_message in normalized_output, (
            f"メッセージ '{message}' が標準エラー出力に含まれていません"
        )
    finally:
        sys.stderr = old_stderr


@given(st.lists(printable_text, min_size=1))
def test_property_10_output_separation_print_profiles(profiles: list):
    """Feature: awsop-cli-migration, Property 10: 出力先の分離

    任意のプロファイル一覧表示は標準エラー出力に出力される。

    検証: 要件5.4, 8.2, 8.3
    """
    # 標準エラー出力をキャプチャ
    old_stderr = sys.stderr
    sys.stderr = StringIO()

    try:
        ui = ConsoleUI()
        ui.print_profiles(profiles)

        # 標準エラー出力に出力されていることを確認
        stderr_output = sys.stderr.getvalue()
        assert len(stderr_output) > 0, "標準エラー出力に何も出力されていません"

        # 少なくとも1つのプロファイル名が含まれていることを確認
        assert any(profile in stderr_output for profile in profiles), (
            "プロファイル名が標準エラー出力に含まれていません"
        )
    finally:
        sys.stderr = old_stderr


def test_property_10_output_separation_spinner():
    """Feature: awsop-cli-migration, Property 10: 出力先の分離

    スピナーは標準エラー出力に表示される。

    検証: 要件5.4, 8.1
    """
    # 標準エラー出力をキャプチャ
    old_stderr = sys.stderr
    sys.stderr = StringIO()

    try:
        ui = ConsoleUI()
        with ui.spinner("テスト中..."):
            pass

        # スピナーは標準エラー出力に出力される
        # （実際の出力内容は確認しないが、エラーが発生しないことを確認）
    finally:
        sys.stderr = old_stderr
