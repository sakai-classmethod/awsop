package services

import (
	"fmt"
	"os"
	"path/filepath"

	"gopkg.in/ini.v1"
)

// CredentialsWriter writes temporary AWS credentials to the credentials file.
type CredentialsWriter struct {
	CredentialsFile string
}

// NewCredentialsWriter creates a new CredentialsWriter.
// If credentialsFile is empty, it defaults to ~/.aws/credentials.
func NewCredentialsWriter(credentialsFile string) *CredentialsWriter {
	if credentialsFile == "" {
		home, err := os.UserHomeDir()
		if err != nil {
			home = "~"
		}
		credentialsFile = filepath.Join(home, ".aws", "credentials")
	}
	return &CredentialsWriter{
		CredentialsFile: credentialsFile,
	}
}

// WriteProfile writes or updates the given profile section in the credentials file.
// If the profile already exists and is not managed by awsop, it returns an error.
func (w *CredentialsWriter) WriteProfile(profileName, accessKeyID, secretAccessKey, sessionToken string) error {
	cfg, err := w.loadOrCreateConfig()
	if err != nil {
		return fmt.Errorf("credentials ファイルの読み込みに失敗しました: %w", err)
	}

	sec, err := cfg.GetSection(profileName)
	if err == nil {
		// Profile section exists; check if managed by awsop.
		manager := sec.Key("manager").String()
		if manager != "awsop" {
			return fmt.Errorf(
				"プロファイル '%s' は既に存在し、awsop管理ではありません。上書きできません。",
				profileName,
			)
		}
	} else {
		// Section does not exist; create it.
		sec, err = cfg.NewSection(profileName)
		if err != nil {
			return fmt.Errorf("プロファイルセクションの作成に失敗しました: %w", err)
		}
	}

	sec.Key("aws_access_key_id").SetValue(accessKeyID)
	sec.Key("aws_secret_access_key").SetValue(secretAccessKey)
	sec.Key("aws_session_token").SetValue(sessionToken)
	sec.Key("manager").SetValue("awsop")

	if err := w.ensureParentDir(); err != nil {
		return err
	}

	if err := cfg.SaveTo(w.CredentialsFile); err != nil {
		return fmt.Errorf("credentials ファイルの保存に失敗しました: %w", err)
	}

	if err := os.Chmod(w.CredentialsFile, 0o600); err != nil {
		return fmt.Errorf("credentials ファイルのパーミッション設定に失敗しました: %w", err)
	}

	return nil
}

// IsManagedByAwsop returns true if the profile section exists and has manager = awsop.
func (w *CredentialsWriter) IsManagedByAwsop(profileName string) bool {
	cfg, err := ini.Load(w.CredentialsFile)
	if err != nil {
		return false
	}

	sec, err := cfg.GetSection(profileName)
	if err != nil {
		return false
	}

	return sec.Key("manager").String() == "awsop"
}

// loadOrCreateConfig loads the credentials file if it exists, or creates an empty config.
func (w *CredentialsWriter) loadOrCreateConfig() (*ini.File, error) {
	if _, err := os.Stat(w.CredentialsFile); err == nil {
		return ini.Load(w.CredentialsFile)
	}
	return ini.Empty(), nil
}

// ensureParentDir creates the parent directory of the credentials file if it does not exist.
func (w *CredentialsWriter) ensureParentDir() error {
	dir := filepath.Dir(w.CredentialsFile)
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return fmt.Errorf("ディレクトリの作成に失敗しました: %w", err)
	}
	return nil
}
