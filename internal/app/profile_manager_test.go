package app

import (
	"os"
	"path/filepath"
	"testing"
)

func TestGetProfile_Success(t *testing.T) {
	dir := t.TempDir()
	configFile := filepath.Join(dir, "config")

	content := `[profile production]
role_arn = arn:aws:iam::123456789012:role/MyRole
region = ap-northeast-1
source_profile = default
external_id = ext-123
mfa_serial = arn:aws:iam::123456789012:mfa/user
`
	if err := os.WriteFile(configFile, []byte(content), 0o644); err != nil {
		t.Fatalf("failed to write config file: %v", err)
	}

	pm := NewProfileManager(configFile)
	profile, err := pm.GetProfile("production")
	if err != nil {
		t.Fatalf("GetProfile returned error: %v", err)
	}

	if profile.Name != "production" {
		t.Errorf("Name: got %q, want %q", profile.Name, "production")
	}
	if profile.RoleARN != "arn:aws:iam::123456789012:role/MyRole" {
		t.Errorf("RoleARN: got %q, want %q", profile.RoleARN, "arn:aws:iam::123456789012:role/MyRole")
	}
	if profile.Region != "ap-northeast-1" {
		t.Errorf("Region: got %q, want %q", profile.Region, "ap-northeast-1")
	}
	if profile.SourceProfile != "default" {
		t.Errorf("SourceProfile: got %q, want %q", profile.SourceProfile, "default")
	}
	if profile.ExternalID != "ext-123" {
		t.Errorf("ExternalID: got %q, want %q", profile.ExternalID, "ext-123")
	}
	if profile.MFASerial != "arn:aws:iam::123456789012:mfa/user" {
		t.Errorf("MFASerial: got %q, want %q", profile.MFASerial, "arn:aws:iam::123456789012:mfa/user")
	}
}

func TestGetProfile_NotFound(t *testing.T) {
	dir := t.TempDir()
	configFile := filepath.Join(dir, "config")

	content := `[profile production]
role_arn = arn:aws:iam::123456789012:role/MyRole
`
	if err := os.WriteFile(configFile, []byte(content), 0o644); err != nil {
		t.Fatalf("failed to write config file: %v", err)
	}

	pm := NewProfileManager(configFile)
	_, err := pm.GetProfile("nonexistent")
	if err == nil {
		t.Fatal("expected error for missing profile, got nil")
	}
}

func TestListProfiles_Success(t *testing.T) {
	dir := t.TempDir()
	configFile := filepath.Join(dir, "config")

	content := `[default]
region = us-east-1

[profile staging]
role_arn = arn:aws:iam::111111111111:role/Staging

[profile production]
role_arn = arn:aws:iam::222222222222:role/Production
`
	if err := os.WriteFile(configFile, []byte(content), 0o644); err != nil {
		t.Fatalf("failed to write config file: %v", err)
	}

	pm := NewProfileManager(configFile)
	profiles, err := pm.ListProfiles()
	if err != nil {
		t.Fatalf("ListProfiles returned error: %v", err)
	}

	if len(profiles) != 3 {
		t.Fatalf("expected 3 profiles, got %d: %v", len(profiles), profiles)
	}

	// Check that all expected profiles are present.
	want := map[string]bool{"default": false, "staging": false, "production": false}
	for _, p := range profiles {
		if _, ok := want[p]; !ok {
			t.Errorf("unexpected profile: %q", p)
		} else {
			want[p] = true
		}
	}
	for name, found := range want {
		if !found {
			t.Errorf("expected profile %q not found in result", name)
		}
	}
}
