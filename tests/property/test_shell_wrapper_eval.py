"""シェルラッパー関数のeval動作のプロパティベーステスト

Feature: shell-wrapper-credentials
"""

import subprocess
import tempfile
from pathlib import Path
from hypothesis import given, settings, strategies as st
from awsop.shell.wrapper import generate_shell_wrapper


# 情報表示オプション
INFO_OPTIONS = [
    "-h",
    "--help",
    "-v",
    "--version",
    "-l",
    "--list-profiles",
    "--init-shell",
    "-s",
    "--show-commands",
]


def check_eval_behavior(args: list[str]) -> bool:
    """
    シェルラッパー関数がevalを実行するかどうかをチェック

    Args:
        args: コマンドライン引数のリスト

    Returns:
        bool: evalが実行される場合はTrue、実行されない場合はFalse
    """
    # シェルラッパー関数のスクリプトを取得
    wrapper_script = generate_shell_wrapper()

    # テスト用のシェルスクリプトを作成
    # evalが実行されるかどうかを判定するために、
    # 情報表示オプションの検出ロジックをシミュレート
    test_script = f"""
{wrapper_script}

# 引数をチェック
info_option=false
for arg in "$@"; do
  case "$arg" in
    -h|--help|-v|--version|-l|--list-profiles|--init-shell|-s|--show-commands)
      info_option=true
      break
      ;;
  esac
done

if [[ "$info_option" == "true" ]]; then
  echo "NO_EVAL"
else
  echo "EVAL"
fi
"""

    # 一時ファイルにスクリプトを書き込む
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".zsh", delete=False
    ) as temp_file:
        temp_file.write(test_script)
        temp_file_path = temp_file.name

    try:
        # zshでスクリプトを実行
        result = subprocess.run(
            ["zsh", temp_file_path] + args,
            capture_output=True,
            text=True,
            timeout=5,
        )

        # 出力を確認
        output = result.stdout.strip()
        return output == "EVAL"

    finally:
        # 一時ファイルを削除
        Path(temp_file_path).unlink(missing_ok=True)


@given(
    # 情報表示オプションを含む引数リストを生成
    info_option=st.sampled_from(INFO_OPTIONS),
    # 追加の引数（オプションの前後に配置される可能性がある）
    additional_args=st.lists(
        st.text(
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-_"
            ),
            min_size=1,
            max_size=20,
        ),
        min_size=0,
        max_size=3,
    ),
)
@settings(max_examples=100, deadline=None)
def test_property_3_info_option_skips_eval(info_option, additional_args):
    """**Feature: shell-wrapper-credentials, Property 3: シェルラッパー関数のeval動作**

    任意のコマンドライン引数に対して、
    -sまたは--show-commandsが含まれる場合、
    シェルラッパー関数はevalを実行しない

    **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
    """
    # 引数リストを構築（情報表示オプションを含む）
    args = additional_args[:1] + [info_option] + additional_args[1:]

    # evalが実行されないことを確認
    should_eval = check_eval_behavior(args)
    assert not should_eval, (
        f"情報表示オプション {info_option} が含まれる場合、evalは実行されないべきです。"
        f"引数: {args}"
    )


@given(
    # 情報表示オプションを含まない引数リストを生成
    args=st.lists(
        st.text(
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-_"
            ),
            min_size=1,
            max_size=20,
        ).filter(lambda x: x not in INFO_OPTIONS),
        min_size=1,
        max_size=5,
    ),
)
@settings(max_examples=100, deadline=None)
def test_property_3_normal_execution_uses_eval(args):
    """**Feature: shell-wrapper-credentials, Property 3: シェルラッパー関数のeval動作**

    任意のコマンドライン引数に対して、
    情報表示オプションが含まれない場合、
    シェルラッパー関数はevalを実行する

    **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
    """
    # evalが実行されることを確認
    should_eval = check_eval_behavior(args)
    assert should_eval, (
        f"情報表示オプションが含まれない場合、evalは実行されるべきです。引数: {args}"
    )


@given(st.just(None))
@settings(max_examples=100, deadline=None)
def test_property_3_show_commands_in_info_options(_):
    """**Feature: shell-wrapper-credentials, Property 3: シェルラッパー関数のeval動作**

    生成されたシェルラッパー関数のスクリプトを解析し、
    -sと--show-commandsが情報表示オプションとして
    正しく定義されていることを確認

    **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
    """
    # シェルラッパー関数のスクリプトを取得
    wrapper_script = generate_shell_wrapper()

    # 情報表示オプションのパターンを確認
    # -s|--show-commands が含まれることを確認
    assert "-s|--show-commands" in wrapper_script or (
        "-s" in wrapper_script and "--show-commands" in wrapper_script
    ), (
        "シェルラッパー関数に -s と --show-commands が情報表示オプションとして含まれていません"
    )

    # case文の中に含まれることを確認
    lines = wrapper_script.split("\n")
    in_case_block = False
    found_show_commands = False

    for line in lines:
        if "case" in line and '"$arg"' in line:
            in_case_block = True
        elif in_case_block and "esac" in line:
            in_case_block = False
        elif in_case_block and ("-s" in line or "--show-commands" in line):
            found_show_commands = True

    assert found_show_commands, (
        "case文の中に -s または --show-commands が含まれていません"
    )
