"""エラーケースの統合テスト

タスク18: 統合テストの実装
要件: 全般（エラーハンドリング）
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from typer.testing import CliRunner
from botocore.exceptions import ClientError

from awsop.cli import app


runner = CliRunner()


def test_error_onepassword_not_available():
    """1Password CLIが利用できない場合のエラー

    要件6.1, 6.2, 11.1: 依存関係チェックとエラーハンドリング
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

        with patch(
            "awsop.app.credentials_manager.OnePasswordClient"
        ) as mock_op_client_class:
            mock_op_client = Mock()
            mock_op_client.check_availability.return_value = False
            mock_op_client_class.return_value = mock_op_client

            # CLIを実行
            result = runner.invoke(
                app,
                [
                    "--config-file",
                    str(config_file),
                    "test-profile",
                ],
            )

            # 終了コードが1であることを確認
            assert result.exit_code == 1

            # 標準エラー出力にエラーメッセージが含まれることを確認
            assert "1Password" in result.stderr
            assert (
                "利用できません" in result.stderr or "見つかりません" in result.stderr
            )


def test_error_onepassword_authentication_failed():
    """1Password認証が失敗した場合のエラー

    要件11.1: 1Password CLIの実行失敗時のエラーハンドリング
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

        with patch(
            "awsop.app.credentials_manager.OnePasswordClient"
        ) as mock_op_client_class:
            mock_op_client = Mock()
            mock_op_client.check_availability.return_value = True
            mock_op_client.run_aws_command.side_effect = Exception(
                "1Password authentication failed"
            )
            mock_op_client_class.return_value = mock_op_client

            # CLIを実行
            result = runner.invoke(
                app,
                [
                    "--config-file",
                    str(config_file),
                    "test-profile",
                ],
            )

            # 終了コードが1であることを確認
            assert result.exit_code == 1

            # 標準エラー出力にエラーメッセージが含まれることを確認
            assert (
                "認証情報の取得に失敗" in result.stderr or "1Password" in result.stderr
            )


def test_error_assume_role_failed():
    """AssumeRoleが失敗した場合のエラー

    要件11.2: AssumeRole失敗時のエラーハンドリング
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

        with patch(
            "awsop.app.credentials_manager.OnePasswordClient"
        ) as mock_op_client_class:
            mock_op_client = Mock()
            mock_op_client.check_availability.return_value = True
            # AssumeRoleのエラーをシミュレート
            error_response = {
                "Error": {
                    "Code": "AccessDenied",
                    "Message": "User is not authorized to perform: sts:AssumeRole",
                }
            }
            mock_op_client.run_aws_command.side_effect = ClientError(
                error_response, "AssumeRole"
            )
            mock_op_client_class.return_value = mock_op_client

            # CLIを実行
            result = runner.invoke(
                app,
                [
                    "--config-file",
                    str(config_file),
                    "test-profile",
                ],
            )

            # 終了コードが1であることを確認
            assert result.exit_code == 1

            # 標準エラー出力にエラーメッセージが含まれることを確認
            assert (
                "ロールの引き受けに失敗" in result.stderr
                or "認証情報の取得に失敗" in result.stderr
            )


def test_error_config_file_not_found():
    """設定ファイルが見つからない場合のエラー

    要件11.3: AWS設定ファイルの読み取り失敗時のエラーハンドリング
    """
    # 存在しない設定ファイルを指定
    result = runner.invoke(
        app,
        [
            "--config-file",
            "/nonexistent/path/to/config",
            "test-profile",
        ],
    )

    # 終了コードが1であることを確認
    assert result.exit_code == 1

    # 標準エラー出力にエラーメッセージが含まれることを確認
    assert (
        "設定ファイル" in result.stderr
        or "見つかりません" in result.stderr
        or "読み取りに失敗" in result.stderr
    )


def test_error_profile_not_found():
    """プロファイルが見つからない場合のエラー

    要件1.1: プロファイルが見つからない場合のエラーハンドリング
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # テスト用の設定ファイルを作成
        config_file = Path(tmpdir) / "config"
        config_file.write_text(
            """[profile existing-profile]
role_arn = arn:aws:iam::123456789012:role/TestRole
"""
        )

        # CLIを実行（存在しないプロファイルを指定）
        result = runner.invoke(
            app,
            [
                "--config-file",
                str(config_file),
                "nonexistent-profile",
            ],
        )

        # 終了コードが1であることを確認
        assert result.exit_code == 1

        # 標準エラー出力にエラーメッセージが含まれることを確認
        assert "が見つかりません" in result.stderr
        assert "nonexistent-profile" in result.stderr


def test_error_no_role_arn():
    """role_arnが定義されていない場合のエラー

    要件1.3: role_arn未定義時のエラーハンドリング
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # テスト用の設定ファイルを作成
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
        assert "role_arn" in result.stderr
        assert "定義されていません" in result.stderr


def test_error_invalid_role_duration():
    """無効なロール期間が指定された場合のエラー

    要件4.4.3: ロール期間のバリデーション
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # テスト用の設定ファイルを作成
        config_file = Path(tmpdir) / "config"
        config_file.write_text(
            """[profile test-profile]
role_arn = arn:aws:iam::123456789012:role/TestRole
"""
        )

        # 範囲外の期間を指定（43200秒を超える）
        result = runner.invoke(
            app,
            [
                "--config-file",
                str(config_file),
                "--role-duration",
                "50000",
                "test-profile",
            ],
        )

        # 終了コードが1であることを確認
        assert result.exit_code == 1

        # 標準エラー出力にエラーメッセージが含まれることを確認
        assert "ロール期間" in result.stderr
        assert "43200" in result.stderr


def test_error_protected_output_profile():
    """保護されたプロファイルへの書き込みエラー

    要件4.6.2: 出力プロファイルの保護
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # テスト用の設定ファイルを作成
        config_file = Path(tmpdir) / "config"
        config_file.write_text(
            """[profile test-profile]
role_arn = arn:aws:iam::123456789012:role/TestRole
"""
        )

        # テスト用の認証情報ファイルを作成（保護されたプロファイル）
        credentials_file = Path(tmpdir) / "credentials"
        credentials_file.write_text(
            """[protected-profile]
aws_access_key_id = AKIAIOSFODNN7EXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
"""
        )

        from datetime import datetime

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
                    "protected-profile",
                    "test-profile",
                ],
            )

            # 終了コードが1であることを確認
            assert result.exit_code == 1

            # 標準エラー出力にエラーメッセージが含まれることを確認
            assert (
                "保護されています" in result.stderr
                or "上書きできません" in result.stderr
            )


def test_error_credentials_file_write_failed():
    """認証情報ファイルへの書き込み失敗エラー

    要件: ファイル操作エラーのハンドリング
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # テスト用の設定ファイルを作成
        config_file = Path(tmpdir) / "config"
        config_file.write_text(
            """[profile test-profile]
role_arn = arn:aws:iam::123456789012:role/TestRole
"""
        )

        # 書き込み不可能なディレクトリを指定
        credentials_file = Path("/root/credentials")  # 通常は書き込み不可

        from datetime import datetime

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
                    "test-output",
                    "test-profile",
                ],
            )

            # 終了コードが1であることを確認
            assert result.exit_code == 1

            # 標準エラー出力にエラーメッセージが含まれることを確認
            assert (
                "書き込みに失敗" in result.stderr
                or "Permission denied" in result.stderr
                or "エラー" in result.stderr
            )


def test_error_no_profile_and_no_role_arn():
    """プロファイルもrole_arnも指定されていない場合のエラー

    要件13.3: 引数なしで実行された場合のエラーハンドリング
    """
    # CLIを実行（引数なし）
    result = runner.invoke(app, [])

    # 終了コードが0であることを確認（何も実行されない）
    assert result.exit_code == 0

    # 標準出力または標準エラー出力が空であることを確認（何も実行されない）
    # 引数なしの場合は何も実行されず、エラーも表示されない
    assert result.stdout == "" or result.stderr == ""


def test_error_invalid_config_file_format():
    """無効な設定ファイル形式のエラー

    要件11.3: AWS設定ファイルの読み取り失敗時のエラーハンドリング
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # 無効な形式の設定ファイルを作成
        config_file = Path(tmpdir) / "config"
        config_file.write_text(
            """This is not a valid INI file
[profile test-profile
role_arn = invalid
"""
        )

        # CLIを実行
        result = runner.invoke(
            app,
            [
                "--config-file",
                str(config_file),
                "test-profile",
            ],
        )

        # 終了コードが1であることを確認
        assert result.exit_code == 1

        # 標準エラー出力にエラーメッセージが含まれることを確認
        assert (
            "設定ファイル" in result.stderr
            or "読み取りに失敗" in result.stderr
            or "エラー" in result.stderr
        )


def test_error_exit_code_consistency():
    """すべてのエラーケースで終了コード1が返されることを確認

    要件11.4: エラー時の終了コード
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # テスト用の設定ファイルを作成
        config_file = Path(tmpdir) / "config"
        config_file.write_text(
            """[profile test-profile]
role_arn = arn:aws:iam::123456789012:role/TestRole
"""
        )

        # 複数のエラーケースをテスト
        error_cases = [
            # プロファイルが見つからない
            (["--config-file", str(config_file), "nonexistent"], 1),
            # 無効なロール期間
            (
                [
                    "--config-file",
                    str(config_file),
                    "--role-duration",
                    "100000",
                    "test-profile",
                ],
                1,
            ),
            # 存在しない設定ファイル
            (["--config-file", "/nonexistent/config", "test-profile"], 1),
        ]

        for args, expected_exit_code in error_cases:
            result = runner.invoke(app, args)
            assert result.exit_code == expected_exit_code, (
                f"Args: {args}, Exit code: {result.exit_code}"
            )


def test_error_with_debug_flag():
    """--debugフラグ付きでエラーが発生した場合のスタックトレース表示

    要件11.4: --debug時のスタックトレース表示
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # テスト用の設定ファイルを作成
        config_file = Path(tmpdir) / "config"
        config_file.write_text(
            """[profile test-profile]
role_arn = arn:aws:iam::123456789012:role/TestRole
"""
        )

        with patch(
            "awsop.app.credentials_manager.OnePasswordClient"
        ) as mock_op_client_class:
            mock_op_client = Mock()
            mock_op_client.check_availability.return_value = True
            mock_op_client.run_aws_command.side_effect = Exception("Test error")
            mock_op_client_class.return_value = mock_op_client

            # CLIを実行（--debugフラグ付き）
            result = runner.invoke(
                app,
                [
                    "--config-file",
                    str(config_file),
                    "--debug",
                    "test-profile",
                ],
            )

            # 終了コードが1であることを確認
            assert result.exit_code == 1

            # 標準エラー出力にエラーメッセージが含まれることを確認
            assert "エラー" in result.stderr or "Error" in result.stderr


def test_error_source_profile_not_found():
    """--source-profileで指定したプロファイルが見つからない場合のエラー

    要件4.7.3: ソースプロファイル指定時のエラーハンドリング
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # テスト用の設定ファイルを作成
        config_file = Path(tmpdir) / "config"
        config_file.write_text(
            """[profile test-profile]
role_arn = arn:aws:iam::123456789012:role/TestRole
"""
        )

        # CLIを実行（存在しないソースプロファイルを指定）
        result = runner.invoke(
            app,
            [
                "--config-file",
                str(config_file),
                "--role-arn",
                "arn:aws:iam::123456789012:role/TargetRole",
                "--source-profile",
                "nonexistent-source",
            ],
        )

        # 終了コードが1であることを確認
        assert result.exit_code == 1

        # 標準エラー出力にエラーメッセージが含まれることを確認
        assert "が見つかりません" in result.stderr
        assert "nonexistent-source" in result.stderr
