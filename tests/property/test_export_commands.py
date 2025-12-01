"""exportコマンドのプロパティテスト"""

from hypothesis import given, settings
from hypothesis import strategies as st
from datetime import datetime, timedelta

from awsop.app.credentials_manager import Credentials, CredentialsManager
from tests.property.strategies import (
    access_keys,
    secret_keys,
    session_tokens,
    regions,
    profile_names,
    expirations,
)


@given(
    access_key_id=access_keys,
    secret_access_key=secret_keys,
    session_token=session_tokens,
    expiration=expirations,
    region=regions,
    profile=profile_names,
)
@settings(max_examples=100, deadline=None)
def test_property_3_export_command_completeness(
    access_key_id: str,
    secret_access_key: str,
    session_token: str,
    expiration: datetime,
    region: str,
    profile: str,
):
    """Feature: awsop-cli-migration, Property 3: exportコマンドの完全性

    任意の認証情報に対して、exportコマンド出力は以下の全ての環境変数を含む:
    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN,
    AWS_REGION, AWS_DEFAULT_REGION, AWS_PROFILE, AWSOP_PROFILE, AWSOP_EXPIRATION

    検証: 要件 1.4, 2.2, 4.1, 4.2
    """
    # 認証情報を作成
    credentials = Credentials(
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        session_token=session_token,
        expiration=expiration,
        region=region,
        profile=profile,
    )

    # CredentialsManagerを使用してexportコマンドを生成
    manager = CredentialsManager()
    export_commands = manager.format_export_commands(credentials)

    # 必須の環境変数が全て含まれていることを確認
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
        assert f"export {var}=" in export_commands, f"{var}が出力に含まれていません"

    # 各環境変数に正しい値が設定されていることを確認
    assert f"export AWS_ACCESS_KEY_ID={access_key_id}" in export_commands
    assert f"export AWS_SECRET_ACCESS_KEY={secret_access_key}" in export_commands
    assert f"export AWS_SESSION_TOKEN={session_token}" in export_commands
    assert f"export AWS_REGION={region}" in export_commands
    assert f"export AWS_DEFAULT_REGION={region}" in export_commands
    assert f"export AWS_PROFILE={profile}" in export_commands
    assert f"export AWSOP_PROFILE={profile}" in export_commands
    assert f"export AWSOP_EXPIRATION={expiration.isoformat()}" in export_commands
