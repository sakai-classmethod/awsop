package services

import (
	"fmt"
	"os"
	"path/filepath"
	"time"

	"gopkg.in/ini.v1"
)

// expirationKey follows the aws-vault / saml2aws convention; AWS SDKs ignore it.
const expirationKey = "x_security_token_expires"

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
func (w *CredentialsWriter) WriteProfile(profileName, accessKeyID, secretAccessKey, sessionToken string, expiration time.Time) error {
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
	sec.Key(expirationKey).SetValue(expiration.UTC().Format(time.RFC3339))

	if err := w.ensureParentDir(); err != nil {
		return err
	}

	return w.save(cfg)
}

// PruneExpired removes awsop-managed profiles whose credentials expired at or
// before now, and returns the removed profile names. Profiles without a
// recorded expiration are kept because their validity is unknown.
func (w *CredentialsWriter) PruneExpired(now time.Time) ([]string, error) {
	if _, err := os.Stat(w.CredentialsFile); os.IsNotExist(err) {
		return nil, nil
	}
	cfg, err := ini.Load(w.CredentialsFile)
	if err != nil {
		return nil, fmt.Errorf("credentials ファイルの読み込みに失敗しました: %w", err)
	}

	var removed []string
	for _, sec := range cfg.Sections() {
		if sec.Key("manager").String() != "awsop" {
			continue
		}
		expiration, err := time.Parse(time.RFC3339, sec.Key(expirationKey).String())
		if err != nil || expiration.After(now) {
			continue
		}
		cfg.DeleteSection(sec.Name())
		removed = append(removed, sec.Name())
	}

	if len(removed) == 0 {
		return nil, nil
	}
	return removed, w.save(cfg)
}

// RemoveProfile deletes an awsop-managed profile from the credentials file.
func (w *CredentialsWriter) RemoveProfile(profileName string) error {
	cfg, err := ini.Load(w.CredentialsFile)
	if err != nil {
		return fmt.Errorf("credentials ファイルの読み込みに失敗しました: %w", err)
	}

	sec, err := cfg.GetSection(profileName)
	if err != nil {
		return fmt.Errorf("プロファイル '%s' が見つかりません", profileName)
	}
	if sec.Key("manager").String() != "awsop" {
		return fmt.Errorf("プロファイル '%s' はawsop管理ではありません。削除できません。", profileName)
	}

	cfg.DeleteSection(profileName)
	return w.save(cfg)
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

func (w *CredentialsWriter) save(cfg *ini.File) error {
	if err := cfg.SaveTo(w.CredentialsFile); err != nil {
		return fmt.Errorf("credentials ファイルの保存に失敗しました: %w", err)
	}

	if err := os.Chmod(w.CredentialsFile, 0o600); err != nil {
		return fmt.Errorf("credentials ファイルのパーミッション設定に失敗しました: %w", err)
	}

	return nil
}

// ensureParentDir creates the parent directory of the credentials file if it does not exist.
func (w *CredentialsWriter) ensureParentDir() error {
	dir := filepath.Dir(w.CredentialsFile)
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return fmt.Errorf("ディレクトリの作成に失敗しました: %w", err)
	}
	return nil
}
