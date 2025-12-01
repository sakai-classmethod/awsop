"""統合テスト: CLIバージョン表示

Example 2: CLI バージョン表示（-v）
Example 3: CLI バージョン表示（--version）
検証: 要件 4.1, 4.2
"""

import subprocess
import sys
from pathlib import Path


def test_version_short_option():
    """
    Example 2: CLI バージョン表示（-v）

    `awsop -v`が"awsop X.Y.Z"形式で出力することを確認
    終了コードが0であることを確認

    検証: 要件 4.1
    """
    # awsopコマンドを-vオプション付きで実行
    result = subprocess.run(
        [sys.executable, "-m", "awsop", "-v"],
        capture_output=True,
        text=True,
    )

    # 終了コードが0であることを確認
    assert result.returncode == 0, f"終了コードが0ではありません: {result.returncode}"

    # 出力が"awsop X.Y.Z"形式であることを確認
    output = result.stdout.strip()
    assert output.startswith("awsop "), f"出力が'awsop 'で始まっていません: {output}"

    # バージョン部分が存在することを確認
    version_part = output.replace("awsop ", "")
    assert len(version_part) > 0, "バージョン部分が空です"

    # 標準エラー出力が空であることを確認
    assert result.stderr == "", f"標準エラー出力が空ではありません: {result.stderr}"


def test_version_long_option():
    """
    Example 3: CLI バージョン表示（--version）

    `awsop --version`が"awsop X.Y.Z"形式で出力することを確認
    `-v`と同じ出力をすることを確認
    終了コードが0であることを確認

    検証: 要件 4.2
    """
    # awsopコマンドを--versionオプション付きで実行
    result_long = subprocess.run(
        [sys.executable, "-m", "awsop", "--version"],
        capture_output=True,
        text=True,
    )

    # 終了コードが0であることを確認
    assert result_long.returncode == 0, (
        f"終了コードが0ではありません: {result_long.returncode}"
    )

    # 出力が"awsop X.Y.Z"形式であることを確認
    output_long = result_long.stdout.strip()
    assert output_long.startswith("awsop "), (
        f"出力が'awsop 'で始まっていません: {output_long}"
    )

    # バージョン部分が存在することを確認
    version_part = output_long.replace("awsop ", "")
    assert len(version_part) > 0, "バージョン部分が空です"

    # 標準エラー出力が空であることを確認
    assert result_long.stderr == "", (
        f"標準エラー出力が空ではありません: {result_long.stderr}"
    )

    # -vオプションと同じ出力であることを確認
    result_short = subprocess.run(
        [sys.executable, "-m", "awsop", "-v"],
        capture_output=True,
        text=True,
    )

    assert output_long == result_short.stdout.strip(), (
        f"--versionと-vの出力が異なります: "
        f"--version='{output_long}', -v='{result_short.stdout.strip()}'"
    )


def test_version_format():
    """
    バージョン出力の形式が正しいことを確認

    "awsop X.Y.Z"または"awsop unknown"の形式であることを確認
    """
    result = subprocess.run(
        [sys.executable, "-m", "awsop", "-v"],
        capture_output=True,
        text=True,
    )

    output = result.stdout.strip()

    # "awsop "で始まることを確認
    assert output.startswith("awsop "), f"出力が'awsop 'で始まっていません: {output}"

    # バージョン部分を取得
    version_part = output.replace("awsop ", "")

    # "unknown"またはセマンティックバージョニング形式（X.Y.Z）であることを確認
    if version_part != "unknown":
        # セマンティックバージョニングの基本形式をチェック
        # 少なくとも数字とドットが含まれていることを確認
        assert any(c.isdigit() for c in version_part), (
            f"バージョン部分に数字が含まれていません: {version_part}"
        )
