package services

import (
	"fmt"
	"os"
	"strings"

	"gopkg.in/ini.v1"
)

// ConfigFileNotFoundError is returned when the AWS config file does not exist.
type ConfigFileNotFoundError struct {
	Path string
}

func (e *ConfigFileNotFoundError) Error() string {
	return fmt.Sprintf("設定ファイルが見つかりません: %s", e.Path)
}

// ProfileNotFoundError is returned when the requested profile is not found in the config file.
type ProfileNotFoundError struct {
	Name string
}

func (e *ProfileNotFoundError) Error() string {
	return fmt.Sprintf("プロファイルが見つかりません: %s", e.Name)
}

// AWSConfigParser reads and parses AWS config files (~/.aws/config).
type AWSConfigParser struct {
	ConfigFile string
}

// NewAWSConfigParser creates a new AWSConfigParser.
// If configFile is empty, it defaults to ~/.aws/config.
func NewAWSConfigParser(configFile string) *AWSConfigParser {
	if configFile == "" {
		home, err := os.UserHomeDir()
		if err != nil {
			// Fall back to a literal path; callers will get a file-not-found
			// error when they try to read.
			configFile = "~/.aws/config"
		} else {
			configFile = home + "/.aws/config"
		}
	}
	return &AWSConfigParser{ConfigFile: configFile}
}

// sectionName returns the INI section name for a given AWS profile name.
// AWS config uses "profile <name>" for non-default profiles and "default" for
// the default profile.
func sectionName(profileName string) string {
	if profileName == "default" {
		return "default"
	}
	return "profile " + profileName
}

// ReadProfile reads a profile's configuration as a map of key-value pairs.
func (p *AWSConfigParser) ReadProfile(profileName string) (map[string]string, error) {
	if _, err := os.Stat(p.ConfigFile); os.IsNotExist(err) {
		return nil, &ConfigFileNotFoundError{Path: p.ConfigFile}
	}

	cfg, err := ini.Load(p.ConfigFile)
	if err != nil {
		return nil, fmt.Errorf("設定ファイルの読み取りに失敗しました: %w", err)
	}

	section, err := cfg.GetSection(sectionName(profileName))
	if err != nil {
		return nil, &ProfileNotFoundError{Name: profileName}
	}

	result := make(map[string]string, len(section.Keys()))
	for _, key := range section.Keys() {
		result[key.Name()] = key.String()
	}
	return result, nil
}

// ListProfiles returns the names of all profiles defined in the config file.
// It strips the "profile " prefix from section names.
func (p *AWSConfigParser) ListProfiles() ([]string, error) {
	if _, err := os.Stat(p.ConfigFile); os.IsNotExist(err) {
		return nil, &ConfigFileNotFoundError{Path: p.ConfigFile}
	}

	cfg, err := ini.Load(p.ConfigFile)
	if err != nil {
		return nil, fmt.Errorf("設定ファイルの読み取りに失敗しました: %w", err)
	}

	var profiles []string
	for _, section := range cfg.Sections() {
		name := section.Name()
		switch {
		case name == "default":
			profiles = append(profiles, "default")
		case strings.HasPrefix(name, "profile "):
			profiles = append(profiles, strings.TrimPrefix(name, "profile "))
		}
		// Skip ini.v1's implicit "DEFAULT" section and any non-profile sections.
	}
	return profiles, nil
}
