"""CLIレイヤーのコンソール起動処理のユニットテスト"""

from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
import json

from awsop.app.credentials_manager import Credentials
from awsop.app.profile_manager import ProfileConfig


class TestConsoleCLIIntegration:
    """CLIレイヤーのコンソール起動処理のユニットテスト"""

    def test_console_link_option_outputs_url_only(self):
        """
        --console-linkオプションでURLのみが標準出力に出力されることを確認

        要件: 3.1, 3.3, 3.4
        """
        # urllib.request.urlopenをモック
        with patch("urllib.request.urlopen") as mock_urlopen:
            # モックレスポンスを設定
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps(
                {"SigninToken": "test-signin-token"}
            ).encode("utf-8")
            mock_response.__enter__.return_value = mock_response
            mock_urlopen.return_value = mock_response

            # ConsoleManagerのopen_consoleをモック
            with patch(
                "awsop.app.console_manager.ConsoleManager.open_console"
            ) as mock_open_console:
                test_url = "https://signin.aws.amazon.com/federation?Action=login&SigninToken=test-token&Destination=https://console.aws.amazon.com/console/home?region=ap-northeast-1"
                mock_open_console.return_value = test_url

                # 1Password CLIのチェックをスキップ
                with patch(
                    "awsop.services.onepassword.OnePasswordClient.check_availability"
                ) as mock_check:
                    mock_check.return_value = True

                    # AssumeRoleをモック
                    with patch(
                        "awsop.app.credentials_manager.CredentialsManager.assume_role"
                    ) as mock_assume_role:
                        mock_assume_role.return_value = Credentials(
                            access_key_id="AKIAIOSFODNN7EXAMPLE",
                            secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                            session_token="FwoGZXIvYXdzEBYaDH...",
                            region="ap-northeast-1",
                            expiration=datetime.now(timezone.utc),
                            profile="test-profile",
                        )

                        # ProfileManagerをモック
                        with patch(
                            "awsop.app.profile_manager.ProfileManager.get_profile"
                        ) as mock_get_profile:
                            mock_get_profile.return_value = ProfileConfig(
                                name="test-profile",
                                role_arn="arn:aws:iam::123456789012:role/TestRole",
                                region="ap-northeast-1",
                                external_id=None,
                            )

                            # 標準出力をキャプチャ
                            from io import StringIO
                            import sys

                            captured_stdout = StringIO()
                            captured_stderr = StringIO()

                            with patch("sys.stdout", captured_stdout):
                                with patch("sys.stderr", captured_stderr):
                                    # CLIを実行
                                    from awsop.cli import main
                                    from typer.testing import CliRunner
                                    from awsop.cli import app

                                    runner = CliRunner()
                                    result = runner.invoke(
                                        app,
                                        ["test-profile", "--console-link"],
                                    )

                                    # 成功することを確認
                                    assert result.exit_code == 0

                                    # open_consoleが呼ばれたことを確認
                                    assert mock_open_console.called

                                    # open_browserがFalseで呼ばれたことを確認
                                    call_kwargs = mock_open_console.call_args[1]
                                    assert call_kwargs["open_browser"] is False

                                    # 標準出力にURLが出力されることを確認
                                    assert test_url in result.stdout

    def test_console_option_opens_browser(self):
        """
        --consoleオプションでブラウザが開かれることを確認

        要件: 1.1, 1.5, 8.2
        """
        # urllib.request.urlopenをモック
        with patch("urllib.request.urlopen") as mock_urlopen:
            # モックレスポンスを設定
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps(
                {"SigninToken": "test-signin-token"}
            ).encode("utf-8")
            mock_response.__enter__.return_value = mock_response
            mock_urlopen.return_value = mock_response

            # webbrowser.openをモック
            with patch("webbrowser.open") as mock_browser:
                mock_browser.return_value = True

                # 1Password CLIのチェックをスキップ
                with patch(
                    "awsop.services.onepassword.OnePasswordClient.check_availability"
                ) as mock_check:
                    mock_check.return_value = True

                    # AssumeRoleをモック
                    with patch(
                        "awsop.app.credentials_manager.CredentialsManager.assume_role"
                    ) as mock_assume_role:
                        mock_assume_role.return_value = Credentials(
                            access_key_id="AKIAIOSFODNN7EXAMPLE",
                            secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                            session_token="FwoGZXIvYXdzEBYaDH...",
                            region="ap-northeast-1",
                            expiration=datetime.now(timezone.utc),
                            profile="test-profile",
                        )

                        # ProfileManagerをモック
                        with patch(
                            "awsop.app.profile_manager.ProfileManager.get_profile"
                        ) as mock_get_profile:
                            mock_get_profile.return_value = ProfileConfig(
                                name="test-profile",
                                role_arn="arn:aws:iam::123456789012:role/TestRole",
                                region="ap-northeast-1",
                                external_id=None,
                            )

                            # CLIを実行
                            from typer.testing import CliRunner
                            from awsop.cli import app

                            runner = CliRunner()
                            result = runner.invoke(
                                app,
                                ["test-profile", "--console"],
                            )

                            # 成功することを確認
                            assert result.exit_code == 0

                            # ブラウザが開かれたことを確認
                            assert mock_browser.called

    def test_console_option_with_service(self):
        """
        --consoleオプションでサービス指定時に正しく動作することを確認

        要件: 2.1
        """
        # urllib.request.urlopenをモック
        with patch("urllib.request.urlopen") as mock_urlopen:
            # モックレスポンスを設定
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps(
                {"SigninToken": "test-signin-token"}
            ).encode("utf-8")
            mock_response.__enter__.return_value = mock_response
            mock_urlopen.return_value = mock_response

            # webbrowser.openをモック
            with patch("webbrowser.open") as mock_browser:
                mock_browser.return_value = True

                # 1Password CLIのチェックをスキップ
                with patch(
                    "awsop.services.onepassword.OnePasswordClient.check_availability"
                ) as mock_check:
                    mock_check.return_value = True

                    # AssumeRoleをモック
                    with patch(
                        "awsop.app.credentials_manager.CredentialsManager.assume_role"
                    ) as mock_assume_role:
                        mock_assume_role.return_value = Credentials(
                            access_key_id="AKIAIOSFODNN7EXAMPLE",
                            secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                            session_token="FwoGZXIvYXdzEBYaDH...",
                            region="ap-northeast-1",
                            expiration=datetime.now(timezone.utc),
                            profile="test-profile",
                        )

                        # ProfileManagerをモック
                        with patch(
                            "awsop.app.profile_manager.ProfileManager.get_profile"
                        ) as mock_get_profile:
                            mock_get_profile.return_value = ProfileConfig(
                                name="test-profile",
                                role_arn="arn:aws:iam::123456789012:role/TestRole",
                                region="ap-northeast-1",
                                external_id=None,
                            )

                            # CLIを実行
                            from typer.testing import CliRunner
                            from awsop.cli import app

                            runner = CliRunner()
                            result = runner.invoke(
                                app,
                                [
                                    "test-profile",
                                    "--console",
                                    "--console-service",
                                    "s3",
                                ],
                            )

                            # 成功することを確認
                            assert result.exit_code == 0

                            # ブラウザが開かれたことを確認
                            assert mock_browser.called

                            # 呼び出されたURLにs3が含まれることを確認
                            called_url = mock_browser.call_args[0][0]
                            assert "s3" in called_url.lower()

    def test_console_and_console_link_are_mutually_exclusive(self):
        """
        --consoleと--console-linkが同時に使用された場合にエラーになることを確認

        要件: 1.1, 3.1
        """
        from typer.testing import CliRunner
        from awsop.cli import app

        runner = CliRunner()
        result = runner.invoke(
            app,
            ["test-profile", "--console", "--console-link"],
        )

        # エラーで終了することを確認
        assert result.exit_code == 1
        assert "エラー" in result.stderr

    def test_console_with_role_arn_option(self):
        """
        --role-arnオプションと--consoleの組み合わせをテスト

        要件: 7.2
        """
        # urllib.request.urlopenをモック
        with patch("urllib.request.urlopen") as mock_urlopen:
            # モックレスポンスを設定
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps(
                {"SigninToken": "test-signin-token"}
            ).encode("utf-8")
            mock_response.__enter__.return_value = mock_response
            mock_urlopen.return_value = mock_response

            # webbrowser.openをモック
            with patch("webbrowser.open") as mock_browser:
                mock_browser.return_value = True

                # 1Password CLIのチェックをスキップ
                with patch(
                    "awsop.services.onepassword.OnePasswordClient.check_availability"
                ) as mock_check:
                    mock_check.return_value = True

                    # AssumeRoleをモック
                    with patch(
                        "awsop.app.credentials_manager.CredentialsManager.assume_role"
                    ) as mock_assume_role:
                        mock_assume_role.return_value = Credentials(
                            access_key_id="AKIAIOSFODNN7EXAMPLE",
                            secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                            session_token="FwoGZXIvYXdzEBYaDH...",
                            region="us-west-2",
                            expiration=datetime.now(timezone.utc),
                            profile="direct-role",
                        )

                        # CLIを実行
                        from typer.testing import CliRunner
                        from awsop.cli import app

                        runner = CliRunner()
                        result = runner.invoke(
                            app,
                            [
                                "--role-arn",
                                "arn:aws:iam::123456789012:role/TestRole",
                                "--console",
                            ],
                        )

                        # 成功することを確認
                        assert result.exit_code == 0

                        # ブラウザが開かれたことを確認
                        assert mock_browser.called

                        # AssumeRoleが正しいロールARNで呼ばれたことを確認
                        call_kwargs = mock_assume_role.call_args[1]
                        assert (
                            call_kwargs["role_arn"]
                            == "arn:aws:iam::123456789012:role/TestRole"
                        )

    def test_console_with_source_profile_option(self):
        """
        --source-profileオプションと--consoleの組み合わせをテスト

        要件: 7.3
        """
        # urllib.request.urlopenをモック
        with patch("urllib.request.urlopen") as mock_urlopen:
            # モックレスポンスを設定
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps(
                {"SigninToken": "test-signin-token"}
            ).encode("utf-8")
            mock_response.__enter__.return_value = mock_response
            mock_urlopen.return_value = mock_response

            # webbrowser.openをモック
            with patch("webbrowser.open") as mock_browser:
                mock_browser.return_value = True

                # 1Password CLIのチェックをスキップ
                with patch(
                    "awsop.services.onepassword.OnePasswordClient.check_availability"
                ) as mock_check:
                    mock_check.return_value = True

                    # AssumeRoleをモック
                    with patch(
                        "awsop.app.credentials_manager.CredentialsManager.assume_role"
                    ) as mock_assume_role:
                        mock_assume_role.return_value = Credentials(
                            access_key_id="AKIAIOSFODNN7EXAMPLE",
                            secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                            session_token="FwoGZXIvYXdzEBYaDH...",
                            region="eu-west-1",
                            expiration=datetime.now(timezone.utc),
                            profile="direct-role",
                        )

                        # ProfileManagerをモック
                        with patch(
                            "awsop.app.profile_manager.ProfileManager.get_profile"
                        ) as mock_get_profile:
                            mock_get_profile.return_value = ProfileConfig(
                                name="source-profile",
                                role_arn=None,
                                region="eu-west-1",
                                external_id=None,
                            )

                            # CLIを実行
                            from typer.testing import CliRunner
                            from awsop.cli import app

                            runner = CliRunner()
                            result = runner.invoke(
                                app,
                                [
                                    "--role-arn",
                                    "arn:aws:iam::123456789012:role/TestRole",
                                    "--source-profile",
                                    "source-profile",
                                    "--console",
                                ],
                            )

                            # 成功することを確認
                            assert result.exit_code == 0

                            # ブラウザが開かれたことを確認
                            assert mock_browser.called

                            # ProfileManagerが呼ばれたことを確認
                            assert mock_get_profile.called
                            assert mock_get_profile.call_args[0][0] == "source-profile"

    def test_console_with_debug_option(self):
        """
        --debugオプションと--consoleの組み合わせをテスト

        要件: 7.4
        """
        # urllib.request.urlopenをモック
        with patch("urllib.request.urlopen") as mock_urlopen:
            # モックレスポンスを設定
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps(
                {"SigninToken": "test-signin-token"}
            ).encode("utf-8")
            mock_response.__enter__.return_value = mock_response
            mock_urlopen.return_value = mock_response

            # webbrowser.openをモック
            with patch("webbrowser.open") as mock_browser:
                mock_browser.return_value = True

                # 1Password CLIのチェックをスキップ
                with patch(
                    "awsop.services.onepassword.OnePasswordClient.check_availability"
                ) as mock_check:
                    mock_check.return_value = True

                    # AssumeRoleをモック
                    with patch(
                        "awsop.app.credentials_manager.CredentialsManager.assume_role"
                    ) as mock_assume_role:
                        mock_assume_role.return_value = Credentials(
                            access_key_id="AKIAIOSFODNN7EXAMPLE",
                            secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                            session_token="FwoGZXIvYXdzEBYaDH...",
                            region="ap-northeast-1",
                            expiration=datetime.now(timezone.utc),
                            profile="test-profile",
                        )

                        # ProfileManagerをモック
                        with patch(
                            "awsop.app.profile_manager.ProfileManager.get_profile"
                        ) as mock_get_profile:
                            mock_get_profile.return_value = ProfileConfig(
                                name="test-profile",
                                role_arn="arn:aws:iam::123456789012:role/TestRole",
                                region="ap-northeast-1",
                                external_id=None,
                            )

                            # CLIを実行
                            from typer.testing import CliRunner
                            from awsop.cli import app

                            runner = CliRunner()
                            result = runner.invoke(
                                app,
                                ["test-profile", "--console", "--debug"],
                            )

                            # 成功することを確認
                            assert result.exit_code == 0

                            # ブラウザが開かれたことを確認
                            assert mock_browser.called

                            # デバッグモードでは詳細なログが出力されることを確認
                            # （実際のログ出力は標準エラー出力に含まれる）
                            # ここでは正常に実行されたことを確認

    def test_console_with_multiple_options(self):
        """
        複数のオプションの組み合わせをテスト

        要件: 7.5
        """
        # urllib.request.urlopenをモック
        with patch("urllib.request.urlopen") as mock_urlopen:
            # モックレスポンスを設定
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps(
                {"SigninToken": "test-signin-token"}
            ).encode("utf-8")
            mock_response.__enter__.return_value = mock_response
            mock_urlopen.return_value = mock_response

            # webbrowser.openをモック
            with patch("webbrowser.open") as mock_browser:
                mock_browser.return_value = True

                # 1Password CLIのチェックをスキップ
                with patch(
                    "awsop.services.onepassword.OnePasswordClient.check_availability"
                ) as mock_check:
                    mock_check.return_value = True

                    # AssumeRoleをモック
                    with patch(
                        "awsop.app.credentials_manager.CredentialsManager.assume_role"
                    ) as mock_assume_role:
                        mock_assume_role.return_value = Credentials(
                            access_key_id="AKIAIOSFODNN7EXAMPLE",
                            secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                            session_token="FwoGZXIvYXdzEBYaDH...",
                            region="us-east-1",
                            expiration=datetime.now(timezone.utc),
                            profile="direct-role",
                        )

                        # ProfileManagerをモック
                        with patch(
                            "awsop.app.profile_manager.ProfileManager.get_profile"
                        ) as mock_get_profile:
                            mock_get_profile.return_value = ProfileConfig(
                                name="source-profile",
                                role_arn=None,
                                region="ap-northeast-1",
                                external_id=None,
                            )

                            # CLIを実行
                            from typer.testing import CliRunner
                            from awsop.cli import app

                            runner = CliRunner()
                            result = runner.invoke(
                                app,
                                [
                                    "--role-arn",
                                    "arn:aws:iam::123456789012:role/TestRole",
                                    "--source-profile",
                                    "source-profile",
                                    "--region",
                                    "us-east-1",
                                    "--console",
                                    "--console-service",
                                    "lambda",
                                    "--debug",
                                ],
                            )

                            # 成功することを確認
                            assert result.exit_code == 0

                            # ブラウザが開かれたことを確認
                            assert mock_browser.called

                            # 呼び出されたURLにlambdaとus-east-1が含まれることを確認
                            called_url = mock_browser.call_args[0][0]
                            assert "lambda" in called_url.lower()
                            # URLデコードして確認
                            import urllib.parse

                            parsed_url = urllib.parse.urlparse(called_url)
                            params = urllib.parse.parse_qs(parsed_url.query)
                            destination_url = params["Destination"][0]
                            assert "region=us-east-1" in destination_url
