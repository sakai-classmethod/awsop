"""unsetコマンドのプロパティテスト"""

from hypothesis import given, settings
from hypothesis import strategies as st

from awsop.app.credentials_manager import CredentialsManager


@settings(max_examples=100, deadline=None)
@given(st.just(None))  # パラメータなしで複数回実行
def test_property_5_unset_command_completeness(_):
    """Feature: remove-aws-profile-export, Property 2: unset コマンドの変数セットの正確性

    全てのunsetコマンド出力は、以下の全ての環境変数をunsetする:
    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN,
    AWS_REGION, AWS_DEFAULT_REGION, AWSOP_PROFILE, AWSOP_EXPIRATION

    AWS_PROFILE は awsop が管理しないため、unset 対象に含まれないことを確認する。

    検証: 要件 2.1, 2.2
    """
    # CredentialsManagerを使用してunsetコマンドを生成
    manager = CredentialsManager()
    unset_commands = manager.format_unset_commands()

    # 必須の環境変数が全てunsetされることを確認
    required_vars = [
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
        "AWS_REGION",
        "AWS_DEFAULT_REGION",
        "AWSOP_PROFILE",
        "AWSOP_EXPIRATION",
    ]

    for var in required_vars:
        assert f"unset {var}" in unset_commands, f"{var}のunsetが出力に含まれていません"

    # AWS_PROFILE が出力に含まれないことを確認
    assert "AWS_PROFILE" not in unset_commands, "AWS_PROFILE がunset出力に含まれています"

    # 各行がunsetコマンドであることを確認（7行）
    lines = unset_commands.strip().split("\n")
    assert len(lines) == 7, f"unsetコマンドの行数が正しくありません: 期待値=7, 実際={len(lines)}"

    for line in lines:
        assert line.startswith("unset "), f"無効なコマンド形式: {line}"
