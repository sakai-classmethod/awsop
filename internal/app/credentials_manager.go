package app

import (
	"fmt"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/sakai-classmethod/awsop/internal/services"
)

// OnePasswordClientAPI defines the 1Password operations used by the manager.
type OnePasswordClientAPI interface {
	CheckAvailability() bool
	RunAWSCommand([]string) (map[string]interface{}, error)
	GetItemCredentials(item, vault string) (string, string, error)
	GetItemOTP(item, vault string) (string, error)
}

// STSClientAPI defines the STS operation used by the manager.
type STSClientAPI interface {
	AssumeRole(roleARN, roleSessionName string, durationSeconds int32, externalID, mfaSerial, mfaToken string) (map[string]interface{}, error)
}

// AssumeRoleParams contains all inputs used to select and execute an
// AssumeRole credential path.
type AssumeRoleParams struct {
	RoleARN       string
	SessionName   string
	Duration      int
	Region        string
	Profile       string
	ExternalID    string
	MFASerial     string
	MFAToken      string
	SourceProfile string
	OpItem        string
	OpVault       string
}

// CredentialsManager orchestrates credential retrieval via 1Password or STS.
type CredentialsManager struct {
	OnePasswordClient OnePasswordClientAPI
	STSClient         STSClientAPI

	newSTSClient                      func(region string) (STSClientAPI, error)
	newSTSClientWithSharedProfile     func(profileName, region string) (STSClientAPI, error)
	newSTSClientWithStaticCredentials func(accessKeyID, secretAccessKey, region string) (STSClientAPI, error)
}

// NewCredentialsManager creates a CredentialsManager with a OnePasswordClient.
// STSClient is nil and created lazily when needed for MFA path.
func NewCredentialsManager() *CredentialsManager {
	return &CredentialsManager{
		OnePasswordClient: services.NewOnePasswordClient(),
		newSTSClient: func(region string) (STSClientAPI, error) {
			return services.NewSTSClient(region)
		},
		newSTSClientWithSharedProfile: func(profileName, region string) (STSClientAPI, error) {
			return services.NewSTSClientWithSharedProfile(profileName, region)
		},
		newSTSClientWithStaticCredentials: func(accessKeyID, secretAccessKey, region string) (STSClientAPI, error) {
			return services.NewSTSClientWithStaticCredentials(accessKeyID, secretAccessKey, region)
		},
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

// AssumeRole obtains temporary credentials by assuming an IAM role through the
// path selected from params.
func (m *CredentialsManager) AssumeRole(params AssumeRoleParams) (*Credentials, error) {
	var response map[string]interface{}
	var err error

	switch {
	case params.MFAToken != "":
		if params.MFASerial == "" {
			return nil, fmt.Errorf("プロファイルに mfa_serial が定義されていません")
		}

		stsClient := m.STSClient
		if stsClient == nil {
			if params.SourceProfile != "" {
				stsClient, err = m.createSTSClientWithSharedProfile(params.SourceProfile, params.Region)
			} else {
				stsClient, err = m.createSTSClient(params.Region)
			}
			if err != nil {
				return nil, fmt.Errorf("STSクライアントの作成に失敗しました: %w", err)
			}
		}
		response, err = stsClient.AssumeRole(
			params.RoleARN,
			params.SessionName,
			int32(params.Duration),
			params.ExternalID,
			params.MFASerial,
			params.MFAToken,
		)
		if err != nil {
			return nil, err
		}

	case params.Duration > 3600 && params.MFASerial != "":
		if params.OpItem == "" {
			return nil, fmt.Errorf("MFA セッション（role chaining）経由では 3600 秒が上限です。~/.aws/config のプロファイルに awsop_op_item を設定するか、-m で MFA トークンを指定してください")
		}
		if !m.OnePasswordClient.CheckAvailability() {
			return nil, fmt.Errorf("1Password CLIが見つかりません。opコマンドをインストールしてください")
		}

		accessKeyID, secretAccessKey, credentialsErr := m.OnePasswordClient.GetItemCredentials(params.OpItem, params.OpVault)
		if credentialsErr != nil {
			return nil, credentialsErr
		}
		otp, otpErr := m.OnePasswordClient.GetItemOTP(params.OpItem, params.OpVault)
		if otpErr != nil {
			return nil, otpErr
		}

		stsClient, clientErr := m.createSTSClientWithStaticCredentials(accessKeyID, secretAccessKey, params.Region)
		if clientErr != nil {
			return nil, fmt.Errorf("STSクライアントの作成に失敗しました: %w", clientErr)
		}
		response, err = stsClient.AssumeRole(
			params.RoleARN,
			params.SessionName,
			int32(params.Duration),
			params.ExternalID,
			params.MFASerial,
			otp,
		)
		if err != nil {
			return nil, err
		}

	default:
		if !m.OnePasswordClient.CheckAvailability() {
			return nil, fmt.Errorf("1Password CLIが見つかりません。opコマンドをインストールしてください")
		}

		command := []string{
			"sts", "assume-role",
			"--role-arn", params.RoleARN,
			"--role-session-name", params.SessionName,
			"--duration-seconds", strconv.Itoa(params.Duration),
		}
		if params.ExternalID != "" {
			command = append(command, "--external-id", params.ExternalID)
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
	resolvedRegion := params.Region
	if resolvedRegion == "" {
		resolvedRegion = "ap-northeast-1"
	}

	return &Credentials{
		AccessKeyID:     accessKeyID,
		SecretAccessKey: secretAccessKey,
		SessionToken:    sessionToken,
		Expiration:      expiration,
		Region:          resolvedRegion,
		Profile:         params.Profile,
	}, nil
}

func (m *CredentialsManager) createSTSClient(region string) (STSClientAPI, error) {
	if m.newSTSClient != nil {
		return m.newSTSClient(region)
	}
	return services.NewSTSClient(region)
}

func (m *CredentialsManager) createSTSClientWithSharedProfile(profileName, region string) (STSClientAPI, error) {
	if m.newSTSClientWithSharedProfile != nil {
		return m.newSTSClientWithSharedProfile(profileName, region)
	}
	return services.NewSTSClientWithSharedProfile(profileName, region)
}

func (m *CredentialsManager) createSTSClientWithStaticCredentials(accessKeyID, secretAccessKey, region string) (STSClientAPI, error) {
	if m.newSTSClientWithStaticCredentials != nil {
		return m.newSTSClientWithStaticCredentials(accessKeyID, secretAccessKey, region)
	}
	return services.NewSTSClientWithStaticCredentials(accessKeyID, secretAccessKey, region)
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
