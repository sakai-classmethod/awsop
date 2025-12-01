"""AWS STSクライアントのプロパティベーステスト"""

import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import patch

from awsop.services.aws_sts import STSClient
from tests.property.strategies import role_arns, session_names, role_durations


class TestSTSClientProperties:
    """STSClientのプロパティテスト"""

    @given(role_arn=role_arns, session_name=session_names, duration=role_durations)
    @settings(max_examples=100, deadline=None)
    def test_property_2_role_arn_validation(
        self, role_arn: str, session_name: str, duration: int
    ):
        """
        Feature: awsop-cli-migration, Property 2: role_arnの検証

        任意のプロファイルに対して、role_arnが定義されている場合はAssumeRoleが実行され、
        定義されていない場合はエラーが返される

        検証: 要件 1.2, 1.3
        """
        client = STSClient()

        # 有効なrole_arnの場合、boto3のassume_roleが呼ばれることを確認
        with patch.object(client.client, "assume_role") as mock_assume_role:
            # モックレスポンスを設定
            mock_assume_role.return_value = {
                "Credentials": {
                    "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                    "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                    "SessionToken": "token",
                    "Expiration": "2024-01-01T00:00:00Z",
                }
            }

            # assume_roleを実行
            result = client.assume_role(
                role_arn=role_arn,
                role_session_name=session_name,
                duration_seconds=duration,
            )

            # boto3のassume_roleが正しいパラメータで呼ばれたことを確認
            mock_assume_role.assert_called_once()
            call_args = mock_assume_role.call_args[1]
            assert call_args["RoleArn"] == role_arn
            assert call_args["RoleSessionName"] == session_name
            assert call_args["DurationSeconds"] == duration

            # レスポンスが返されることを確認
            assert "Credentials" in result

    @given(session_name=session_names, duration=role_durations)
    @settings(max_examples=100)
    def test_property_2_empty_role_arn_raises_error(
        self, session_name: str, duration: int
    ):
        """
        Feature: awsop-cli-migration, Property 2: role_arnの検証

        role_arnが空の場合はエラーが返される

        検証: 要件 1.3
        """
        client = STSClient()

        # 空のrole_arnでエラーが発生することを確認
        with pytest.raises(ValueError, match="role_arnは必須です"):
            client.assume_role(
                role_arn="",
                role_session_name=session_name,
                duration_seconds=duration,
            )

    @given(
        invalid_arn=st.text(min_size=1, max_size=100).filter(
            lambda x: not x.startswith("arn:aws:iam::")
        ),
        session_name=session_names,
        duration=role_durations,
    )
    @settings(max_examples=100)
    def test_property_2_invalid_role_arn_format_raises_error(
        self, invalid_arn: str, session_name: str, duration: int
    ):
        """
        Feature: awsop-cli-migration, Property 2: role_arnの検証

        無効な形式のrole_arnの場合はエラーが返される

        検証: 要件 1.2, 1.3
        """
        client = STSClient()

        # 無効な形式のrole_arnでエラーが発生することを確認
        with pytest.raises(ValueError, match="無効なrole_arn形式です"):
            client.assume_role(
                role_arn=invalid_arn,
                role_session_name=session_name,
                duration_seconds=duration,
            )

    @given(
        role_arn=role_arns,
        session_name=session_names,
        duration=st.integers(min_value=900, max_value=43200),
    )
    @settings(max_examples=100, deadline=None)
    def test_property_8_valid_role_duration(
        self, role_arn: str, session_name: str, duration: int
    ):
        """
        Feature: awsop-cli-migration, Property 8: ロール期間の検証

        任意のロール期間指定に対して、900から43200秒の範囲内であれば受け入れる

        検証: 要件 4.4.1, 4.4.3
        """
        client = STSClient()

        # 有効な期間の場合、boto3のassume_roleが呼ばれることを確認
        with patch.object(client.client, "assume_role") as mock_assume_role:
            # モックレスポンスを設定
            mock_assume_role.return_value = {
                "Credentials": {
                    "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                    "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                    "SessionToken": "token",
                    "Expiration": "2024-01-01T00:00:00Z",
                }
            }

            # assume_roleを実行
            result = client.assume_role(
                role_arn=role_arn,
                role_session_name=session_name,
                duration_seconds=duration,
            )

            # boto3のassume_roleが正しい期間で呼ばれたことを確認
            call_args = mock_assume_role.call_args[1]
            assert call_args["DurationSeconds"] == duration
            assert 900 <= duration <= 43200

            # レスポンスが返されることを確認
            assert "Credentials" in result

    @given(
        role_arn=role_arns,
        session_name=session_names,
        duration=st.integers(min_value=1, max_value=899),
    )
    @settings(max_examples=100)
    def test_property_8_duration_too_short_raises_error(
        self, role_arn: str, session_name: str, duration: int
    ):
        """
        Feature: awsop-cli-migration, Property 8: ロール期間の検証

        ロール期間が900秒未満の場合はエラーが返される

        検証: 要件 4.4.1, 4.4.3
        """
        client = STSClient()

        # 期間が短すぎる場合はエラーが発生することを確認
        with pytest.raises(
            ValueError, match="ロール期間は900秒以上である必要があります"
        ):
            client.assume_role(
                role_arn=role_arn,
                role_session_name=session_name,
                duration_seconds=duration,
            )

    @given(
        role_arn=role_arns,
        session_name=session_names,
        duration=st.integers(min_value=43201, max_value=100000),
    )
    @settings(max_examples=100)
    def test_property_8_duration_too_long_raises_error(
        self, role_arn: str, session_name: str, duration: int
    ):
        """
        Feature: awsop-cli-migration, Property 8: ロール期間の検証

        ロール期間が43200秒を超える場合はエラーが返される

        検証: 要件 4.4.1, 4.4.3
        """
        client = STSClient()

        # 期間が長すぎる場合はエラーが発生することを確認
        with pytest.raises(
            ValueError, match="ロール期間は43200秒以下である必要があります"
        ):
            client.assume_role(
                role_arn=role_arn,
                role_session_name=session_name,
                duration_seconds=duration,
            )
