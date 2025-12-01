"""設定ファイル優先順位のプロパティベーステスト"""

import tempfile
from pathlib import Path
from hypothesis import given, strategies as st, settings
from awsop.services.aws_config import AWSConfigParser
from awsop.app.profile_manager import ProfileManager


# AWS設定ファイルのプロファイル名ストラテジー
valid_profile_names = st.text(
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-_"
    ),
    min_size=1,
    max_size=50,
)

# プロファイル設定のストラテジー
profile_config = st.fixed_dictionaries(
    {
        "role_arn": st.builds(
            lambda account, role: f"arn:aws:iam::{account}:role/{role}",
            account=st.integers(min_value=100000000000, max_value=999999999999),
            role=st.text(
                alphabet=st.characters(
                    whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-_"
                ),
                min_size=1,
                max_size=50,
            ),
        ),
        "region": st.sampled_from(
            [
                "us-east-1",
                "us-west-2",
                "eu-west-1",
                "ap-northeast-1",
                "ap-southeast-1",
            ]
        ),
    }
)


def create_config_file(profiles: dict[str, dict]) -> Path:
    """テスト用のAWS設定ファイルを作成

    Args:
        profiles: プロファイル名と設定の辞書

    Returns:
        作成された設定ファイルのパス
    """
    temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".ini")

    for profile_name, config in profiles.items():
        # defaultプロファイルは特別扱い
        if profile_name == "default":
            temp_file.write(f"[default]\n")
        else:
            temp_file.write(f"[profile {profile_name}]\n")

        for key, value in config.items():
            temp_file.write(f"{key} = {value}\n")
        temp_file.write("\n")

    temp_file.close()
    return Path(temp_file.name)


@given(
    profile_name=valid_profile_names,
    config=profile_config,
)
@settings(max_examples=100)
def test_property_12_config_file_priority(profile_name: str, config: dict):
    """Feature: awsop-cli-migration, Property 12: 設定ファイルの優先順位

    任意の実行に対して、--config-fileまたは--credentials-fileが指定された場合は
    それを使用し、指定されない場合はデフォルトの ~/.aws/config と
    ~/.aws/credentials を使用する

    **検証: 要件 10.1, 10.2, 10.3**
    """
    # テスト用のカスタム設定ファイルを作成
    custom_config_file = create_config_file({profile_name: config})

    try:
        # カスタム設定ファイルを指定した場合
        parser_custom = AWSConfigParser(config_file=str(custom_config_file))
        result_custom = parser_custom.read_profile(profile_name)

        # カスタム設定ファイルから正しく読み取れることを確認
        assert result_custom["role_arn"] == config["role_arn"]
        assert result_custom["region"] == config["region"]

        # ProfileManagerでもカスタム設定ファイルが使用されることを確認
        profile_manager = ProfileManager(config_file=str(custom_config_file))
        profile_config_obj = profile_manager.get_profile(profile_name)

        assert profile_config_obj.name == profile_name
        assert profile_config_obj.role_arn == config["role_arn"]
        assert profile_config_obj.region == config["region"]

    finally:
        # テストファイルをクリーンアップ
        custom_config_file.unlink()


@given(
    profile_name=valid_profile_names,
    default_config=profile_config,
    custom_config=profile_config,
)
@settings(max_examples=100)
def test_custom_config_overrides_default(
    profile_name: str, default_config: dict, custom_config: dict
):
    """カスタム設定ファイルがデフォルトより優先される

    同じプロファイル名でも、カスタム設定ファイルを指定した場合は
    そちらの設定が使用される
    """
    # デフォルト設定ファイルとカスタム設定ファイルを作成
    default_file = create_config_file({profile_name: default_config})
    custom_file = create_config_file({profile_name: custom_config})

    try:
        # デフォルト設定ファイルを使用
        parser_default = AWSConfigParser(config_file=str(default_file))
        result_default = parser_default.read_profile(profile_name)

        # カスタム設定ファイルを使用
        parser_custom = AWSConfigParser(config_file=str(custom_file))
        result_custom = parser_custom.read_profile(profile_name)

        # それぞれの設定ファイルから正しい値が読み取れることを確認
        assert result_default["role_arn"] == default_config["role_arn"]
        assert result_default["region"] == default_config["region"]

        assert result_custom["role_arn"] == custom_config["role_arn"]
        assert result_custom["region"] == custom_config["region"]

        # 異なる設定が読み取れることを確認（設定が異なる場合）
        if default_config["role_arn"] != custom_config["role_arn"]:
            assert result_default["role_arn"] != result_custom["role_arn"]

    finally:
        # テストファイルをクリーンアップ
        default_file.unlink()
        custom_file.unlink()


def test_default_config_file_path():
    """設定ファイルを指定しない場合、デフォルトパスが使用される"""
    # デフォルトパスを使用するパーサーを作成
    parser = AWSConfigParser()

    # デフォルトパスが設定されていることを確認
    assert parser.config_file == Path("~/.aws/config").expanduser()


def test_custom_config_file_path():
    """カスタム設定ファイルパスが正しく設定される"""
    custom_path = "/tmp/custom_config"
    parser = AWSConfigParser(config_file=custom_path)

    # カスタムパスが設定されていることを確認
    assert parser.config_file == Path(custom_path).expanduser()


@given(
    profiles=st.dictionaries(
        keys=valid_profile_names,
        values=profile_config,
        min_size=1,
        max_size=5,
    )
)
@settings(max_examples=100)
def test_list_profiles_with_custom_config(profiles: dict[str, dict]):
    """カスタム設定ファイルからプロファイル一覧を取得できる"""
    custom_config_file = create_config_file(profiles)

    try:
        # カスタム設定ファイルを指定してプロファイル一覧を取得
        parser = AWSConfigParser(config_file=str(custom_config_file))
        result = parser.list_profiles()

        # 全てのプロファイルが取得できることを確認
        assert len(result) == len(profiles)
        assert set(result) == set(profiles.keys())

    finally:
        # テストファイルをクリーンアップ
        custom_config_file.unlink()
