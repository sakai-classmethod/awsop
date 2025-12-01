"""show-commandsオプションのプロパティテスト"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

from hypothesis import given, settings
from typer.testing import CliRunner

from awsop.cli import app
from tests.property.strategies import (
    profile_names,
    role_arns,
    regions,
    access_keys,
    secret_keys,
    session_tokens,
    expirations,
)


runner = CliRunner()


@given(
    profile=profile_names,
    role_arn=role_arns,
    region=regions,
    access_key_id=access_keys,
    secret_access_key=secret_keys,
    session_token=session_tokens,
    expiration=expirations,
)
@settings(max_examples=100, deadline=None)
def test_property_2_show_commands_option(
    profile: str,
    role_arn: str,
    region: str,
    access_key_id: str,
    secret_access_key: str,
    session_token: str,
    expiration: datetime,
):
    """Feature: shell-wrapper-credentials, Property 2: show-commandsオプション使用時の動作

    任意の有効なプロファイルと認証情報に対して、--show-commandsオプションを指定した場合、
    標準出力にexportコマンドが含まれ、標準エラー出力に有効期限情報とexportコマンドの
    両方が含まれる必要があります。

    検証: 要件 2.1, 2.2
    """
    # テスト用の設定ファイルを作成
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config"
        config_file.write_text(
            f"""[profile {profile}]
role_arn = {role_arn}
region = {region}
source_profile = default
"""
        )

        # モックのレスポンスを作成
        mock_response = {
            "Credentials": {
                "AccessKeyId": access_key_id,
                "SecretAccessKey": secret_access_key,
                "SessionToken": session_token,
                "Expiration": expiration,
            }
        }

        # OnePasswordClientとSTSClientをモック
        with (
            patch(
                "awsop.app.credentials_manager.OnePasswordClient"
            ) as mock_op_client_class,
            patch("awsop.app.credentials_manager.STSClient") as mock_sts_client_class,
        ):
            # モックインスタンスを設定
            mock_op_client = Mock()
            mock_op_client.check_availability.return_value = True
            mock_op_client.run_aws_command.return_value = mock_response
            mock_op_client_class.return_value = mock_op_client

            mock_sts_client = Mock()
            mock_sts_client_class.return_value = mock_sts_client

            # CLIを実行（--show-commandsオプション付き）
            result = runner.invoke(
                app,
                [
                    "--config-file",
                    str(config_file),
                    "--show-commands",
                    profile,
                ],
                catch_exceptions=False,
            )

            # 終了コードが0であることを確認
            assert result.exit_code == 0, (
                f"Exit code: {result.exit_code}, "
                f"stdout: {result.stdout}, "
                f"stderr: {result.stderr}"
            )

            # 標準出力にexportコマンドが含まれないことを確認
            assert "export AWS_ACCESS_KEY_ID" not in result.stdout, (
                "exportコマンドが標準出力に含まれています"
            )

            # 標準エラー出力に有効期限情報が含まれることを確認
            assert "Credentials will expire" in result.stderr, (
                "有効期限情報が標準エラー出力に含まれていません"
            )

            # 標準エラー出力にexportコマンドが含まれることを確認
            assert f"export AWS_ACCESS_KEY_ID={access_key_id}" in result.stderr, (
                "AWS_ACCESS_KEY_IDが標準エラー出力に含まれていません"
            )
            assert (
                f"export AWS_SECRET_ACCESS_KEY={secret_access_key}" in result.stderr
            ), "AWS_SECRET_ACCESS_KEYが標準エラー出力に含まれていません"
            assert f"export AWS_SESSION_TOKEN={session_token}" in result.stderr, (
                "AWS_SESSION_TOKENが標準エラー出力に含まれていません"
            )
            assert f"export AWS_REGION={region}" in result.stderr, (
                "AWS_REGIONが標準エラー出力に含まれていません"
            )
            assert f"export AWS_DEFAULT_REGION={region}" in result.stderr, (
                "AWS_DEFAULT_REGIONが標準エラー出力に含まれていません"
            )


@given(
    profile=profile_names,
    role_arn=role_arns,
    region=regions,
    access_key_id=access_keys,
    secret_access_key=secret_keys,
    session_token=session_tokens,
    expiration=expirations,
)
@settings(max_examples=100, deadline=None)
def test_property_1_default_behavior(
    profile: str,
    role_arn: str,
    region: str,
    access_key_id: str,
    secret_access_key: str,
    session_token: str,
    expiration: datetime,
):
    """Feature: shell-wrapper-credentials, Property 1: デフォルト動作でのexportコマンド出力

    任意の有効なプロファイルと認証情報に対して、--show-commandsオプションなしで実行した場合、
    標準出力にexportコマンドが含まれ、標準エラー出力には有効期限情報のみが含まれる必要があります。

    検証: 要件 1.1, 1.4, 1.5
    """
    # テスト用の設定ファイルを作成
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config"
        config_file.write_text(
            f"""[profile {profile}]
role_arn = {role_arn}
region = {region}
source_profile = default
"""
        )

        # モックのレスポンスを作成
        mock_response = {
            "Credentials": {
                "AccessKeyId": access_key_id,
                "SecretAccessKey": secret_access_key,
                "SessionToken": session_token,
                "Expiration": expiration,
            }
        }

        # OnePasswordClientとSTSClientをモック
        with (
            patch(
                "awsop.app.credentials_manager.OnePasswordClient"
            ) as mock_op_client_class,
            patch("awsop.app.credentials_manager.STSClient") as mock_sts_client_class,
        ):
            # モックインスタンスを設定
            mock_op_client = Mock()
            mock_op_client.check_availability.return_value = True
            mock_op_client.run_aws_command.return_value = mock_response
            mock_op_client_class.return_value = mock_op_client

            mock_sts_client = Mock()
            mock_sts_client_class.return_value = mock_sts_client

            # CLIを実行（--show-commandsオプションなし）
            result = runner.invoke(
                app,
                [
                    "--config-file",
                    str(config_file),
                    profile,
                ],
                catch_exceptions=False,
            )

            # 終了コードが0であることを確認
            assert result.exit_code == 0, (
                f"Exit code: {result.exit_code}, "
                f"stdout: {result.stdout}, "
                f"stderr: {result.stderr}"
            )

            # 標準出力にexportコマンドが含まれることを確認
            assert f"export AWS_ACCESS_KEY_ID={access_key_id}" in result.stdout, (
                "AWS_ACCESS_KEY_IDが標準出力に含まれていません"
            )
            assert (
                f"export AWS_SECRET_ACCESS_KEY={secret_access_key}" in result.stdout
            ), "AWS_SECRET_ACCESS_KEYが標準出力に含まれていません"
            assert f"export AWS_SESSION_TOKEN={session_token}" in result.stdout, (
                "AWS_SESSION_TOKENが標準出力に含まれていません"
            )
            assert f"export AWS_REGION={region}" in result.stdout, (
                "AWS_REGIONが標準出力に含まれていません"
            )
            assert f"export AWS_DEFAULT_REGION={region}" in result.stdout, (
                "AWS_DEFAULT_REGIONが標準出力に含まれていません"
            )

            # 標準エラー出力に有効期限情報が含まれることを確認
            assert "Credentials will expire" in result.stderr, (
                "有効期限情報が標準エラー出力に含まれていません"
            )

            # 標準エラー出力にexportコマンドが含まれないことを確認
            assert "export AWS_ACCESS_KEY_ID" not in result.stderr, (
                "exportコマンドが標準エラー出力に含まれています"
            )
