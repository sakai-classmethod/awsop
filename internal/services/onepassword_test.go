package services

import (
	"errors"
	"os/exec"
	"reflect"
	"strings"
	"testing"
)

func TestCheckAvailability(t *testing.T) {
	client := NewOnePasswordClient()
	got := client.CheckAvailability()

	// The expected result depends on whether "op" is installed on the
	// machine running the tests.  We verify that the method returns the
	// same answer as a direct LookPath check.
	_, err := exec.LookPath("op")
	want := err == nil

	if got != want {
		t.Errorf("CheckAvailability() = %v, want %v", got, want)
	}
}

func TestGetItemCredentials(t *testing.T) {
	var gotArgs []string
	client := &OnePasswordClient{
		runCommand: func(args ...string) ([]byte, error) {
			gotArgs = append([]string(nil), args...)
			return []byte(`{"fields":[{"label":"AWS Access Key ID","value":"access-value"},{"label":"aws_secret_access_key","value":"secret-value"}]}`), nil
		},
	}

	accessKeyID, secretAccessKey, err := client.GetItemCredentials("AWS production", "Engineering")
	if err != nil {
		t.Fatalf("GetItemCredentials returned error: %v", err)
	}
	if accessKeyID != "access-value" || secretAccessKey != "secret-value" {
		t.Fatalf("credentials = (%q, %q)", accessKeyID, secretAccessKey)
	}
	wantArgs := []string{"item", "get", "AWS production", "--format", "json", "--reveal", "--vault", "Engineering"}
	if !reflect.DeepEqual(gotArgs, wantArgs) {
		t.Errorf("args = %#v, want %#v", gotArgs, wantArgs)
	}
}

func TestGetItemCredentials_NormalizesLabels(t *testing.T) {
	client := &OnePasswordClient{
		runCommand: func(_ ...string) ([]byte, error) {
			return []byte(`{"fields":[{"label":"Access_Key ID","value":"access-value"},{"label":"Secret Access_Key","value":"secret-value"}]}`), nil
		},
	}

	accessKeyID, secretAccessKey, err := client.GetItemCredentials("item", "")
	if err != nil {
		t.Fatalf("GetItemCredentials returned error: %v", err)
	}
	if accessKeyID != "access-value" || secretAccessKey != "secret-value" {
		t.Fatalf("credentials = (%q, %q)", accessKeyID, secretAccessKey)
	}
}

func TestGetItemCredentials_MissingFieldDoesNotLeakValues(t *testing.T) {
	client := &OnePasswordClient{
		runCommand: func(_ ...string) ([]byte, error) {
			return []byte(`{"fields":[{"label":"username","value":"sensitive-user"},{"label":"access key id","value":"sensitive-access"}]}`), nil
		},
	}

	_, _, err := client.GetItemCredentials("item", "")
	if err == nil {
		t.Fatal("expected error")
	}
	if !strings.Contains(err.Error(), "username") || !strings.Contains(err.Error(), "access key id") {
		t.Errorf("error does not list labels: %v", err)
	}
	if strings.Contains(err.Error(), "sensitive-user") || strings.Contains(err.Error(), "sensitive-access") {
		t.Errorf("error leaks field values: %v", err)
	}
}

func TestGetItemOTP(t *testing.T) {
	client := &OnePasswordClient{
		runCommand: func(args ...string) ([]byte, error) {
			if !reflect.DeepEqual(args, []string{"item", "get", "item", "--otp", "--vault", "vault"}) {
				t.Errorf("args = %#v", args)
			}
			return []byte(" 123456\n"), nil
		},
	}

	got, err := client.GetItemOTP("item", "vault")
	if err != nil {
		t.Fatalf("GetItemOTP returned error: %v", err)
	}
	if got != "123456" {
		t.Errorf("OTP = %q", got)
	}
}

func TestGetItemCredentials_CommandErrorDoesNotLeakOutput(t *testing.T) {
	client := &OnePasswordClient{
		runCommand: func(_ ...string) ([]byte, error) {
			return []byte("sensitive-output"), errors.New("command failed")
		},
	}

	_, _, err := client.GetItemCredentials("item", "")
	if err == nil {
		t.Fatal("expected error")
	}
	if strings.Contains(err.Error(), "sensitive-output") {
		t.Errorf("error leaks command output: %v", err)
	}
}
