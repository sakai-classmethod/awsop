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
    # ただし、--role-arnが指定されている場合は処理を続行
    if profile is None and not show_commands and not role_arn:
        print("使用方法: awsop [OPTIONS] [PROFILE]", file=sys.stderr)
        print("詳細は --help オプションを参照してください", file=sys.stderr)
        sys.exit(0)

    # プロファイル切り替え処理（タスク13, 15）
    if profile or role_arn:
        from awsop.app.credentials_manager import CredentialsManager
        from awsop.ui.console import ConsoleUI
        from awsop.services.credentials_writer import CredentialsWriter
        from awsop.services.onepassword import OnePasswordClient
        from datetime import datetime

        ui = ConsoleUI()

        # 1Password CLIの利用可能性をチェック（要件6.1, 6.2）
        # ただし、--mfa-tokenが指定されている場合はスキップ
        if not mfa_token:
            op_client = OnePasswordClient()
            if not op_client.check_availability():
                ui.error(
                    "1Password CLIが利用できません。opコマンドをインストールしてください。"
                )
                sys.exit(1)

        try:
            # ロール期間のバリデーション（要件4.4.3）
            if role_duration < 1 or role_duration > 43200:
                ui.error(
                    f"ロール期間は1から43200秒の範囲で指定してください（指定値: {role_duration}秒）"
                )
                sys.exit(1)

            # セッション名の決定（要件4.3.1, 4.3.2）
            if not session_name:
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                session_name = f"awsop-{timestamp}"

            # ロールARNと外部IDの決定
            effective_role_arn = None
            effective_external_id = external_id
            effective_region = region
            effective_profile = profile

            # --role-arnオプションが指定された場合（要件4.7.1）
            if role_arn:
                effective_role_arn = role_arn
                effective_profile = effective_profile or "direct-role"

                # --source-profileが指定された場合、そのプロファイルから設定を取得（要件4.7.3）
                if source_profile:
                    profile_manager = ProfileManager(config_file=config_file)
                    source_config = profile_manager.get_profile(source_profile)
                    # リージョンが指定されていない場合、ソースプロファイルのリージョンを使用
                    if not effective_region:
                        effective_region = source_config.region

            # プロファイルが指定された場合
            elif profile:
                # ProfileManagerを使用してプロファイル設定を取得（要件1.1）
                profile_manager = ProfileManager(config_file=config_file)
                profile_config = profile_manager.get_profile(profile)

                # role_arnが定義されているかチェック（要件1.2, 1.3）
                if not profile_config.role_arn:
                    ui.error(
                        f"プロファイル '{profile}' に role_arn が定義されていません"
                    )
                    sys.exit(1)

                effective_role_arn = profile_config.role_arn

                # リージョンの決定（要件4.2.1, 4.2.2, 4.2.3）
                # --region オプション > プロファイルのregion > デフォルト（ap-northeast-1）
                if not effective_region:
                    effective_region = profile_config.region

                # 外部IDの決定（プロファイルの設定 < コマンドラインオプション）
                if not effective_external_id:
                    effective_external_id = profile_config.external_id

            # リージョンのデフォルト値（要件4.2.3）
            if not effective_region:
                effective_region = "ap-northeast-1"

            # CredentialsManagerを使用して認証情報を取得
            credentials_manager = CredentialsManager()

            # スピナーを表示しながら認証情報を取得（要件8.1）
            with ui.spinner("1Password経由で認証情報を取得中..."):
                credentials = credentials_manager.assume_role(
                    role_arn=effective_role_arn,
                    session_name=session_name,
                    duration=role_duration,
                    region=effective_region,
                    profile=effective_profile,
                    external_id=effective_external_id,
                    mfa_token=mfa_token,
                )

            # --output-profileオプションが指定された場合、認証情報をファイルに書き込む（要件4.6.1）
            if output_profile:
                credentials_writer = CredentialsWriter(
                    credentials_file=credentials_file
                )

                try:
                    credentials_writer.write_profile(
                        profile_name=output_profile,
                        access_key_id=credentials.access_key_id,
                        secret_access_key=credentials.secret_access_key,
                        session_token=credentials.session_token,
                    )
                    ui.success(
                        f"認証情報をプロファイル '{output_profile}' に書き込みました"
                    )
                except ValueError as e:
                    # プロファイルが保護されている場合（要件4.6.2）
                    ui.error(str(e))
                    sys.exit(1)

            # 有効期限情報を常に表示（標準エラー出力）（要件1.1, 1.4）
            import zoneinfo

            jst = zoneinfo.ZoneInfo("Asia/Tokyo")
            expiration_jst = credentials.expiration.astimezone(jst)
            expiration_str = expiration_jst.strftime("%Y-%m-%d %H:%M:%S %Z")
            # Rich markupで角括弧をエスケープ（\[...] でリテラル表示）
            ui.info(f"\\[{effective_profile}] Credentials will expire {expiration_str}")

            # --show-commandsオプションが指定された場合のみ、exportコマンドを標準出力に出力（要件1.2, 1.3）
            if show_commands:
                export_commands = credentials_manager.format_export_commands(
                    credentials
                )
                print(export_commands)

        except FileNotFoundError as e:
            # 要件11.3: AWS設定ファイルの読み取りが失敗
            ui.error("AWS設定ファイルの読み取りに失敗しました")
            if debug:
                import traceback

                traceback.print_exc()
            sys.exit(1)
        except KeyError as e:
            # プロファイルが見つからない場合
            ui.error(f"プロファイル '{profile or source_profile}' が見つかりません")
            if debug:
                import traceback

                traceback.print_exc()
            sys.exit(1)
        except RuntimeError as e:
            # 要件11.1, 11.2: 1Password認証失敗、AssumeRole失敗など
            error_message = str(e)
            ui.error(error_message)
            if debug:
                import traceback

                traceback.print_exc()
            sys.exit(1)
        except ValueError as e:
            # バリデーションエラー（出力プロファイル保護など）
            ui.error(str(e))
            if debug:
                import traceback

                traceback.print_exc()
            sys.exit(1)
        except Exception as e:
            # その他の予期しないエラー
            ui.error(f"予期しないエラーが発生しました: {str(e)}")
            if debug:
                import traceback

                traceback.print_exc()
            sys.exit(1)
        return


if __name__ == "__main__":
    app()
