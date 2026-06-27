package services

import (
	"errors"
	"os"
	"path/filepath"
	"testing"
)

func TestReadProfile_Success(t *testing.T) {
	dir := t.TempDir()
	configPath := filepath.Join(dir, "config")

	content := `[default]
region = us-east-1

[profile production]
region = ap-northeast-1
role_arn = arn:aws:iam::123456789012:role/admin
source_profile = default
`
	if err := os.WriteFile(configPath, []byte(content), 0644); err != nil {
		t.Fatalf("failed to write temp config: %v", err)
	}

	parser := NewAWSConfigParser(configPath)

	// Read a named profile.
	profile, err := parser.ReadProfile("production")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if got := profile["region"]; got != "ap-northeast-1" {
		t.Errorf("region: got %q, want %q", got, "ap-northeast-1")
	}
	if got := profile["role_arn"]; got != "arn:aws:iam::123456789012:role/admin" {
		t.Errorf("role_arn: got %q, want %q", got, "arn:aws:iam::123456789012:role/admin")
	}
	if got := profile["source_profile"]; got != "default" {
		t.Errorf("source_profile: got %q, want %q", got, "default")
	}
}

func TestReadProfile_FileNotFound(t *testing.T) {
	parser := NewAWSConfigParser("/nonexistent/path/config")

	_, err := parser.ReadProfile("default")
	if err == nil {
		t.Fatal("expected error, got nil")
	}

	var notFound *ConfigFileNotFoundError
	if !errors.As(err, &notFound) {
		t.Fatalf("expected ConfigFileNotFoundError, got %T: %v", err, err)
	}
	if notFound.Path != "/nonexistent/path/config" {
		t.Errorf("path: got %q, want %q", notFound.Path, "/nonexistent/path/config")
	}
}

func TestReadProfile_ProfileNotFound(t *testing.T) {
	dir := t.TempDir()
	configPath := filepath.Join(dir, "config")

	content := `[default]
region = us-east-1
`
	if err := os.WriteFile(configPath, []byte(content), 0644); err != nil {
		t.Fatalf("failed to write temp config: %v", err)
	}

	parser := NewAWSConfigParser(configPath)

	_, err := parser.ReadProfile("nonexistent")
	if err == nil {
		t.Fatal("expected error, got nil")
	}

	var notFound *ProfileNotFoundError
	if !errors.As(err, &notFound) {
		t.Fatalf("expected ProfileNotFoundError, got %T: %v", err, err)
	}
	if notFound.Name != "nonexistent" {
		t.Errorf("name: got %q, want %q", notFound.Name, "nonexistent")
	}
}

func TestListProfiles(t *testing.T) {
	dir := t.TempDir()
	configPath := filepath.Join(dir, "config")

	content := `[profile dev]
region = us-west-2

[profile staging]
region = eu-west-1

[profile production]
region = ap-northeast-1
`
	if err := os.WriteFile(configPath, []byte(content), 0644); err != nil {
		t.Fatalf("failed to write temp config: %v", err)
	}

	parser := NewAWSConfigParser(configPath)

	profiles, err := parser.ListProfiles()
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	expected := map[string]bool{
		"dev":        true,
		"staging":    true,
		"production": true,
	}

	if len(profiles) != len(expected) {
		t.Fatalf("profile count: got %d, want %d", len(profiles), len(expected))
	}

	for _, p := range profiles {
		if !expected[p] {
			t.Errorf("unexpected profile: %q", p)
		}
	}
}

func TestListProfiles_DefaultProfile(t *testing.T) {
	dir := t.TempDir()
	configPath := filepath.Join(dir, "config")

	content := `[default]
region = us-east-1

[profile production]
region = ap-northeast-1
`
	if err := os.WriteFile(configPath, []byte(content), 0644); err != nil {
		t.Fatalf("failed to write temp config: %v", err)
	}

	parser := NewAWSConfigParser(configPath)

	profiles, err := parser.ListProfiles()
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	hasDefault := false
	hasProduction := false
	for _, p := range profiles {
		switch p {
		case "default":
			hasDefault = true
		case "production":
			hasProduction = true
		}
	}

	if !hasDefault {
		t.Error("expected 'default' profile to be listed")
	}
	if !hasProduction {
		t.Error("expected 'production' profile to be listed")
	}
	if len(profiles) != 2 {
		t.Errorf("profile count: got %d, want 2 (profiles: %v)", len(profiles), profiles)
	}
}
