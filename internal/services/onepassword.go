package services

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"strings"
)

// OnePasswordClient wraps the 1Password CLI (op) for AWS credential retrieval.
type OnePasswordClient struct{}

// NewOnePasswordClient creates a new OnePasswordClient.
func NewOnePasswordClient() *OnePasswordClient {
	return &OnePasswordClient{}
}

// CheckAvailability returns true if the "op" command exists in PATH.
func (c *OnePasswordClient) CheckAvailability() bool {
	_, err := exec.LookPath("op")
	return err == nil
}

// envVarsToRemove lists the environment variables that must be stripped
// before invoking the op plugin so they do not leak into the subprocess.
var envVarsToRemove = map[string]struct{}{
	"AWS_ACCESS_KEY_ID":     {},
	"AWS_SECRET_ACCESS_KEY": {},
	"AWS_SESSION_TOKEN":     {},
	"AWS_DEFAULT_REGION":    {},
	"AWS_REGION":            {},
	"AWSOP_PROFILE":         {},
	"AWSOP_EXPIRATION":      {},
}

// RunAWSCommand executes an AWS CLI command through the 1Password plugin and
// returns the parsed JSON output.
func (c *OnePasswordClient) RunAWSCommand(command []string) (map[string]interface{}, error) {
	args := append([]string{"plugin", "run", "--", "aws"}, command...)
	cmd := exec.Command("op", args...)

	// Build a filtered copy of the environment.
	env := make([]string, 0, len(os.Environ()))
	for _, e := range os.Environ() {
		key, _, _ := strings.Cut(e, "=")
		if _, remove := envVarsToRemove[key]; !remove {
			env = append(env, e)
		}
	}
	cmd.Env = env

	var stdoutBuf, stderrBuf strings.Builder
	cmd.Stdout = &stdoutBuf
	cmd.Stderr = &stderrBuf

	if err := cmd.Run(); err != nil {
		return nil, fmt.Errorf("op command failed: %w\n%s", err, stderrBuf.String())
	}

	var result map[string]interface{}
	if err := json.Unmarshal([]byte(stdoutBuf.String()), &result); err != nil {
		return nil, fmt.Errorf("failed to parse JSON output: %w", err)
	}

	return result, nil
}
