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

    # --unset オプションの処理
    if unset:
        from awsop.app.credentials_manager import CredentialsManager

        credentials_manager = CredentialsManager()
        unset_commands = credentials_manager.format_unset_commands()
        print(unset_commands)
        return

    # 引数なしで実行された場合はヘルプを表示
    if profile is None and not show_commands:
        print("使用方法: awsop [OPTIONS] [PROFILE]", file=sys.stderr)
        print("詳細は --help オプションを参照してください", file=sys.stderr)
        sys.exit(0)

    # プロファイル切り替え処理（タスク13）
    if profile:
        from awsop.app.credentials_manager import CredentialsManager
        from awsop.ui.console import ConsoleUI
        from datetime import datetime

        ui = ConsoleUI()

        try:
            # ProfileManagerを使用してプロファイル設定を取得（要件1.1）
            profile_manager = ProfileManager(config_file=config_file)
            profile_config = profile_manager.get_profile(profile)

            # role_arnが定義されているかチェック（要件1.2, 1.3）
            if not profile_config.role_arn:
                ui.error(f"プロファイル '{profile}' に role_arn が定義されていません")
                sys.exit(1)

            # リージョンの決定（要件4.2.1, 4.2.2, 4.2.3）
            # --region オプション > プロファイルのregion > デフォルト（ap-northeast-1）
            effective_region = region or profile_config.region or "ap-northeast-1"

            # セッション名の決定（要件4.3.1, 4.3.2）
            if not session_name:
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                session_name = f"awsop-{timestamp}"

            # CredentialsManagerを使用して認証情報を取得
            credentials_manager = CredentialsManager()

            # スピナーを表示しながら認証情報を取得（要件8.1）
            with ui.spinner("1Password経由で認証情報を取得中..."):
                credentials = credentials_manager.assume_role(
                    role_arn=profile_config.role_arn,
                    session_name=session_name,
                    duration=role_duration,
                    region=effective_region,
                    profile=profile,
                    external_id=profile_config.external_id or external_id,
                    mfa_token=mfa_token,
                )

            # exportコマンドを標準出力に出力（要件1.4, 5.4）
            export_commands = credentials_manager.format_export_commands(credentials)
            print(export_commands)

            # --show-commandsオプションがない場合は、有効期限も表示
            if not show_commands:
                # JSTに変換して表示
                import zoneinfo

                jst = zoneinfo.ZoneInfo("Asia/Tokyo")
                expiration_jst = credentials.expiration.astimezone(jst)
                expiration_str = expiration_jst.strftime("%Y-%m-%d %H:%M:%S %Z")
                ui.info(f"[{profile}] Credentials will expire {expiration_str}")

        except FileNotFoundError:
            ui.error("AWS設定ファイルが見つかりません")
            if debug:
                import traceback

                traceback.print_exc()
            sys.exit(1)
        except KeyError:
            ui.error(f"プロファイル '{profile}' が見つかりません")
            if debug:
                import traceback

                traceback.print_exc()
            sys.exit(1)
        except RuntimeError as e:
            ui.error(str(e))
            if debug:
                import traceback

                traceback.print_exc()
            sys.exit(1)
        except Exception as e:
            ui.error(f"予期しないエラーが発生しました: {str(e)}")
            if debug:
                import traceback

                traceback.print_exc()
            sys.exit(1)
        return


if __name__ == "__main__":
    app()
