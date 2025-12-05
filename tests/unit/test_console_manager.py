"""ConsoleManagerのユニットテスト"""

from datetime import datetime
from unittest.mock import MagicMock, patch
import pytest

from awsop.app.console_manager import ConsoleManager
from awsop.app.credentials_manager import Credentials


class TestConsoleManager:
    """ConsoleManagerクラスのテスト"""

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

    def test_open_console_basic(self):
        """基本的なコンソール起動のテスト（要件1.1, 1.5）"""
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
            result = manager.open_console(credentials)

            # URLが返されることを確認
            assert result.startswith("https://signin.aws.amazon.com/federation")
            assert "SigninToken=test-signin-token" in result

            # ブラウザが開かれることを確認
            mock_browser.assert_called_once()

            # ConsoleServiceのメソッドが正しく呼ばれることを確認
            mock_console_service.get_amazon_domain.assert_called_once_with("us-east-1")
            mock_console_service.get_signin_token.assert_called_once_with(
                access_key_id="AKIAIOSFODNN7EXAMPLE",
                secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                session_token="test-session-token",
                amazon_domain="aws.amazon.com",
            )
            mock_console_service.build_destination_url.assert_called_once_with(
                service="console",
                region="us-east-1",
                amazon_domain="aws.amazon.com",
            )

    def test_open_console_with_service(self):
        """サービス指定でのコンソール起動のテスト（要件2.1）"""
        # モックのConsoleServiceを作成
        mock_console_service = MagicMock()
        mock_console_service.get_amazon_domain.return_value = "aws.amazon.com"
        mock_console_service.get_signin_token.return_value = "test-signin-token"
        mock_console_service.build_destination_url.return_value = (
            "https://console.aws.amazon.com/s3/home?region=us-east-1"
        )
        mock_console_service.generate_console_url.return_value = "https://signin.aws.amazon.com/federation?Action=login&SigninToken=test-signin-token"

        manager = ConsoleManager(console_service=mock_console_service)
        credentials = self.create_test_credentials()

        with patch("webbrowser.open") as mock_browser:
            result = manager.open_console(credentials, service="s3")

            # URLが返されることを確認
            assert result.startswith("https://signin.aws.amazon.com/federation")

            # ブラウザが開かれることを確認
            mock_browser.assert_called_once()

            # build_destination_urlが正しいサービス名で呼ばれることを確認
            mock_console_service.build_destination_url.assert_called_once_with(
                service="s3",
                region="us-east-1",
                amazon_domain="aws.amazon.com",
            )

    def test_open_console_without_browser(self):
        """ブラウザを開かずにURLのみを取得するテスト"""
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
            result = manager.open_console(credentials, open_browser=False)

            # URLが返されることを確認
            assert result.startswith("https://signin.aws.amazon.com/federation")

            # ブラウザが開かれないことを確認
            mock_browser.assert_not_called()

    def test_open_console_browser_error(self):
        """ブラウザ起動エラーのハンドリングテスト（要件5.3）"""
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

    def test_open_console_signin_token_error(self):
        """サインイントークン取得エラーのテスト"""
        # モックのConsoleServiceを作成
        mock_console_service = MagicMock()
        mock_console_service.get_amazon_domain.return_value = "aws.amazon.com"
        # サインイントークン取得時にエラーを発生させる
        mock_console_service.get_signin_token.side_effect = RuntimeError(
            "AWS Federation Endpointへの接続に失敗しました"
        )

        manager = ConsoleManager(console_service=mock_console_service)
        credentials = self.create_test_credentials()

        # RuntimeErrorが発生することを確認
        with pytest.raises(RuntimeError) as exc_info:
            manager.open_console(credentials)

        # エラーメッセージを確認
        assert "AWS Federation Endpointへの接続に失敗しました" in str(exc_info.value)

    def test_open_console_with_different_regions(self):
        """異なるリージョンでのコンソール起動のテスト"""
        # GovCloudリージョンのテスト
        mock_console_service = MagicMock()
        mock_console_service.get_amazon_domain.return_value = "amazonaws-us-gov.com"
        mock_console_service.get_signin_token.return_value = "test-signin-token"
        mock_console_service.build_destination_url.return_value = (
            "https://console.amazonaws-us-gov.com/console/home?region=us-gov-west-1"
        )
        mock_console_service.generate_console_url.return_value = (
            "https://signin.amazonaws-us-gov.com/federation?Action=login"
        )

        manager = ConsoleManager(console_service=mock_console_service)
        credentials = self.create_test_credentials(region="us-gov-west-1")

        with patch("webbrowser.open"):
            result = manager.open_console(credentials, open_browser=False)

            # GovCloudドメインが使用されることを確認
            mock_console_service.get_amazon_domain.assert_called_once_with(
                "us-gov-west-1"
            )
            assert result.startswith("https://signin.amazonaws-us-gov.com/federation")

    def test_open_console_with_custom_service_url(self):
        """カスタムサービスURLでのコンソール起動のテスト"""
        # モックのConsoleServiceを作成
        mock_console_service = MagicMock()
        mock_console_service.get_amazon_domain.return_value = "aws.amazon.com"
        mock_console_service.get_signin_token.return_value = "test-signin-token"
        # 完全なURLを返す
        mock_console_service.build_destination_url.return_value = (
            "https://quicksight.aws.amazon.com"
        )
        mock_console_service.generate_console_url.return_value = "https://signin.aws.amazon.com/federation?Action=login&SigninToken=test-signin-token"

        manager = ConsoleManager(console_service=mock_console_service)
        credentials = self.create_test_credentials()

        with patch("webbrowser.open"):
            result = manager.open_console(
                credentials,
                service="https://quicksight.aws.amazon.com",
                open_browser=False,
            )

            # URLが返されることを確認
            assert result.startswith("https://signin.aws.amazon.com/federation")

            # build_destination_urlが完全なURLで呼ばれることを確認
            mock_console_service.build_destination_url.assert_called_once_with(
                service="https://quicksight.aws.amazon.com",
                region="us-east-1",
                amazon_domain="aws.amazon.com",
            )
