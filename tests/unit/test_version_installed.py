"""
ユニットテスト: インストール済み環境でのバージョン取得

**Example 1: インストール済み環境でのバージョン取得**
**Validates: Requirements 2.2**
"""

import tomllib
from pathlib import Path


def test_version_matches_pyproject():
    """
    __version__がpyproject.tomlで定義されたバージョンと一致することを確認

    要件:
    - 2.2: パッケージがインストールされている場合、pyproject.tomlで定義されたバージョンを返す
    """
    # pyproject.tomlからバージョンを読み取る
    pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        pyproject_data = tomllib.load(f)

    expected_version = pyproject_data["project"]["version"]

    # awsopモジュールから__version__をインポート
    from awsop import __version__

    # バージョンが一致することを確認
    assert __version__ == expected_version, (
        f"Expected version '{expected_version}' from pyproject.toml, "
        f"but got '{__version__}'"
    )


def test_version_is_not_unknown():
    """
    インストール済み環境では"unknown"ではないことを確認

    要件:
    - 2.2: 正しいバージョンを返す（フォールバック値ではない）
    """
    from awsop import __version__

    # "unknown"でないことを確認
    assert __version__ != "unknown", (
        "Version should not be 'unknown' in installed environment"
    )


def test_version_is_valid_string():
    """
    バージョンが有効な文字列形式であることを確認

    要件:
    - 2.4: 文字列形式のバージョン番号を返す
    """
    from awsop import __version__

    # 文字列型であることを確認
    assert isinstance(__version__, str), f"Version must be str, got {type(__version__)}"

    # 空文字列でないことを確認
    assert len(__version__) > 0, "Version must not be empty"

    # セマンティックバージョニング形式の基本チェック（X.Y.Z形式）
    parts = __version__.split(".")
    assert len(parts) >= 2, (
        f"Version should follow semantic versioning (X.Y.Z), got '{__version__}'"
    )
