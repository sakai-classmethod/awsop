package services

import (
	"context"
	"strings"
	"testing"
	"time"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/service/sts"
	"github.com/aws/aws-sdk-go-v2/service/sts/types"
)

type mockSTSAPI struct {
	input *sts.AssumeRoleInput
}

func (m *mockSTSAPI) AssumeRole(_ context.Context, input *sts.AssumeRoleInput, _ ...func(*sts.Options)) (*sts.AssumeRoleOutput, error) {
	m.input = input
	return &sts.AssumeRoleOutput{
		Credentials: &types.Credentials{
			AccessKeyId:     aws.String("temporary-access-key"),
			SecretAccessKey: aws.String("temporary-secret-key"),
			SessionToken:    aws.String("temporary-session-token"),
			Expiration:      aws.Time(time.Date(2026, 8, 4, 12, 0, 0, 0, time.UTC)),
		},
	}, nil
}

func TestSTSClientAssumeRole_WithMFA(t *testing.T) {
	mock := &mockSTSAPI{}
	client := &STSClient{client: mock}

	_, err := client.AssumeRole(
		"arn:aws:iam::123456789012:role/Admin",
		"awsop-test",
		7200,
		"external-id",
		"arn:aws:iam::123456789012:mfa/user",
		"123456",
	)
	if err != nil {
		t.Fatalf("AssumeRole returned error: %v", err)
	}

	if got := aws.ToString(mock.input.SerialNumber); got != "arn:aws:iam::123456789012:mfa/user" {
		t.Errorf("SerialNumber = %q", got)
	}
	if got := aws.ToString(mock.input.TokenCode); got != "123456" {
		t.Errorf("TokenCode = %q", got)
	}
	if got := aws.ToInt32(mock.input.DurationSeconds); got != 7200 {
		t.Errorf("DurationSeconds = %d", got)
	}
	if got := aws.ToString(mock.input.ExternalId); got != "external-id" {
		t.Errorf("ExternalId = %q", got)
	}
}

func TestSTSClientAssumeRole_WithoutMFA(t *testing.T) {
	mock := &mockSTSAPI{}
	client := &STSClient{client: mock}

	_, err := client.AssumeRole("arn:aws:iam::123456789012:role/Admin", "awsop-test", 3600, "", "", "")
	if err != nil {
		t.Fatalf("AssumeRole returned error: %v", err)
	}
	if mock.input.SerialNumber != nil {
		t.Errorf("SerialNumber = %q, want nil", aws.ToString(mock.input.SerialNumber))
	}
	if mock.input.TokenCode != nil {
		t.Errorf("TokenCode = %q, want nil", aws.ToString(mock.input.TokenCode))
	}
}

func TestSTSClientAssumeRole_RejectsIncompleteMFA(t *testing.T) {
	tests := []struct {
		name      string
		mfaSerial string
		mfaToken  string
	}{
		{name: "serial only", mfaSerial: "arn:aws:iam::123456789012:mfa/user"},
		{name: "token only", mfaToken: "123456"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			mock := &mockSTSAPI{}
			client := &STSClient{client: mock}
			_, err := client.AssumeRole("arn:aws:iam::123456789012:role/Admin", "awsop-test", 3600, "", tt.mfaSerial, tt.mfaToken)
			if err == nil || !strings.Contains(err.Error(), "MFA") {
				t.Fatalf("error = %v, want Japanese MFA error", err)
			}
			if mock.input != nil {
				t.Fatal("STS AssumeRole was called")
			}
		})
	}
}
