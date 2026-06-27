package app

import (
	"strings"
	"testing"
	"time"
)

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
