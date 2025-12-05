"""コンソール機能のエラーハンドリングのユニットテスト

要件: 5.1, 5.2, 5.3, 5.4, 5.5
"""

from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
import urllib.error
import json
import pytest

from awsop.app.console_manager import ConsoleManager
from awsop.app.credentials_manager import Credentials
from awsop.services.console_service import ConsoleService


class TestConsoleServiceErrorHandling:
    """ConsoleServiceのエラーハンドリングテスト"""

    def test_signin_token_network_error(self):
        """
        ネットワークエラー時のハンドリングテスト

        要件: 5.4
        """
        service = ConsoleService()

        # urllib.request.urlopenをモックしてネットワークエラーを発生させる
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError("Network is unreachable")

            # RuntimeErrorが発生することを確認
            with pytest.raises(RuntimeError) as exc_info:
                service.get_signin_token(
                    access_key_id="AKIAIOSFODNN7EXAMPLE",
                    secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                    session_token="test-session-token",
                    amazon_domain="aws.amazon.com",
                )

            # エラーメッセージを確認
            error_message = str(exc_info.value)
            assert "AWS Federation Endpointへの接続に失敗しました" in error_message
            assert "Network is unreachable" in error_message

    def test_signin_token_timeout_error(self):
        """
        タイムアウトエラー時のハンドリングテスト

        要件: 5.4
        """
        service = ConsoleService()

        # urllib.request.urlopenをモックしてタイムアウトエラーを発生させる
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError("timed out")

            # RuntimeErrorが発生することを確認
            with pytest.raises(RuntimeError) as exc_info:
                service.get_signin_token(
                    access_key_id="AKIAIOSFODNN7EXAMPLE",
                    secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                    session_token="test-session-token",
                    amazon_domain="aws.amazon.com",
                )

            # エラーメッセージを確認
            error_message = str(exc_info.value)
            assert "AWS Federation Endpointへの接続に失敗しました" in error_message

    def test_signin_token_invalid_json_response(self):
        """
        無効なJSONレスポンス時のハンドリングテスト

        要件: 5.2
        """
        service = ConsoleService()

        # urllib.request.urlopenをモックして無効なJSONを返す
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = MagicMock()
            mock_response.read.return_value = b"Invalid JSON"
            mock_response.__enter__.return_value = mock_response
            mock_urlopen.return_value = mock_response

            # RuntimeErrorが発生することを確認
            with pytest.raises(RuntimeError) as exc_info:
                service.get_signin_token(
                    access_key_id="AKIAIOSFODNN7EXAMPLE",
                    secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                    session_token="test-session-token",
                    amazon_domain="aws.amazon.com",
                )

            # エラーメッセージを確認
            error_message = str(exc_info.value)
            assert "レスポンスの解析に失敗しました" in error_message

    def test_signin_token_missing_in_response(self):
        """
        レスポンスにサインイントークンが含まれない場合のハンドリングテスト

        要件: 5.2
        """
        service = ConsoleService()

        # urllib.request.urlopenをモックしてトークンなしのレスポンスを返す
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps({}).encode("utf-8")
            mock_response.__enter__.return_value = mock_response
            mock_urlopen.return_value = mock_response

            # RuntimeErrorが発生することを確認
            with pytest.raises(RuntimeError) as exc_info:
                service.get_signin_token(
                    access_key_id="AKIAIOSFODNN7EXAMPLE",
                    secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                    session_token="test-session-token",
                    amazon_domain="aws.amazon.com",
                )

            # エラーメッセージを確認
            error_message = str(exc_info.value)
            assert "サインイントークンがレスポンスに含まれていません" in error_message

    def test_signin_token_http_error(self):
        """
        HTTPエラー時のハンドリングテスト

        要件: 5.2, 5.4
        """
        service = ConsoleService()

        # urllib.request.urlopenをモックしてHTTPエラーを発生させる
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.HTTPError(
                url="https://signin.aws.amazon.com/federation",
                code=403,
                msg="Forbidden",
                hdrs={},
                fp=None,
            )

            # RuntimeErrorが発生することを確認
            with pytest.raises(RuntimeError) as exc_info:
                service.get_signin_token(
                    access_key_id="AKIAIOSFODNN7EXAMPLE",
                    secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                    session_token="test-session-token",
                    amazon_domain="aws.amazon.com",
                )

            # エラーメッセージを確認
            error_message = str(exc_info.value)
            assert "AWS Federation Endpointへの接続に失敗しました" in error_message


class TestConsoleManagerErrorHandling:
    """ConsoleManagerのエラーハンドリングテスト"""

    def create_test_credentials(self, region: str = "us-east-1") -> Credentials:
        """テスト用の認証情報を作成"""
        return Credentials(
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            session_token="test-session-token",
            expiration=datetime(2024, 12, 31, 23, 59, 59),
            region=region,
            profile="test-profile",
        )

    def test_browser_launch_failure(self):
        """
        ブラウザ起動失敗時のハンドリングテスト

        要件: 5.3
        """
        # モックのConsoleServiceを作成
        mock_console_service = MagicMock()
        mock_console_service.get_amazon_domain.return_value = "aws.amazon.com"
        mock_console_service.get_signin_token.return_value = "test-signin-token"
        mock_console_service.build_destination_url.return_value = (
            "https://console.aws.amazon.com/console/home?region=us-east-1"
        )
        mock_console_service.generate_console_url.return_value = "https://signin.aws.amazon.com/federation?Action=login&SigninToken=test-signin-token"

        manager = ConsoleManager(console_service=mock_console_service)
        credentials = self.create_test_credentials()

        with patch("webbrowser.open") as mock_browser:
            # ブラウザ起動時にエラーを発生させる
            mock_browser.side_effect = Exception("ブラウザが見つかりません")

            # RuntimeErrorが発生することを確認
            with pytest.raises(RuntimeError) as exc_info:
                manager.open_console(credentials)

            # エラーメッセージにURLが含まれることを確認
            error_message = str(exc_info.value)
            assert "ブラウザの起動に失敗しました" in error_message
            assert "https://signin.aws.amazon.com/federation" in error_message
            assert "以下のURLを手動で開いてください" in error_message

    def test_signin_token_failure_propagation(self):
        """
        サインイントークン取得失敗がConsoleManagerに伝播することを確認

        要件: 5.2
        """
        # モックのConsoleServiceを作成
        mock_console_service = MagicMock()
        mock_console_service.get_amazon_domain.return_value = "aws.amazon.com"
        # サインイントークン取得時にエラーを発生させる
        mock_console_service.get_signin_token.side_effect = RuntimeError(
            "AWS Federation Endpointへの接続に失敗しました: Network is unreachable"
        )

        manager = ConsoleManager(console_service=mock_console_service)
        credentials = self.create_test_credentials()

        # RuntimeErrorが発生することを確認
        with pytest.raises(RuntimeError) as exc_info:
            manager.open_console(credentials)

        # エラーメッセージを確認
        error_message = str(exc_info.value)
        assert "AWS Federation Endpointへの接続に失敗しました" in error_message

    def test_unexpected_error_handling(self):
        """
        予期しないエラーのハンドリングテスト

        要件: 5.2
        """
        # モックのConsoleServiceを作成
        mock_console_service = MagicMock()
        mock_console_service.get_amazon_domain.side_effect = Exception(
            "予期しないエラー"
        )

        manager = ConsoleManager(console_service=mock_console_service)
        credentials = self.create_test_credentials()

        # RuntimeErrorが発生することを確認
        with pytest.raises(RuntimeError) as exc_info:
            manager.open_console(credentials)

        # エラーメッセージを確認
        error_message = str(exc_info.value)
        assert "コンソールURLの生成に失敗しました" in error_message


class TestCLIErrorHandling:
    """CLIレイヤーのエラーハンドリングテスト"""

    def test_credentials_acquisition_failure(self):
        """
        認証情報取得失敗時のハンドリングテスト

        要件: 5.1
        """
        # 1Password CLIのチェックをスキップ
        with patch(
            "awsop.services.onepassword.OnePasswordClient.check_availability"
        ) as mock_check:
            mock_check.return_value = True

            # AssumeRoleをモックしてエラーを発生させる
            with patch(
                "awsop.app.credentials_manager.CredentialsManager.assume_role"
            ) as mock_assume_role:
                mock_assume_role.side_effect = RuntimeError(
                    "1Password認証に失敗しました"
                )

                # ProfileManagerをモック
                with patch(
                    "awsop.app.profile_manager.ProfileManager.get_profile"
                ) as mock_get_profile:
                    from awsop.app.profile_manager import ProfileConfig

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

                    # エラーで終了することを確認
                    assert result.exit_code == 1

                    # エラーメッセージを確認
                    assert "1Password認証に失敗しました" in result.stderr

    def test_console_url_generation_failure(self):
        """
        コンソールURL生成失敗時のハンドリングテスト

        要件: 5.2
        """
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
                    from awsop.app.profile_manager import ProfileConfig

                    mock_get_profile.return_value = ProfileConfig(
                        name="test-profile",
                        role_arn="arn:aws:iam::123456789012:role/TestRole",
                        region="ap-northeast-1",
                        external_id=None,
                    )

                    # ConsoleManagerをモックしてエラーを発生させる
                    with patch(
                        "awsop.app.console_manager.ConsoleManager.open_console"
                    ) as mock_open_console:
                        mock_open_console.side_effect = RuntimeError(
                            "AWS Federation Endpointへの接続に失敗しました: Network is unreachable"
                        )

                        # CLIを実行
                        from typer.testing import CliRunner
                        from awsop.cli import app

                        runner = CliRunner()
                        result = runner.invoke(
                            app,
                            ["test-profile", "--console"],
                        )

                        # エラーで終了することを確認
                        assert result.exit_code == 1

                        # エラーメッセージを確認
                        assert (
                            "AWS Federation Endpointへの接続に失敗しました"
                            in result.stderr
                        )

    def test_browser_launch_failure_in_cli(self):
        """
        CLIレイヤーでのブラウザ起動失敗時のハンドリングテスト

        要件: 5.3
        """
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
                    from awsop.app.profile_manager import ProfileConfig

                    mock_get_profile.return_value = ProfileConfig(
                        name="test-profile",
                        role_arn="arn:aws:iam::123456789012:role/TestRole",
                        region="ap-northeast-1",
                        external_id=None,
                    )

                    # ConsoleManagerをモックしてブラウザ起動エラーを発生させる
                    with patch(
                        "awsop.app.console_manager.ConsoleManager.open_console"
                    ) as mock_open_console:
                        test_url = "https://signin.aws.amazon.com/federation?Action=login&SigninToken=test-token"
                        mock_open_console.side_effect = RuntimeError(
                            f"ブラウザの起動に失敗しました: ブラウザが見つかりません\n"
                            f"以下のURLを手動で開いてください:\n{test_url}"
                        )

                        # CLIを実行
                        from typer.testing import CliRunner
                        from awsop.cli import app

                        runner = CliRunner()
                        result = runner.invoke(
                            app,
                            ["test-profile", "--console"],
                        )

                        # エラーで終了することを確認
                        assert result.exit_code == 1

                        # エラーメッセージにURLが含まれることを確認
                        assert "ブラウザの起動に失敗しました" in result.stderr
                        assert test_url in result.stderr
                        assert "以下のURLを手動で開いてください" in result.stderr

    def test_debug_mode_stack_trace(self):
        """
        デバッグモードでのスタックトレース表示テスト

        要件: 5.5
        """
        # 1Password CLIのチェックをスキップ
        with patch(
            "awsop.services.onepassword.OnePasswordClient.check_availability"
        ) as mock_check:
            mock_check.return_value = True

            # AssumeRoleをモックしてエラーを発生させる
            with patch(
                "awsop.app.credentials_manager.CredentialsManager.assume_role"
            ) as mock_assume_role:
                mock_assume_role.side_effect = RuntimeError(
                    "1Password認証に失敗しました"
                )

                # ProfileManagerをモック
                with patch(
                    "awsop.app.profile_manager.ProfileManager.get_profile"
                ) as mock_get_profile:
                    from awsop.app.profile_manager import ProfileConfig

                    mock_get_profile.return_value = ProfileConfig(
                        name="test-profile",
                        role_arn="arn:aws:iam::123456789012:role/TestRole",
                        region="ap-northeast-1",
                        external_id=None,
                    )

                    # traceback.print_excをモック
                    with patch("traceback.print_exc") as mock_traceback:
                        # CLIを実行（デバッグモード）
                        from typer.testing import CliRunner
                        from awsop.cli import app

                        runner = CliRunner()
                        result = runner.invoke(
                            app,
                            ["test-profile", "--console", "--debug"],
                        )

                        # エラーで終了することを確認
                        assert result.exit_code == 1

                        # スタックトレースが出力されたことを確認
                        assert mock_traceback.called

    def test_network_error_in_cli(self):
        """
        CLIレイヤーでのネットワークエラーのハンドリングテスト

        要件: 5.4
        """
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
                    from awsop.app.profile_manager import ProfileConfig

                    mock_get_profile.return_value = ProfileConfig(
                        name="test-profile",
                        role_arn="arn:aws:iam::123456789012:role/TestRole",
                        region="ap-northeast-1",
                        external_id=None,
                    )

                    # urllib.request.urlopenをモックしてネットワークエラーを発生させる
                    with patch("urllib.request.urlopen") as mock_urlopen:
                        mock_urlopen.side_effect = urllib.error.URLError(
                            "Network is unreachable"
                        )

                        # CLIを実行
                        from typer.testing import CliRunner
                        from awsop.cli import app

                        runner = CliRunner()
                        result = runner.invoke(
                            app,
                            ["test-profile", "--console"],
                        )

                        # エラーで終了することを確認
                        assert result.exit_code == 1

                        # エラーメッセージを確認
                        assert (
                            "AWS Federation Endpointへの接続に失敗しました"
                            in result.stderr
                        )
