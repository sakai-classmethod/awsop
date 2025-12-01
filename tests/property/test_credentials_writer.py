"""CredentialsWriterのプロパティベーステスト"""

import tempfile
from pathlib import Path
from configparser import ConfigParser

from hypothesis import given, settings
from hypothesis import strategies as st

from awsop.services.credentials_writer import CredentialsWriter
from tests.property.strategies import (
    profile_names,
    access_keys,
    secret_keys,
    session_tokens,
)


@given(
    profile_name=profile_names,
    access_key_id=access_keys,
    secret_access_key=secret_keys,
    session_token=session_tokens,
)
@settings(max_examples=100)
def test_property_9_output_profile_protection(
    profile_name: str,
    access_key_id: str,
    secret_access_key: str,
    session_token: str,
):
    """Feature: awsop-cli-migration, Property 9: 出力プロファイルの保護

    任意の出力プロファイル名に対して、そのプロファイルが既に存在し
    `manager = awsop` プロパティがない場合はエラーを返し、
    プロパティがある場合は上書きを許可する

    **検証: 要件 4.6.2, 4.6.3**
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        credentials_file = Path(tmpdir) / "credentials"
        writer = CredentialsWriter(str(credentials_file))

        # ケース1: 新規プロファイルの場合は正常に書き込める
        writer.write_profile(
            profile_name,
            access_key_id,
            secret_access_key,
            session_token,
        )

        # プロファイルが作成され、manager = awsop が設定されていることを確認
        assert credentials_file.exists()
        assert writer.is_managed_by_awsop(profile_name)

        parser = ConfigParser()
        parser.read(credentials_file)
        assert parser.has_section(profile_name)
        assert parser.get(profile_name, "manager") == "awsop"
        assert parser.get(profile_name, "aws_access_key_id") == access_key_id

        # ケース2: awsop管理のプロファイルは上書き可能
        new_access_key = "AKIAIOSFODNN7EXAMPLE2"
        writer.write_profile(
            profile_name,
            new_access_key,
            secret_access_key,
            session_token,
        )

        parser = ConfigParser()
        parser.read(credentials_file)
        assert parser.get(profile_name, "aws_access_key_id") == new_access_key
        assert parser.get(profile_name, "manager") == "awsop"


@given(
    profile_name=profile_names,
    access_key_id=access_keys,
    secret_access_key=secret_keys,
    session_token=session_tokens,
)
@settings(max_examples=100)
def test_property_9_non_managed_profile_protection(
    profile_name: str,
    access_key_id: str,
    secret_access_key: str,
    session_token: str,
):
    """Feature: awsop-cli-migration, Property 9: 出力プロファイルの保護（非管理プロファイル）

    manager = awsop プロパティがないプロファイルは上書きできない

    **検証: 要件 4.6.2**
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        credentials_file = Path(tmpdir) / "credentials"

        # 既存のプロファイルを作成（awsop管理ではない）
        parser = ConfigParser()
        parser.add_section(profile_name)
        parser.set(profile_name, "aws_access_key_id", "AKIAIOSFODNN7EXAMPLE")
        parser.set(
            profile_name,
            "aws_secret_access_key",
            "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        )
        # manager プロパティを設定しない

        credentials_file.parent.mkdir(parents=True, exist_ok=True)
        with open(credentials_file, "w") as f:
            parser.write(f)

        writer = CredentialsWriter(str(credentials_file))

        # awsop管理ではないプロファイルへの書き込みはエラー
        try:
            writer.write_profile(
                profile_name,
                access_key_id,
                secret_access_key,
                session_token,
            )
            # エラーが発生しなかった場合はテスト失敗
            assert False, "ValueError が発生すべき"
        except ValueError as e:
            # エラーメッセージに適切な内容が含まれることを確認
            assert "awsop管理ではありません" in str(e) or "上書きできません" in str(e)


@given(
    profile_name=profile_names,
    access_key_id=access_keys,
    secret_access_key=secret_keys,
    session_token=session_tokens,
)
@settings(max_examples=100)
def test_file_permissions_are_600(
    profile_name: str,
    access_key_id: str,
    secret_access_key: str,
    session_token: str,
):
    """ファイルパーミッションが600に設定されることを確認

    **検証: 要件 4.6.1**
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        credentials_file = Path(tmpdir) / "credentials"
        writer = CredentialsWriter(str(credentials_file))

        writer.write_profile(
            profile_name,
            access_key_id,
            secret_access_key,
            session_token,
        )

        # ファイルパーミッションが600であることを確認
        import stat

        file_stat = credentials_file.stat()
        file_mode = stat.S_IMODE(file_stat.st_mode)
        assert file_mode == 0o600, f"Expected 0o600, got {oct(file_mode)}"
