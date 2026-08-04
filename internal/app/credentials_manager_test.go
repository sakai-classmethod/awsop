package app

import (
	"fmt"
	"strings"
	"testing"
	"time"
)

type mockOnePasswordClient struct {
	available           bool
	runAWSCommandCalls  int
	getCredentialsCalls int
	getOTPCalls         int
	accessKeyID         string
	secretAccessKey     string
	otp                 string
	credentialItem      string
	credentialVault     string
	otpItem             string
	otpVault            string
}

func (m *mockOnePasswordClient) CheckAvailability() bool { return m.available }

func (m *mockOnePasswordClient) RunAWSCommand(_ []string) (map[string]interface{}, error) {
	m.runAWSCommandCalls++
	return testAssumeRoleResponse(), nil
}

func (m *mockOnePasswordClient) GetItemCredentials(item, vault string) (string, string, error) {
	m.getCredentialsCalls++
	m.credentialItem, m.credentialVault = item, vault
	return m.accessKeyID, m.secretAccessKey, nil
}

func (m *mockOnePasswordClient) GetItemOTP(item, vault string) (string, error) {
	m.getOTPCalls++
	m.otpItem, m.otpVault = item, vault
	return m.otp, nil
}

type mockSTSClient struct {
	calls      int
	mfaSerial  string
	mfaToken   string
	externalID string
}

func (m *mockSTSClient) AssumeRole(_, _ string, _ int32, externalID, mfaSerial, mfaToken string) (map[string]interface{}, error) {
	m.calls++
	m.externalID = externalID
	m.mfaSerial = mfaSerial
	m.mfaToken = mfaToken
	return testAssumeRoleResponse(), nil
}

func testAssumeRoleResponse() map[string]interface{} {
	return map[string]interface{}{
		"Credentials": map[string]interface{}{
			"AccessKeyId":     "temporary-access-key",
			"SecretAccessKey": "temporary-secret-key",
			"SessionToken":    "temporary-session-token",
			"Expiration":      "2026-08-04T12:00:00Z",
		},
	}
}

func TestFormatExportCommands(t *testing.T) {
	m := &CredentialsManager{}
	expiration := time.Date(2026, 6, 27, 12, 0, 0, 0, time.UTC)
	creds := &Credentials{
		AccessKeyID:     "AKIAIOSFODNN7EXAMPLE",
		SecretAccessKey: "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
		SessionToken:    "FwoGZXIvYXdzEBYaDH+EXAMPLETOKEN",
		Expiration:      expiration,
		Region:          "ap-northeast-1",
		Profile:         "production",
	}

	result := m.FormatExportCommands(creds)
	lines := strings.Split(result, "\n")

	if len(lines) != 7 {
		t.Fatalf("expected 7 lines, got %d", len(lines))
	}

	expected := []string{
		"export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE",
		"export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
		"export AWS_SESSION_TOKEN=FwoGZXIvYXdzEBYaDH+EXAMPLETOKEN",
		"export AWS_REGION=ap-northeast-1",
		"export AWS_DEFAULT_REGION=ap-northeast-1",
		"export AWSOP_PROFILE=production",
		"export AWSOP_EXPIRATION=" + expiration.Format(time.RFC3339),
	}

	for i, want := range expected {
		if lines[i] != want {
			t.Errorf("line %d: got %q, want %q", i, lines[i], want)
		}
	}
}

func TestFormatUnsetCommands(t *testing.T) {
	m := &CredentialsManager{}
	result := m.FormatUnsetCommands()
	lines := strings.Split(result, "\n")

	if len(lines) != 7 {
		t.Fatalf("expected 7 lines, got %d", len(lines))
	}

	expected := []string{
		"unset AWS_ACCESS_KEY_ID",
		"unset AWS_SECRET_ACCESS_KEY",
		"unset AWS_SESSION_TOKEN",
		"unset AWS_REGION",
		"unset AWS_DEFAULT_REGION",
		"unset AWSOP_PROFILE",
		"unset AWSOP_EXPIRATION",
	}

	for i, want := range expected {
		if lines[i] != want {
			t.Errorf("line %d: got %q, want %q", i, lines[i], want)
		}
	}
}

func TestGetCachedCredentials_ValidCache(t *testing.T) {
	expiration := time.Now().Add(1 * time.Hour).UTC().Format(time.RFC3339)

	t.Setenv("AWSOP_PROFILE", "myprofile")
	t.Setenv("AWS_ACCESS_KEY_ID", "AKIAIOSFODNN7EXAMPLE")
	t.Setenv("AWS_SECRET_ACCESS_KEY", "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY")
	t.Setenv("AWS_SESSION_TOKEN", "FwoGZXIvYXdzEBYaDH+EXAMPLETOKEN")
	t.Setenv("AWSOP_EXPIRATION", expiration)
	t.Setenv("AWS_REGION", "us-west-2")

	m := &CredentialsManager{}
	creds := m.GetCachedCredentials("myprofile", "", 5*time.Minute)

	if creds == nil {
		t.Fatal("expected non-nil credentials, got nil")
	}
	if creds.AccessKeyID != "AKIAIOSFODNN7EXAMPLE" {
		t.Errorf("AccessKeyID: got %q, want %q", creds.AccessKeyID, "AKIAIOSFODNN7EXAMPLE")
	}
	if creds.SecretAccessKey != "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY" {
		t.Errorf("SecretAccessKey: got %q, want %q", creds.SecretAccessKey, "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY")
	}
	if creds.SessionToken != "FwoGZXIvYXdzEBYaDH+EXAMPLETOKEN" {
		t.Errorf("SessionToken: got %q, want %q", creds.SessionToken, "FwoGZXIvYXdzEBYaDH+EXAMPLETOKEN")
	}
	if creds.Region != "us-west-2" {
		t.Errorf("Region: got %q, want %q", creds.Region, "us-west-2")
	}
	if creds.Profile != "myprofile" {
		t.Errorf("Profile: got %q, want %q", creds.Profile, "myprofile")
	}
}

func TestGetCachedCredentials_NoProfile(t *testing.T) {
	// AWSOP_PROFILE is not set (t.Setenv not called for it)
	t.Setenv("AWS_ACCESS_KEY_ID", "AKIAIOSFODNN7EXAMPLE")
	t.Setenv("AWS_SECRET_ACCESS_KEY", "secret")
	t.Setenv("AWS_SESSION_TOKEN", "token")
	t.Setenv("AWSOP_EXPIRATION", time.Now().Add(1*time.Hour).UTC().Format(time.RFC3339))

	m := &CredentialsManager{}
	creds := m.GetCachedCredentials("myprofile", "", 5*time.Minute)

	if creds != nil {
		t.Fatalf("expected nil credentials when AWSOP_PROFILE is missing, got %+v", creds)
	}
}

func TestGetCachedCredentials_MismatchProfile(t *testing.T) {
	t.Setenv("AWSOP_PROFILE", "other-profile")
	t.Setenv("AWS_ACCESS_KEY_ID", "AKIAIOSFODNN7EXAMPLE")
	t.Setenv("AWS_SECRET_ACCESS_KEY", "secret")
	t.Setenv("AWS_SESSION_TOKEN", "token")
	t.Setenv("AWSOP_EXPIRATION", time.Now().Add(1*time.Hour).UTC().Format(time.RFC3339))

	m := &CredentialsManager{}
	creds := m.GetCachedCredentials("myprofile", "", 5*time.Minute)

	if creds != nil {
		t.Fatalf("expected nil credentials when profile mismatches, got %+v", creds)
	}
}

func TestGetCachedCredentials_MissingVars(t *testing.T) {
	tests := []struct {
		name    string
		envVars map[string]string
	}{
		{
			name: "missing AWS_ACCESS_KEY_ID",
			envVars: map[string]string{
				"AWSOP_PROFILE":         "myprofile",
				"AWS_SECRET_ACCESS_KEY": "secret",
				"AWS_SESSION_TOKEN":     "token",
				"AWSOP_EXPIRATION":      time.Now().Add(1 * time.Hour).UTC().Format(time.RFC3339),
			},
		},
		{
			name: "missing AWS_SECRET_ACCESS_KEY",
			envVars: map[string]string{
				"AWSOP_PROFILE":     "myprofile",
				"AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE",
				"AWS_SESSION_TOKEN": "token",
				"AWSOP_EXPIRATION":  time.Now().Add(1 * time.Hour).UTC().Format(time.RFC3339),
			},
		},
		{
			name: "missing AWS_SESSION_TOKEN",
			envVars: map[string]string{
				"AWSOP_PROFILE":         "myprofile",
				"AWS_ACCESS_KEY_ID":     "AKIAIOSFODNN7EXAMPLE",
				"AWS_SECRET_ACCESS_KEY": "secret",
				"AWSOP_EXPIRATION":      time.Now().Add(1 * time.Hour).UTC().Format(time.RFC3339),
			},
		},
		{
			name: "missing AWSOP_EXPIRATION",
			envVars: map[string]string{
				"AWSOP_PROFILE":         "myprofile",
				"AWS_ACCESS_KEY_ID":     "AKIAIOSFODNN7EXAMPLE",
				"AWS_SECRET_ACCESS_KEY": "secret",
				"AWS_SESSION_TOKEN":     "token",
			},
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			for k, v := range tc.envVars {
				t.Setenv(k, v)
			}

			m := &CredentialsManager{}
			creds := m.GetCachedCredentials("myprofile", "", 5*time.Minute)

			if creds != nil {
				t.Fatalf("expected nil credentials when %s, got %+v", tc.name, creds)
			}
		})
	}
}

func TestGetCachedCredentials_Expired(t *testing.T) {
	// Set expiration to 2 minutes from now, but require 5 minutes TTL
	expiration := time.Now().Add(2 * time.Minute).UTC().Format(time.RFC3339)

	t.Setenv("AWSOP_PROFILE", "myprofile")
	t.Setenv("AWS_ACCESS_KEY_ID", "AKIAIOSFODNN7EXAMPLE")
	t.Setenv("AWS_SECRET_ACCESS_KEY", "secret")
	t.Setenv("AWS_SESSION_TOKEN", "token")
	t.Setenv("AWSOP_EXPIRATION", expiration)

	m := &CredentialsManager{}
	creds := m.GetCachedCredentials("myprofile", "", 5*time.Minute)

	if creds != nil {
		t.Fatalf("expected nil credentials when expired (TTL insufficient), got %+v", creds)
	}
}

func TestAssumeRole_MFATokenUsesSharedProfileDirectPath(t *testing.T) {
	onePassword := &mockOnePasswordClient{available: true}
	stsClient := &mockSTSClient{}
	var gotProfile, gotRegion string
	manager := NewCredentialsManager()
	manager.OnePasswordClient = onePassword
	manager.newSTSClientWithSharedProfile = func(profileName, region string) (STSClientAPI, error) {
		gotProfile, gotRegion = profileName, region
		return stsClient, nil
	}

	_, err := manager.AssumeRole(AssumeRoleParams{
		RoleARN:       "arn:aws:iam::123456789012:role/Admin",
		SessionName:   "awsop-test",
		Duration:      7200,
		Region:        "ap-northeast-1",
		Profile:       "production",
		ExternalID:    "external-id",
		MFASerial:     "arn:aws:iam::123456789012:mfa/user",
		MFAToken:      "123456",
		SourceProfile: "base",
	})
	if err != nil {
		t.Fatalf("AssumeRole returned error: %v", err)
	}
	if gotProfile != "base" || gotRegion != "ap-northeast-1" {
		t.Errorf("shared profile factory args = (%q, %q)", gotProfile, gotRegion)
	}
	if stsClient.mfaSerial != "arn:aws:iam::123456789012:mfa/user" || stsClient.mfaToken != "123456" {
		t.Errorf("MFA args = (%q, %q)", stsClient.mfaSerial, stsClient.mfaToken)
	}
	if stsClient.externalID != "external-id" {
		t.Errorf("external ID = %q", stsClient.externalID)
	}
	if onePassword.runAWSCommandCalls != 0 {
		t.Fatal("1Password plugin path was called")
	}
}

func TestAssumeRole_MFATokenRequiresMFASerial(t *testing.T) {
	manager := NewCredentialsManager()
	_, err := manager.AssumeRole(AssumeRoleParams{
		RoleARN:     "arn:aws:iam::123456789012:role/Admin",
		SessionName: "awsop-test",
		Duration:    3600,
		MFAToken:    "123456",
	})
	if err == nil || !strings.Contains(err.Error(), "プロファイルに mfa_serial が定義されていません") {
		t.Fatalf("error = %v", err)
	}
}

func TestAssumeRole_MFATokenWithoutSourceProfileUsesDefaultDirectPath(t *testing.T) {
	stsClient := &mockSTSClient{}
	var gotRegion string
	manager := NewCredentialsManager()
	manager.newSTSClient = func(region string) (STSClientAPI, error) {
		gotRegion = region
		return stsClient, nil
	}

	_, err := manager.AssumeRole(AssumeRoleParams{
		RoleARN:     "arn:aws:iam::123456789012:role/Admin",
		SessionName: "awsop-test",
		Duration:    3600,
		Region:      "us-west-2",
		MFASerial:   "arn:aws:iam::123456789012:mfa/user",
		MFAToken:    "123456",
	})
	if err != nil {
		t.Fatalf("AssumeRole returned error: %v", err)
	}
	if gotRegion != "us-west-2" || stsClient.calls != 1 {
		t.Errorf("default STS path = region:%q calls:%d", gotRegion, stsClient.calls)
	}
}

func TestAssumeRole_LongDurationWithMFANoItemFailsFast(t *testing.T) {
	onePassword := &mockOnePasswordClient{available: true}
	manager := NewCredentialsManager()
	manager.OnePasswordClient = onePassword
	manager.newSTSClient = func(_ string) (STSClientAPI, error) {
		return nil, fmt.Errorf("must not be called")
	}

	_, err := manager.AssumeRole(AssumeRoleParams{
		RoleARN:     "arn:aws:iam::123456789012:role/Admin",
		SessionName: "awsop-test",
		Duration:    7200,
		MFASerial:   "arn:aws:iam::123456789012:mfa/user",
	})
	if err == nil || !strings.Contains(err.Error(), "3600 秒が上限") || !strings.Contains(err.Error(), "awsop_op_item") {
		t.Fatalf("error = %v", err)
	}
	if onePassword.runAWSCommandCalls != 0 || onePassword.getCredentialsCalls != 0 || onePassword.getOTPCalls != 0 {
		t.Fatal("1Password was called before fail-fast error")
	}
}

func TestAssumeRole_LongDurationWithItemUsesStaticCredentials(t *testing.T) {
	onePassword := &mockOnePasswordClient{
		available:       true,
		accessKeyID:     "long-term-access-key",
		secretAccessKey: "long-term-secret-key",
		otp:             "654321",
	}
	stsClient := &mockSTSClient{}
	var gotAccessKeyID, gotSecretAccessKey, gotRegion string
	manager := NewCredentialsManager()
	manager.OnePasswordClient = onePassword
	manager.newSTSClientWithStaticCredentials = func(accessKeyID, secretAccessKey, region string) (STSClientAPI, error) {
		gotAccessKeyID, gotSecretAccessKey, gotRegion = accessKeyID, secretAccessKey, region
		return stsClient, nil
	}

	_, err := manager.AssumeRole(AssumeRoleParams{
		RoleARN:     "arn:aws:iam::123456789012:role/Admin",
		SessionName: "awsop-test",
		Duration:    7200,
		Region:      "ap-northeast-1",
		MFASerial:   "arn:aws:iam::123456789012:mfa/user",
		OpItem:      "AWS production",
		OpVault:     "Engineering",
	})
	if err != nil {
		t.Fatalf("AssumeRole returned error: %v", err)
	}
	if gotAccessKeyID != "long-term-access-key" || gotSecretAccessKey != "long-term-secret-key" || gotRegion != "ap-northeast-1" {
		t.Errorf("static factory args = (%q, %q, %q)", gotAccessKeyID, gotSecretAccessKey, gotRegion)
	}
	if stsClient.mfaToken != "654321" {
		t.Errorf("MFA token = %q", stsClient.mfaToken)
	}
	if onePassword.getCredentialsCalls != 1 || onePassword.getOTPCalls != 1 || onePassword.runAWSCommandCalls != 0 {
		t.Errorf("1Password calls = credentials:%d otp:%d plugin:%d", onePassword.getCredentialsCalls, onePassword.getOTPCalls, onePassword.runAWSCommandCalls)
	}
	if onePassword.credentialItem != "AWS production" || onePassword.credentialVault != "Engineering" || onePassword.otpItem != "AWS production" || onePassword.otpVault != "Engineering" {
		t.Errorf("1Password item args = credentials:(%q, %q) otp:(%q, %q)", onePassword.credentialItem, onePassword.credentialVault, onePassword.otpItem, onePassword.otpVault)
	}
}

func TestAssumeRole_DefaultDurationKeepsPluginPath(t *testing.T) {
	onePassword := &mockOnePasswordClient{available: true}
	manager := NewCredentialsManager()
	manager.OnePasswordClient = onePassword

	_, err := manager.AssumeRole(AssumeRoleParams{
		RoleARN:     "arn:aws:iam::123456789012:role/Admin",
		SessionName: "awsop-test",
		Duration:    3600,
		MFASerial:   "arn:aws:iam::123456789012:mfa/user",
	})
	if err != nil {
		t.Fatalf("AssumeRole returned error: %v", err)
	}
	if onePassword.runAWSCommandCalls != 1 || onePassword.getCredentialsCalls != 0 || onePassword.getOTPCalls != 0 {
		t.Errorf("1Password calls = credentials:%d otp:%d plugin:%d", onePassword.getCredentialsCalls, onePassword.getOTPCalls, onePassword.runAWSCommandCalls)
	}
}
