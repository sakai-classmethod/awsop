"""シェルラッパー関数のユニットテスト"""

import pytest
from awsop.shell.wrapper import generate_shell_wrapper


def test_generate_shell_wrapper_contains_function():
    """シェル関数が含まれることを確認"""
    output = generate_shell_wrapper()

    # awsop関数の定義が含まれることを確認
    assert "function awsop()" in output
    assert "local output" in output
    assert "command awsop" in output
    assert "eval" in output


def test_generate_shell_wrapper_contains_completion():
    """補完スクリプトが含まれることを確認"""
    output = generate_shell_wrapper()

    # 補完関数の定義が含まれることを確認
    assert "_awsop()" in output
    assert "profiles=" in output
    assert "~/.aws/config" in output
    assert "_describe 'profile' profiles" in output
    assert "compdef _awsop awsop" in output


def test_generate_shell_wrapper_contains_error_handling():
    """エラーハンドリングが含まれることを確認"""
    output = generate_shell_wrapper()

    # エラーハンドリングのロジックが含まれることを確認
    assert "exit_code=$?" in output
    assert "if [[ $exit_code -eq 0 ]]" in output
    assert "return $exit_code" in output


def test_generate_shell_wrapper_contains_profile_extraction():
    """プロファイル抽出の正規表現が含まれることを確認"""
    output = generate_shell_wrapper()

    # sedコマンドによるプロファイル抽出が含まれることを確認
    assert "sed -nE" in output
    assert r"s/^\[(profile )?([^]]+)\]/\2/p" in output


def test_generate_shell_wrapper_returns_string():
    """文字列を返すことを確認"""
    output = generate_shell_wrapper()

    assert isinstance(output, str)
    assert len(output) > 0


def test_generate_shell_wrapper_contains_usage_hint():
    """使用方法のヒントが含まれることを確認"""
    output = generate_shell_wrapper()

    # zstyleの設定ヒントが含まれることを確認
    assert "zstyle" in output
    assert "matcher-list" in output
