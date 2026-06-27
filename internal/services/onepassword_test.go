package services

import (
	"os/exec"
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
