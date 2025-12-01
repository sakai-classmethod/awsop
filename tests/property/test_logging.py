"""ログレベル制御のプロパティベーステスト

Feature: awsop-cli-migration, Property 11: ログレベルの制御
検証: 要件 9.1, 9.2, 9.3
"""

import logging
import sys
from io import StringIO

from hypothesis import given, strategies as st

from awsop.logging import setup_logging


@given(
    info=st.booleans(),
    debug=st.booleans(),
)
def test_property_11_log_level_control(info: bool, debug: bool) -> None:
    """
    Feature: awsop-cli-migration, Property 11: ログレベルの制御

    任意の実行に対して:
    - --debug が指定された場合は DEBUG レベル以上のログを表示
    - --info が指定された場合は INFO レベル以上のログを表示
    - 指定されない場合は WARNING レベル以上のログのみを表示

    検証: 要件 9.1, 9.2, 9.3
    """
    # ログ設定を実行
    setup_logging(info=info, debug=debug)

    # 期待されるログレベルを決定
    if debug:
        expected_level = logging.DEBUG
    elif info:
        expected_level = logging.INFO
    else:
        expected_level = logging.WARNING

    # ルートロガーのレベルを確認
    root_logger = logging.getLogger()
    assert root_logger.level == expected_level, (
        f"ログレベルが期待値と一致しません: "
        f"期待={logging.getLevelName(expected_level)}, "
        f"実際={logging.getLevelName(root_logger.level)}"
    )

    # ハンドラーが標準エラー出力に設定されていることを確認
    handlers = root_logger.handlers
    assert len(handlers) > 0, "ハンドラーが設定されていません"

    # 少なくとも1つのハンドラーが stderr に出力することを確認
    has_stderr_handler = any(
        hasattr(handler, "stream") and handler.stream == sys.stderr
        for handler in handlers
    )
    assert has_stderr_handler, "標準エラー出力へのハンドラーが設定されていません"


def test_log_level_priority() -> None:
    """
    ログレベルの優先順位をテスト

    debug > info > デフォルト(WARNING)
    """
    # debug=True の場合、info の値に関わらず DEBUG レベル
    setup_logging(info=True, debug=True)
    assert logging.getLogger().level == logging.DEBUG

    setup_logging(info=False, debug=True)
    assert logging.getLogger().level == logging.DEBUG

    # debug=False, info=True の場合、INFO レベル
    setup_logging(info=True, debug=False)
    assert logging.getLogger().level == logging.INFO

    # 両方 False の場合、WARNING レベル
    setup_logging(info=False, debug=False)
    assert logging.getLogger().level == logging.WARNING


def test_log_output_to_stderr() -> None:
    """
    ログが標準エラー出力に出力されることをテスト
    """
    # 標準エラー出力をキャプチャするための StringIO を作成
    captured_stderr = StringIO()

    # 一時的に sys.stderr を置き換えてからログ設定
    old_stderr = sys.stderr
    sys.stderr = captured_stderr

    try:
        # ログ設定（この時点で stderr が StringIO になっている）
        setup_logging(debug=True)

        # ログメッセージを出力
        logger = logging.getLogger(__name__)
        test_message = "テストメッセージ"
        logger.debug(test_message)

        # 標準エラー出力の内容を取得
        stderr_output = captured_stderr.getvalue()

        # メッセージが含まれていることを確認
        assert test_message in stderr_output, (
            f"ログメッセージが標準エラー出力に含まれていません: {stderr_output}"
        )
    finally:
        # 標準エラー出力を復元
        sys.stderr = old_stderr
        # ロガーをクリーンアップ
        logging.getLogger().handlers.clear()
