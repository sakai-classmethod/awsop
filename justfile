# awsop development tasks

# Default recipe: show help
default:
    @just --list

# Build the binary
build:
    go build -o awsop ./cmd/awsop/

# Build with version tag
build-release version:
    go build -ldflags "-X github.com/sakai-classmethod/awsop/internal/cli.Version={{version}}" -o awsop ./cmd/awsop/

# Run all tests
test:
    go test ./internal/...

# Run tests with verbose output
test-v:
    go test -v ./internal/...

# Run tests with coverage report
test-cov:
    go test -coverprofile=coverage.out ./internal/...
    go tool cover -html=coverage.out -o coverage.html
    @echo "Coverage report: coverage.html"

# Run go vet
vet:
    go vet ./...

# Format code
fmt:
    gofmt -w cmd/ internal/

# Run all checks (vet + test)
check: vet test

# Install to $GOPATH/bin
install:
    go install ./cmd/awsop/

# Install with version
install-release version:
    go install -ldflags "-X github.com/sakai-classmethod/awsop/internal/cli.Version={{version}}" ./cmd/awsop/

# Clean build artifacts
clean:
    rm -f awsop coverage.out coverage.html
