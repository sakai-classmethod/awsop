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


def test_generate_shell_wrapper_contains_info_option_detection():
    """情報表示オプションの検出ロジックが含まれることを確認"""
    output = generate_shell_wrapper()

    # 情報表示オプションの検出ロジックが含まれることを確認
    assert "info_option=false" in output
    assert "for arg in" in output
    assert "case" in output
    assert "-h|--help" in output
    assert "-v|--version" in output
    assert "-l|--list-profiles" in output
    assert "--init-shell" in output
    assert 'if [[ "$info_option" == "true" ]]' in output


def test_generate_shell_wrapper_info_option_skips_eval():
    """情報表示オプション使用時にevalをスキップすることを確認"""
    output = generate_shell_wrapper()

    # 情報表示オプションの場合は直接実行することを確認
    assert "command awsop" in output
    # evalの前に条件分岐があることを確認
    lines = output.split("\n")
    info_option_check_found = False
    eval_found = False
    for i, line in enumerate(lines):
        if 'if [[ "$info_option" == "true" ]]' in line:
            info_option_check_found = True
            # この後にcommand awsopがあることを確認
            for j in range(i + 1, min(i + 5, len(lines))):
                if "command awsop" in lines[j] and "eval" not in lines[j]:
                    eval_found = True
                    break
    assert info_option_check_found
    assert eval_found
