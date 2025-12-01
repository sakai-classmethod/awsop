# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

awsop is a CLI tool for managing AWS credentials via 1Password integration. It retrieves temporary AWS credentials using 1Password CLI (`op`) with Touch ID, eliminating the need to store long-term credentials in plaintext files.

## Development Commands

```bash
# Install dependencies
uv sync

# Install as CLI tool in dev mode
uv tool install -e .

# Run tests
uv run pytest

# Run specific test file
uv run pytest tests/unit/test_onepassword.py

# Run specific test function
uv run pytest tests/unit/test_onepassword.py::test_check_availability

# Run tests with coverage
uv run pytest --cov=src --cov-report=html

# Lint and format
uv run ruff format src tests
uv run ruff check src tests
uv run ruff check --fix src tests

# Run the CLI
awsop --help
awsop --list-profiles
awsop production --debug
```

## Architecture

```
src/awsop/
├── cli.py              # CLI entry point (Typer app, option parsing)
├── logging.py          # Logging configuration
├── app/
│   ├── profile_manager.py     # ProfileConfig dataclass, reads ~/.aws/config
│   └── credentials_manager.py # Credentials dataclass, orchestrates assume-role
├── services/
│   ├── aws_config.py         # AWSConfigParser - parses ~/.aws/config
│   ├── aws_sts.py            # STSClient - boto3 STS wrapper
│   ├── onepassword.py        # OnePasswordClient - op CLI wrapper
│   └── credentials_writer.py # Writes to ~/.aws/credentials
├── shell/
│   └── wrapper.py     # Generates zsh wrapper function for eval
└── ui/
    └── console.py     # ConsoleUI - Rich-based stderr output (spinner, colors)
```

### Key Design Patterns

- CLI layer (`cli.py`) handles argument parsing and error handling
- Application layer (`app/`) orchestrates business logic
- Services layer (`services/`) handles external integrations (1Password, AWS, filesystem)
- UI layer (`ui/`) outputs status messages to stderr (keeps stdout clean for `eval`)

### Output Convention

- `stdout`: export/unset commands only (for shell `eval`)
- `stderr`: all user feedback (spinner, success/error messages via Rich)

## Test Structure

```
tests/
├── unit/           # Component tests with mocks
├── property/       # Hypothesis property-based tests
└── integration/    # End-to-end flow tests
```

## Key Dependencies

- `typer`: CLI framework
- `rich`: Terminal UI (spinner, colors)
- `boto3`: AWS SDK
- `hypothesis`: Property-based testing

## Important Notes

- This tool requires 1Password CLI (`op`) to be installed and signed in
- The shell wrapper (`--init-shell`) must be added to `.zshrc` for `eval` to work
- Protected profiles in `~/.aws/credentials` require `manager = awsop` to be overwritten
