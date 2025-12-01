"""ヘルプオプションのプロパティベーステスト

Feature: help-option-fix
"""

import subprocess
import sys
from hypothesis import given, settings, strategies as st


@given(
    # ヘルプオプションの後に追加される引数（ヘルプが優先されるため無視される）
    trailing_args=st.lists(
        st.text(
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
            min_size=1,
            max_size=10,
        ),
        max_size=3,
    ),
)
@settings(max_examples=100, deadline=None)
def test_help_option_equivalence(trailing_args):
    """**Feature: help-option-fix, Property 1: ヘルプオプションの等価性**

    任意の追加のコマンドライン引数の組み合わせについて、
    -hを使用した場合と--helpを使用した場合で、
    システムは同じヘルプメッセージを表示する

    **Validates: Requirements 1.2**
    """
    # -h を使用した場合（ヘルプオプションを最初に配置）
    result_short = subprocess.run(
        [sys.executable, "-m", "awsop", "-h"] + trailing_args,
        capture_output=True,
        text=True,
    )

    # --help を使用した場合（ヘルプオプションを最初に配置）
    result_long = subprocess.run(
        [sys.executable, "-m", "awsop", "--help"] + trailing_args,
        capture_output=True,
        text=True,
    )

    # 両方とも成功すること
    assert result_short.returncode == 0
    assert result_long.returncode == 0

    # 同じ出力を生成すること
    assert result_short.stdout == result_long.stdout


@given(
    # ヘルプオプションの選択
    help_option=st.sampled_from(["-h", "--help"]),
    # ヘルプオプションの後に続く無害な引数（無視される）
    trailing_args=st.lists(
        st.text(
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
            min_size=1,
            max_size=10,
        ),
        max_size=3,
    ),
)
@settings(max_examples=100)
def test_help_option_priority(help_option, trailing_args):
    """**Feature: help-option-fix, Property 2: ヘルプオプションの優先度**

    任意のコマンドライン引数の組み合わせについて、
    ヘルプオプション（-hまたは--help）が含まれる場合、
    システムは他の処理をスキップしてヘルプメッセージを表示し、
    終了コード0を返す

    **Validates: Requirements 2.3**
    """
    # ヘルプオプションを最初に配置（後続の引数は無視される）
    cmd_args = [help_option] + trailing_args

    result = subprocess.run(
        [sys.executable, "-m", "awsop"] + cmd_args,
        capture_output=True,
        text=True,
    )

    # 終了コードが0であること
    assert result.returncode == 0

    # ヘルプメッセージが表示されること
    assert "AWS credentials manager" in result.stdout
    assert "--help" in result.stdout or "-h" in result.stdout

    # エラーメッセージが表示されないこと
    assert "Error" not in result.stderr
    assert "エラー" not in result.stderr


@given(
    # ヘルプメッセージに表示される短縮オプションをテスト
    option=st.sampled_from(["-h", "-v", "-l"]),
)
@settings(max_examples=100)
def test_help_message_implementation_consistency(option):
    """**Feature: help-option-fix, Property 3: ヘルプメッセージと実装の一貫性**

    任意のヘルプメッセージに表示される短縮オプションについて、
    そのオプションを実際に使用した場合、
    システムは対応する機能を正しく実行する

    **Validates: Requirements 3.2**
    """
    # まずヘルプメッセージを取得
    help_result = subprocess.run(
        [sys.executable, "-m", "awsop", "--help"],
        capture_output=True,
        text=True,
    )

    # ヘルプメッセージに短縮オプションが表示されているか確認
    if option in help_result.stdout:
        # 短縮オプションを実際に使用
        result = subprocess.run(
            [sys.executable, "-m", "awsop", option],
            capture_output=True,
            text=True,
        )

        # オプションが機能すること（エラーにならないこと）
        # -h: ヘルプを表示（終了コード0）
        # -v: バージョンを表示（終了コード0）
        # -l: プロファイルリストを表示（終了コード0）
        assert result.returncode == 0

        # "No such option"エラーが表示されないこと
        assert "No such option" not in result.stderr
        assert "No such option" not in result.stdout


@given(
    # 無効なオプション文字列を生成
    # "--"で始まり、有効なオプション名ではない文字列
    invalid_option=st.one_of(
        # 単一文字の無効なオプション（--h, --x など）
        st.builds(lambda c: f"--{c}", st.sampled_from("abcdefgijkmnopqrstuwxyz")),
        # ランダムな無効なロングオプション
        st.builds(
            lambda s: f"--{s}",
            st.text(
                alphabet=st.characters(whitelist_categories=("Ll", "Nd")),
                min_size=2,
                max_size=15,
            ).filter(
                lambda s: s
                not in [
                    "help",
                    "version",
                    "list-profiles",
                    "init-shell",
                    "region",
                    "output",
                    "debug",
                    "refresh",
                ]
            ),
        ),
    ),
)
@settings(max_examples=100)
def test_invalid_option_error_handling(invalid_option):
    """**Feature: help-option-fix, Property 4: 無効なオプションのエラーハンドリング**

    任意の無効なオプション文字列について、
    システムはエラーメッセージを表示し、
    非ゼロの終了コードを返す

    **Validates: Requirements 3.3**
    """
    result = subprocess.run(
        [sys.executable, "-m", "awsop", invalid_option],
        capture_output=True,
        text=True,
    )

    # 非ゼロの終了コードを返すこと
    assert result.returncode != 0

    # エラーメッセージが表示されること
    # Typerは通常stderrにエラーを出力する
    error_output = result.stderr + result.stdout

    # "No such option"または類似のエラーメッセージが含まれること
    assert (
        "No such option" in error_output
        or "Error" in error_output
        or "Invalid" in error_output
        or "Usage" in error_output
    )
