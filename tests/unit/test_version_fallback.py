"""
ユニットテスト: パッケージ未インストール時のフォールバック

**Edge Case 1: パッケージ未インストール時のフォールバック**
**Validates: Requirements 3.1, 3.2, 3.3, 3.4**
"""

import pytest
from unittest.mock import patch
from importlib.metadata import PackageNotFoundError


def test_version_fallback_on_package_not_found():
    """
    PackageNotFoundErrorが発生した場合に"unknown"が返されることを確認

    要件:
    - 3.1: フォールバック値を返す
    - 3.2: PackageNotFoundErrorをキャッチして処理
    - 3.3: "unknown"を返す
    - 3.4: 正常に動作を継続
    """
    import importlib
    import awsop

    # importlib.metadata.versionをモックしてPackageNotFoundErrorを発生させる
    with patch("importlib.metadata.version", side_effect=PackageNotFoundError):
        # モジュールを再インポートしてフォールバック処理を実行
        importlib.reload(awsop)

        # __version__が"unknown"になることを確認
        assert awsop.__version__ == "unknown", (
            f"Expected 'unknown' but got '{awsop.__version__}'"
        )

    # テスト後、モジュールを正常な状態に戻す
    importlib.reload(awsop)


def test_no_exception_propagation_on_fallback():
    """
    フォールバック処理で例外が伝播しないことを確認

    要件:
    - 3.2: 例外をキャッチして処理
    - 3.4: 正常に動作を継続
    """
    import importlib
    import awsop

    # PackageNotFoundErrorが発生しても例外が伝播しないことを確認
    with patch("importlib.metadata.version", side_effect=PackageNotFoundError):
        try:
            importlib.reload(awsop)
            # 例外が発生しないことを確認
            assert True
        except PackageNotFoundError:
            pytest.fail("PackageNotFoundError should not propagate")

    # テスト後、モジュールを正常な状態に戻す
    importlib.reload(awsop)


def test_fallback_version_is_string():
    """
    フォールバック時も文字列型を返すことを確認

    要件:
    - 3.3: 明確な代替バージョン文字列を返す
    """
    import importlib
    import awsop

    with patch("importlib.metadata.version", side_effect=PackageNotFoundError):
        importlib.reload(awsop)

        # 文字列型であることを確認
        assert isinstance(awsop.__version__, str), (
            f"Fallback version must be str, got {type(awsop.__version__)}"
        )

        # 空文字列でないことを確認
        assert len(awsop.__version__) > 0, "Fallback version must not be empty"

    # テスト後、モジュールを正常な状態に戻す
    importlib.reload(awsop)
