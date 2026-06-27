"""awsop 認証情報キャッシュのテスト"""

from datetime import datetime, timedelta, timezone

from awsop.app.credentials_manager import CredentialsManager


class DummyClient:
    pass


def create_manager() -> CredentialsManager:
    return CredentialsManager(
        onepassword_client=DummyClient(),
        sts_client=DummyClient(),
    )


def test_get_cached_credentials_returns_valid_environment_credentials():
    manager = create_manager()
    now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    expiration = now + timedelta(hours=1)
    env = {
        "AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE",
        "AWS_SECRET_ACCESS_KEY": "secret",
        "AWS_SESSION_TOKEN": "token",
        "AWS_REGION": "us-west-2",
        "AWSOP_PROFILE": "test-profile",
        "AWSOP_EXPIRATION": expiration.isoformat(),
    }

    credentials = manager.get_cached_credentials(
        profile="test-profile",
        env=env,
        now=now,
    )

    assert credentials is not None
    assert credentials.access_key_id == "AKIAIOSFODNN7EXAMPLE"
    assert credentials.secret_access_key == "secret"
    assert credentials.session_token == "token"
    assert credentials.region == "us-west-2"
    assert credentials.profile == "test-profile"
    assert credentials.expiration == expiration


def test_get_cached_credentials_rejects_different_profile():
    manager = create_manager()
    now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    env = {
        "AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE",
        "AWS_SECRET_ACCESS_KEY": "secret",
        "AWS_SESSION_TOKEN": "token",
        "AWSOP_PROFILE": "other-profile",
        "AWSOP_EXPIRATION": (now + timedelta(hours=1)).isoformat(),
    }

    credentials = manager.get_cached_credentials(
        profile="test-profile",
        env=env,
        now=now,
    )

    assert credentials is None


def test_get_cached_credentials_rejects_near_expiration():
    manager = create_manager()
    now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    env = {
        "AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE",
        "AWS_SECRET_ACCESS_KEY": "secret",
        "AWS_SESSION_TOKEN": "token",
        "AWSOP_PROFILE": "test-profile",
        "AWSOP_EXPIRATION": (now + timedelta(minutes=4)).isoformat(),
    }

    credentials = manager.get_cached_credentials(
        profile="test-profile",
        env=env,
        now=now,
    )

    assert credentials is None
