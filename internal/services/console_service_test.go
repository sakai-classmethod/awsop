package services

import (
	"testing"
)

func TestGetAmazonDomain_Standard(t *testing.T) {
	svc := NewConsoleService()
	got := svc.GetAmazonDomain("ap-northeast-1")
	want := "aws.amazon.com"
	if got != want {
		t.Errorf("GetAmazonDomain(%q) = %q, want %q", "ap-northeast-1", got, want)
	}
}

func TestGetAmazonDomain_GovCloud(t *testing.T) {
	svc := NewConsoleService()
	got := svc.GetAmazonDomain("us-gov-west-1")
	want := "amazonaws-us-gov.com"
	if got != want {
		t.Errorf("GetAmazonDomain(%q) = %q, want %q", "us-gov-west-1", got, want)
	}
}

func TestGetAmazonDomain_China(t *testing.T) {
	svc := NewConsoleService()
	got := svc.GetAmazonDomain("cn-north-1")
	want := "amazonaws.cn"
	if got != want {
		t.Errorf("GetAmazonDomain(%q) = %q, want %q", "cn-north-1", got, want)
	}
}

func TestBuildDestinationURL_Console(t *testing.T) {
	svc := NewConsoleService()
	got := svc.BuildDestinationURL("console", "ap-northeast-1", "aws.amazon.com")
	want := "https://console.aws.amazon.com/console/home?region=ap-northeast-1"
	if got != want {
		t.Errorf("BuildDestinationURL(console) = %q, want %q", got, want)
	}
}

func TestBuildDestinationURL_Service(t *testing.T) {
	svc := NewConsoleService()
	got := svc.BuildDestinationURL("s3", "ap-northeast-1", "aws.amazon.com")
	want := "https://console.aws.amazon.com/s3/home?region=ap-northeast-1"
	if got != want {
		t.Errorf("BuildDestinationURL(s3) = %q, want %q", got, want)
	}
}

func TestBuildDestinationURL_Shortcut(t *testing.T) {
	svc := NewConsoleService()
	got := svc.BuildDestinationURL("l", "us-east-1", "aws.amazon.com")
	want := "https://console.aws.amazon.com/lambda/home?region=us-east-1"
	if got != want {
		t.Errorf("BuildDestinationURL(l) = %q, want %q", got, want)
	}
}

func TestBuildDestinationURL_FullURL(t *testing.T) {
	svc := NewConsoleService()
	input := "https://console.aws.amazon.com/ec2/v2/home?region=us-east-1#Instances:"
	got := svc.BuildDestinationURL(input, "us-east-1", "aws.amazon.com")
	if got != input {
		t.Errorf("BuildDestinationURL(full URL) = %q, want %q", got, input)
	}
}

func TestBuildDestinationURL_TemplateURL(t *testing.T) {
	svc := NewConsoleService()
	got := svc.BuildDestinationURL("logs", "ap-northeast-1", "aws.amazon.com")
	want := "https://console.aws.amazon.com/cloudwatch/home?region=ap-northeast-1#logsV2:log-groups"
	if got != want {
		t.Errorf("BuildDestinationURL(logs) = %q, want %q", got, want)
	}
}
