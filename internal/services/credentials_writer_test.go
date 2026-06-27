package services

import (
	"os"
	"path/filepath"
	"testing"

	"gopkg.in/ini.v1"
)

func TestWriteProfile_NewFile(t *testing.T) {
	dir := t.TempDir()
	credFile := filepath.Join(dir, ".aws", "credentials")

	w := NewCredentialsWriter(credFile)
	err := w.WriteProfile("myprofile", "AKID", "SECRET", "TOKEN")
	if err != nil {
		t.Fatalf("WriteProfile returned error: %v", err)
	}

	// Verify file was created
	cfg, err := ini.Load(credFile)
	if err != nil {
		t.Fatalf("failed to load written file: %v", err)
	}

	sec, err := cfg.GetSection("myprofile")
	if err != nil {
		t.Fatalf("section 'myprofile' not found: %v", err)
	}

	if v := sec.Key("aws_access_key_id").String(); v != "AKID" {
		t.Errorf("aws_access_key_id: got %q, want %q", v, "AKID")
	}
	if v := sec.Key("aws_secret_access_key").String(); v != "SECRET" {
		t.Errorf("aws_secret_access_key: got %q, want %q", v, "SECRET")
	}
	if v := sec.Key("aws_session_token").String(); v != "TOKEN" {
		t.Errorf("aws_session_token: got %q, want %q", v, "TOKEN")
	}
	if v := sec.Key("manager").String(); v != "awsop" {
		t.Errorf("manager: got %q, want %q", v, "awsop")
	}

	// Verify file permissions
	info, err := os.Stat(credFile)
	if err != nil {
		t.Fatalf("failed to stat file: %v", err)
	}
	if perm := info.Mode().Perm(); perm != 0o600 {
		t.Errorf("file permissions: got %o, want 600", perm)
	}
}

func TestWriteProfile_ExistingManaged(t *testing.T) {
	dir := t.TempDir()
	credFile := filepath.Join(dir, "credentials")

	// Create an existing file with a managed profile
	existingContent := `[myprofile]
aws_access_key_id     = OLD_AKID
aws_secret_access_key = OLD_SECRET
aws_session_token     = OLD_TOKEN
manager               = awsop
`
	if err := os.WriteFile(credFile, []byte(existingContent), 0o600); err != nil {
		t.Fatalf("failed to write existing file: %v", err)
	}

	w := NewCredentialsWriter(credFile)
	err := w.WriteProfile("myprofile", "NEW_AKID", "NEW_SECRET", "NEW_TOKEN")
	if err != nil {
		t.Fatalf("WriteProfile returned error: %v", err)
	}

	cfg, err := ini.Load(credFile)
	if err != nil {
		t.Fatalf("failed to load written file: %v", err)
	}

	sec, err := cfg.GetSection("myprofile")
	if err != nil {
		t.Fatalf("section 'myprofile' not found: %v", err)
	}

	if v := sec.Key("aws_access_key_id").String(); v != "NEW_AKID" {
		t.Errorf("aws_access_key_id: got %q, want %q", v, "NEW_AKID")
	}
	if v := sec.Key("aws_secret_access_key").String(); v != "NEW_SECRET" {
		t.Errorf("aws_secret_access_key: got %q, want %q", v, "NEW_SECRET")
	}
	if v := sec.Key("aws_session_token").String(); v != "NEW_TOKEN" {
		t.Errorf("aws_session_token: got %q, want %q", v, "NEW_TOKEN")
	}
	if v := sec.Key("manager").String(); v != "awsop" {
		t.Errorf("manager: got %q, want %q", v, "awsop")
	}
}

func TestWriteProfile_ExistingNotManaged(t *testing.T) {
	dir := t.TempDir()
	credFile := filepath.Join(dir, "credentials")

	// Create an existing file with a non-managed profile (no manager key)
	existingContent := `[myprofile]
aws_access_key_id     = MANUAL_AKID
aws_secret_access_key = MANUAL_SECRET
`
	if err := os.WriteFile(credFile, []byte(existingContent), 0o600); err != nil {
		t.Fatalf("failed to write existing file: %v", err)
	}

	w := NewCredentialsWriter(credFile)
	err := w.WriteProfile("myprofile", "NEW_AKID", "NEW_SECRET", "NEW_TOKEN")
	if err == nil {
		t.Fatal("expected error when overwriting non-managed profile, got nil")
	}
}

func TestIsManagedByAwsop_True(t *testing.T) {
	dir := t.TempDir()
	credFile := filepath.Join(dir, "credentials")

	content := `[myprofile]
aws_access_key_id     = AKID
aws_secret_access_key = SECRET
aws_session_token     = TOKEN
manager               = awsop
`
	if err := os.WriteFile(credFile, []byte(content), 0o600); err != nil {
		t.Fatalf("failed to write file: %v", err)
	}

	w := NewCredentialsWriter(credFile)
	if !w.IsManagedByAwsop("myprofile") {
		t.Error("expected IsManagedByAwsop to return true for managed profile")
	}
}

func TestIsManagedByAwsop_False(t *testing.T) {
	dir := t.TempDir()
	credFile := filepath.Join(dir, "credentials")

	content := `[myprofile]
aws_access_key_id     = AKID
aws_secret_access_key = SECRET
`
	if err := os.WriteFile(credFile, []byte(content), 0o600); err != nil {
		t.Fatalf("failed to write file: %v", err)
	}

	w := NewCredentialsWriter(credFile)

	// Profile exists but not managed
	if w.IsManagedByAwsop("myprofile") {
		t.Error("expected IsManagedByAwsop to return false for non-managed profile")
	}

	// Profile does not exist
	if w.IsManagedByAwsop("nonexistent") {
		t.Error("expected IsManagedByAwsop to return false for missing profile")
	}
}
