"""
プロパティベーステスト: バージョン文字列の型保証

**Feature: version-management, Property 1: バージョン文字列の型保証**
**Validates: Requirements 2.4**
"""

from hypothesis import given, settings, strategies as st
from unittest.mock import patch
from importlib.metadata import PackageNotFoundError


@settings(max_examples=100)
@given(st.just(None))
def test_version_is_always_string_installed(dummy):
    """
    インストール済み環境で__version__が常に文字列型であることを検証

    任意のバージョン取得において、返される値は文字列型でなければならない
    """
    # 実際のインストール済み環境での動作をテスト
    from awsop import __version__

    assert isinstance(__version__, str), (
        f"__version__ must be str, got {type(__version__)}"
    )
    assert len(__version__) > 0, "__version__ must not be empty"


@settings(max_examples=100)
@given(st.just(None))
def test_version_is_always_string_fallback(dummy):
    """
    フォールバック環境で__version__が常に文字列型であることを検証

    パッケージが見つからない場合でも、文字列型を返すことを保証
    """
    # PackageNotFoundErrorをシミュレートしてフォールバック動作をテスト
    with patch("importlib.metadata.version", side_effect=PackageNotFoundError):
        # モジュールを再インポートしてフォールバック処理を実行
        import importlib
        import awsop

        importlib.reload(awsop)

        assert isinstance(awsop.__version__, str), (
            f"__version__ must be str even in fallback, got {type(awsop.__version__)}"
        )
        assert awsop.__version__ == "unknown", (
            f"Fallback version should be 'unknown', got '{awsop.__version__}'"
        )
