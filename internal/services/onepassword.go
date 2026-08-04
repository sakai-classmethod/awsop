package services

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"strings"
	"unicode"
)

// OnePasswordClient wraps the 1Password CLI (op) for AWS credential retrieval.
type OnePasswordClient struct {
	runCommand func(args ...string) ([]byte, error)
}

// NewOnePasswordClient creates a new OnePasswordClient.
func NewOnePasswordClient() *OnePasswordClient {
	return &OnePasswordClient{runCommand: runOPCommand}
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

// GetItemCredentials retrieves long-term AWS credentials directly from a
// 1Password item without invoking the AWS shell plugin.
func (c *OnePasswordClient) GetItemCredentials(item, vault string) (string, string, error) {
	args := []string{"item", "get", item, "--format", "json", "--reveal"}
	if vault != "" {
		args = append(args, "--vault", vault)
	}

	output, err := c.commandRunner()(args...)
	if err != nil {
		return "", "", fmt.Errorf("1Passwordアイテムから認証情報を取得できませんでした: %w", err)
	}

	var itemData struct {
		Fields []struct {
			Label string `json:"label"`
			Value string `json:"value"`
		} `json:"fields"`
	}
	if err := json.Unmarshal(output, &itemData); err != nil {
		return "", "", fmt.Errorf("1PasswordアイテムのJSONを解析できませんでした: %w", err)
	}

	var accessKeyID, secretAccessKey string
	labels := make([]string, 0, len(itemData.Fields))
	for _, field := range itemData.Fields {
		labels = append(labels, field.Label)
		switch normalizeItemFieldLabel(field.Label) {
		case "accesskeyid", "awsaccesskeyid":
			accessKeyID = field.Value
		case "secretaccesskey", "awssecretaccesskey":
			secretAccessKey = field.Value
		}
	}

	if accessKeyID == "" || secretAccessKey == "" {
		return "", "", fmt.Errorf("1PasswordアイテムにAWS長期認証情報のフィールドが見つかりません（存在するlabel: %s）", strings.Join(labels, ", "))
	}

	return accessKeyID, secretAccessKey, nil
}

// GetItemOTP retrieves the current one-time password directly from a
// 1Password item.
func (c *OnePasswordClient) GetItemOTP(item, vault string) (string, error) {
	args := []string{"item", "get", item, "--otp"}
	if vault != "" {
		args = append(args, "--vault", vault)
	}

	output, err := c.commandRunner()(args...)
	if err != nil {
		return "", fmt.Errorf("1PasswordアイテムからOTPを取得できませんでした: %w", err)
	}

	otp := strings.TrimSpace(string(output))
	if otp == "" {
		return "", fmt.Errorf("1PasswordアイテムのOTPが空です")
	}
	return otp, nil
}

func (c *OnePasswordClient) commandRunner() func(args ...string) ([]byte, error) {
	if c.runCommand != nil {
		return c.runCommand
	}
	return runOPCommand
}

func runOPCommand(args ...string) ([]byte, error) {
	cmd := exec.Command("op", args...)
	var stdoutBuf strings.Builder
	cmd.Stdout = &stdoutBuf
	if err := cmd.Run(); err != nil {
		return nil, fmt.Errorf("op command failed: %w", err)
	}
	return []byte(stdoutBuf.String()), nil
}

func normalizeItemFieldLabel(label string) string {
	return strings.Map(func(r rune) rune {
		if r == '_' || unicode.IsSpace(r) {
			return -1
		}
		return unicode.ToLower(r)
	}, label)
}
