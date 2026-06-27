package services

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"
)

// serviceMapping maps service short names to full names or URL templates.
var serviceMapping = map[string]string{
	"api":              "apigateway",
	"c9":               "cloud9",
	"cfn":              "cloudformation",
	"cw":               "cloudwatch",
	"ddb":              "dynamodb",
	"eb":               "elasticbeanstalk",
	"ec":               "elasticache",
	"es":               "elasticsearch",
	"gd":               "guardduty",
	"k8s":              "eks",
	"l":                "lambda",
	"logs":             "https://console.{amazon_domain}/cloudwatch/home?region={region}#logsV2:log-groups",
	"r53":              "route53",
	"secret":           "secretsmanager",
	"sfn":              "states",
	"ssm":              "systems-manager",
	"acm":              "acm",
	"athena":           "athena",
	"batch":            "batch",
	"cloudfront":       "cloudfront",
	"cloudtrail":       "cloudtrail",
	"codebuild":        "codebuild",
	"codecommit":       "codecommit",
	"codedeploy":       "codedeploy",
	"codepipeline":     "codepipeline",
	"cognito":          "cognito",
	"config":           "config",
	"dynamodb":         "dynamodb",
	"ec2":              "ec2",
	"ecr":              "ecr",
	"ecs":              "ecs",
	"efs":              "efs",
	"eks":              "eks",
	"elasticache":      "elasticache",
	"elasticbeanstalk": "elasticbeanstalk",
	"elb":              "ec2/v2/home?region={region}#LoadBalancers:",
	"emr":              "emr",
	"events":           "events",
	"glue":             "glue",
	"iam":              "iam",
	"kinesis":          "kinesis",
	"kms":              "kms",
	"lambda":           "lambda",
	"rds":              "rds",
	"redshift":         "redshift",
	"route53":          "route53",
	"s3":               "s3",
	"sagemaker":        "sagemaker",
	"secretsmanager":   "secretsmanager",
	"sns":              "sns",
	"sqs":              "sqs",
	"stepfunctions":    "states",
	"vpc":              "vpc",
	"waf":              "wafv2",
}

// ConsoleService handles AWS Console URL generation via federation.
type ConsoleService struct{}

// NewConsoleService creates a new ConsoleService.
func NewConsoleService() *ConsoleService {
	return &ConsoleService{}
}

// GetSigninToken retrieves a federation signin token from AWS.
func (s *ConsoleService) GetSigninToken(accessKeyID, secretAccessKey, sessionToken, amazonDomain string) (string, error) {
	sessionJSON, err := json.Marshal(map[string]string{
		"sessionId":    accessKeyID,
		"sessionKey":   secretAccessKey,
		"sessionToken": sessionToken,
	})
	if err != nil {
		return "", fmt.Errorf("セッション情報のJSON変換に失敗しました: %w", err)
	}

	federationURL := fmt.Sprintf(
		"https://signin.%s/federation?Action=getSigninToken&Session=%s",
		amazonDomain,
		url.QueryEscape(string(sessionJSON)),
	)

	client := &http.Client{Timeout: 30 * time.Second}
	resp, err := client.Get(federationURL)
	if err != nil {
		return "", fmt.Errorf("サインイントークンの取得に失敗しました: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("レスポンスの読み取りに失敗しました: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("サインイントークンの取得に失敗しました (ステータス: %d): %s", resp.StatusCode, string(body))
	}

	var result map[string]string
	if err := json.Unmarshal(body, &result); err != nil {
		return "", fmt.Errorf("レスポンスのJSON解析に失敗しました: %w", err)
	}

	signinToken, ok := result["SigninToken"]
	if !ok || signinToken == "" {
		return "", fmt.Errorf("レスポンスにSigninTokenが含まれていません")
	}

	return signinToken, nil
}

// GenerateConsoleURL builds the federated login URL for the AWS Console.
func (s *ConsoleService) GenerateConsoleURL(signinToken, destinationURL, amazonDomain string) string {
	return fmt.Sprintf(
		"https://signin.%s/federation?Action=login&Issuer=&Destination=%s&SigninToken=%s",
		amazonDomain,
		url.QueryEscape(destinationURL),
		url.QueryEscape(signinToken),
	)
}

// GetAmazonDomain returns the appropriate Amazon domain for the given region.
func (s *ConsoleService) GetAmazonDomain(region string) string {
	switch {
	case strings.HasPrefix(region, "us-gov-"):
		return "amazonaws-us-gov.com"
	case strings.HasPrefix(region, "cn-"):
		return "amazonaws.cn"
	default:
		return "aws.amazon.com"
	}
}

// BuildDestinationURL constructs the destination URL for the AWS Console.
func (s *ConsoleService) BuildDestinationURL(service, region, amazonDomain string) string {
	// If the service is already a full URL, return as-is.
	if strings.HasPrefix(service, "http://") || strings.HasPrefix(service, "https://") {
		return service
	}

	// Look up the service in the mapping; default to the service name itself.
	mapped, ok := serviceMapping[service]
	if !ok {
		mapped = service
	}

	// If the mapped value is a full URL template, perform substitution.
	if strings.HasPrefix(mapped, "http://") || strings.HasPrefix(mapped, "https://") {
		mapped = strings.ReplaceAll(mapped, "{region}", region)
		mapped = strings.ReplaceAll(mapped, "{amazon_domain}", amazonDomain)
		return mapped
	}

	// If mapped value is "console", build the console home URL.
	if mapped == "console" {
		return fmt.Sprintf("https://console.%s/console/home?region=%s", amazonDomain, region)
	}

	// Default: build the standard service console URL.
	return fmt.Sprintf("https://console.%s/%s/home?region=%s", amazonDomain, mapped, region)
}
