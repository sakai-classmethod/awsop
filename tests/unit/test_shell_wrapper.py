"""シェルラッパー関数のユニットテスト"""

import subprocess
import tempfile
from pathlib import Path

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


def test_generate_shell_wrapper_contains_options_list():
    """オプションリストが定義されていることを確認"""
    output = generate_shell_wrapper()

    # オプションリストの定義が含まれることを確認
    assert "local -a profiles options" in output
    assert "options=(" in output


def test_generate_shell_wrapper_contains_all_short_options():
    """すべての短縮形オプションが含まれることを確認"""
    output = generate_shell_wrapper()

    # 短縮形オプションが含まれることを確認
    short_options = [
        "-h",
        "-s",
        "-u",
        "-l",
        "-r",
        "-n",
        "-d",
        "-m",
        "-o",
        "-a",
        "-p",
        "-e",
        "-c",
        "-i",
        "-v",
    ]

    for option in short_options:
        # 'option:description' の形式で含まれることを確認
        assert f"'{option}:" in output, f"短縮形オプション {option} が見つかりません"


def test_generate_shell_wrapper_contains_all_long_options():
    """すべての長形式オプションが含まれることを確認"""
    output = generate_shell_wrapper()

    # 長形式オプションが含まれることを確認
    long_options = [
        "--help",
        "--show-commands",
        "--unset",
        "--list-profiles",
        "--init-shell",
        "--region",
        "--session-name",
        "--role-duration",
        "--mfa-token",
        "--output-profile",
        "--role-arn",
        "--source-profile",
        "--external-id",
        "--config-file",
        "--credentials-file",
        "--info",
        "--debug",
        "--version",
    ]

    for option in long_options:
        # 'option:description' の形式で含まれることを確認
        assert f"'{option}:" in output, f"長形式オプション {option} が見つかりません"


def test_generate_shell_wrapper_options_have_descriptions():
    """すべてのオプションに説明が含まれることを確認"""
    output = generate_shell_wrapper()

    # オプション定義の部分を抽出
    lines = output.split("\n")
    in_options_block = False
    option_lines = []

    for line in lines:
        if "options=(" in line:
            in_options_block = True
            continue
        if in_options_block:
            if ")" in line and not line.strip().startswith("'"):
                break
            if line.strip().startswith("'"):
                option_lines.append(line.strip())

    # 各オプション行が 'option:description' の形式であることを確認
    for line in option_lines:
        # 'option:description' の形式をチェック
        assert line.startswith("'"), f"オプション行が ' で始まっていません: {line}"
        assert ":" in line, f"オプション行に : が含まれていません: {line}"

        # コロンの後に説明があることを確認
        parts = line.split(":", 1)
        assert len(parts) == 2, f"オプション行の形式が不正です: {line}"
        assert len(parts[1].strip("'")) > 0, f"オプションの説明が空です: {line}"


def test_generate_shell_wrapper_option_format_consistency():
    """オプションの形式が一貫していることを確認"""
    output = generate_shell_wrapper()

    # オプション定義の部分を抽出
    lines = output.split("\n")
    in_options_block = False
    option_lines = []

    for line in lines:
        if "options=(" in line:
            in_options_block = True
            continue
        if in_options_block:
            if ")" in line and not line.strip().startswith("'"):
                break
            if line.strip().startswith("'"):
                option_lines.append(line.strip())

    # すべてのオプション行が同じ形式であることを確認
    for line in option_lines:
        # 'option:description' の形式
        assert line.startswith("'"), f"オプション行が ' で始まっていません: {line}"
        assert line.endswith("'"), f"オプション行が ' で終わっていません: {line}"

        # コロンが1つだけ含まれることを確認（オプション名と説明の区切り）
        content = line.strip("'")
        assert content.count(":") == 1, f"オプション行のコロンの数が不正です: {line}"


def test_generate_shell_wrapper_contains_context_variables():
    """文脈認識のための変数が定義されていることを確認"""
    output = generate_shell_wrapper()

    # 文脈認識のための変数が含まれることを確認
    assert 'prev_word="${words[CURRENT-1]}"' in output
    assert 'current_word="${words[CURRENT]}"' in output


def test_generate_shell_wrapper_contains_context_logic():
    """文脈に応じた補完ロジックが含まれることを確認"""
    output = generate_shell_wrapper()

    # プロファイル値を必要とするオプションの後の処理
    assert '"$prev_word" == "--source-profile"' in output
    assert '"$prev_word" == "--output-profile"' in output
    assert '"$prev_word" == "-p"' in output
    assert '"$prev_word" == "-o"' in output

    # 現在の単語が - で始まる場合の処理
    assert '"$current_word" == -*' in output

    # オプション補完の呼び出し
    assert "_describe 'option' options" in output


def test_generate_shell_wrapper_context_logic_order():
    """文脈認識ロジックの順序が正しいことを確認"""
    output = generate_shell_wrapper()

    # ロジックの順序を確認
    lines = output.split("\n")

    # 各条件の位置を見つける
    profile_option_check_line = -1
    current_word_check_line = -1
    else_line = -1

    for i, line in enumerate(lines):
        if '"$prev_word" == "--source-profile"' in line:
            profile_option_check_line = i
        elif '"$current_word" == -*' in line:
            current_word_check_line = i
        elif line.strip() == "else":
            # 最後のelseを見つける
            if current_word_check_line > 0 and i > current_word_check_line:
                else_line = i

    # 順序が正しいことを確認
    assert profile_option_check_line > 0, (
        "プロファイルオプションチェックが見つかりません"
    )
    assert current_word_check_line > 0, "現在の単語チェックが見つかりません"
    assert else_line > 0, "elseブロックが見つかりません"
    assert profile_option_check_line < current_word_check_line < else_line, (
        "文脈認識ロジックの順序が不正です"
    )


# 後方互換性のテスト（タスク5.1）


def test_backward_compatibility_awsop_function_exists():
    """生成されたスクリプトにawsop()関数が含まれることを確認"""
    output = generate_shell_wrapper()

    # awsop関数の定義が含まれることを確認
    assert "function awsop()" in output, "awsop()関数が見つかりません"


def test_backward_compatibility_completion_function_exists():
    """生成されたスクリプトに_awsop()補完関数が含まれることを確認"""
    output = generate_shell_wrapper()

    # _awsop補完関数の定義が含まれることを確認
    assert "_awsop()" in output, "_awsop()補完関数が見つかりません"
    assert "compdef _awsop awsop" in output, "compdef登録が見つかりません"


def test_backward_compatibility_awsop_function_logic_unchanged():
    """awsop()関数のロジックが変更されていないことを確認"""
    output = generate_shell_wrapper()

    # awsop関数の重要なロジックが保持されていることを確認
    # 1. 情報表示オプションの検出
    assert "info_option=false" in output, "info_optionフラグが見つかりません"
    assert "for arg in" in output, "引数ループが見つかりません"
    assert "-h|--help|-v|--version|-l|--list-profiles|--init-shell" in output, (
        "情報表示オプションのパターンが見つかりません"
    )

    # 2. 情報表示オプションの場合の処理
    assert 'if [[ "$info_option" == "true" ]]' in output, (
        "info_optionチェックが見つかりません"
    )
    assert "command awsop" in output, "command awsopが見つかりません"

    # 3. 通常の認証情報取得の場合の処理
    assert "local output" in output, "output変数が見つかりません"
    assert "output=$(command awsop" in output, "outputキャプチャが見つかりません"
    assert "local exit_code=$?" in output, "exit_code変数が見つかりません"

    # 4. evalの実行
    assert "if [[ $exit_code -eq 0 ]]" in output, "exit_codeチェックが見つかりません"
    assert 'eval "$output"' in output, "evalが見つかりません"
    assert "return $exit_code" in output, "returnが見つかりません"


def test_backward_compatibility_profile_completion_preserved():
    """既存のプロファイル補完動作が保持されていることを確認"""
    output = generate_shell_wrapper()

    # プロファイル補完の重要な要素が保持されていることを確認
    # 1. プロファイルリストの取得
    assert "if [[ -f ~/.aws/config ]]" in output, "設定ファイルチェックが見つかりません"
    assert "profiles=($(sed -nE" in output, "プロファイル抽出コマンドが見つかりません"
    assert r"s/^\[(profile )?([^]]+)\]/\2/p" in output, (
        "プロファイル抽出の正規表現が見つかりません"
    )

    # 2. プロファイル補完の提供
    assert "_describe 'profile' profiles" in output, "プロファイル補完が見つかりません"

    # 3. デフォルトでプロファイル補完を提供（elseブロック）
    lines = output.split("\n")
    else_found = False
    describe_after_else = False

    for i, line in enumerate(lines):
        if line.strip() == "else":
            else_found = True
            # elseの後に_describe 'profile'があることを確認
            for j in range(i + 1, min(i + 5, len(lines))):
                if "_describe 'profile' profiles" in lines[j]:
                    describe_after_else = True
                    break

    assert else_found, "elseブロックが見つかりません"
    assert describe_after_else, "elseブロック内にプロファイル補完が見つかりません"


def test_backward_compatibility_zsh_syntax_check():
    """zsh構文チェック（zsh -n）を実行"""
    output = generate_shell_wrapper()

    # 一時ファイルにスクリプトを書き込む
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".zsh", delete=False
    ) as temp_file:
        temp_file.write(output)
        temp_file_path = temp_file.name

    try:
        # zsh -n で構文チェック
        result = subprocess.run(
            ["zsh", "-n", temp_file_path],
            capture_output=True,
            text=True,
            timeout=5,
        )

        # 構文エラーがないことを確認
        assert result.returncode == 0, (
            f"zsh構文チェックが失敗しました:\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )
    finally:
        # 一時ファイルを削除
        Path(temp_file_path).unlink(missing_ok=True)
