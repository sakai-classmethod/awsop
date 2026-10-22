package cli

import "testing"

func TestCanReuseCachedCredentials(t *testing.T) {
	tests := []struct {
		name string
		args []string
		want bool
	}{
		{"profile only", []string{"production"}, true},
		{"output profile needs fresh credentials", []string{"production", "--output-profile", "prod-temp"}, false},
		{"explicit role duration needs fresh credentials", []string{"production", "-d", "43200"}, false},
		{"force refresh", []string{"production", "--force-refresh"}, false},
		{"mfa token", []string{"production", "-m", "123456"}, false},
		{"role arn", []string{"--role-arn", "arn:aws:iam::123456789012:role/Admin"}, false},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			cmd := NewRootCommand()
			if err := cmd.ParseFlags(tt.args); err != nil {
				t.Fatalf("ParseFlags: %v", err)
			}
			if got := canReuseCachedCredentials(cmd); got != tt.want {
				t.Errorf("canReuseCachedCredentials(%v) = %v, want %v", tt.args, got, tt.want)
			}
		})
	}
}

func TestValidateRoleDuration(t *testing.T) {
	for _, d := range []int{900, 3600, 43200} {
		if err := validateRoleDuration(d); err != nil {
			t.Errorf("validateRoleDuration(%d) = %v, want nil", d, err)
		}
	}
	for _, d := range []int{0, 899, 43201} {
		if err := validateRoleDuration(d); err == nil {
			t.Errorf("validateRoleDuration(%d) = nil, want error", d)
		}
	}
}
