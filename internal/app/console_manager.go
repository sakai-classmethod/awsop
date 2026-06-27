package app

import (
	"os/exec"

	"github.com/sakai-classmethod/awsop/internal/services"
)

// ConsoleManager orchestrates AWS Console URL generation and browser launching.
type ConsoleManager struct {
	consoleService *services.ConsoleService
}

// NewConsoleManager creates a new ConsoleManager with a ConsoleService.
func NewConsoleManager() *ConsoleManager {
	return &ConsoleManager{
		consoleService: services.NewConsoleService(),
	}
}

// OpenConsole generates a federated AWS Console URL and optionally opens it in the browser.
// It returns the generated URL or an error.
func (m *ConsoleManager) OpenConsole(credentials *Credentials, service string, openBrowser bool) (string, error) {
	if service == "" {
		service = "console"
	}

	amazonDomain := m.consoleService.GetAmazonDomain(credentials.Region)

	signinToken, err := m.consoleService.GetSigninToken(
		credentials.AccessKeyID,
		credentials.SecretAccessKey,
		credentials.SessionToken,
		amazonDomain,
	)
	if err != nil {
		return "", err
	}

	destinationURL := m.consoleService.BuildDestinationURL(service, credentials.Region, amazonDomain)
	consoleURL := m.consoleService.GenerateConsoleURL(signinToken, destinationURL, amazonDomain)

	if openBrowser {
		_ = exec.Command("open", consoleURL).Start()
	}

	return consoleURL, nil
}
