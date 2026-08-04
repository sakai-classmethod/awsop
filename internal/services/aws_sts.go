package services

import (
	"context"
	"fmt"
	"strings"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/credentials"
	"github.com/aws/aws-sdk-go-v2/service/sts"
)

type stsAPI interface {
	AssumeRole(context.Context, *sts.AssumeRoleInput, ...func(*sts.Options)) (*sts.AssumeRoleOutput, error)
}

// STSClient is a wrapper around the AWS STS client.
type STSClient struct {
	client stsAPI
}

// NewSTSClient creates a new STSClient using the default AWS configuration.
func NewSTSClient(region string) (*STSClient, error) {
	cfg, err := config.LoadDefaultConfig(context.TODO(), config.WithRegion(region))
	if err != nil {
		return nil, fmt.Errorf("AWS設定の読み込みに失敗しました: %w", err)
	}

	return &STSClient{
		client: newSTSFromConfig(cfg, region),
	}, nil
}

// NewSTSClientWithSharedProfile creates a new STSClient using credentials from
// the named shared AWS profile.
func NewSTSClientWithSharedProfile(profileName, region string) (*STSClient, error) {
	cfg, err := config.LoadDefaultConfig(
		context.TODO(),
		config.WithSharedConfigProfile(profileName),
		config.WithRegion(region),
	)
	if err != nil {
		return nil, fmt.Errorf("AWS設定の読み込みに失敗しました: %w", err)
	}

	return &STSClient{
		client: newSTSFromConfig(cfg, region),
	}, nil
}

// NewSTSClientWithStaticCredentials creates a new STSClient using long-term
// credentials held only in memory. No session token is supplied.
func NewSTSClientWithStaticCredentials(accessKeyID, secretAccessKey, region string) (*STSClient, error) {
	cfg, err := config.LoadDefaultConfig(
		context.TODO(),
		config.WithCredentialsProvider(credentials.NewStaticCredentialsProvider(accessKeyID, secretAccessKey, "")),
		config.WithRegion(region),
	)
	if err != nil {
		return nil, fmt.Errorf("AWS設定の読み込みに失敗しました: %w", err)
	}

	return &STSClient{
		client: newSTSFromConfig(cfg, region),
	}, nil
}

func newSTSFromConfig(cfg aws.Config, region string) *sts.Client {
	return sts.NewFromConfig(cfg, func(options *sts.Options) {
		options.Region = region
	})
}

// AssumeRole executes an STS AssumeRole call and returns the credentials as a map.
func (s *STSClient) AssumeRole(roleARN, roleSessionName string, durationSeconds int32, externalID, mfaSerial, mfaToken string) (map[string]interface{}, error) {
	// roleARNの検証
	if roleARN == "" {
		return nil, fmt.Errorf("role_arnは必須です")
	}

	if !strings.HasPrefix(roleARN, "arn:aws:iam::") {
		return nil, fmt.Errorf("無効なrole_arn形式です: %s", roleARN)
	}

	// duration_secondsの検証
	if durationSeconds < 900 {
		return nil, fmt.Errorf("ロール期間は900秒以上である必要があります")
	}

	if durationSeconds > 43200 {
		return nil, fmt.Errorf("ロール期間は43200秒以下である必要があります")
	}

	if (mfaSerial == "") != (mfaToken == "") {
		return nil, fmt.Errorf("MFAを使用する場合はmfa_serialとMFAトークンの両方を指定してください")
	}

	// AssumeRoleリクエストのパラメータを構築
	input := &sts.AssumeRoleInput{
		RoleArn:         &roleARN,
		RoleSessionName: &roleSessionName,
		DurationSeconds: &durationSeconds,
	}

	// 外部IDが指定されている場合は追加
	if externalID != "" {
		input.ExternalId = &externalID
	}

	if mfaSerial != "" {
		input.SerialNumber = &mfaSerial
		input.TokenCode = &mfaToken
	}

	// AssumeRoleを実行
	output, err := s.client.AssumeRole(context.TODO(), input)
	if err != nil {
		errMsg := err.Error()

		if strings.Contains(errMsg, "AccessDenied") || strings.Contains(errMsg, "AccessDeniedException") {
			return nil, fmt.Errorf("ロールの引き受けに失敗しました: アクセスが拒否されました (%s)", errMsg)
		}

		if strings.Contains(errMsg, "InvalidParameterValue") {
			return nil, fmt.Errorf("ロールの引き受けに失敗しました: 無効なパラメータです (%s)", errMsg)
		}

		return nil, fmt.Errorf("ロールの引き受けに失敗しました: %s", errMsg)
	}

	// レスポンスをmap形式で返却
	result := map[string]interface{}{
		"Credentials": map[string]interface{}{
			"AccessKeyId":     *output.Credentials.AccessKeyId,
			"SecretAccessKey": *output.Credentials.SecretAccessKey,
			"SessionToken":    *output.Credentials.SessionToken,
			"Expiration":      output.Credentials.Expiration.Format("2006-01-02T15:04:05Z"),
		},
	}

	return result, nil
}
