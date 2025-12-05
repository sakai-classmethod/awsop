"""ConsoleServiceのプロパティベーステスト"""

from hypothesis import given, settings
from hypothesis import strategies as st
from unittest.mock import patch, MagicMock
import json
import urllib.parse

from awsop.services.console_service import ConsoleService
from tests.property.strategies import (
    access_keys,
    secret_keys,
    session_tokens,
    all_regions,
    service_names,
    full_urls,
    signin_tokens,
)


class TestConsoleServiceProperties:
    """ConsoleServiceのプロパティテスト"""

    @given(
        access_key_id=access_keys,
        secret_access_key=secret_keys,
        session_token=session_tokens,
        region=all_regions,
    )
    @settings(max_examples=100, deadline=None)
    def test_property_1_signin_token_consistency(
        self,
        access_key_id: str,
        secret_access_key: str,
        session_token: str,
        region: str,
    ):
        """
        Feature: console-browser-launch, Property 1: サインイントークン取得の一貫性

        任意の有効な一時認証情報（AccessKeyId、SecretAccessKey、SessionToken）に対して、
        システムはAWS Federation Endpointを呼び出し、これらの認証情報を使用して
        サインイントークンを取得する

        検証: 要件 1.2, 1.3
        """
        service = ConsoleService()
        amazon_domain = service.get_amazon_domain(region)

        # urllib.request.urlopenをモック
        with patch("urllib.request.urlopen") as mock_urlopen:
            # モックレスポンスを設定
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps(
                {"SigninToken": "test-token-12345"}
            ).encode("utf-8")
            mock_response.__enter__.return_value = mock_response
            mock_urlopen.return_value = mock_response

            # サインイントークンを取得
            token = service.get_signin_token(
                access_key_id=access_key_id,
                secret_access_key=secret_access_key,
                session_token=session_token,
                amazon_domain=amazon_domain,
            )

            # urlopenが呼ばれたことを確認
            assert mock_urlopen.called
            call_args = mock_urlopen.call_args[0][0]

            # URLにFederation Endpointが含まれることを確認
            assert f"https://signin.{amazon_domain}/federation" in call_args

            # URLパラメータを解析
            parsed_url = urllib.parse.urlparse(call_args)
            params = urllib.parse.parse_qs(parsed_url.query)

            # Actionパラメータが正しいことを確認
            assert params["Action"][0] == "getSigninToken"

            # Sessionパラメータに認証情報が含まれることを確認
            session_data = json.loads(params["Session"][0])
            assert session_data["sessionId"] == access_key_id
            assert session_data["sessionKey"] == secret_access_key
            assert session_data["sessionToken"] == session_token

            # トークンが返されることを確認
            assert token == "test-token-12345"

    @given(region=all_regions, signin_token=signin_tokens, service=service_names)
    @settings(max_examples=100, deadline=None)
    def test_property_2_region_in_url(
        self, region: str, signin_token: str, service: str
    ):
        """
        Feature: console-browser-launch, Property 2: リージョンのURL反映

        任意のAWSリージョンに対して、生成されるコンソールURLは
        そのリージョンをパラメータとして含む

        検証: 要件 1.4
        """
        console_service = ConsoleService()
        amazon_domain = console_service.get_amazon_domain(region)

        # デスティネーションURLを構築
        destination_url = console_service.build_destination_url(
            service=service,
            region=region,
            amazon_domain=amazon_domain,
        )

        # コンソールURLを生成
        console_url = console_service.generate_console_url(
            signin_token=signin_token,
            destination_url=destination_url,
            amazon_domain=amazon_domain,
        )

        # URLにリージョンが含まれることを確認
        assert f"region={region}" in console_url or region in destination_url

    @given(region=all_regions, service=service_names)
    @settings(max_examples=100, deadline=None)
    def test_property_5_template_variable_substitution(self, region: str, service: str):
        """
        Feature: console-browser-launch, Property 5: テンプレート変数の置換

        任意のテンプレート変数（{region}、{amazon_domain}）を含むURLに対して、
        システムは適切な値で置換する

        検証: 要件 2.4, 4.5
        """
        console_service = ConsoleService()
        amazon_domain = console_service.get_amazon_domain(region)

        # デスティネーションURLを構築
        destination_url = console_service.build_destination_url(
            service=service,
            region=region,
            amazon_domain=amazon_domain,
        )

        # テンプレート変数が置換されていることを確認
        assert "{region}" not in destination_url
        assert "{amazon_domain}" not in destination_url

        # 実際の値が含まれることを確認
        assert region in destination_url
        assert amazon_domain in destination_url

    @given(full_url=full_urls, region=all_regions)
    @settings(max_examples=100, deadline=None)
    def test_property_6_full_url_passthrough(self, full_url: str, region: str):
        """
        Feature: console-browser-launch, Property 6: 完全なURLの透過的処理

        任意の完全なURL（http://またはhttps://で始まる）に対して、
        システムはそのURLをデスティネーションとして使用する

        検証: 要件 2.5
        """
        console_service = ConsoleService()
        amazon_domain = console_service.get_amazon_domain(region)

        # 完全なURLを渡す
        destination_url = console_service.build_destination_url(
            service=full_url,
            region=region,
            amazon_domain=amazon_domain,
        )

        # 完全なURLがそのまま返されることを確認
        assert destination_url == full_url

    @given(
        access_key_id=access_keys,
        secret_access_key=secret_keys,
        session_token=session_tokens,
        region=all_regions,
        service=service_names,
    )
    @settings(max_examples=100, deadline=None)
    def test_property_8_complete_authenticated_url(
        self,
        access_key_id: str,
        secret_access_key: str,
        session_token: str,
        region: str,
        service: str,
    ):
        """
        Feature: console-browser-launch, Property 8: 完全な認証済みURL生成

        任意の有効な認証情報に対して、生成されるURLはサインイントークンと
        デスティネーションURLを含む完全な認証済みURLである

        検証: 要件 3.5
        """
        console_service = ConsoleService()
        amazon_domain = console_service.get_amazon_domain(region)

        # urllib.request.urlopenをモック
        with patch("urllib.request.urlopen") as mock_urlopen:
            # モックレスポンスを設定
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps(
                {"SigninToken": "test-signin-token"}
            ).encode("utf-8")
            mock_response.__enter__.return_value = mock_response
            mock_urlopen.return_value = mock_response

            # サインイントークンを取得
            signin_token = console_service.get_signin_token(
                access_key_id=access_key_id,
                secret_access_key=secret_access_key,
                session_token=session_token,
                amazon_domain=amazon_domain,
            )

            # デスティネーションURLを構築
            destination_url = console_service.build_destination_url(
                service=service,
                region=region,
                amazon_domain=amazon_domain,
            )

            # コンソールURLを生成
            console_url = console_service.generate_console_url(
                signin_token=signin_token,
                destination_url=destination_url,
                amazon_domain=amazon_domain,
            )

            # URLが完全な認証済みURLであることを確認
            assert console_url.startswith(f"https://signin.{amazon_domain}/federation")

            # URLパラメータを解析
            parsed_url = urllib.parse.urlparse(console_url)
            params = urllib.parse.parse_qs(parsed_url.query)

            # 必要なパラメータが含まれることを確認
            assert "Action" in params
            assert params["Action"][0] == "login"
            assert "SigninToken" in params
            assert params["SigninToken"][0] == signin_token
            assert "Destination" in params
            assert params["Destination"][0] == destination_url

    @given(region=all_regions)
    @settings(max_examples=100, deadline=None)
    def test_property_9_region_based_domain_determination(self, region: str):
        """
        Feature: console-browser-launch, Property 9: リージョンベースのドメイン決定

        任意のAWSリージョンに対して、システムは以下のルールでAmazonドメインを決定する：
        - us-gov-で始まる場合: amazonaws-us-gov.com
        - cn-で始まる場合: amazonaws.cn
        - その他の場合: aws.amazon.com

        検証: 要件 4.1, 4.2, 4.3
        """
        console_service = ConsoleService()
        amazon_domain = console_service.get_amazon_domain(region)

        # リージョンに応じた正しいドメインが返されることを確認
        if region.startswith("us-gov-"):
            assert amazon_domain == "amazonaws-us-gov.com"
        elif region.startswith("cn-"):
            assert amazon_domain == "amazonaws.cn"
        else:
            assert amazon_domain == "aws.amazon.com"

    @given(
        access_key_id=access_keys,
        secret_access_key=secret_keys,
        session_token=session_tokens,
        region=all_regions,
        service=service_names,
    )
    @settings(max_examples=100, deadline=None)
    def test_property_10_domain_consistency(
        self,
        access_key_id: str,
        secret_access_key: str,
        session_token: str,
        region: str,
        service: str,
    ):
        """
        Feature: console-browser-launch, Property 10: ドメインの一貫性

        任意のリージョンに対して、Federation EndpointとコンソールURLで
        使用されるAmazonドメインは同一である

        検証: 要件 4.4
        """
        console_service = ConsoleService()
        amazon_domain = console_service.get_amazon_domain(region)

        # urllib.request.urlopenをモック
        with patch("urllib.request.urlopen") as mock_urlopen:
            # モックレスポンスを設定
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps(
                {"SigninToken": "test-token"}
            ).encode("utf-8")
            mock_response.__enter__.return_value = mock_response
            mock_urlopen.return_value = mock_response

            # サインイントークンを取得
            signin_token = console_service.get_signin_token(
                access_key_id=access_key_id,
                secret_access_key=secret_access_key,
                session_token=session_token,
                amazon_domain=amazon_domain,
            )

            # Federation Endpoint URLを確認
            federation_call_url = mock_urlopen.call_args[0][0]
            assert f"https://signin.{amazon_domain}/federation" in federation_call_url

            # デスティネーションURLを構築
            destination_url = console_service.build_destination_url(
                service=service,
                region=region,
                amazon_domain=amazon_domain,
            )

            # コンソールURLを生成
            console_url = console_service.generate_console_url(
                signin_token=signin_token,
                destination_url=destination_url,
                amazon_domain=amazon_domain,
            )

            # コンソールURLにも同じドメインが使用されることを確認
            assert f"https://signin.{amazon_domain}/federation" in console_url
            assert amazon_domain in destination_url

    @given(region=all_regions)
    @settings(max_examples=100, deadline=None)
    def test_property_3_service_mapping_conversion(self, region: str):
        """
        Feature: console-browser-launch, Property 3: サービスマッピングの変換

        任意のサービスマッピングに存在する短縮名に対して、
        システムは対応する完全なサービス名またはURLパスに変換する

        検証: 要件 2.2, 6.2, 6.3
        """
        console_service = ConsoleService()
        amazon_domain = console_service.get_amazon_domain(region)

        # すべてのマッピングエントリをテスト
        for short_name, expected_mapping in console_service.SERVICE_MAPPING.items():
            destination_url = console_service.build_destination_url(
                service=short_name,
                region=region,
                amazon_domain=amazon_domain,
            )

            # マッピングが完全なURLテンプレートの場合
            if expected_mapping.startswith("http://") or expected_mapping.startswith(
                "https://"
            ):
                # テンプレート変数が置換されていることを確認
                expected_url = expected_mapping.format(
                    region=region, amazon_domain=amazon_domain
                )
                assert destination_url == expected_url
            else:
                # サービス名が正しく変換されていることを確認
                assert expected_mapping in destination_url
                assert region in destination_url

    @given(region=all_regions, data=st.data())
    @settings(max_examples=100, deadline=None)
    def test_property_4_unknown_service_passthrough(self, region: str, data):
        """
        Feature: console-browser-launch, Property 4: 未知のサービス名の透過的処理

        任意のサービスマッピングに存在しないサービス名に対して、
        システムはそのサービス名をそのままURLパスとして使用する

        検証: 要件 2.3
        """
        console_service = ConsoleService()
        amazon_domain = console_service.get_amazon_domain(region)

        # マッピングに存在しない未知のサービス名を生成
        unknown_service = data.draw(
            st.text(
                alphabet=st.characters(
                    whitelist_categories=("Ll", "Nd"), whitelist_characters="-"
                ),
                min_size=3,
                max_size=20,
            ).filter(
                lambda s: s not in console_service.SERVICE_MAPPING
                and not s.startswith("http://")
                and not s.startswith("https://")
            )
        )

        # 未知のサービス名でデスティネーションURLを構築
        destination_url = console_service.build_destination_url(
            service=unknown_service,
            region=region,
            amazon_domain=amazon_domain,
        )

        # 未知のサービス名がそのままURLに含まれることを確認
        assert unknown_service in destination_url
        assert region in destination_url
        assert amazon_domain in destination_url

    @given(region=all_regions)
    @settings(max_examples=100, deadline=None)
    def test_property_12_mapping_template_processing(self, region: str):
        """
        Feature: console-browser-launch, Property 12: マッピングテンプレートの処理

        任意の完全なURLを値として持つサービスマッピングエントリに対して、
        システムはそのURLをテンプレートとして使用し、変数を置換する

        検証: 要件 6.4
        """
        console_service = ConsoleService()
        amazon_domain = console_service.get_amazon_domain(region)

        # テンプレートURLを持つマッピングエントリを抽出
        template_mappings = {
            k: v
            for k, v in console_service.SERVICE_MAPPING.items()
            if (v.startswith("http://") or v.startswith("https://"))
            and ("{region}" in v or "{amazon_domain}" in v)
        }

        # テンプレートマッピングが存在することを確認
        assert len(template_mappings) > 0, "テンプレートマッピングが定義されていません"

        # 各テンプレートマッピングをテスト
        for short_name, template_url in template_mappings.items():
            destination_url = console_service.build_destination_url(
                service=short_name,
                region=region,
                amazon_domain=amazon_domain,
            )

            # テンプレート変数が置換されていることを確認
            assert "{region}" not in destination_url
            assert "{amazon_domain}" not in destination_url

            # 実際の値が含まれることを確認
            assert region in destination_url
            assert amazon_domain in destination_url

            # 期待されるURLと一致することを確認
            expected_url = template_url.format(
                region=region, amazon_domain=amazon_domain
            )
            assert destination_url == expected_url
