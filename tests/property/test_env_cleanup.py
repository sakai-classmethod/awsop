"""環境変数クリアのプロパティテスト"""

import json
from unittest.mock import patch, MagicMock

from hypothesis import given, settings
from hypothesis import strategies as st

from awsop.services.onepassword import OnePasswordClient


# クリア対象の7変数
CLEARED_VARS = [
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "AWS_DEFAULT_REGION",
    "AWS_REGION",
    "AWSOP_PROFILE",
    "AWSOP_EXPIRATION",
]

# ランダムな環境変数値のストラテジー
env_values = st.text(
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-_=/"
    ),
    min_size=1,
    max_size=50,
)

# 追加のランダム環境変数（対象外の変数）
extra_env_vars = st.dictionaries(
    keys=st.text(
        alphabet=st.characters(
            whitelist_categories=("Lu", "Nd"), whitelist_characters="_"
        ),
        min_size=1,
        max_size=20,
    ).filter(lambda k: k not in CLEARED_VARS and k != "AWS_PROFILE"),
    values=env_values,
    min_size=0,
    max_size=10,
)


@given(
    cleared_values=st.fixed_dictionaries(
        {var: env_values for var in CLEARED_VARS}
    ),
    aws_profile_value=env_values,
    extra_vars=extra_env_vars,
)
@settings(max_examples=100, deadline=None)
def test_property_3_env_cleanup_variable_set(
    cleared_values: dict,
    aws_profile_value: str,
    extra_vars: dict,
):
    """Feature: remove-aws-profile-export, Property 3: 環境変数クリアの変数セットの正確性

    任意の環境変数セット（対象7変数と AWS_PROFILE を含む）に対して、
    run_aws_command() が準備する環境は以下を満たす:
    - AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN,
      AWS_DEFAULT_REGION, AWS_REGION, AWSOP_PROFILE, AWSOP_EXPIRATION が除去されている
    - AWS_PROFILE が保持されている（クリア対象に含まれない）

    検証: 要件 3.1, 3.2
    """
    # テスト用の環境変数辞書を構築
    fake_environ = {}
    fake_environ.update(extra_vars)
    fake_environ.update(cleared_values)
    fake_environ["AWS_PROFILE"] = aws_profile_value

    client = OnePasswordClient()

    mock_result = MagicMock()
    mock_result.stdout = json.dumps({"result": "ok"})

    captured_env = {}

    def capture_subprocess_run(*args, **kwargs):
        """subprocess.run に渡された env を記録する"""
        captured_env.update(kwargs.get("env", {}))
        return mock_result

    with patch("os.environ.copy", return_value=fake_environ.copy()):
        with patch("subprocess.run", side_effect=capture_subprocess_run):
            client.run_aws_command(["sts", "get-caller-identity"])

    # 対象7変数が除去されていることを確認
    for var in CLEARED_VARS:
        assert var not in captured_env, \
            f"{var} が環境から除去されていません"

    # AWS_PROFILE が保持されていることを確認
    assert "AWS_PROFILE" in captured_env, \
        "AWS_PROFILE が環境から除去されています（保持されるべきです）"
    assert captured_env["AWS_PROFILE"] == aws_profile_value, \
        "AWS_PROFILE の値が変更されています"

    # 追加の環境変数が保持されていることを確認
    for key, value in extra_vars.items():
        assert key in captured_env, \
            f"対象外の環境変数 {key} が除去されています"
