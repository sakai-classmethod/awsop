"""プロファイル切り替えの統合テスト

タスク13: CLIレイヤーの実装（プロファイル切り替え）
要件: 1.1, 1.2, 1.4, 8.1, 8.2
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime
from typer.testing import CliRunner

from awsop.cli import app


runner = CliRunner()


def test_profile_switching_success():
    """プロファイル切り替えが成功する場合のテスト

    要件1.1: プロファイル名を指定して実行すると、~/.aws/configからプロファイル設定を読み取る
    要件1.2: プロファイルにrole_arnが定義されている場合、AssumeRoleを実行する
    要件1.4: AssumeRoleが成功すると、一時認証情報をexportコマンド形式で標準出力に出力する
    要件8.1: 1Password経由で認証情報を取得している間、スピナーを表示する
    要件8.2: 認証情報の取得が完了すると、プロファイル名と有効期限を表示する
    """
    # テスト用の設定ファイルを作成
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config"
        config_file.write_text(
            """[profile test-profile]
role_arn = arn:aws:iam::123456789012:role/TestRole
region = us-west-2
source_profile = default
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
                    "test-profile",
                ],
                catch_exceptions=False,
            )

            # 終了コードが0であることを確認
            assert result.exit_code == 0, (
                f"Exit code: {result.exit_code}, stderr: {result.stderr}"
            )

            # --show-commandsオプション付きの場合は標準エラー出力にexportコマンドが含まれる（要件2.1）
            assert "export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE" in result.stderr
            assert (
                "export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
                in result.stderr
            )
            assert "export AWS_SESSION_TOKEN=FwoGZXIvYXdzEBYaDH..." in result.stderr
            assert "export AWS_REGION=us-west-2" in result.stderr
            assert "export AWS_DEFAULT_REGION=us-west-2" in result.stderr
            assert "export AWS_PROFILE" not in result.stderr
            assert "export AWSOP_PROFILE=test-profile" in result.stderr
            assert "export AWSOP_EXPIRATION=" in result.stderr

            # 標準出力にはexportコマンドが含まれない
            assert "export AWS_ACCESS_KEY_ID" not in result.stdout


def test_profile_switching_no_role_arn():
    """role_arnが定義されていない場合のエラーテスト

    要件1.3: プロファイルにrole_arnが定義されていない場合、エラーメッセージを表示して終了する
    """
    # テスト用の設定ファイルを作成
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config"
        config_file.write_text(
            """[profile no-role-profile]
region = ap-northeast-1
"""
        )

        # CLIを実行
        result = runner.invoke(
            app,
            [
                "--config-file",
                str(config_file),
                "no-role-profile",
            ],
        )

        # 終了コードが1であることを確認
        assert result.exit_code == 1

        # 標準エラー出力にエラーメッセージが含まれることを確認
        assert "role_arn が定義されていません" in result.stderr


def test_profile_switching_profile_not_found():
    """プロファイルが見つからない場合のエラーテスト

    要件1.1: プロファイルが見つからない場合、エラーメッセージを表示して終了する
    """
    # テスト用の設定ファイルを作成
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config"
        config_file.write_text(
            """[profile test-profile]
role_arn = arn:aws:iam::123456789012:role/TestRole
"""
        )

        # CLIを実行
        result = runner.invoke(
            app,
            [
                "--config-file",
                str(config_file),
                "non-existent-profile",
            ],
        )

        # 終了コードが1であることを確認
        assert result.exit_code == 1

        # 標準エラー出力にエラーメッセージが含まれることを確認
        assert "が見つかりません" in result.stderr


def test_profile_switching_with_region_override():
    """--regionオプションでリージョンを上書きする場合のテスト

    要件4.2.1: --regionオプションでリージョンを指定すると、プロファイルのregionを上書きする
    """
    # テスト用の設定ファイルを作成
    with tempfile.TemporaryDirectory() as tmpdir:
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

        # OnePasswordClientをモック
        with patch(
            "awsop.app.credentials_manager.OnePasswordClient"
        ) as mock_op_client_class:
            mock_op_client = Mock()
            mock_op_client.check_availability.return_value = True
            mock_op_client.run_aws_command.return_value = mock_response
            mock_op_client_class.return_value = mock_op_client

            # CLIを実行（--regionオプションと--show-commandsオプション付き）
            result = runner.invoke(
                app,
                [
                    "--config-file",
                    str(config_file),
                    "--region",
                    "ap-northeast-1",
                    "--show-commands",
                    "test-profile",
                ],
                catch_exceptions=False,
            )

            # 終了コードが0であることを確認
            assert result.exit_code == 0

            # --show-commandsオプション付きの場合は標準エラー出力にap-northeast-1が含まれることを確認
            assert "export AWS_REGION=ap-northeast-1" in result.stderr
            assert "export AWS_DEFAULT_REGION=ap-northeast-1" in result.stderr


def test_profile_switching_without_show_commands():
    """--show-commandsオプションなしの場合のテスト

    デフォルトではexportコマンドを標準出力に出力し、有効期限メッセージを標準エラー出力に表示する
    """
    # テスト用の設定ファイルを作成
    with tempfile.TemporaryDirectory() as tmpdir:
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

        # OnePasswordClientをモック
        with patch(
            "awsop.app.credentials_manager.OnePasswordClient"
        ) as mock_op_client_class:
            mock_op_client = Mock()
            mock_op_client.check_availability.return_value = True
            mock_op_client.run_aws_command.return_value = mock_response
            mock_op_client_class.return_value = mock_op_client

            # CLIを実行（--show-commandsオプションなし）
            result = runner.invoke(
                app,
                [
                    "--config-file",
                    str(config_file),
                    "test-profile",
                ],
                catch_exceptions=False,
            )

            # 終了コードが0であることを確認
            assert result.exit_code == 0

            # 標準出力にexportコマンドが含まれることを確認（要件1.1）
            assert "export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE" in result.stdout
            assert (
                "export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
                in result.stdout
            )
            assert "export AWS_SESSION_TOKEN=FwoGZXIvYXdzEBYaDH..." in result.stdout
            assert "export AWS_REGION=us-west-2" in result.stdout

            # 標準エラー出力に有効期限メッセージが含まれることを確認（要件1.4）
            assert "Credentials will expire" in result.stderr
            assert "JST" in result.stderr


def test_profile_switching_with_default_region():
    """リージョンが指定されていない場合のデフォルトリージョンテスト

    要件4.2.3: プロファイルにregionが定義されていない場合、デフォルトリージョン（ap-northeast-1）を使用する
    """
    # テスト用の設定ファイルを作成
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config"
        config_file.write_text(
            """[profile test-profile]
role_arn = arn:aws:iam::123456789012:role/TestRole
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

        # OnePasswordClientをモック
        with patch(
            "awsop.app.credentials_manager.OnePasswordClient"
        ) as mock_op_client_class:
            mock_op_client = Mock()
            mock_op_client.check_availability.return_value = True
            mock_op_client.run_aws_command.return_value = mock_response
            mock_op_client_class.return_value = mock_op_client

            # CLIを実行（--show-commandsオプション付き）
            result = runner.invoke(
                app,
                [
                    "--config-file",
                    str(config_file),
                    "--show-commands",
                    "test-profile",
                ],
                catch_exceptions=False,
            )

            # 終了コードが0であることを確認
            assert result.exit_code == 0

            # --show-commandsオプション付きの場合は標準エラー出力にap-northeast-1が含まれることを確認
            assert "export AWS_REGION=ap-northeast-1" in result.stderr
            assert "export AWS_DEFAULT_REGION=ap-northeast-1" in result.stderr
