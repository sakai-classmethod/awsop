"""unsetコマンドのプロパティテスト"""

from hypothesis import given, settings
from hypothesis import strategies as st

from awsop.app.credentials_manager import CredentialsManager


@settings(max_examples=100, deadline=None)
@given(st.just(None))  # パラメータなしで複数回実行
def test_property_5_unset_command_completeness(_):
    """Feature: awsop-cli-migration, Property 5: unsetコマンドの完全性

    全てのunsetコマンド出力は、以下の全ての環境変数をunsetする:
    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN,
    AWS_REGION, AWS_DEFAULT_REGION, AWS_PROFILE, AWSOP_PROFILE, AWSOP_EXPIRATION

    検証: 要件 4.1.2
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
        "AWS_PROFILE",
        "AWSOP_PROFILE",
        "AWSOP_EXPIRATION",
    ]

    for var in required_vars:
        assert f"unset {var}" in unset_commands, f"{var}のunsetが出力に含まれていません"

    # 各行がunsetコマンドであることを確認
    lines = unset_commands.strip().split("\n")
    assert len(lines) == len(required_vars), "unsetコマンドの行数が正しくありません"

    for line in lines:
        assert line.startswith("unset "), f"無効なコマンド形式: {line}"
