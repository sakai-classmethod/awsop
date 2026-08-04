package app

import "time"

// ProfileConfig represents an AWS profile configuration from ~/.aws/config.
type ProfileConfig struct {
	Name          string
	RoleARN       string
	Region        string
	SourceProfile string
	ExternalID    string
	MFASerial     string
	OpItem        string
	OpVault       string
}

// Credentials represents temporary AWS credentials obtained via STS.
type Credentials struct {
	AccessKeyID     string
	SecretAccessKey string
	SessionToken    string
	Expiration      time.Time
	Region          string
	Profile         string
}
