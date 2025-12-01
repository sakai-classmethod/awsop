"""AWS設定パーサーのプロパティベーステスト"""

import tempfile
from pathlib import Path
from hypothesis import given, strategies as st, settings
from awsop.services.aws_config import AWSConfigParser


# AWS設定ファイルのプロファイル名ストラテジー
# AWS設定ファイルでは英数字、ハイフン、アンダースコアが使用可能
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
def test_property_1_profile_config_reading(profile_name: str, config: dict):
    """Feature: awsop-cli-migration, Property 1: プロファイル設定の読み取り

    任意の有効なプロファイル名に対して、システムは ~/.aws/config から
    そのプロファイルの設定を正しく読み取り、role_arn、region、
    その他の設定値を取得できる

    **検証: 要件 1.1**
    """
    # テスト用の設定ファイルを作成
    profiles = {profile_name: config}
    config_file = create_config_file(profiles)

    try:
        # AWSConfigParserでプロファイルを読み取る
        parser = AWSConfigParser(config_file=str(config_file))
        result = parser.read_profile(profile_name)

        # 設定が正しく読み取れることを確認
        assert "role_arn" in result
        assert "region" in result
        assert result["role_arn"] == config["role_arn"]
        assert result["region"] == config["region"]
    finally:
        # テストファイルをクリーンアップ
        config_file.unlink()


@given(profile_name=valid_profile_names)
@settings(max_examples=100)
def test_profile_not_found_raises_error(profile_name: str):
    """存在しないプロファイルを読み取ろうとするとエラーが発生する"""
    # 空の設定ファイルを作成
    config_file = create_config_file({})

    try:
        parser = AWSConfigParser(config_file=str(config_file))

        # 存在しないプロファイルを読み取ろうとするとKeyErrorが発生
        try:
            parser.read_profile(profile_name)
            assert False, "KeyErrorが発生するべき"
        except KeyError as e:
            assert profile_name in str(e)
    finally:
        config_file.unlink()


def test_default_profile_handling():
    """defaultプロファイルが正しく処理される"""
    config = {
        "role_arn": "arn:aws:iam::123456789012:role/TestRole",
        "region": "ap-northeast-1",
    }
    config_file = create_config_file({"default": config})

    try:
        parser = AWSConfigParser(config_file=str(config_file))
        result = parser.read_profile("default")

        assert result["role_arn"] == config["role_arn"]
        assert result["region"] == config["region"]
    finally:
        config_file.unlink()


@given(
    profiles=st.dictionaries(
        keys=valid_profile_names,
        values=profile_config,
        min_size=1,
        max_size=10,
    )
)
@settings(max_examples=100)
def test_property_4_profile_list_completeness(profiles: dict[str, dict]):
    """Feature: awsop-cli-migration, Property 4: プロファイル一覧の完全性

    任意のAWS設定ファイルに対して、システムは全てのプロファイル名を抽出し、
    各プロファイル名を1行ずつ出力する

    **検証: 要件 3.1, 3.2**
    """
    # テスト用の設定ファイルを作成
    config_file = create_config_file(profiles)

    try:
        # AWSConfigParserでプロファイル一覧を取得
        parser = AWSConfigParser(config_file=str(config_file))
        result = parser.list_profiles()

        # 全てのプロファイルが取得できることを確認
        assert len(result) == len(profiles)
        assert set(result) == set(profiles.keys())

        # 各プロファイル名が文字列であることを確認
        for profile_name in result:
            assert isinstance(profile_name, str)
            assert len(profile_name) > 0
    finally:
        config_file.unlink()


def test_empty_config_returns_empty_list():
    """空の設定ファイルは空のリストを返す"""
    config_file = create_config_file({})

    try:
        parser = AWSConfigParser(config_file=str(config_file))
        result = parser.list_profiles()

        assert result == []
    finally:
        config_file.unlink()


def test_list_profiles_with_default():
    """defaultプロファイルを含むリストが正しく取得できる"""
    profiles = {
        "default": {
            "role_arn": "arn:aws:iam::123456789012:role/DefaultRole",
            "region": "us-east-1",
        },
        "production": {
            "role_arn": "arn:aws:iam::123456789012:role/ProdRole",
            "region": "ap-northeast-1",
        },
    }
    config_file = create_config_file(profiles)

    try:
        parser = AWSConfigParser(config_file=str(config_file))
        result = parser.list_profiles()

        assert len(result) == 2
        assert "default" in result
        assert "production" in result
    finally:
        config_file.unlink()
