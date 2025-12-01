"""シェルラッパー関数の生成"""


def generate_shell_wrapper() -> str:
    """
    zsh用のシェルラッパー関数と補完スクリプトを生成

    Returns:
        str: シェルスクリプト文字列
    """
    return """# awsop シェルラッパー関数
function awsop() {
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
  local -a profiles
  if [[ -f ~/.aws/config ]]; then
    profiles=($(sed -nE 's/^\\[(profile )?([^]]+)\\]/\\2/p' ~/.aws/config))
  fi

  # 正規表現による部分一致補完を有効化
  _describe 'profile' profiles
}
compdef _awsop awsop

# zsh の matcher-list 設定で部分一致を有効化
# ユーザーは .zshrc に以下を追加することを推奨:
# zstyle ':completion:*' matcher-list 'm:{a-z}={A-Z}' 'r:|[._-]=* r:|=*' 'l:|=* r:|=*'
"""
