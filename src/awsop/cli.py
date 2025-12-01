"""CLIレイヤー - コマンドライン引数の解析とバリデーション"""

import typer
from typing import Optional

app = typer.Typer(
    add_completion=False,  # 補完機能は--init-shellで提供
    rich_markup_mode="rich",
    help="AWS credentials manager with 1Password integration",
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
    region: Optional[str] = typer.Option(None, "--region", help="AWS region"),
    session_name: Optional[str] = typer.Option(
        None, "--session-name", help="AssumeRole session name"
    ),
    role_duration: int = typer.Option(
        3600,
        "--role-duration",
        help="Role duration in seconds (default: 3600)",
    ),
    mfa_token: Optional[str] = typer.Option(None, "--mfa-token", help="MFA token"),
    output_profile: Optional[str] = typer.Option(
        None, "--output-profile", "-o", help="Output profile name"
    ),
    role_arn: Optional[str] = typer.Option(
        None, "--role-arn", help="Role ARN to assume"
    ),
    source_profile: Optional[str] = typer.Option(
        None, "--source-profile", help="Source profile for credentials"
    ),
    external_id: Optional[str] = typer.Option(
        None, "--external-id", help="External ID for AssumeRole"
    ),
    config_file: Optional[str] = typer.Option(
        None, "--config-file", help="AWS config file path"
    ),
    credentials_file: Optional[str] = typer.Option(
        None, "--credentials-file", help="AWS credentials file path"
    ),
    info: bool = typer.Option(False, "--info", help="Show INFO level logs"),
    debug: bool = typer.Option(False, "--debug", help="Show DEBUG level logs"),
    version: bool = typer.Option(False, "--version", "-v", help="Show version"),
) -> None:
    """AWS credentials manager with 1Password integration"""
    # 実装は後続のタスクで行う
    pass


if __name__ == "__main__":
    app()
