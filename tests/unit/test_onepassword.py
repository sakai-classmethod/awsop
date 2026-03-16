"""OnePasswordClientのユニットテスト"""

import json
import subprocess
from unittest.mock import patch, MagicMock
import pytest

from awsop.services.onepassword import OnePasswordClient


class TestOnePasswordClient:
    """OnePasswordClientクラスのテスト"""

    def test_check_availability_when_op_exists(self):
        """opコマンドが存在する場合、Trueを返す"""
        client = OnePasswordClient()

        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/local/bin/op"

            result = client.check_availability()

            assert result is True
            mock_which.assert_called_once_with("op")

    def test_check_availability_when_op_not_exists(self):
        """opコマンドが存在しない場合、Falseを返す"""
        client = OnePasswordClient()

        with patch("shutil.which") as mock_which:
            mock_which.return_value = None

            result = client.check_availability()

            assert result is False
            mock_which.assert_called_once_with("op")

    def test_run_aws_command_success(self):
        """op plugin runが成功した場合、JSON結果を返す"""
        client = OnePasswordClient()

        # モックの戻り値
        expected_output = {
            "Credentials": {
                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "SessionToken": "token123",
            }
        }

        mock_result = MagicMock()
        mock_result.stdout = json.dumps(expected_output)

        # AWS_PROFILE を含む環境変数をモック
        fake_environ = {
            "HOME": "/home/test",
            "AWS_ACCESS_KEY_ID": "old-key",
            "AWS_SECRET_ACCESS_KEY": "old-secret",
            "AWS_SESSION_TOKEN": "old-token",
            "AWS_PROFILE": "my-profile",
        }

        with patch("os.environ.copy", return_value=fake_environ.copy()):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = mock_result

                result = client.run_aws_command(
                    [
                        "sts",
                        "assume-role",
                        "--role-arn",
                        "arn:aws:iam::123456789012:role/test",
                    ]
                )

                assert result == expected_output
                # envパラメータが渡されることを確認
                assert mock_run.call_count == 1
                call_args = mock_run.call_args
                assert call_args[1]["capture_output"] is True
                assert call_args[1]["text"] is True
                assert call_args[1]["check"] is True
                assert "env" in call_args[1]
                # AWS関連の環境変数がクリアされていることを確認
                env = call_args[1]["env"]
                assert "AWS_ACCESS_KEY_ID" not in env
                assert "AWS_SECRET_ACCESS_KEY" not in env
                assert "AWS_SESSION_TOKEN" not in env
                # AWS_PROFILE が環境に保持されていることを確認（要件 3.1, 3.2）
                assert "AWS_PROFILE" in env, \
                    "AWS_PROFILE が環境から除去されています（保持されるべきです）"
                assert env["AWS_PROFILE"] == "my-profile"

    def test_run_aws_command_failure(self):
        """op plugin runが失敗した場合、CalledProcessErrorを発生させる"""
        client = OnePasswordClient()

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                returncode=1,
                cmd=["op", "plugin", "run", "--", "aws", "sts", "assume-role"],
                stderr="Error: authentication failed",
            )

            with pytest.raises(subprocess.CalledProcessError):
                client.run_aws_command(["sts", "assume-role"])

    def test_run_aws_command_invalid_json(self):
        """出力が無効なJSONの場合、JSONDecodeErrorを発生させる"""
        client = OnePasswordClient()

        mock_result = MagicMock()
        mock_result.stdout = "invalid json output"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = mock_result

            with pytest.raises(json.JSONDecodeError):
                client.run_aws_command(["sts", "get-caller-identity"])
