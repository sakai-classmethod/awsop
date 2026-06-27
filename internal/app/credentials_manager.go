package app

import (
	"fmt"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/sakai-classmethod/awsop/internal/services"
)

// CredentialsManager orchestrates credential retrieval via 1Password or STS.
type CredentialsManager struct {
	OnePasswordClient *services.OnePasswordClient
	STSClient         *services.STSClient
}

// NewCredentialsManager creates a CredentialsManager with a OnePasswordClient.
// STSClient is nil and created lazily when needed for MFA path.
func NewCredentialsManager() *CredentialsManager {
	return &CredentialsManager{
		OnePasswordClient: services.NewOnePasswordClient(),
	}
}

// GetCachedCredentials checks environment variables for cached credentials
// that are still valid for at least minTTL. Returns nil if not found or expired.
func (m *CredentialsManager) GetCachedCredentials(profile string, region string, minTTL time.Duration) *Credentials {
	if minTTL == 0 {
		minTTL = 5 * time.Minute
	}

	// AWSOP_PROFILE must match profile
	cachedProfile := os.Getenv("AWSOP_PROFILE")
	if cachedProfile == "" || cachedProfile != profile {
		return nil
	}

	// All required environment variables must be set
	accessKeyID := os.Getenv("AWS_ACCESS_KEY_ID")
	secretAccessKey := os.Getenv("AWS_SECRET_ACCESS_KEY")
	sessionToken := os.Getenv("AWS_SESSION_TOKEN")
	expirationStr := os.Getenv("AWSOP_EXPIRATION")

	if accessKeyID == "" || secretAccessKey == "" || sessionToken == "" || expirationStr == "" {
		return nil
	}

	// Parse expiration as RFC3339/ISO8601
	expiration, err := time.Parse(time.RFC3339, expirationStr)
	if err != nil {
		return nil
	}

	// Check if expired (expiration <= now + minTTL)
	if !expiration.After(time.Now().Add(minTTL)) {
		return nil
	}

	// Determine region: param > AWS_REGION > AWS_DEFAULT_REGION > default
	resolvedRegion := region
	if resolvedRegion == "" {
		resolvedRegion = os.Getenv("AWS_REGION")
	}
	if resolvedRegion == "" {
		resolvedRegion = os.Getenv("AWS_DEFAULT_REGION")
	}
	if resolvedRegion == "" {
		resolvedRegion = "ap-northeast-1"
	}

	return &Credentials{
		AccessKeyID:     accessKeyID,
		SecretAccessKey: secretAccessKey,
		SessionToken:    sessionToken,
		Expiration:      expiration,
		Region:          resolvedRegion,
		Profile:         profile,
	}
}

// AssumeRole obtains temporary credentials by assuming an IAM role.
// If mfaToken is provided, uses STS directly; otherwise uses 1Password CLI.
func (m *CredentialsManager) AssumeRole(roleARN, sessionName string, duration int, region, profile string, externalID, mfaToken string) (*Credentials, error) {
	var response map[string]interface{}
	var err error

	if mfaToken != "" {
		// MFA path: use STS directly
		if m.STSClient == nil {
			stsClient, stsErr := services.NewSTSClient()
			if stsErr != nil {
				return nil, fmt.Errorf("STSクライアントの作成に失敗しました: %w", stsErr)
			}
			m.STSClient = stsClient
		}
		response, err = m.STSClient.AssumeRole(roleARN, sessionName, int32(duration), externalID)
		if err != nil {
			return nil, err
		}
	} else {
		// 1Password path
		if !m.OnePasswordClient.CheckAvailability() {
			return nil, fmt.Errorf("1Password CLIが見つかりません。opコマンドをインストールしてください")
		}

		command := []string{
			"sts", "assume-role",
			"--role-arn", roleARN,
			"--role-session-name", sessionName,
			"--duration-seconds", strconv.Itoa(duration),
		}
		if externalID != "" {
			command = append(command, "--external-id", externalID)
		}

		response, err = m.OnePasswordClient.RunAWSCommand(command)
		if err != nil {
			return nil, err
		}
	}

	// Extract credentials from response
	credsRaw, ok := response["Credentials"]
	if !ok {
		return nil, fmt.Errorf("レスポンスにCredentialsフィールドがありません")
	}

	credsMap, ok := credsRaw.(map[string]interface{})
	if !ok {
		return nil, fmt.Errorf("Credentialsフィールドの型が不正です")
	}

	accessKeyID, _ := credsMap["AccessKeyId"].(string)
	secretAccessKey, _ := credsMap["SecretAccessKey"].(string)
	sessionToken, _ := credsMap["SessionToken"].(string)

	// Parse Expiration (string in ISO 8601 format)
	var expiration time.Time
	switch v := credsMap["Expiration"].(type) {
	case string:
		parsed, parseErr := time.Parse(time.RFC3339, v)
		if parseErr != nil {
			return nil, fmt.Errorf("expiration の解析に失敗しました: %w", parseErr)
		}
		expiration = parsed
	default:
		return nil, fmt.Errorf("Expirationフィールドの型が不正です")
	}

	// Determine region
	resolvedRegion := region
	if resolvedRegion == "" {
		resolvedRegion = "ap-northeast-1"
	}

	return &Credentials{
		AccessKeyID:     accessKeyID,
		SecretAccessKey: secretAccessKey,
		SessionToken:    sessionToken,
		Expiration:      expiration,
		Region:          resolvedRegion,
		Profile:         profile,
	}, nil
}

// FormatExportCommands returns shell export commands for the given credentials.
func (m *CredentialsManager) FormatExportCommands(creds *Credentials) string {
	lines := []string{
		"export AWS_ACCESS_KEY_ID=" + creds.AccessKeyID,
		"export AWS_SECRET_ACCESS_KEY=" + creds.SecretAccessKey,
		"export AWS_SESSION_TOKEN=" + creds.SessionToken,
		"export AWS_REGION=" + creds.Region,
		"export AWS_DEFAULT_REGION=" + creds.Region,
		"export AWSOP_PROFILE=" + creds.Profile,
		"export AWSOP_EXPIRATION=" + creds.Expiration.Format(time.RFC3339),
	}
	return strings.Join(lines, "\n")
}

// FormatUnsetCommands returns shell unset commands to clear credential variables.
func (m *CredentialsManager) FormatUnsetCommands() string {
	lines := []string{
		"unset AWS_ACCESS_KEY_ID",
		"unset AWS_SECRET_ACCESS_KEY",
		"unset AWS_SESSION_TOKEN",
		"unset AWS_REGION",
		"unset AWS_DEFAULT_REGION",
		"unset AWSOP_PROFILE",
		"unset AWSOP_EXPIRATION",
	}
	return strings.Join(lines, "\n")
}
