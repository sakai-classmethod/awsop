package cli

import (
	"errors"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/sakai-classmethod/awsop/internal/app"
	"github.com/sakai-classmethod/awsop/internal/services"
	"github.com/sakai-classmethod/awsop/internal/shell"
	"github.com/sakai-classmethod/awsop/internal/ui"
	"github.com/spf13/cobra"
)

// Version is set at build time via ldflags.
var Version = "dev"

// NewRootCommand creates the root cobra.Command for awsop.
func NewRootCommand() *cobra.Command {
	var (
		showCommands    bool
		unset           bool
		listProfiles    bool
		initShell       bool
		region          string
		sessionName     string
		roleDuration    int
		mfaToken        string
		outputProfile   string
		roleARN         string
		sourceProfile   string
		externalID      string
		configFile      string
		credentialsFile string
		console         bool
		consoleService  string
		consoleLink     bool
		forceRefresh    bool
		info            bool
		debug           bool
		version         bool
	)

	cmd := &cobra.Command{
		Use:           "awsop [profile]",
		Short:         "AWS credentials manager with 1Password integration",
		SilenceUsage:  true,
		SilenceErrors: true,
		Args:          cobra.MaximumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			// Setup logging
			if debug {
				log.SetFlags(log.LstdFlags | log.Lshortfile)
				log.SetOutput(os.Stderr)
			} else if info {
				log.SetFlags(log.LstdFlags)
				log.SetOutput(os.Stderr)
			} else {
				log.SetOutput(nil)
			}

			// --version
			if version {
				fmt.Printf("awsop %s\n", Version)
				return nil
			}

			// --console and --console-link are mutually exclusive
			if console && consoleLink {
				fmt.Fprintln(os.Stderr, "エラー: --console と --console-link は同時に使用できません")
				os.Exit(1)
			}

			// --init-shell
			if initShell {
				fmt.Println(shell.GenerateShellWrapper())
				return nil
			}

			// --list-profiles
			if listProfiles {
				profileManager := app.NewProfileManager(configFile)
				profiles, err := profileManager.ListProfiles()
				if err != nil {
					var cfnf *services.ConfigFileNotFoundError
					if errors.As(err, &cfnf) {
						fmt.Fprintln(os.Stderr, "エラー: AWS設定ファイルが見つかりません")
						os.Exit(1)
					}
					fmt.Fprintf(os.Stderr, "エラー: プロファイル一覧の取得に失敗しました: %v\n", err)
					os.Exit(1)
				}
				for _, p := range profiles {
					fmt.Println(p)
				}
				return nil
			}

			// --unset
			if unset {
				credentialsManager := app.NewCredentialsManager()
				fmt.Println(credentialsManager.FormatUnsetCommands())
				return nil
			}

			// Extract positional profile argument
			var profile string
			if len(args) > 0 {
				profile = args[0]
			}

			// No profile and no action flags: print usage to stderr and exit 0
			if profile == "" && !showCommands && roleARN == "" && !console && consoleService == "" && !consoleLink {
				fmt.Fprintln(os.Stderr, "使用方法: awsop [OPTIONS] [PROFILE]")
				fmt.Fprintln(os.Stderr, "詳細は --help オプションを参照してください")
				os.Exit(0)
			}

			// Profile/credential flow
			if profile != "" || roleARN != "" || console || consoleService != "" || consoleLink {
				consoleUI := ui.NewConsoleUI()

				// Validate role_duration
				if roleDuration < 1 || roleDuration > 43200 {
					consoleUI.Error(fmt.Sprintf("ロール期間は1から43200秒の範囲で指定してください（指定値: %d秒）", roleDuration))
					os.Exit(1)
				}

				// Generate session name if not provided
				if sessionName == "" {
					timestamp := time.Now().Format("20060102150405")
					sessionName = "awsop-" + timestamp
				}

				// Determine effective values
				effectiveRoleARN := ""
				effectiveExternalID := externalID
				effectiveRegion := region
				effectiveProfile := profile

				if roleARN != "" {
					// --role-arn option specified
					effectiveRoleARN = roleARN
					if effectiveProfile == "" {
						effectiveProfile = "direct-role"
					}

					// If --source-profile is specified, get region from it
					if sourceProfile != "" {
						profileManager := app.NewProfileManager(configFile)
						sourceConfig, err := profileManager.GetProfile(sourceProfile)
						if err != nil {
							var pnf *services.ProfileNotFoundError
							if errors.As(err, &pnf) {
								consoleUI.Error(fmt.Sprintf("プロファイル '%s' が見つかりません", sourceProfile))
								os.Exit(1)
							}
							var cfnf *services.ConfigFileNotFoundError
							if errors.As(err, &cfnf) {
								consoleUI.Error("AWS設定ファイルの読み取りに失敗しました")
								os.Exit(1)
							}
							consoleUI.Error(fmt.Sprintf("プロファイル '%s' が見つかりません", sourceProfile))
							os.Exit(1)
						}
						if effectiveRegion == "" {
							effectiveRegion = sourceConfig.Region
						}
					}
				} else if profile != "" {
					// Profile specified
					profileManager := app.NewProfileManager(configFile)
					profileConfig, err := profileManager.GetProfile(profile)
					if err != nil {
						var pnf *services.ProfileNotFoundError
						if errors.As(err, &pnf) {
							consoleUI.Error(fmt.Sprintf("プロファイル '%s' が見つかりません", profile))
							os.Exit(1)
						}
						var cfnf *services.ConfigFileNotFoundError
						if errors.As(err, &cfnf) {
							consoleUI.Error("AWS設定ファイルの読み取りに失敗しました")
							if debug {
								log.Printf("Error: %v", err)
							}
							os.Exit(1)
						}
						consoleUI.Error(fmt.Sprintf("プロファイル '%s' が見つかりません", profile))
						os.Exit(1)
					}

					if profileConfig.RoleARN == "" {
						consoleUI.Error(fmt.Sprintf("プロファイル '%s' に role_arn が定義されていません", profile))
						os.Exit(1)
					}

					effectiveRoleARN = profileConfig.RoleARN

					if effectiveRegion == "" {
						effectiveRegion = profileConfig.Region
					}

					if effectiveExternalID == "" {
						effectiveExternalID = profileConfig.ExternalID
					}
				}

				// Default region
				if effectiveRegion == "" {
					effectiveRegion = "ap-northeast-1"
				}

				credentialsManager := app.NewCredentialsManager()

				var credentials *app.Credentials

				// Check cache
				cacheProfile := effectiveProfile
				if cacheProfile == "" {
					cacheProfile = os.Getenv("AWSOP_PROFILE")
				}
				canUseCache := !forceRefresh && mfaToken == "" && roleARN == "" && cacheProfile != ""
				if canUseCache {
					cacheRegion := effectiveRegion
					if effectiveProfile == "" && region == "" {
						cacheRegion = ""
					}

					credentials = credentialsManager.GetCachedCredentials(cacheProfile, cacheRegion, 0)
					if credentials != nil {
						effectiveProfile = credentials.Profile
						effectiveRegion = credentials.Region
						consoleUI.Info(fmt.Sprintf("[%s] Cached credentials reused", effectiveProfile))
					}
				}

				if credentials == nil {
					if effectiveRoleARN == "" {
						consoleUI.Error("プロファイルまたは --role-arn を指定してください")
						os.Exit(1)
					}

					// Check 1Password availability (skip if --mfa-token is provided)
					if mfaToken == "" && !credentialsManager.OnePasswordClient.CheckAvailability() {
						consoleUI.Error("1Password CLIが利用できません。opコマンドをインストールしてください。")
						os.Exit(1)
					}

					// Show spinner while assuming role
					var assumeErr error
					spinnerErr := consoleUI.Spinner("1Password経由で認証情報を取得中...", func() error {
						credentials, assumeErr = credentialsManager.AssumeRole(
							effectiveRoleARN,
							sessionName,
							roleDuration,
							effectiveRegion,
							effectiveProfile,
							effectiveExternalID,
							mfaToken,
						)
						return assumeErr
					})
					if spinnerErr != nil {
						consoleUI.Error(spinnerErr.Error())
						if debug {
							log.Printf("AssumeRole error: %v", spinnerErr)
						}
						os.Exit(1)
					}
				}

				// --output-profile: write credentials to file
				if outputProfile != "" {
					credentialsWriter := services.NewCredentialsWriter(credentialsFile)
					writeErr := credentialsWriter.WriteProfile(
						outputProfile,
						credentials.AccessKeyID,
						credentials.SecretAccessKey,
						credentials.SessionToken,
					)
					if writeErr != nil {
						consoleUI.Error(writeErr.Error())
						os.Exit(1)
					}
					consoleUI.Success(fmt.Sprintf("認証情報をプロファイル '%s' に書き込みました", outputProfile))
				}

				// Console launch
				if console || consoleService != "" || consoleLink {
					consoleManager := app.NewConsoleManager()

					serviceName := consoleService
					if serviceName == "" {
						serviceName = "console"
					}

					var consoleURL string
					spinnerErr := consoleUI.Spinner("コンソールURLを生成中...", func() error {
						var err error
						consoleURL, err = consoleManager.OpenConsole(
							credentials,
							serviceName,
							!consoleLink, // --console-link: do not open browser
						)
						return err
					})
					if spinnerErr != nil {
						consoleUI.Error(spinnerErr.Error())
						if debug {
							log.Printf("Console error: %v", spinnerErr)
						}
						os.Exit(1)
					}

					if consoleLink {
						consoleUI.Info("コンソールURLを生成しました")
						// Print URL to stdout without newline
						fmt.Print(consoleURL)
					} else {
						consoleUI.Success(fmt.Sprintf("AWSコンソールをブラウザで開きました: %s", serviceName))
					}

					// Do not output export commands for console launch
					return nil
				}

				// Format and print export commands
				exportCommands := credentialsManager.FormatExportCommands(credentials)

				if showCommands {
					// --show-commands: print to stderr
					fmt.Fprintln(os.Stderr, exportCommands)
				} else {
					// Default: print to stdout
					fmt.Println(exportCommands)
				}

				// Print expiration info to stderr in JST
				jst, _ := time.LoadLocation("Asia/Tokyo")
				expirationJST := credentials.Expiration.In(jst)
				expirationStr := expirationJST.Format("2006-01-02 15:04:05 MST")
				consoleUI.Info(fmt.Sprintf("[%s] Credentials will expire %s", effectiveProfile, expirationStr))
			}

			return nil
		},
	}

	// Define flags
	flags := cmd.Flags()
	flags.BoolVarP(&showCommands, "show-commands", "s", false, "Show export commands")
	flags.BoolVarP(&unset, "unset", "u", false, "Clear environment variables")
	flags.BoolVarP(&listProfiles, "list-profiles", "l", false, "List available profiles")
	flags.BoolVar(&initShell, "init-shell", false, "Output shell wrapper function")
	flags.StringVarP(&region, "region", "r", "", "AWS region")
	flags.StringVarP(&sessionName, "session-name", "n", "", "AssumeRole session name")
	flags.IntVarP(&roleDuration, "role-duration", "d", 3600, "Role duration in seconds (default: 3600)")
	flags.StringVarP(&mfaToken, "mfa-token", "m", "", "MFA token")
	flags.StringVarP(&outputProfile, "output-profile", "o", "", "Output profile name")
	flags.StringVarP(&roleARN, "role-arn", "a", "", "Role ARN to assume")
	flags.StringVarP(&sourceProfile, "source-profile", "p", "", "Source profile for credentials")
	flags.StringVarP(&externalID, "external-id", "e", "", "External ID for AssumeRole")
	flags.StringVar(&configFile, "config-file", "", "AWS config file path")
	flags.StringVar(&credentialsFile, "credentials-file", "", "AWS credentials file path")
	flags.BoolVarP(&console, "console", "c", false, "Open AWS console in browser")
	flags.StringVar(&consoleService, "console-service", "", "AWS service to open (e.g., s3, lambda)")
	flags.BoolVar(&consoleLink, "console-link", false, "Print console URL without opening browser")
	flags.BoolVar(&forceRefresh, "force-refresh", false, "Force refresh credentials even if cached credentials are still valid")
	flags.BoolVarP(&info, "info", "i", false, "Show INFO level logs")
	flags.BoolVar(&debug, "debug", false, "Show DEBUG level logs")
	flags.BoolVarP(&version, "version", "v", false, "Show version")

	return cmd
}
