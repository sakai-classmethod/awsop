package services

import (
	"os"
	"path/filepath"
	"testing"
	"time"

	"gopkg.in/ini.v1"
)

func TestWriteProfile_NewFile(t *testing.T) {
	dir := t.TempDir()
	credFile := filepath.Join(dir, ".aws", "credentials")

	w := NewCredentialsWriter(credFile)
	err := w.WriteProfile("myprofile", "AKID", "SECRET", "TOKEN", testExpiration)
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

var testExpiration = time.Date(2026, 10, 22, 1, 13, 34, 0, time.UTC)

func TestWriteProfile_RecordsExpiration(t *testing.T) {
	credFile := filepath.Join(t.TempDir(), "credentials")

	if err := NewCredentialsWriter(credFile).WriteProfile("myprofile", "AKID", "SECRET", "TOKEN", testExpiration); err != nil {
		t.Fatalf("WriteProfile returned error: %v", err)
	}

	cfg, err := ini.Load(credFile)
	if err != nil {
		t.Fatalf("failed to load written file: %v", err)
	}
	if v := cfg.Section("myprofile").Key("x_security_token_expires").String(); v != "2026-10-22T01:13:34Z" {
		t.Errorf("x_security_token_expires: got %q", v)
	}
}

func TestPruneExpired_RemovesOnlyExpiredAwsopProfiles(t *testing.T) {
	credFile := filepath.Join(t.TempDir(), "credentials")
	content := `[expired]
aws_access_key_id        = AKID
manager                  = awsop
x_security_token_expires = 2026-10-21T00:00:00Z

[valid]
aws_access_key_id        = AKID
manager                  = awsop
x_security_token_expires = 2026-10-22T00:00:00Z

[without-expiration]
aws_access_key_id = AKID
manager           = awsop

[manual]
aws_access_key_id        = AKID
x_security_token_expires = 2026-10-21T00:00:00Z
`
	if err := os.WriteFile(credFile, []byte(content), 0o600); err != nil {
		t.Fatalf("failed to write file: %v", err)
	}

	removed, err := NewCredentialsWriter(credFile).PruneExpired(time.Date(2026, 10, 21, 12, 0, 0, 0, time.UTC))
	if err != nil {
		t.Fatalf("PruneExpired returned error: %v", err)
	}
	if len(removed) != 1 || removed[0] != "expired" {
		t.Errorf("removed = %v, want [expired]", removed)
	}

	cfg, err := ini.Load(credFile)
	if err != nil {
		t.Fatalf("failed to load file: %v", err)
	}
	if cfg.HasSection("expired") {
		t.Error("expired awsop profile should be removed")
	}
	for _, name := range []string{"valid", "without-expiration", "manual"} {
		if !cfg.HasSection(name) {
			t.Errorf("profile %q should be kept", name)
		}
	}
}

func TestPruneExpired_MissingFileIsNoop(t *testing.T) {
	credFile := filepath.Join(t.TempDir(), "credentials")

	removed, err := NewCredentialsWriter(credFile).PruneExpired(time.Now())
	if err != nil || len(removed) != 0 {
		t.Fatalf("PruneExpired = (%v, %v), want no removals", removed, err)
	}
	if _, err := os.Stat(credFile); !os.IsNotExist(err) {
		t.Error("PruneExpired should not create the credentials file")
	}
}

func TestRemoveProfile_RemovesAwsopProfile(t *testing.T) {
	credFile := filepath.Join(t.TempDir(), "credentials")
	w := NewCredentialsWriter(credFile)
	if err := w.WriteProfile("myprofile", "AKID", "SECRET", "TOKEN", testExpiration); err != nil {
		t.Fatalf("WriteProfile returned error: %v", err)
	}

	if err := w.RemoveProfile("myprofile"); err != nil {
		t.Fatalf("RemoveProfile returned error: %v", err)
	}

	cfg, err := ini.Load(credFile)
	if err != nil {
		t.Fatalf("failed to load file: %v", err)
	}
	if cfg.HasSection("myprofile") {
		t.Error("profile should be removed")
	}
}

func TestRemoveProfile_RefusesProfileNotManagedByAwsop(t *testing.T) {
	credFile := filepath.Join(t.TempDir(), "credentials")
	content := `[myprofile]
aws_access_key_id = MANUAL_AKID
`
	if err := os.WriteFile(credFile, []byte(content), 0o600); err != nil {
		t.Fatalf("failed to write file: %v", err)
	}

	if err := NewCredentialsWriter(credFile).RemoveProfile("myprofile"); err == nil {
		t.Fatal("expected error when removing non-managed profile, got nil")
	}
	cfg, _ := ini.Load(credFile)
	if !cfg.HasSection("myprofile") {
		t.Error("non-managed profile must be kept")
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
	err := w.WriteProfile("myprofile", "NEW_AKID", "NEW_SECRET", "NEW_TOKEN", testExpiration)
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
	err := w.WriteProfile("myprofile", "NEW_AKID", "NEW_SECRET", "NEW_TOKEN", testExpiration)
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
