"""エンドツーエンドの統合テスト

タスク18: 統合テストの実装
要件: 全般
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime
from typer.testing import CliRunner

from awsop.cli import app


runner = CliRunner()


def test_complete_workflow_with_output_profile():
    """完全なワークフロー: プロファイル切り替え + 認証情報ファイル書き込み

    要件1.1, 1.2, 1.4, 4.6.1: プロファイル切り替えと認証情報ファイル書き込みの統合
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # テスト用の設定ファイルを作成
        config_file = Path(tmpdir) / "config"
        config_file.write_text(
            """[profile test-profile]
role_arn = arn:aws:iam::123456789012:role/TestRole
region = us-west-2
source_profile = default
"""
        )

        # テスト用の認証情報ファイルを作成
        credentials_file = Path(tmpdir) / "credentials"
        credentials_file.write_text("")

        # モックのレスポンスを作成
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

            # CLIを実行（--output-profileオプション付き）
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

            # 終了コードが0であることを確認
            assert result.exit_code == 0

            # 標準出力にexportコマンドが含まれることを確認
            assert "export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE" in result.stdout

            # 認証情報ファイルに書き込まれたことを確認
            credentials_content = credentials_file.read_text()
            assert "[output-test]" in credentials_content
            assert "aws_access_key_id = AKIAIOSFODNN7EXAMPLE" in credentials_content
            assert "manager = awsop" in credentials_content


def test_complete_workflow_with_all_options():
    """すべてのオプションを組み合わせた完全なワークフロー

    要件: 複数オプションの同時使用
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

        with patch(
            "awsop.app.credentials_manager.OnePasswordClient"
        ) as mock_op_client_class:
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
                    "custom-session",
                    "--role-duration",
                    "7200",
                    "--external-id",
                    "external-123",
                    "--show-commands",
                    "--info",
                    "test-profile",
                ],
                catch_exceptions=False,
            )

            # 終了コードが0であることを確認
            assert result.exit_code == 0

            # 標準出力にexportコマンドが含まれることを確認
            assert "export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE" in result.stdout
            # リージョンが上書きされていることを確認
            assert "export AWS_REGION=ap-northeast-1" in result.stdout
            assert "export AWS_DEFAULT_REGION=ap-northeast-1" in result.stdout


def test_workflow_with_role_arn_and_source_profile():
    """--role-arnと--source-profileを組み合わせたワークフロー

    要件4.7.2, 4.7.3: ロールARN指定とソースプロファイル指定の組み合わせ
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

        with patch(
            "awsop.app.credentials_manager.OnePasswordClient"
        ) as mock_op_client_class:
            mock_op_client = Mock()
            mock_op_client.check_availability.return_value = True
            mock_op_client.run_aws_command.return_value = mock_response
            mock_op_client_class.return_value = mock_op_client

            # CLIを実行（--role-arnと--source-profileオプション付き）
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

            # 終了コードが0であることを確認
            assert result.exit_code == 0

            # 標準出力にexportコマンドが含まれることを確認
            assert "export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE" in result.stdout


def test_workflow_unset_commands():
    """unsetコマンドのワークフロー

    要件4.1.1, 4.1.2: 認証情報のクリア
    """
    # CLIを実行（--unsetオプション付き）
    result = runner.invoke(
        app,
        ["--unset"],
        catch_exceptions=False,
    )

    # 終了コードが0であることを確認
    assert result.exit_code == 0

    # 標準出力にunsetコマンドが含まれることを確認
    assert "unset AWS_ACCESS_KEY_ID" in result.stdout
    assert "unset AWS_SECRET_ACCESS_KEY" in result.stdout
    assert "unset AWS_SESSION_TOKEN" in result.stdout
    assert "unset AWS_REGION" in result.stdout
    assert "unset AWS_DEFAULT_REGION" in result.stdout
    assert "unset AWS_PROFILE" in result.stdout
    assert "unset AWSOP_PROFILE" in result.stdout
    assert "unset AWSOP_EXPIRATION" in result.stdout


def test_workflow_list_profiles():
    """プロファイル一覧表示のワークフロー

    要件3.1, 3.2: プロファイル一覧表示
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # テスト用の設定ファイルを作成
        config_file = Path(tmpdir) / "config"
        config_file.write_text(
            """[profile profile1]
role_arn = arn:aws:iam::123456789012:role/Role1

[profile profile2]
role_arn = arn:aws:iam::123456789012:role/Role2

[profile profile3]
role_arn = arn:aws:iam::123456789012:role/Role3
"""
        )

        # CLIを実行（--list-profilesオプション付き）
        result = runner.invoke(
            app,
            [
                "--config-file",
                str(config_file),
                "--list-profiles",
            ],
            catch_exceptions=False,
        )

        # 終了コードが0であることを確認
        assert result.exit_code == 0

        # 標準出力にプロファイル名が含まれることを確認
        assert "profile1" in result.stdout
        assert "profile2" in result.stdout
        assert "profile3" in result.stdout


def test_workflow_init_shell():
    """シェル初期化のワークフロー

    要件5.1, 5.2, 5.3: シェル統合
    """
    # CLIを実行（--init-shellオプション付き）
    result = runner.invoke(
        app,
        ["--init-shell"],
        catch_exceptions=False,
    )

    # 終了コードが0であることを確認
    assert result.exit_code == 0

    # 標準出力にシェルラッパー関数が含まれることを確認
    assert "function awsop()" in result.stdout
    assert "eval" in result.stdout
    # 補完スクリプトが含まれることを確認
    assert "_awsop()" in result.stdout
    assert "compdef _awsop awsop" in result.stdout


def test_workflow_version():
    """バージョン表示のワークフロー

    要件12.1, 12.2: バージョン情報表示
    """
    # CLIを実行（--versionオプション付き）
    result = runner.invoke(
        app,
        ["--version"],
        catch_exceptions=False,
    )

    # 終了コードが0であることを確認
    assert result.exit_code == 0

    # 標準出力にバージョン情報が含まれることを確認
    assert "awsop" in result.stdout
    # バージョン番号の形式を確認（X.Y.Z）
    import re

    assert re.search(r"\d+\.\d+\.\d+", result.stdout)


def test_workflow_help():
    """ヘルプ表示のワークフロー

    要件13.1, 13.2: ヘルプ表示
    """
    # CLIを実行（--helpオプション付き）
    result = runner.invoke(
        app,
        ["--help"],
        catch_exceptions=False,
    )

    # 終了コードが0であることを確認
    assert result.exit_code == 0

    # 標準出力にヘルプメッセージが含まれることを確認
    assert "Usage:" in result.stdout or "使用方法:" in result.stdout
    # 主要なオプションが含まれることを確認
    assert "--region" in result.stdout
    assert "--session-name" in result.stdout
    assert "--role-arn" in result.stdout


def test_workflow_with_logging():
    """ログレベル指定のワークフロー

    要件9.1, 9.2, 9.3: ログレベル制御
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

        with patch(
            "awsop.app.credentials_manager.OnePasswordClient"
        ) as mock_op_client_class:
            mock_op_client = Mock()
            mock_op_client.check_availability.return_value = True
            mock_op_client.run_aws_command.return_value = mock_response
            mock_op_client_class.return_value = mock_op_client

            # CLIを実行（--debugオプション付き）
            result = runner.invoke(
                app,
                [
                    "--config-file",
                    str(config_file),
                    "--debug",
                    "--show-commands",
                    "test-profile",
                ],
                catch_exceptions=False,
            )

            # 終了コードが0であることを確認
            assert result.exit_code == 0

            # 標準エラー出力にDEBUGログが含まれることを確認
            assert "DEBUG" in result.stderr or "デバッグ" in result.stderr.lower()


def test_workflow_sequential_profile_switching():
    """連続したプロファイル切り替えのワークフロー

    要件2.1: 認証情報の上書き
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # テスト用の設定ファイルを作成
        config_file = Path(tmpdir) / "config"
        config_file.write_text(
            """[profile profile1]
role_arn = arn:aws:iam::123456789012:role/Role1
region = us-west-2

[profile profile2]
role_arn = arn:aws:iam::123456789012:role/Role2
region = ap-northeast-1
"""
        )

        # モックのレスポンスを作成
        mock_response1 = {
            "Credentials": {
                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE1",
                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY1",
                "SessionToken": "FwoGZXIvYXdzEBYaDH1...",
                "Expiration": datetime(2024, 12, 31, 23, 59, 59),
            }
        }

        mock_response2 = {
            "Credentials": {
                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE2",
                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY2",
                "SessionToken": "FwoGZXIvYXdzEBYaDH2...",
                "Expiration": datetime(2024, 12, 31, 23, 59, 59),
            }
        }

        with patch(
            "awsop.app.credentials_manager.OnePasswordClient"
        ) as mock_op_client_class:
            mock_op_client = Mock()
            mock_op_client.check_availability.return_value = True
            mock_op_client_class.return_value = mock_op_client

            # 最初のプロファイルに切り替え
            mock_op_client.run_aws_command.return_value = mock_response1
            result1 = runner.invoke(
                app,
                [
                    "--config-file",
                    str(config_file),
                    "--show-commands",
                    "profile1",
                ],
                catch_exceptions=False,
            )

            assert result1.exit_code == 0
            assert "AKIAIOSFODNN7EXAMPLE1" in result1.stdout
            assert "us-west-2" in result1.stdout

            # 2番目のプロファイルに切り替え
            mock_op_client.run_aws_command.return_value = mock_response2
            result2 = runner.invoke(
                app,
                [
                    "--config-file",
                    str(config_file),
                    "--show-commands",
                    "profile2",
                ],
                catch_exceptions=False,
            )

            assert result2.exit_code == 0
            # 新しい認証情報が出力されることを確認
            assert "AKIAIOSFODNN7EXAMPLE2" in result2.stdout
            # 新しいリージョンが出力されることを確認
            assert "ap-northeast-1" in result2.stdout
            # 古い認証情報は含まれない
            assert "AKIAIOSFODNN7EXAMPLE1" not in result2.stdout
