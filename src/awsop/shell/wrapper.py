"""シェルラッパー関数の生成"""


def generate_shell_wrapper() -> str:
    """
    zsh用のシェルラッパー関数と補完スクリプトを生成

    Returns:
        str: シェルスクリプト文字列
    """
    return """# awsop シェルラッパー関数
function awsop() {
  # ヘルプ、バージョン、リストなどの情報表示オプションをチェック
  local info_option=false
  for arg in "$@"; do
    case "$arg" in
      -h|--help|-v|--version|-l|--list-profiles|--init-shell|-s|--show-commands)
        info_option=true
        break
        ;;
    esac
  done

  if [[ "$info_option" == "true" ]]; then
    # 情報表示オプションの場合は eval せずに直接実行
    command awsop "$@"
    return $?
  fi

  # 通常の認証情報取得の場合は eval
  local output
  # stdout のみをキャプチャ（stderr はそのままターミナルに表示）
  output=$(command awsop "$@")
  local exit_code=$?

  if [[ $exit_code -eq 0 ]]; then
    # export コマンドを eval
    eval "$output"
  fi
  return $exit_code
}

# zsh 補完（正規表現による部分一致）
_awsop() {
  local -a profiles options
  local prev_word="${words[CURRENT-1]}"
  local current_word="${words[CURRENT]}"
  
  # オプションリストの定義
  options=(
    '-h:ヘルプを表示'
    '--help:ヘルプを表示'
    '-s:exportコマンドを表示'
    '--show-commands:exportコマンドを表示'
    '-u:環境変数をクリア'
    '--unset:環境変数をクリア'
    '-l:プロファイル一覧を表示'
    '--list-profiles:プロファイル一覧を表示'
    '--init-shell:シェルラッパー関数を出力'
    '-r:AWSリージョンを指定'
    '--region:AWSリージョンを指定'
    '-n:セッション名を指定'
    '--session-name:セッション名を指定'
    '-d:ロール期間を指定（秒）'
    '--role-duration:ロール期間を指定（秒）'
    '-m:MFAトークンを指定'
    '--mfa-token:MFAトークンを指定'
    '-o:出力プロファイル名を指定'
    '--output-profile:出力プロファイル名を指定'
    '-a:ロールARNを指定'
    '--role-arn:ロールARNを指定'
    '-p:ソースプロファイルを指定'
    '--source-profile:ソースプロファイルを指定'
    '-e:外部IDを指定'
    '--external-id:外部IDを指定'
    '-c:設定ファイルパスを指定'
    '--config-file:設定ファイルパスを指定'
    '--credentials-file:認証情報ファイルパスを指定'
    '-i:INFOレベルのログを表示'
    '--info:INFOレベルのログを表示'
    '--debug:DEBUGレベルのログを表示'
    '-v:バージョンを表示'
    '--version:バージョンを表示'
  )
  
  # プロファイルリストを取得
  if [[ -f ~/.aws/config ]]; then
    profiles=($(sed -nE 's/^\\[(profile )?([^]]+)\\]/\\2/p' ~/.aws/config))
  fi

  # 文脈に応じて補完タイプを決定
  if [[ "$prev_word" == "--source-profile" ]] || [[ "$prev_word" == "--output-profile" ]] || [[ "$prev_word" == "-p" ]] || [[ "$prev_word" == "-o" ]]; then
    # プロファイル名を必要とするオプションの後
    _describe 'profile' profiles
  elif [[ "$current_word" == -* ]]; then
    # 現在の単語が - で始まる場合はオプション補完
    _describe 'option' options
  else
    # それ以外はプロファイル補完
    _describe 'profile' profiles
  fi
}
compdef _awsop awsop

# zsh の matcher-list 設定で部分一致を有効化
# ユーザーは .zshrc に以下を追加することを推奨:
# zstyle ':completion:*' matcher-list 'm:{a-z}={A-Z}' 'r:|[._-]=* r:|=*' 'l:|=* r:|=*'
"""
