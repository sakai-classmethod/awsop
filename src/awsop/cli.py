"""CLIレイヤー - コマンドライン引数の解析とバリデーション"""

import sys
import typer
from typing import Optional

from awsop import __version__
from awsop.logging import setup_logging
from awsop.app.profile_manager import ProfileManager
from awsop.shell.wrapper import generate_shell_wrapper

app = typer.Typer(
    add_completion=False,  # 補完機能は--init-shellで提供
    rich_markup_mode="rich",
    help="AWS credentials manager with 1Password integration",
    # -h を --help の短縮形として有効化
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app.command()
def main(
    profile: Optional[str] = typer.Argument(None, help="AWS profile name"),
    show_commands: bool = typer.Option(
        False, "--show-commands", "-s", help="Show export commands"
    ),
    unset: bool = typer.Option(
        False, "--unset", "-u", help="Clear environment variables"
    ),
    list_profiles: bool = typer.Option(
        False, "--list-profiles", "-l", help="List available profiles"
    ),
    init_shell: bool = typer.Option(
        False, "--init-shell", help="Output shell wrapper function"
    ),
    region: Optional[str] = typer.Option(None, "--region", "-r", help="AWS region"),
    session_name: Optional[str] = typer.Option(
        None, "--session-name", "-n", help="AssumeRole session name"
    ),
    role_duration: int = typer.Option(
        3600,
        "--role-duration",
        "-d",
        help="Role duration in seconds (default: 3600)",
    ),
    mfa_token: Optional[str] = typer.Option(
        None, "--mfa-token", "-m", help="MFA token"
    ),
    output_profile: Optional[str] = typer.Option(
        None, "--output-profile", "-o", help="Output profile name"
    ),
    role_arn: Optional[str] = typer.Option(
        None, "--role-arn", "-a", help="Role ARN to assume"
    ),
    source_profile: Optional[str] = typer.Option(
        None, "--source-profile", "-p", help="Source profile for credentials"
    ),
    external_id: Optional[str] = typer.Option(
        None, "--external-id", "-e", help="External ID for AssumeRole"
    ),
    config_file: Optional[str] = typer.Option(
        None, "--config-file", "-c", help="AWS config file path"
    ),
    credentials_file: Optional[str] = typer.Option(
        None, "--credentials-file", help="AWS credentials file path"
    ),
    info: bool = typer.Option(False, "--info", "-i", help="Show INFO level logs"),
    debug: bool = typer.Option(False, "--debug", help="Show DEBUG level logs"),
    version: bool = typer.Option(False, "--version", "-v", help="Show version"),
) -> None:
    """AWS credentials manager with 1Password integration"""
    # ログレベルの設定
    setup_logging(info=info, debug=debug)

    # --version オプションの処理
    if version:
        print(f"awsop {__version__}")
        return

    # --init-shell オプションの処理
    if init_shell:
        print(generate_shell_wrapper())
        return

    # --list-profiles オプションの処理
    if list_profiles:
        try:
            profile_manager = ProfileManager(config_file=config_file)
            profiles = profile_manager.list_profiles()
            for profile_name in profiles:
                print(profile_name)
        except FileNotFoundError:
            print("エラー: AWS設定ファイルが見つかりません", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"エラー: プロファイル一覧の取得に失敗しました: {e}", file=sys.stderr)
            if debug:
                import traceback

                traceback.print_exc()
            sys.exit(1)
        return

    # 引数なしで実行された場合はヘルプを表示
    if profile is None and not show_commands and not unset:
        print("使用方法: awsop [OPTIONS] [PROFILE]", file=sys.stderr)
        print("詳細は --help オプションを参照してください", file=sys.stderr)
        sys.exit(0)

    # 実装は後続のタスクで行う
    pass


if __name__ == "__main__":
    app()
