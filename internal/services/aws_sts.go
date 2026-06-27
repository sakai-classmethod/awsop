package services

import (
	"context"
	"fmt"
	"strings"

	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/sts"
)

// STSClient is a wrapper around the AWS STS client.
type STSClient struct {
	client *sts.Client
}

// NewSTSClient creates a new STSClient using the default AWS configuration.
func NewSTSClient() (*STSClient, error) {
	cfg, err := config.LoadDefaultConfig(context.TODO())
	if err != nil {
		return nil, fmt.Errorf("AWS設定の読み込みに失敗しました: %w", err)
	}

	return &STSClient{
		client: sts.NewFromConfig(cfg),
	}, nil
}

// AssumeRole executes an STS AssumeRole call and returns the credentials as a map.
func (s *STSClient) AssumeRole(roleARN, roleSessionName string, durationSeconds int32, externalID string) (map[string]interface{}, error) {
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
