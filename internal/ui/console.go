package ui

import (
	"fmt"
	"os"
	"sync"
	"time"
)

const (
	colorReset = "\033[0m"
	colorRed   = "\033[31m"
	colorGreen = "\033[32m"
	colorBlue  = "\033[34m"
	colorDim   = "\033[2m"
	clearLine  = "\r\033[K"
)

var spinnerFrames = []string{"⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"}

// ConsoleUI outputs user-facing messages to stderr.
type ConsoleUI struct{}

// NewConsoleUI creates a new ConsoleUI.
func NewConsoleUI() *ConsoleUI {
	return &ConsoleUI{}
}

// Success prints a green checkmark followed by the message to stderr.
func (u *ConsoleUI) Success(message string) {
	fmt.Fprintf(os.Stderr, "%s✓%s %s\n", colorGreen, colorReset, message)
}

// Error prints a red cross followed by the message to stderr.
func (u *ConsoleUI) Error(message string) {
	fmt.Fprintf(os.Stderr, "%s✗%s %s\n", colorRed, colorReset, message)
}

// Info prints a blue info symbol followed by the message to stderr.
func (u *ConsoleUI) Info(message string) {
	fmt.Fprintf(os.Stderr, "%sℹ%s %s\n", colorBlue, colorReset, message)
}

// Debug prints a dim debug message to stderr.
func (u *ConsoleUI) Debug(message string) {
	fmt.Fprintf(os.Stderr, "%s🔍 %s%s\n", colorDim, message, colorReset)
}

// Spinner shows a spinner animation on stderr while fn executes.
// It returns the error from fn.
func (u *ConsoleUI) Spinner(text string, fn func() error) error {
	var wg sync.WaitGroup
	done := make(chan struct{})

	wg.Add(1)
	go func() {
		defer wg.Done()
		i := 0
		for {
			select {
			case <-done:
				fmt.Fprint(os.Stderr, clearLine)
				return
			default:
				fmt.Fprintf(os.Stderr, "\r%s %s", spinnerFrames[i%len(spinnerFrames)], text)
				i++
				time.Sleep(80 * time.Millisecond)
			}
		}
	}()

	err := fn()

	close(done)
	wg.Wait()

	return err
}
