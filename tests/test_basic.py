"""基本的なテスト - プロジェクト構造の確認"""

import awsop


def test_version():
    """バージョン情報が正しく設定されているか確認"""
    # バージョンが文字列型であることを確認
    assert isinstance(awsop.__version__, str)
    # 空文字列でないことを確認
    assert len(awsop.__version__) > 0
    # 詳細なバージョンチェックはtest_version_installed.pyで実施


def test_imports():
    """主要なモジュールがインポートできるか確認"""
    from awsop.app.profile_manager import ProfileManager, ProfileConfig
    from awsop.app.credentials_manager import CredentialsManager, Credentials
    from awsop.services.aws_config import AWSConfigParser
    from awsop.services.onepassword import OnePasswordClient
    from awsop.services.aws_sts import STSClient
    from awsop.services.credentials_writer import CredentialsWriter
    from awsop.ui.console import ConsoleUI
    from awsop.shell.wrapper import generate_shell_wrapper

    # インポートが成功すればテストパス
    assert True
