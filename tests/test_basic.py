"""基本的なテスト - プロジェクト構造の確認"""

import awsop


def test_version():
    """バージョン情報が正しく設定されているか確認"""
    assert awsop.__version__ == "1.0.0"


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
