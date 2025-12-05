"""コンソール機能の統合テスト

タスク9: 統合テストの実装
要件: 1.1, 2.1, 3.1, 3.2, 7.1, 7.2, 7.3
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typer.testing import CliRunner

from awsop.cli import app


runner = CliRunner()


def create_mock_signin_response():
    """サインイントークンのモックレスポンスを作成"""
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"SigninToken": "test-signin-token"}'
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = False
    return mock_response


def test_console_basic_launch():
    """基本的なコンソール起動のエンドツーエンドテスト

    要件1.1: 指定プロファイルでAWSコンソールをブラウザで開く
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

        # モックのレスポンスを作成
        mock_response = {
            "Credentials": {
                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "SessionToken": "FwoGZXIvYXdzEBYaDH...",
                "Expiration": datetime(2024, 12, 31, 23, 59, 59),
            }
        }

        with (
            patch(
                "awsop.app.credentials_manager.OnePasswordClient"
            ) as mock_op_client_class,
            patch("urllib.request.urlopen", return_value=create_mock_signin_response()),
            patch("webbrowser.open", return_value=True) as mock_browser,
        ):
            mock_op_client = Mock()
            mock_op_client.check_availability.return_value = True
            mock_op_client.run_aws_command.return_value = mock_response
            mock_op_client_class.return_value = mock_op_client

            # CLIを実行（--consoleオプション付き）
            result = runner.invoke(
                app,
                [
                    "--config-file",
                    str(config_file),
                    "--console",
                    "test-profile",
                ],
                catch_exceptions=False,
            )

            # 終了コードが0であることを確認
            assert result.exit_code == 0

            # ブラウザが開かれたことを確認
            assert mock_browser.called
            # 呼び出されたURLを確認
            called_url = mock_browser.call_args[0][0]
            assert "signin.aws.amazon.com/federation" in called_url
            assert "Action=login" in called_url
            assert "SigninToken=test-signin-token" in called_url


def test_console_with_service():
    """サービス指定でのコンソール起動テスト

    要件2.1: 特定のAWSサービスのコンソールページを開く
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # テスト用の設定ファイルを作成
        config_file = Path(tmpdir) / "config"
        config_file.write_text(
            """[profile test-profile]
role_arn = arn:aws:iam::123456789012:role/TestRole
region = us-east-1
"""
        )

        # モックのレスポンスを作成
        mock_response = {
            "Credentials": {
                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "SessionToken": "FwoGZXIvYXdzEBYaDH...",
                "Expiration": datetime(2024, 12, 31, 23, 59, 59),
            }
        }

        with (
            patch(
                "awsop.app.credentials_manager.OnePasswordClient"
            ) as mock_op_client_class,
            patch("urllib.request.urlopen", return_value=create_mock_signin_response()),
            patch("webbrowser.open", return_value=True) as mock_browser,
        ):
            mock_op_client = Mock()
            mock_op_client.check_availability.return_value = True
            mock_op_client.run_aws_command.return_value = mock_response
            mock_op_client_class.return_value = mock_op_client

            # CLIを実行（--consoleと--console-serviceオプション付き）
            result = runner.invoke(
                app,
                [
                    "--config-file",
                    str(config_file),
                    "--console",
                    "--console-service",
                    "s3",
                    "test-profile",
                ],
                catch_exceptions=False,
            )

            # 終了コードが0であることを確認
            assert result.exit_code == 0

            # ブラウザが開かれたことを確認
            assert mock_browser.called
            # 呼び出されたURLにS3サービスが含まれることを確認
            called_url = mock_browser.call_args[0][0]
            assert "s3" in called_url.lower()


def test_console_with_service_shortname():
    """サービス短縮名でのコンソール起動テスト

    要件2.1, 6.2, 6.3: サービスマッピングを使用した短縮名の変換
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # テスト用の設定ファイルを作成
        config_file = Path(tmpdir) / "config"
        config_file.write_text(
            """[profile test-profile]
role_arn = arn:aws:iam::123456789012:role/TestRole
region = us-east-1
"""
        )

        # モックのレスポンスを作成
        mock_response = {
            "Credentials": {
                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "SessionToken": "FwoGZXIvYXdzEBYaDH...",
                "Expiration": datetime(2024, 12, 31, 23, 59, 59),
            }
        }

        with (
            patch(
                "awsop.app.credentials_manager.OnePasswordClient"
            ) as mock_op_client_class,
            patch("urllib.request.urlopen", return_value=create_mock_signin_response()),
            patch("webbrowser.open", return_value=True) as mock_browser,
        ):
            mock_op_client = Mock()
            mock_op_client.check_availability.return_value = True
            mock_op_client.run_aws_command.return_value = mock_response
            mock_op_client_class.return_value = mock_op_client

            # CLIを実行（短縮名"l"でLambdaを指定）
            result = runner.invoke(
                app,
                [
                    "--config-file",
                    str(config_file),
                    "--console",
                    "--console-service",
                    "l",
                    "test-profile",
                ],
                catch_exceptions=False,
            )

            # 終了コードが0であることを確認
            assert result.exit_code == 0

            # ブラウザが開かれたことを確認
            assert mock_browser.called
            # 呼び出されたURLにlambdaサービスが含まれることを確認
            called_url = mock_browser.call_args[0][0]
            assert "lambda" in called_url.lower()


def test_console_link_output():
    """--console-linkオプションでのURL出力テスト

    要件3.1, 3.2: コンソールURLを標準出力に出力し、ブラウザを開かない
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

        # モックのレスポンスを作成
        mock_response = {
            "Credentials": {
                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "SessionToken": "FwoGZXIvYXdzEBYaDH...",
                "Expiration": datetime(2024, 12, 31, 23, 59, 59),
            }
        }

        with (
            patch(
                "awsop.app.credentials_manager.OnePasswordClient"
            ) as mock_op_client_class,
            patch("urllib.request.urlopen", return_value=create_mock_signin_response()),
            patch("webbrowser.open", return_value=True) as mock_browser,
        ):
            mock_op_client = Mock()
            mock_op_client.check_availability.return_value = True
            mock_op_client.run_aws_command.return_value = mock_response
            mock_op_client_class.return_value = mock_op_client

            # CLIを実行（--console-linkオプション付き）
            result = runner.invoke(
                app,
                [
                    "--config-file",
                    str(config_file),
                    "--console-link",
                    "test-profile",
                ],
                catch_exceptions=False,
            )

            # 終了コードが0であることを確認
            assert result.exit_code == 0

            # ブラウザが開かれていないことを確認
            assert not mock_browser.called

            # 標準出力にURLが含まれることを確認
            assert "signin.aws.amazon.com/federation" in result.stdout
            assert "Action=login" in result.stdout
            assert "SigninToken=test-signin-token" in result.stdout


def test_console_link_with_service():
    """--console-linkオプションとサービス指定の組み合わせテスト

    要件3.2: 指定サービスのコンソールURLを標準出力に出力
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # テスト用の設定ファイルを作成
        config_file = Path(tmpdir) / "config"
        config_file.write_text(
            """[profile test-profile]
role_arn = arn:aws:iam::123456789012:role/TestRole
region = ap-northeast-1
"""
        )

        # モックのレスポンスを作成
        mock_response = {
            "Credentials": {
                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "SessionToken": "FwoGZXIvYXdzEBYaDH...",
                "Expiration": datetime(2024, 12, 31, 23, 59, 59),
            }
        }

        with (
            patch(
                "awsop.app.credentials_manager.OnePasswordClient"
            ) as mock_op_client_class,
            patch("urllib.request.urlopen", return_value=create_mock_signin_response()),
            patch("webbrowser.open", return_value=True) as mock_browser,
        ):
            mock_op_client = Mock()
            mock_op_client.check_availability.return_value = True
            mock_op_client.run_aws_command.return_value = mock_response
            mock_op_client_class.return_value = mock_op_client

            # CLIを実行（--console-linkとサービス指定）
            result = runner.invoke(
                app,
                [
                    "--config-file",
                    str(config_file),
                    "--console-link",
                    "--console-service",
                    "ec2",
                    "test-profile",
                ],
                catch_exceptions=False,
            )

            # 終了コードが0であることを確認
            assert result.exit_code == 0

            # ブラウザが開かれていないことを確認
            assert not mock_browser.called

            # 標準出力にURLとEC2サービスが含まれることを確認
            assert "signin.aws.amazon.com/federation" in result.stdout
            assert "ec2" in result.stdout.lower()


def test_console_with_region_option():
    """--regionオプションとコンソール起動の組み合わせテスト

    要件7.1: --regionオプションで指定されたリージョンのコンソールを開く
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

        # モックのレスポンスを作成
        mock_response = {
            "Credentials": {
                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "SessionToken": "FwoGZXIvYXdzEBYaDH...",
                "Expiration": datetime(2024, 12, 31, 23, 59, 59),
            }
        }

        with (
            patch(
                "awsop.app.credentials_manager.OnePasswordClient"
            ) as mock_op_client_class,
            patch("urllib.request.urlopen", return_value=create_mock_signin_response()),
            patch("webbrowser.open", return_value=True) as mock_browser,
        ):
            mock_op_client = Mock()
            mock_op_client.check_availability.return_value = True
            mock_op_client.run_aws_command.return_value = mock_response
            mock_op_client_class.return_value = mock_op_client

            # CLIを実行（--regionオプション付き）
            result = runner.invoke(
                app,
                [
                    "--config-file",
                    str(config_file),
                    "--region",
                    "eu-west-1",
                    "--console",
                    "test-profile",
                ],
                catch_exceptions=False,
            )

            # 終了コードが0であることを確認
            assert result.exit_code == 0

            # ブラウザが開かれたことを確認
            assert mock_browser.called
            # 呼び出されたURLに指定したリージョンが含まれることを確認
            called_url = mock_browser.call_args[0][0]
            assert "eu-west-1" in called_url


def test_console_with_role_arn_option():
    """--role-arnオプションとコンソール起動の組み合わせテスト

    要件7.2: --role-arnオプションで指定されたロールの認証情報でコンソールを開く
    """
    # モックのレスポンスを作成
    mock_response = {
        "Credentials": {
            "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
            "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "SessionToken": "FwoGZXIvYXdzEBYaDH...",
            "Expiration": datetime(2024, 12, 31, 23, 59, 59),
        }
    }

    with (
        patch(
            "awsop.app.credentials_manager.OnePasswordClient"
        ) as mock_op_client_class,
        patch("urllib.request.urlopen", return_value=create_mock_signin_response()),
        patch("webbrowser.open", return_value=True) as mock_browser,
    ):
        mock_op_client = Mock()
        mock_op_client.check_availability.return_value = True
        mock_op_client.run_aws_command.return_value = mock_response
        mock_op_client_class.return_value = mock_op_client

        # CLIを実行（--role-arnオプション付き）
        result = runner.invoke(
            app,
            [
                "--role-arn",
                "arn:aws:iam::123456789012:role/DirectRole",
                "--console",
            ],
            catch_exceptions=False,
        )

        # 終了コードが0であることを確認
        assert result.exit_code == 0

        # ブラウザが開かれたことを確認
        assert mock_browser.called


def test_console_with_source_profile_option():
    """--source-profileオプションとコンソール起動の組み合わせテスト

    要件7.3: --source-profileオプションでソースプロファイルの設定を考慮
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

        # モックのレスポンスを作成
        mock_response = {
            "Credentials": {
                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "SessionToken": "FwoGZXIvYXdzEBYaDH...",
                "Expiration": datetime(2024, 12, 31, 23, 59, 59),
            }
        }

        with (
            patch(
                "awsop.app.credentials_manager.OnePasswordClient"
            ) as mock_op_client_class,
            patch("urllib.request.urlopen", return_value=create_mock_signin_response()),
            patch("webbrowser.open", return_value=True) as mock_browser,
        ):
            mock_op_client = Mock()
            mock_op_client.check_availability.return_value = True
            mock_op_client.run_aws_command.return_value = mock_response
            mock_op_client_class.return_value = mock_op_client

            # CLIを実行（--source-profileと--role-arnオプション付き）
            result = runner.invoke(
                app,
                [
                    "--config-file",
                    str(config_file),
                    "--role-arn",
                    "arn:aws:iam::123456789012:role/TargetRole",
                    "--source-profile",
                    "source-profile",
                    "--console",
                ],
                catch_exceptions=False,
            )

            # 終了コードが0であることを確認
            assert result.exit_code == 0

            # ブラウザが開かれたことを確認
            assert mock_browser.called


def test_console_with_multiple_options():
    """複数のオプションを組み合わせたコンソール起動テスト

    要件7.1, 7.2, 7.3: 複数オプションの組み合わせ
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

        # モックのレスポンスを作成
        mock_response = {
            "Credentials": {
                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "SessionToken": "FwoGZXIvYXdzEBYaDH...",
                "Expiration": datetime(2024, 12, 31, 23, 59, 59),
            }
        }

        with (
            patch(
                "awsop.app.credentials_manager.OnePasswordClient"
            ) as mock_op_client_class,
            patch("urllib.request.urlopen", return_value=create_mock_signin_response()),
            patch("webbrowser.open", return_value=True) as mock_browser,
        ):
            mock_op_client = Mock()
            mock_op_client.check_availability.return_value = True
            mock_op_client.run_aws_command.return_value = mock_response
            mock_op_client_class.return_value = mock_op_client

            # CLIを実行（複数オプション付き）
            result = runner.invoke(
                app,
                [
                    "--config-file",
                    str(config_file),
                    "--region",
                    "ap-northeast-1",
                    "--session-name",
                    "console-session",
                    "--console",
                    "--console-service",
                    "dynamodb",
                    "test-profile",
                ],
                catch_exceptions=False,
            )

            # 終了コードが0であることを確認
            assert result.exit_code == 0

            # ブラウザが開かれたことを確認
            assert mock_browser.called
            # 呼び出されたURLに指定したリージョンとサービスが含まれることを確認
            called_url = mock_browser.call_args[0][0]
            assert "ap-northeast-1" in called_url
            assert "dynamodb" in called_url.lower()


def test_console_govcloud_region():
    """GovCloudリージョンでのコンソール起動テスト

    要件4.1: GovCloudリージョンで正しいドメインを使用
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # テスト用の設定ファイルを作成
        config_file = Path(tmpdir) / "config"
        config_file.write_text(
            """[profile govcloud-profile]
role_arn = arn:aws-us-gov:iam::123456789012:role/GovRole
region = us-gov-west-1
"""
        )

        # モックのレスポンスを作成
        mock_response = {
            "Credentials": {
                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "SessionToken": "FwoGZXIvYXdzEBYaDH...",
                "Expiration": datetime(2024, 12, 31, 23, 59, 59),
            }
        }

        with (
            patch(
                "awsop.app.credentials_manager.OnePasswordClient"
            ) as mock_op_client_class,
            patch("urllib.request.urlopen", return_value=create_mock_signin_response()),
            patch("webbrowser.open", return_value=True) as mock_browser,
        ):
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
                    "--console",
                    "govcloud-profile",
                ],
                catch_exceptions=False,
            )

            # 終了コードが0であることを確認
            assert result.exit_code == 0

            # ブラウザが開かれたことを確認
            assert mock_browser.called
            # 呼び出されたURLにGovCloudドメインが含まれることを確認
            called_url = mock_browser.call_args[0][0]
            assert "amazonaws-us-gov.com" in called_url


def test_console_china_region():
    """中国リージョンでのコンソール起動テスト

    要件4.2: 中国リージョンで正しいドメインを使用
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # テスト用の設定ファイルを作成
        config_file = Path(tmpdir) / "config"
        config_file.write_text(
            """[profile china-profile]
role_arn = arn:aws-cn:iam::123456789012:role/ChinaRole
region = cn-north-1
"""
        )

        # モックのレスポンスを作成
        mock_response = {
            "Credentials": {
                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "SessionToken": "FwoGZXIvYXdzEBYaDH...",
                "Expiration": datetime(2024, 12, 31, 23, 59, 59),
            }
        }

        with (
            patch(
                "awsop.app.credentials_manager.OnePasswordClient"
            ) as mock_op_client_class,
            patch("urllib.request.urlopen", return_value=create_mock_signin_response()),
            patch("webbrowser.open", return_value=True) as mock_browser,
        ):
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
                    "--console",
                    "china-profile",
                ],
                catch_exceptions=False,
            )

            # 終了コードが0であることを確認
            assert result.exit_code == 0

            # ブラウザが開かれたことを確認
            assert mock_browser.called
            # 呼び出されたURLに中国ドメインが含まれることを確認
            called_url = mock_browser.call_args[0][0]
            assert "amazonaws.cn" in called_url
