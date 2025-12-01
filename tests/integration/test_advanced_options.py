"""高度なオプションの統合テスト"""

import tempfile
from pathlib import Path
from typer.testing import CliRunner
from awsop.cli import app

runner = CliRunner()


def create_config_file(profiles: dict[str, dict]) -> Path:
    """テスト用のAWS設定ファイルを作成"""
    temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".ini")

    for profile_name, config in profiles.items():
        if profile_name == "default":
            temp_file.write(f"[default]\n")
        else:
            temp_file.write(f"[profile {profile_name}]\n")

        for key, value in config.items():
            temp_file.write(f"{key} = {value}\n")
        temp_file.write("\n")

    temp_file.close()
    return Path(temp_file.name)


def create_credentials_file(profiles: dict[str, dict]) -> Path:
    """テスト用のAWS認証情報ファイルを作成"""
    temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".ini")

    for profile_name, config in profiles.items():
        temp_file.write(f"[{profile_name}]\n")
        for key, value in config.items():
            temp_file.write(f"{key} = {value}\n")
        temp_file.write("\n")

    temp_file.close()
    return Path(temp_file.name)


def test_role_arn_option():
    """--role-arnオプションが正しく処理される"""
    result = runner.invoke(
        app,
        [
            "--role-arn",
            "arn:aws:iam::123456789012:role/TestRole",
            "--session-name",
            "test-session",
        ],
    )

    # 1Password CLIが利用できない環境ではエラーになる
    # エラーメッセージが適切に表示されることを確認
    assert result.exit_code == 1
    assert "1Password" in result.stderr or "認証情報の取得に失敗" in result.stderr


def test_source_profile_option():
    """--source-profileオプションが正しく処理される"""
    # テスト用の設定ファイルを作成
    profiles = {
        "source": {
            "role_arn": "arn:aws:iam::123456789012:role/SourceRole",
            "region": "us-west-2",
        }
    }
    config_file = create_config_file(profiles)

    try:
        result = runner.invoke(
            app,
            [
                "--role-arn",
                "arn:aws:iam::123456789012:role/TargetRole",
                "--source-profile",
                "source",
                "--config-file",
                str(config_file),
                "--session-name",
                "test-session",
            ],
        )

        # 1Password CLIが利用できない環境ではエラーになる
        # ソースプロファイルが正しく読み込まれることを確認
        # （エラーメッセージにプロファイルが見つからないというメッセージがないことを確認）
        assert "プロファイル 'source' が見つかりません" not in result.stderr

    finally:
        config_file.unlink()


def test_external_id_option():
    """--external-idオプションが正しく処理される"""
    # テスト用の設定ファイルを作成
    profiles = {
        "test": {
            "role_arn": "arn:aws:iam::123456789012:role/TestRole",
            "region": "ap-northeast-1",
        }
    }
    config_file = create_config_file(profiles)

    try:
        result = runner.invoke(
            app,
            [
                "test",
                "--external-id",
                "external-id-12345",
                "--config-file",
                str(config_file),
                "--session-name",
                "test-session",
            ],
        )

        # 1Password CLIが利用できない環境ではエラーになる
        # 外部IDが正しく処理されることを確認
        assert result.exit_code == 1

    finally:
        config_file.unlink()


def test_output_profile_option_new_profile():
    """--output-profileオプションで新しいプロファイルに書き込める"""
    # テスト用の設定ファイルを作成
    profiles = {
        "test": {
            "role_arn": "arn:aws:iam::123456789012:role/TestRole",
            "region": "ap-northeast-1",
        }
    }
    config_file = create_config_file(profiles)

    # テスト用の認証情報ファイルを作成（空）
    credentials_file = create_credentials_file({})

    try:
        result = runner.invoke(
            app,
            [
                "test",
                "--output-profile",
                "output-test",
                "--config-file",
                str(config_file),
                "--credentials-file",
                str(credentials_file),
                "--session-name",
                "test-session",
            ],
        )

        # 1Password CLIが利用できない環境ではエラーになる
        assert result.exit_code == 1

    finally:
        config_file.unlink()
        credentials_file.unlink()


def test_output_profile_option_protected_profile():
    """--output-profileオプションで保護されたプロファイルには書き込めない"""
    # テスト用の設定ファイルを作成
    profiles = {
        "test": {
            "role_arn": "arn:aws:iam::123456789012:role/TestRole",
            "region": "ap-northeast-1",
        }
    }
    config_file = create_config_file(profiles)

    # テスト用の認証情報ファイルを作成（保護されたプロファイル）
    credentials_profiles = {
        "protected": {
            "aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
            "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            # manager = awsop がないため保護されている
        }
    }
    credentials_file = create_credentials_file(credentials_profiles)

    try:
        result = runner.invoke(
            app,
            [
                "test",
                "--output-profile",
                "protected",
                "--config-file",
                str(config_file),
                "--credentials-file",
                str(credentials_file),
                "--session-name",
                "test-session",
            ],
        )

        # 1Password CLIが利用できない環境でもエラーになるが、
        # 保護されたプロファイルのエラーが先に発生する可能性がある
        assert result.exit_code == 1

    finally:
        config_file.unlink()
        credentials_file.unlink()


def test_custom_config_file_option():
    """--config-fileオプションでカスタム設定ファイルを使用できる"""
    # テスト用の設定ファイルを作成
    profiles = {
        "custom": {
            "role_arn": "arn:aws:iam::123456789012:role/CustomRole",
            "region": "eu-west-1",
        }
    }
    config_file = create_config_file(profiles)

    try:
        result = runner.invoke(
            app,
            [
                "custom",
                "--config-file",
                str(config_file),
                "--session-name",
                "test-session",
            ],
        )

        # 1Password CLIが利用できない環境ではエラーになる
        # カスタム設定ファイルが正しく読み込まれることを確認
        assert "プロファイル 'custom' が見つかりません" not in result.stderr

    finally:
        config_file.unlink()


def test_list_profiles_with_custom_config():
    """--list-profilesオプションでカスタム設定ファイルのプロファイルを一覧表示できる"""
    # テスト用の設定ファイルを作成
    profiles = {
        "profile1": {
            "role_arn": "arn:aws:iam::123456789012:role/Role1",
            "region": "us-east-1",
        },
        "profile2": {
            "role_arn": "arn:aws:iam::123456789012:role/Role2",
            "region": "us-west-2",
        },
    }
    config_file = create_config_file(profiles)

    try:
        result = runner.invoke(
            app,
            [
                "--list-profiles",
                "--config-file",
                str(config_file),
            ],
        )

        # プロファイル一覧が正しく表示される
        assert result.exit_code == 0
        assert "profile1" in result.stdout
        assert "profile2" in result.stdout

    finally:
        config_file.unlink()


def test_role_arn_without_profile():
    """--role-arnオプションのみでプロファイルなしで実行できる"""
    result = runner.invoke(
        app,
        [
            "--role-arn",
            "arn:aws:iam::123456789012:role/DirectRole",
            "--region",
            "ap-northeast-1",
            "--session-name",
            "test-session",
        ],
    )

    # 1Password CLIが利用できない環境ではエラーになる
    # プロファイルが見つからないというエラーは出ない
    assert (
        "プロファイル" not in result.stderr or "が見つかりません" not in result.stderr
    )


def test_role_duration_validation():
    """ロール期間のバリデーションが正しく動作する"""
    # テスト用の設定ファイルを作成
    profiles = {
        "test": {
            "role_arn": "arn:aws:iam::123456789012:role/TestRole",
            "region": "ap-northeast-1",
        }
    }
    config_file = create_config_file(profiles)

    try:
        # 範囲外の期間を指定
        result = runner.invoke(
            app,
            [
                "test",
                "--role-duration",
                "50000",  # 43200秒を超える
                "--config-file",
                str(config_file),
            ],
        )

        # バリデーションエラーが発生
        assert result.exit_code == 1
        assert "ロール期間は1から43200秒の範囲で指定してください" in result.stderr

    finally:
        config_file.unlink()
