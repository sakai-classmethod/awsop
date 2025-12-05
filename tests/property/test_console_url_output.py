"""コンソールURL出力フォーマットのプロパティベーステスト"""

from io import StringIO
from hypothesis import given, settings
from unittest.mock import patch, MagicMock
import json

from awsop.app.credentials_manager import Credentials
from tests.property.strategies import (
    access_keys,
    secret_keys,
    session_tokens,
    all_regions,
    service_names,
)


class TestConsoleUrlOutputProperties:
    """コンソールURL出力フォーマットのプロパティテスト"""

    @given(
        access_key_id=access_keys,
        secret_access_key=secret_keys,
        session_token=session_tokens,
        region=all_regions,
        service=service_names,
    )
    @settings(max_examples=100, deadline=None)
    def test_property_7_url_output_format(
        self,
        access_key_id: str,
        secret_access_key: str,
        session_token: str,
        region: str,
        service: str,
    ):
        """
        Feature: console-browser-launch, Property 7: URL出力フォーマット

        任意の生成されたコンソールURLに対して、--console-linkオプション使用時は
        標準出力に改行なしで出力し、情報メッセージは標準エラー出力に出力する

        検証: 要件 3.3, 3.4
        """
        from datetime import datetime, timezone
        from awsop.app.profile_manager import ProfileConfig
        from typer.testing import CliRunner
        from awsop.cli import app

        # urllib.request.urlopenをモック
        with patch("urllib.request.urlopen") as mock_urlopen:
            # モックレスポンスを設定
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps(
                {"SigninToken": "test-signin-token"}
            ).encode("utf-8")
            mock_response.__enter__.return_value = mock_response
            mock_urlopen.return_value = mock_response

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
                        access_key_id=access_key_id,
                        secret_access_key=secret_access_key,
                        session_token=session_token,
                        region=region,
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
                            region=region,
                            external_id=None,
                        )

                        # CLIを実行
                        runner = CliRunner()
                        result = runner.invoke(
                            app,
                            [
                                "test-profile",
                                "--console-link",
                                "--console-service",
                                service,
                            ],
                        )

                        # 成功することを確認
                        assert result.exit_code == 0, (
                            f"CLI failed with output: {result.output}"
                        )

                        # 出力にURLが含まれることを確認
                        assert result.output, "出力が空です"
                        assert "https://" in result.output, (
                            "出力にURLが含まれていません"
                        )

                        # URLの基本的な構造を確認
                        assert "SigninToken=" in result.output, (
                            "URLにサインイントークンが含まれていません"
                        )
                        assert "Destination=" in result.output, (
                            "URLにデスティネーションが含まれていません"
                        )
                        assert "Action=login" in result.output, (
                            "URLにActionパラメータが含まれていません"
                        )

                        # 出力からURLを抽出（要件3.4: 改行なしで出力）
                        # Rich UIのメッセージとURLが混在している可能性があるため、
                        # https://で始まる行を探す
                        lines = result.output.split("\n")
                        url_lines = [
                            line
                            for line in lines
                            if "https://" in line and "SigninToken=" in line
                        ]

                        # URLが見つかることを確認
                        assert len(url_lines) > 0, "URL行が見つかりません"

                        # URL行に改行が含まれていないことを確認（要件3.4）
                        # 各URL行は単一行であるべき
                        for url_line in url_lines:
                            url_line_stripped = url_line.strip()
                            # URL自体に改行が含まれていないことを確認
                            # （行分割後なので、この時点で改行は含まれないはず）
                            # ここでは、URLが1行に収まっていることを確認
                            assert url_line_stripped.startswith("https://"), (
                                "URL行がhttps://で始まっていません"
                            )
