"""CLIレイヤー - コマンドライン引数の解析とバリデーション"""

import typer
from typing import Optional

app = typer.Typer()


@app.command()
def main(
    profile: Optional[str] = typer.Argument(None, help="AWSプロファイル名"),
    show_commands: bool = typer.Option(
        False, "--show-commands", "-s", help="exportコマンドを表示"
    ),
    unset: bool = typer.Option(False, "--unset", "-u", help="環境変数をクリア"),
    list_profiles: bool = typer.Option(
        False, "--list-profiles", "-l", help="プロファイル一覧を表示"
    ),
    init_shell: bool = typer.Option(
        False, "--init-shell", help="シェルラッパー関数を出力"
    ),
    region: Optional[str] = typer.Option(None, "--region", help="AWSリージョン"),
    session_name: Optional[str] = typer.Option(
        None, "--session-name", help="セッション名"
    ),
    role_duration: int = typer.Option(3600, "--role-duration", help="ロール期間（秒）"),
    mfa_token: Optional[str] = typer.Option(None, "--mfa-token", help="MFAトークン"),
    output_profile: Optional[str] = typer.Option(
        None, "--output-profile", "-o", help="出力プロファイル名"
    ),
    role_arn: Optional[str] = typer.Option(None, "--role-arn", help="ロールARN"),
    source_profile: Optional[str] = typer.Option(
        None, "--source-profile", help="ソースプロファイル"
    ),
    external_id: Optional[str] = typer.Option(None, "--external-id", help="外部ID"),
    config_file: Optional[str] = typer.Option(
        None, "--config-file", help="AWS設定ファイルパス"
    ),
    credentials_file: Optional[str] = typer.Option(
        None, "--credentials-file", help="AWS認証情報ファイルパス"
    ),
    info: bool = typer.Option(False, "--info", help="INFOレベルのログを表示"),
    debug: bool = typer.Option(False, "--debug", help="DEBUGレベルのログを表示"),
    version: bool = typer.Option(False, "--version", "-v", help="バージョン情報を表示"),
) -> None:
    """1Password連携によるAWS認証情報管理ツール"""
    # TODO: 実装は後続のタスクで行う
    pass


if __name__ == "__main__":
    app()
