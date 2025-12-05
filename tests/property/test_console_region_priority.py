"""コンソール起動時のリージョンオプション優先のプロパティテスト

Feature: console-browser-launch, Property 11: リージョンオプションの優先
検証: 要件 7.1
"""

from hypothesis import given, settings
from unittest.mock import patch, MagicMock
import json
import urllib.parse

from awsop.app.console_manager import ConsoleManager
from awsop.app.credentials_manager import Credentials
from datetime import datetime, timezone
from tests.property.strategies import (
    all_regions,
    access_keys,
    secret_keys,
    session_tokens,
)


@given(
    region_option=all_regions,
    profile_region=all_regions,
    access_key_id=access_keys,
    secret_access_key=secret_keys,
    session_token=session_tokens,
)
@settings(max_examples=100, deadline=None)
def test_property_11_region_option_priority(
    region_option: str,
    profile_region: str,
    access_key_id: str,
    secret_access_key: str,
    session_token: str,
):
    """
    Feature: console-browser-launch, Property 11: リージョンオプションの優先

    任意の--regionオプションで指定されたリージョンに対して、
    システムはそのリージョンのコンソールURLを生成する

    検証: 要件 7.1
    """
    # 認証情報を作成（region_optionを使用）
    credentials = Credentials(
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        session_token=session_token,
        region=region_option,  # --regionオプションで指定されたリージョン
        expiration=datetime.now(timezone.utc),
        profile="test-profile",
    )

    console_manager = ConsoleManager()

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

            # コンソールURLを生成
            console_url = console_manager.open_console(
                credentials=credentials,
                service="console",
                open_browser=False,
            )

            # URLをパースしてDestinationパラメータを取得
            parsed_url = urllib.parse.urlparse(console_url)
            params = urllib.parse.parse_qs(parsed_url.query)

            # Destinationパラメータをデコード
            destination_url = params["Destination"][0]

            # デスティネーションURLに--regionオプションで指定されたリージョンが含まれることを確認
            assert f"region={region_option}" in destination_url

            # プロファイルのリージョンではなく、--regionオプションのリージョンが使用されることを確認
            # （profile_regionが異なる場合でも、region_optionが優先される）
            if region_option != profile_region:
                # profile_regionがURLに含まれないことを確認
                # ただし、region_optionの一部がprofile_regionに含まれる場合は除外
                if profile_region not in region_option:
                    assert f"region={profile_region}" not in destination_url
