# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

awsop is a CLI tool for managing AWS credentials via 1Password integration. It retrieves temporary AWS credentials using 1Password CLI (`op`) with Touch ID, eliminating the need to store long-term credentials in plaintext files.

## Development Commands

```bash
# Build
go build -o awsop ./cmd/awsop/

# Build with version
go build -ldflags "-X github.com/sakai-classmethod/awsop/internal/cli.Version=1.0.0" -o awsop ./cmd/awsop/

# Run tests
go test ./internal/...

# Run tests with verbose output
go test -v ./internal/...

# Run specific test
go test -v -run TestReadProfile ./internal/services/

# Run tests with coverage
go test -coverprofile=coverage.out ./internal/...
go tool cover -html=coverage.out

# Vet
go vet ./...

# Run the CLI (during development)
go run ./cmd/awsop/ --help
go run ./cmd/awsop/ --list-profiles
go run ./cmd/awsop/ production --debug
```

## Architecture

```
cmd/awsop/
└── main.go              # Entry point
internal/
├── cli/
│   └── root.go          # Cobra root command, all flags and main logic
├── app/
│   ├── types.go              # ProfileConfig, Credentials structs
│   ├── profile_manager.go    # Reads ~/.aws/config profiles
│   ├── credentials_manager.go # Cache check, AssumeRole, export/unset formatting
│   └── console_manager.go    # Console URL generation, browser launch
├── services/
│   ├── aws_config.go         # AWSConfigParser - parses ~/.aws/config (INI)
│   ├── aws_sts.go            # STSClient - aws-sdk-go-v2 STS wrapper
│   ├── onepassword.go        # OnePasswordClient - op CLI wrapper
│   ├── console_service.go    # Federation endpoint, service URL mapping
│   └── credentials_writer.go # Writes to ~/.aws/credentials
├── ui/
│   └── console.go     # ConsoleUI - ANSI colored stderr output (spinner, status)
└── shell/
    └── wrapper.go     # Generates zsh wrapper function for eval
```

### Key Design Patterns

- CLI layer (`internal/cli/`) handles argument parsing and error handling via cobra
- Application layer (`internal/app/`) orchestrates business logic
- Services layer (`internal/services/`) handles external integrations (1Password, AWS, filesystem)
- UI layer (`internal/ui/`) outputs status messages to stderr (keeps stdout clean for `eval`)

### Output Convention

- `stdout`: export/unset commands only (for shell `eval`)
- `stderr`: all user feedback (spinner, success/error messages)

## Test Structure

```
internal/
├── services/
│   ├── aws_config_test.go
│   ├── console_service_test.go
│   ├── credentials_writer_test.go
│   └── onepassword_test.go
└── app/
    ├── credentials_manager_test.go
    └── profile_manager_test.go
```

## Key Dependencies

- `github.com/spf13/cobra`: CLI framework
- `github.com/aws/aws-sdk-go-v2`: AWS SDK (STS only)
- `gopkg.in/ini.v1`: INI file parsing for AWS config/credentials

## Important Notes

- This tool requires 1Password CLI (`op`) to be installed and signed in
- The shell wrapper (`--init-shell`) must be added to `.zshrc` for `eval` to work
- Protected profiles in `~/.aws/credentials` require `manager = awsop` to be overwritten
- Version is injected via `-ldflags` at build time; defaults to `dev`
