"""シェルラッパー関数経由での認証情報設定の統合テスト

Feature: shell-wrapper-credentials, Property 4: 環境変数の設定
検証: 要件 1.2, 1.3
"""

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
def test_property_4_environment_variables_set(
    profile: str,
    role_arn: str,
    region: str,
    access_key_id: str,
    secret_access_key: str,
    session_token: str,
    expiration: datetime,
):
    """Feature: shell-wrapper-credentials, Property 4: 環境変数の設定

    任意の有効なプロファイルと認証情報に対して、シェルラッパー関数経由で
    --show-commandsなしで実行した場合、標準出力にexportコマンドが含まれ、
    それをevalすることでAWS_ACCESS_KEY_ID、AWS_SECRET_ACCESS_KEY、
    AWS_SESSION_TOKEN、AWS_REGION、AWS_DEFAULT_REGIONが環境変数に設定される必要があります。

    検証: 要件 1.2, 1.3
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
            # これらのコマンドをevalすることで環境変数が設定される
            assert f"export AWS_ACCESS_KEY_ID={access_key_id}" in result.stdout, (
                "AWS_ACCESS_KEY_IDのexportコマンドが標準出力に含まれていません"
            )
            assert (
                f"export AWS_SECRET_ACCESS_KEY={secret_access_key}" in result.stdout
            ), "AWS_SECRET_ACCESS_KEYのexportコマンドが標準出力に含まれていません"
            assert f"export AWS_SESSION_TOKEN={session_token}" in result.stdout, (
                "AWS_SESSION_TOKENのexportコマンドが標準出力に含まれていません"
            )
            assert f"export AWS_REGION={region}" in result.stdout, (
                "AWS_REGIONのexportコマンドが標準出力に含まれていません"
            )
            assert f"export AWS_DEFAULT_REGION={region}" in result.stdout, (
                "AWS_DEFAULT_REGIONのexportコマンドが標準出力に含まれていません"
            )

            # 標準出力の内容が有効なシェルコマンドであることを確認
            # 各行がexportコマンドまたは空行であることを検証
            for line in result.stdout.strip().split("\n"):
                if line.strip():  # 空行でない場合
                    assert line.startswith("export "), (
                        f"標準出力に無効な行が含まれています: {line}"
                    )
