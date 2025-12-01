"""オプション組み合わせの統合テスト

タスク18: 統合テストの実装
要件: 全般（オプション組み合わせ）
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime
from typer.testing import CliRunner

from awsop.cli import app


runner = CliRunner()


def test_combination_region_and_session_name():
    """--regionと--session-nameの組み合わせ

    要件4.2.1, 4.3.1: リージョン指定とセッション名指定の組み合わせ
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # テスト用の設定ファイルを作成
        config_file = Path(tmpdir) / "config"
        config_file.write_text(
            """[profile test-profile]
role_arn = arn:aws:iam::123456789012:role/TestRole
region = us-west-2
"""
        )

        mock_response = {
            "Credentials": {
                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "SessionToken": "FwoGZXIvYXdzEBYaDH...",
                "Expiration": datetime(2024, 12, 31, 23, 59, 59),
            }
        }

        with patch(
            "awsop.app.credentials_manager.OnePasswordClient"
        ) as mock_op_client_class:
            mock_op_client = Mock()
            mock_op_client.check_availability.return_value = True
            mock_op_client.run_aws_command.return_value = mock_response
            mock_op_client_class.return_value = mock_op_client

            # CLIを実行
            result = runner.invoke(
                app,
                [
                    "--config-file",
                    str(config_file),
                    "--region",
                    "ap-northeast-1",
                    "--session-name",
                    "custom-session",
                    "--show-commands",
                    "test-profile",
                ],
                catch_exceptions=False,
            )

            assert result.exit_code == 0
            assert "export AWS_REGION=ap-northeast-1" in result.stdout
            assert "export AWS_DEFAULT_REGION=ap-northeast-1" in result.stdout


def test_combination_role_duration_and_external_id():
    """--role-durationと--external-idの組み合わせ

    要件4.4.1, 4.8.1: ロール期間指定と外部ID指定の組み合わせ
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # テスト用の設定ファイルを作成
        config_file = Path(tmpdir) / "config"
        config_file.write_text(
            """[profile test-profile]
role_arn = arn:aws:iam::123456789012:role/TestRole
"""
        )

        mock_response = {
            "Credentials": {
                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "SessionToken": "FwoGZXIvYXdzEBYaDH...",
                "Expiration": datetime(2024, 12, 31, 23, 59, 59),
            }
        }

        with patch(
            "awsop.app.credentials_manager.OnePasswordClient"
        ) as mock_op_client_class:
            mock_op_client = Mock()
            mock_op_client.check_availability.return_value = True
            mock_op_client.run_aws_command.return_value = mock_response
            mock_op_client_class.return_value = mock_op_client

            # CLIを実行
            result = runner.invoke(
                app,
                [
                    "--config-file",
                    str(config_file),
                    "--role-duration",
                    "7200",
                    "--external-id",
                    "external-123",
                    "--show-commands",
                    "test-profile",
                ],
                catch_exceptions=False,
            )

            assert result.exit_code == 0
            assert "export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE" in result.stdout


def test_combination_output_profile_and_show_commands():
    """--output-profileと--show-commandsの組み合わせ

    要件4.1.1, 4.6.1: export表示と認証情報ファイル書き込みの組み合わせ
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # テスト用の設定ファイルを作成
        config_file = Path(tmpdir) / "config"
        config_file.write_text(
            """[profile test-profile]
role_arn = arn:aws:iam::123456789012:role/TestRole
"""
        )

        # テスト用の認証情報ファイルを作成
        credentials_file = Path(tmpdir) / "credentials"
        credentials_file.write_text("")

        mock_response = {
            "Credentials": {
                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "SessionToken": "FwoGZXIvYXdzEBYaDH...",
                "Expiration": datetime(2024, 12, 31, 23, 59, 59),
            }
        }

        with patch(
            "awsop.app.credentials_manager.OnePasswordClient"
        ) as mock_op_client_class:
            mock_op_client = Mock()
            mock_op_client.check_availability.return_value = True
            mock_op_client.run_aws_command.return_value = mock_response
            mock_op_client_class.return_value = mock_op_client

            # CLIを実行
            result = runner.invoke(
                app,
                [
                    "--config-file",
                    str(config_file),
                    "--credentials-file",
                    str(credentials_file),
                    "--output-profile",
                    "output-test",
                    "--show-commands",
                    "test-profile",
                ],
                catch_exceptions=False,
            )

            assert result.exit_code == 0
            # exportコマンドが標準出力に含まれる
            assert "export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE" in result.stdout
            # 認証情報ファイルにも書き込まれる
            credentials_content = credentials_file.read_text()
            assert "[output-test]" in credentials_content


def test_combination_role_arn_and_region():
    """--role-arnと--regionの組み合わせ

    要件4.2.1, 4.7.1: ロールARN指定とリージョン指定の組み合わせ
    """
    mock_response = {
        "Credentials": {
            "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
            "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "SessionToken": "FwoGZXIvYXdzEBYaDH...",
            "Expiration": datetime(2024, 12, 31, 23, 59, 59),
        }
    }

    with patch(
        "awsop.app.credentials_manager.OnePasswordClient"
    ) as mock_op_client_class:
        mock_op_client = Mock()
        mock_op_client.check_availability.return_value = True
        mock_op_client.run_aws_command.return_value = mock_response
        mock_op_client_class.return_value = mock_op_client

        # CLIを実行
        result = runner.invoke(
            app,
            [
                "--role-arn",
                "arn:aws:iam::123456789012:role/DirectRole",
                "--region",
                "eu-west-1",
                "--show-commands",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert "export AWS_REGION=eu-west-1" in result.stdout
        assert "export AWS_DEFAULT_REGION=eu-west-1" in result.stdout


def test_combination_source_profile_and_role_arn():
    """--source-profileと--role-arnの組み合わせ

    要件4.7.2, 4.7.3: ソースプロファイル指定とロールARN指定の組み合わせ
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # テスト用の設定ファイルを作成
        config_file = Path(tmpdir) / "config"
        config_file.write_text(
            """[profile source-profile]
role_arn = arn:aws:iam::123456789012:role/SourceRole
region = us-west-2
"""
        )

        mock_response = {
            "Credentials": {
                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "SessionToken": "FwoGZXIvYXdzEBYaDH...",
                "Expiration": datetime(2024, 12, 31, 23, 59, 59),
            }
        }

        with patch(
            "awsop.app.credentials_manager.OnePasswordClient"
        ) as mock_op_client_class:
            mock_op_client = Mock()
            mock_op_client.check_availability.return_value = True
            mock_op_client.run_aws_command.return_value = mock_response
            mock_op_client_class.return_value = mock_op_client

            # CLIを実行
            result = runner.invoke(
                app,
                [
                    "--config-file",
                    str(config_file),
                    "--role-arn",
                    "arn:aws:iam::123456789012:role/TargetRole",
                    "--source-profile",
                    "source-profile",
                    "--show-commands",
                ],
                catch_exceptions=False,
            )

            assert result.exit_code == 0
            assert "export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE" in result.stdout


def test_combination_all_logging_options():
    """--infoと--debugの組み合わせ（--debugが優先される）

    要件9.1, 9.2: ログレベル指定の組み合わせ
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # テスト用の設定ファイルを作成
        config_file = Path(tmpdir) / "config"
        config_file.write_text(
            """[profile test-profile]
role_arn = arn:aws:iam::123456789012:role/TestRole
"""
        )

        mock_response = {
            "Credentials": {
                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "SessionToken": "FwoGZXIvYXdzEBYaDH...",
                "Expiration": datetime(2024, 12, 31, 23, 59, 59),
            }
        }

        with patch(
            "awsop.app.credentials_manager.OnePasswordClient"
        ) as mock_op_client_class:
            mock_op_client = Mock()
            mock_op_client.check_availability.return_value = True
            mock_op_client.run_aws_command.return_value = mock_response
            mock_op_client_class.return_value = mock_op_client

            # CLIを実行（--infoと--debugの両方を指定）
            result = runner.invoke(
                app,
                [
                    "--config-file",
                    str(config_file),
                    "--info",
                    "--debug",
                    "--show-commands",
                    "test-profile",
                ],
                catch_exceptions=False,
            )

            assert result.exit_code == 0
            # DEBUGログが表示される（--debugが優先）
            assert "DEBUG" in result.stderr or "デバッグ" in result.stderr.lower()


def test_combination_custom_config_and_credentials_files():
    """--config-fileと--credentials-fileの組み合わせ

    要件10.1, 10.2: カスタム設定ファイルとカスタム認証情報ファイルの組み合わせ
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # テスト用の設定ファイルを作成
        config_file = Path(tmpdir) / "custom_config"
        config_file.write_text(
            """[profile custom-profile]
role_arn = arn:aws:iam::123456789012:role/CustomRole
"""
        )

        # テスト用の認証情報ファイルを作成
        credentials_file = Path(tmpdir) / "custom_credentials"
        credentials_file.write_text("")

        mock_response = {
            "Credentials": {
                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "SessionToken": "FwoGZXIvYXdzEBYaDH...",
                "Expiration": datetime(2024, 12, 31, 23, 59, 59),
            }
        }

        with patch(
            "awsop.app.credentials_manager.OnePasswordClient"
        ) as mock_op_client_class:
            mock_op_client = Mock()
            mock_op_client.check_availability.return_value = True
            mock_op_client.run_aws_command.return_value = mock_response
            mock_op_client_class.return_value = mock_op_client

            # CLIを実行
            result = runner.invoke(
                app,
                [
                    "--config-file",
                    str(config_file),
                    "--credentials-file",
                    str(credentials_file),
                    "--output-profile",
                    "output-custom",
                    "--show-commands",
                    "custom-profile",
                ],
                catch_exceptions=False,
            )

            assert result.exit_code == 0
            assert "export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE" in result.stdout
            # カスタム認証情報ファイルに書き込まれる
            credentials_content = credentials_file.read_text()
            assert "[output-custom]" in credentials_content


def test_combination_all_assume_role_options():
    """AssumeRole関連のすべてのオプションの組み合わせ

    要件4.3.1, 4.4.1, 4.8.1: セッション名、ロール期間、外部IDの組み合わせ
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # テスト用の設定ファイルを作成
        config_file = Path(tmpdir) / "config"
        config_file.write_text(
            """[profile test-profile]
role_arn = arn:aws:iam::123456789012:role/TestRole
"""
        )

        mock_response = {
            "Credentials": {
                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "SessionToken": "FwoGZXIvYXdzEBYaDH...",
                "Expiration": datetime(2024, 12, 31, 23, 59, 59),
            }
        }

        with patch(
            "awsop.app.credentials_manager.OnePasswordClient"
        ) as mock_op_client_class:
            mock_op_client = Mock()
            mock_op_client.check_availability.return_value = True
            mock_op_client.run_aws_command.return_value = mock_response
            mock_op_client_class.return_value = mock_op_client

            # CLIを実行
            result = runner.invoke(
                app,
                [
                    "--config-file",
                    str(config_file),
                    "--session-name",
                    "full-options-session",
                    "--role-duration",
                    "10800",
                    "--external-id",
                    "ext-id-456",
                    "--show-commands",
                    "test-profile",
                ],
                catch_exceptions=False,
            )

            assert result.exit_code == 0
            assert "export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE" in result.stdout


def test_combination_region_override_with_output_profile():
    """リージョン上書きと認証情報ファイル書き込みの組み合わせ

    要件4.2.1, 4.6.1: リージョン指定と認証情報ファイル書き込みの組み合わせ
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # テスト用の設定ファイルを作成
        config_file = Path(tmpdir) / "config"
        config_file.write_text(
            """[profile test-profile]
role_arn = arn:aws:iam::123456789012:role/TestRole
region = us-west-2
"""
        )

        # テスト用の認証情報ファイルを作成
        credentials_file = Path(tmpdir) / "credentials"
        credentials_file.write_text("")

        mock_response = {
            "Credentials": {
                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "SessionToken": "FwoGZXIvYXdzEBYaDH...",
                "Expiration": datetime(2024, 12, 31, 23, 59, 59),
            }
        }

        with patch(
            "awsop.app.credentials_manager.OnePasswordClient"
        ) as mock_op_client_class:
            mock_op_client = Mock()
            mock_op_client.check_availability.return_value = True
            mock_op_client.run_aws_command.return_value = mock_response
            mock_op_client_class.return_value = mock_op_client

            # CLIを実行
            result = runner.invoke(
                app,
                [
                    "--config-file",
                    str(config_file),
                    "--credentials-file",
                    str(credentials_file),
                    "--region",
                    "ap-northeast-1",
                    "--output-profile",
                    "output-region",
                    "--show-commands",
                    "test-profile",
                ],
                catch_exceptions=False,
            )

            assert result.exit_code == 0
            # リージョンが上書きされている
            assert "export AWS_REGION=ap-northeast-1" in result.stdout
            # 認証情報ファイルに書き込まれる
            credentials_content = credentials_file.read_text()
            assert "[output-region]" in credentials_content


def test_combination_role_arn_with_all_options():
    """--role-arnと他のすべてのオプションの組み合わせ

    要件: 複数オプションの同時使用
    """
    mock_response = {
        "Credentials": {
            "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
            "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "SessionToken": "FwoGZXIvYXdzEBYaDH...",
            "Expiration": datetime(2024, 12, 31, 23, 59, 59),
        }
    }

    with patch(
        "awsop.app.credentials_manager.OnePasswordClient"
    ) as mock_op_client_class:
        mock_op_client = Mock()
        mock_op_client.check_availability.return_value = True
        mock_op_client.run_aws_command.return_value = mock_response
        mock_op_client_class.return_value = mock_op_client

        # CLIを実行
        result = runner.invoke(
            app,
            [
                "--role-arn",
                "arn:aws:iam::123456789012:role/CompleteRole",
                "--region",
                "eu-central-1",
                "--session-name",
                "complete-session",
                "--role-duration",
                "14400",
                "--external-id",
                "complete-ext-id",
                "--show-commands",
                "--debug",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert "export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE" in result.stdout
        assert "export AWS_REGION=eu-central-1" in result.stdout
