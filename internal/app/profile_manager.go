package app

import "github.com/sakai-classmethod/awsop/internal/services"

// ProfileManager provides operations on AWS profiles defined in ~/.aws/config.
type ProfileManager struct {
	parser *services.AWSConfigParser
}

// NewProfileManager creates a new ProfileManager that reads profiles from the
// given config file. If configFile is empty, AWSConfigParser defaults to
// ~/.aws/config.
func NewProfileManager(configFile string) *ProfileManager {
	return &ProfileManager{
		parser: services.NewAWSConfigParser(configFile),
	}
}

// GetProfile reads the named profile from the AWS config file and returns a
// ProfileConfig populated with the relevant fields.
func (m *ProfileManager) GetProfile(profileName string) (*ProfileConfig, error) {
	values, err := m.parser.ReadProfile(profileName)
	if err != nil {
		return nil, err
	}

	return &ProfileConfig{
		Name:          profileName,
		RoleARN:       values["role_arn"],
		Region:        values["region"],
		SourceProfile: values["source_profile"],
		ExternalID:    values["external_id"],
		MFASerial:     values["mfa_serial"],
		OpItem:        values["awsop_op_item"],
		OpVault:       values["awsop_op_vault"],
	}, nil
}

// ListProfiles returns the names of all profiles defined in the config file.
func (m *ProfileManager) ListProfiles() ([]string, error) {
	return m.parser.ListProfiles()
}
