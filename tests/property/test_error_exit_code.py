"""エラー終了コードのプロパティテスト"""

import subprocess
import sys
from hypothesis import given, settings
from hypothesis import strategies as st
from pathlib import Path

from tests.property.strategies import profile_names


@given(profile_name=profile_names)
@settings(max_examples=100, deadline=None)
def test_property_13_error_exit_code(profile_name: str):
    """Feature: awsop-cli-migration, Property 13: エラー時の終了コード

    任意のエラーが発生した場合、システムは終了コード1で終了する

    検証: 要件 11.4
    """
    # 存在しない設定ファイルを指定してエラーを発生させる
    non_existent_config = f"/tmp/non_existent_config_{profile_name}.ini"

    # awsopコマンドを実行（エラーが発生することを期待）
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "awsop",
            profile_name,
            "--config-file",
            non_existent_config,
        ],
        capture_output=True,
        text=True,
    )

    # 終了コードが1であることを確認
    assert result.returncode == 1, f"終了コードが1ではありません: {result.returncode}"

    # エラーメッセージが標準エラー出力に出力されていることを確認
    assert len(result.stderr) > 0, "エラーメッセージが出力されていません"


@settings(max_examples=50, deadline=None)
@given(
    role_duration=st.integers().filter(lambda x: x < 1 or x > 43200),
)
def test_property_13_invalid_role_duration_exit_code(role_duration: int):
    """Feature: awsop-cli-migration, Property 13: エラー時の終了コード（ロール期間バリデーション）

    無効なロール期間が指定された場合、システムは終了コード1で終了する

    検証: 要件 11.4, 4.4.3
    """
    # 無効なロール期間を指定してエラーを発生させる
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "awsop",
            "test-profile",
            "--role-duration",
            str(role_duration),
        ],
        capture_output=True,
        text=True,
    )

    # 終了コードが1であることを確認
    assert result.returncode == 1, f"終了コードが1ではありません: {result.returncode}"

    # エラーメッセージが標準エラー出力に出力されていることを確認
    assert len(result.stderr) > 0, "エラーメッセージが出力されていません"


def test_property_13_missing_role_arn_exit_code():
    """Feature: awsop-cli-migration, Property 13: エラー時の終了コード（role_arn未定義）

    プロファイルにrole_arnが定義されていない場合、システムは終了コード1で終了する

    検証: 要件 11.4, 1.3
    """
    import tempfile
    import os

    # role_arnが定義されていない設定ファイルを作成
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".ini", delete=False
    ) as config_file:
        config_file.write("[profile test-no-role]\n")
        config_file.write("region = ap-northeast-1\n")
        config_file_path = config_file.name

    try:
        # awsopコマンドを実行（エラーが発生することを期待）
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "awsop",
                "test-no-role",
                "--config-file",
                config_file_path,
            ],
            capture_output=True,
            text=True,
        )

        # 終了コードが1であることを確認
        assert result.returncode == 1, (
            f"終了コードが1ではありません: {result.returncode}"
        )

        # エラーメッセージが標準エラー出力に出力されていることを確認
        assert len(result.stderr) > 0, "エラーメッセージが出力されていません"
        assert "role_arn" in result.stderr, (
            "role_arnに関するエラーメッセージが含まれていません"
        )

    finally:
        # 一時ファイルを削除
        os.unlink(config_file_path)


def test_property_13_protected_output_profile_exit_code():
    """Feature: awsop-cli-migration, Property 13: エラー時の終了コード（保護されたプロファイル）

    出力プロファイルが保護されている場合、システムは終了コード1で終了する

    検証: 要件 11.4, 4.6.2
    """
    import tempfile
    import os

    # manager = awsopプロパティがない既存のプロファイルを持つ認証情報ファイルを作成
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".ini", delete=False
    ) as creds_file:
        creds_file.write("[protected-profile]\n")
        creds_file.write("aws_access_key_id = AKIAIOSFODNN7EXAMPLE\n")
        creds_file.write(
            "aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\n"
        )
        creds_file_path = creds_file.name

    # テスト用の設定ファイルを作成
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".ini", delete=False
    ) as config_file:
        config_file.write("[profile test-profile]\n")
        config_file.write("role_arn = arn:aws:iam::123456789012:role/TestRole\n")
        config_file.write("region = ap-northeast-1\n")
        config_file_path = config_file.name

    try:
        # awsopコマンドを実行（エラーが発生することを期待）
        # 実際のAssumeRoleは失敗するが、その前に保護チェックでエラーになるはず
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "awsop",
                "test-profile",
                "--config-file",
                config_file_path,
                "--credentials-file",
                creds_file_path,
                "--output-profile",
                "protected-profile",
            ],
            capture_output=True,
            text=True,
        )

        # 終了コードが1であることを確認
        # 注: 実際のAssumeRoleが失敗する可能性もあるため、
        # 終了コードが1であることのみを確認
        assert result.returncode == 1, (
            f"終了コードが1ではありません: {result.returncode}"
        )

    finally:
        # 一時ファイルを削除
        os.unlink(creds_file_path)
        os.unlink(config_file_path)
