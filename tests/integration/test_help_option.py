"""ヘルプオプションの統合テスト

要件1.1, 1.2, 4.1, 4.2, 4.4をテストする
"""

import subprocess
import sys
import tempfile
import os


def test_help_with_long_option():
    """--helpオプションでヘルプが表示されることを確認（要件1.1）"""
    result = subprocess.run(
        [sys.executable, "-m", "awsop", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "AWS credentials manager" in result.stdout
    assert "--help" in result.stdout or "-h" in result.stdout


def test_help_with_short_option():
    """-hオプションでヘルプが表示されることを確認（要件1.1）"""
    result = subprocess.run(
        [sys.executable, "-m", "awsop", "-h"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "AWS credentials manager" in result.stdout
    assert "--help" in result.stdout or "-h" in result.stdout


def test_help_options_produce_same_output():
    """-hと--helpが同じヘルプメッセージを表示することを確認（要件1.2）"""
    result_long = subprocess.run(
        [sys.executable, "-m", "awsop", "--help"],
        capture_output=True,
        text=True,
    )

    result_short = subprocess.run(
        [sys.executable, "-m", "awsop", "-h"],
        capture_output=True,
        text=True,
    )

    assert result_long.returncode == 0
    assert result_short.returncode == 0
    assert result_long.stdout == result_short.stdout


def test_shell_wrapper_help_long_option():
    """シェルラッパー経由で--helpが正しく表示されることを確認（要件4.1）"""
    from awsop.shell.wrapper import generate_shell_wrapper

    # 一時的なシェルスクリプトを作成
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
        # シェルラッパー関数を書き込み
        f.write("#!/bin/zsh\n")
        f.write(generate_shell_wrapper())
        f.write("\n")
        # ヘルプオプションを実行
        f.write("awsop --help\n")
        script_path = f.name

    try:
        # zshでスクリプトを実行
        result = subprocess.run(
            ["zsh", script_path],
            capture_output=True,
            text=True,
        )

        # ヘルプメッセージが表示されることを確認
        assert result.returncode == 0
        assert "AWS credentials manager" in result.stdout
        # ヘルプ表示に関連するzshエラーが発生しないことを確認（要件4.4）
        # compdefは補完システムの問題なので無視
        stderr_without_compdef = "\n".join(
            line for line in result.stderr.split("\n") if "compdef" not in line
        )
        assert "parse error" not in stderr_without_compdef.lower()
        assert "eval" not in stderr_without_compdef.lower()
    finally:
        # 一時ファイルを削除
        os.unlink(script_path)


def test_shell_wrapper_help_short_option():
    """シェルラッパー経由で-hが正しく表示されることを確認（要件4.2）"""
    from awsop.shell.wrapper import generate_shell_wrapper

    # 一時的なシェルスクリプトを作成
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
        # シェルラッパー関数を書き込み
        f.write("#!/bin/zsh\n")
        f.write(generate_shell_wrapper())
        f.write("\n")
        # ヘルプオプションを実行
        f.write("awsop -h\n")
        script_path = f.name

    try:
        # zshでスクリプトを実行
        result = subprocess.run(
            ["zsh", script_path],
            capture_output=True,
            text=True,
        )

        # ヘルプメッセージが表示されることを確認
        assert result.returncode == 0
        assert "AWS credentials manager" in result.stdout
        # ヘルプ表示に関連するzshエラーが発生しないことを確認（要件4.4）
        # compdefは補完システムの問題なので無視
        stderr_without_compdef = "\n".join(
            line for line in result.stderr.split("\n") if "compdef" not in line
        )
        assert "parse error" not in stderr_without_compdef.lower()
        assert "eval" not in stderr_without_compdef.lower()
    finally:
        # 一時ファイルを削除
        os.unlink(script_path)


def test_invalid_option_error():
    """無効なオプション（--hなど）が適切にエラーになることを確認（要件1.4）"""
    result = subprocess.run(
        [sys.executable, "-m", "awsop", "--h"],
        capture_output=True,
        text=True,
    )

    # 非ゼロの終了コードを返すこと
    assert result.returncode != 0

    # エラーメッセージが表示されること
    error_output = result.stderr + result.stdout
    assert "No such option" in error_output or "Error" in error_output


def test_invalid_option_suggests_alternative():
    """無効なオプションのエラーメッセージに代替案が含まれることを確認（要件3.3）"""
    result = subprocess.run(
        [sys.executable, "-m", "awsop", "--hlp"],
        capture_output=True,
        text=True,
    )

    # 非ゼロの終了コードを返すこと
    assert result.returncode != 0

    # エラーメッセージが表示されること
    error_output = result.stderr + result.stdout
    assert "No such option" in error_output or "Error" in error_output

    # 代替案が提示されること（Typerは類似のオプションを提案する）
    # または使用方法が表示されること
    assert "Did you mean" in error_output or "Usage" in error_output
