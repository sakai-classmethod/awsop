package main

import (
	"os"

	"github.com/sakai-classmethod/awsop/internal/cli"
)

func main() {
	cmd := cli.NewRootCommand()
	if err := cmd.Execute(); err != nil {
		os.Exit(1)
	}
}
