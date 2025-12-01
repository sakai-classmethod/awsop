"""ログ設定モジュール"""

import logging
import sys


def setup_logging(info: bool = False, debug: bool = False) -> None:
    """
    ログレベルを設定する

    Args:
        info: INFO レベルのログを表示するかどうか
        debug: DEBUG レベルのログを表示するかどうか

    Notes:
        - debug が True の場合、DEBUG レベル以上のログを表示
        - info が True の場合、INFO レベル以上のログを表示
        - どちらも False の場合、WARNING レベル以上のログのみを表示
        - すべてのログは標準エラー出力に出力される
    """
    if debug:
        level = logging.DEBUG
    elif info:
        level = logging.INFO
    else:
        level = logging.WARNING

    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
        force=True,  # 既存の設定を上書き
    )
