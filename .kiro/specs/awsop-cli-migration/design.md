# 設計書

## 概要

本ドキュメントは、awsop Python CLI ツールの技術設計を定義する。本システムは、1Password 連携による AWS 認証情報の取得と AssumeRole を行い、既存のシェル関数と同等の機能を提供する。

## アーキテクチャ

### システム構成

```
┌─────────────────────────────────────────────────────────┐
│                     ユーザーシェル                        │
│  eval "$(awsop <profile> [options])"                    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  awsop CLI (Python)                      │
│  ┌─────────────────────────────────────────────────┐   │
│  │           CLI Layer (Typer)                      │   │
│  │  - コマンドライン引数解析                          │   │
│  │  - オプション検証                                  │   │
│  └──────────────────┬──────────────────────────────┘   │
│                     │                                    │
│  ┌─────────────────▼──────────────────────────────┐   │
│  │         Application Layer                        │   │
│  │  - プロファイル管理                                │   │
│  │  - 認証情報取得フロー                              │   │
│  │  - 出力フォーマット                                │   │
│  └──────────────────┬──────────────────────────────┘   │
│                     │                                    │
│  ┌─────────────────▼──────────────────────────────┐   │
│  │         Service Layer                            │   │
│  │  - AWS Config Parser                             │   │
│  │  - 1Password Integration                         │   │
│  │  - AWS STS Client                                │   │
│  │  - Credentials Writer                            │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│1Password │  │AWS Config│  │AWS STS   │
│   CLI    │  │  Files   │  │   API    │
└──────────┘  └──────────┘  └──────────┘
```

### レイヤー構成

1. **CLI Layer**: Typer を使用したコマンドライン引数の解析とバリデーション
2. **Application Layer**: ビジネスロジックの実装
3. **Service Layer**: 外部システムとの統合

## コンポーネントと インターフェース

### CLI Layer

#### `cli.py`

```python
import typer
from typing import Optional

app = typer.Typer()

@app.command()
def main(
    profile: Optional[str] = typer.Argument(None),
    show_commands: bool = typer.Option(False, "--show-commands", "-s"),
    unset: bool = typer.Option(False, "--unset", "-u"),
    list_profiles: bool = typer.Option(False, "--list-profiles", "-l"),
    init_shell: bool = typer.Option(False, "--init-shell"),
    region: Optional[str] = typer.Option(None, "--region"),
    session_name: Optional[str] = typer.Option(None, "--session-name"),
    role_duration: int = typer.Option(3600, "--role-duration"),
    mfa_token: Optional[str] = typer.Option(None, "--mfa-token"),
    output_profile: Optional[str] = typer.Option(None, "--output-profile", "-o"),
    role_arn: Optional[str] = typer.Option(None, "--role-arn"),
    source_profile: Optional[str] = typer.Option(None, "--source-profile"),
    external_id: Optional[str] = typer.Option(None, "--external-id"),
    config_file: Optional[str] = typer.Option(None, "--config-file"),
    credentials_file: Optional[str] = typer.Option(None, "--credentials-file"),
    info: bool = typer.Option(False, "--info"),
    debug: bool = typer.Option(False, "--debug"),
    version: bool = typer.Option(False, "--version", "-v"),
) -> None:
    """1Password 連携による AWS 認証情報管理ツール"""
    pass
```

### Application Layer

#### `app/profile_manager.py`

プロファイル管理を担当するクラス。

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class ProfileConfig:
    """プロファイル設定"""
    name: str
    role_arn: Optional[str]
    region: Optional[str]
    source_profile: Optional[str]
    external_id: Optional[str]
    mfa_serial: Optional[str]

class ProfileManager:
    """プロファイル管理クラス"""

    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "~/.aws/config"

    def get_profile(self, profile_name: str) -> ProfileConfig:
        """プロファイル設定を取得"""
        pass

    def list_profiles(self) -> list[str]:
        """プロファイル一覧を取得"""
        pass
```

#### `app/credentials_manager.py`

認証情報の取得と管理を担当するクラス。

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Credentials:
    """AWS 認証情報"""
    access_key_id: str
    secret_access_key: str
    session_token: str
    expiration: datetime
    region: str
    profile: str

class CredentialsManager:
    """認証情報管理クラス"""

    def assume_role(
        self,
        role_arn: str,
        session_name: str,
        duration: int,
        external_id: Optional[str] = None,
        mfa_token: Optional[str] = None,
    ) -> Credentials:
        """ロールを引き受けて認証情報を取得"""
        pass

    def format_export_commands(self, credentials: Credentials) -> str:
        """export コマンド形式で出力"""
        pass

    def format_unset_commands(self) -> str:
        """unset コマンド形式で出力"""
        pass
```

### Service Layer

#### `services/aws_config.py`

AWS 設定ファイルの読み取りを担当するクラス。

```python
from configparser import ConfigParser
from pathlib import Path
from typing import Optional

class AWSConfigParser:
    """AWS 設定ファイルパーサー"""

    def __init__(self, config_file: Optional[str] = None):
        self.config_file = Path(config_file or "~/.aws/config").expanduser()

    def read_profile(self, profile_name: str) -> dict:
        """プロファイル設定を読み取る"""
        pass

    def list_profiles(self) -> list[str]:
        """プロファイル一覧を取得"""
        pass
```

#### `services/onepassword.py`

1Password CLI との統合を担当するクラス。

```python
import subprocess
import json
from typing import Optional

class OnePasswordClient:
    """1Password CLI クライアント"""

    def check_availability(self) -> bool:
        """op コマンドの存在確認"""
        pass

    def run_aws_command(self, command: list[str]) -> dict:
        """op plugin run 経由で AWS コマンドを実行"""
        pass
```

#### `services/aws_sts.py`

AWS STS API との統合を担当するクラス。

```python
from typing import Optional
from datetime import datetime

class STSClient:
    """AWS STS クライアント"""

    def assume_role(
        self,
        role_arn: str,
        role_session_name: str,
        duration_seconds: int = 3600,
        external_id: Optional[str] = None,
    ) -> dict:
        """AssumeRole を実行"""
        pass
```

#### `services/credentials_writer.py`

認証情報ファイルへの書き込みを担当するクラス。

```python
from pathlib import Path
from typing import Optional

class CredentialsWriter:
    """認証情報ファイルライター"""

    def __init__(self, credentials_file: Optional[str] = None):
        self.credentials_file = Path(
            credentials_file or "~/.aws/credentials"
        ).expanduser()

    def write_profile(
        self,
        profile_name: str,
        access_key_id: str,
        secret_access_key: str,
        session_token: str,
    ) -> None:
        """プロファイルに認証情報を書き込む"""
        pass

    def is_managed_by_awsop(self, profile_name: str) -> bool:
        """プロファイルが awsop 管理かチェック"""
        pass
```

### UI Layer

#### `ui/console.py`

Rich を使用した UI 表示を担当するクラス。

```python
from rich.console import Console
from rich.spinner import Spinner
from contextlib import contextmanager

class ConsoleUI:
    """コンソール UI"""

    def __init__(self):
        self.console = Console(stderr=True)

    @contextmanager
    def spinner(self, text: str):
        """スピナー表示"""
        pass

    def success(self, message: str):
        """成功メッセージ表示"""
        pass

    def error(self, message: str):
        """エラーメッセージ表示"""
        pass

    def info(self, message: str):
        """情報メッセージ表示"""
        pass
```

## データモデル

### ProfileConfig

プロファイル設定を表すデータクラス。

```python
@dataclass
class ProfileConfig:
    name: str
    role_arn: Optional[str] = None
    region: Optional[str] = None
    source_profile: Optional[str] = None
    external_id: Optional[str] = None
    mfa_serial: Optional[str] = None
```

### Credentials

AWS 認証情報を表すデータクラス。

```python
@dataclass
class Credentials:
    access_key_id: str
    secret_access_key: str
    session_token: str
    expiration: datetime
    region: str
    profile: str
```

### AssumeRoleRequest

AssumeRole リクエストパラメータを表すデータクラス。

```python
@dataclass
class AssumeRoleRequest:
    role_arn: str
    role_session_name: str
    duration_seconds: int = 3600
    external_id: Optional[str] = None
    mfa_token: Optional[str] = None
```

## 正確性プロパティ

_プロパティとは、システムの全ての有効な実行において真であるべき特性や動作のことです。本質的には、システムが何をすべきかについての形式的な記述です。プロパティは、人間が読める仕様と機械で検証可能な正確性保証の橋渡しとなります。_

### プロパティ 1: プロファイル設定の読み取り

*任意の*有効なプロファイル名に対して、システムは `~/.aws/config` からそのプロファイルの設定を正しく読み取り、role_arn、region、その他の設定値を取得できる

**検証: 要件 1.1**

### プロパティ 2: role_arn の検証

*任意の*プロファイルに対して、role_arn が定義されている場合は AssumeRole が実行され、定義されていない場合はエラーが返される

**検証: 要件 1.2, 1.3**

### プロパティ 3: export コマンドの完全性

*任意の*認証情報に対して、export コマンド出力は以下の全ての環境変数を含む: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN, AWS_REGION, AWS_DEFAULT_REGION, AWS_PROFILE, AWSOP_PROFILE, AWSOP_EXPIRATION

**検証: 要件 1.4, 2.2, 4.1, 4.2**

### プロパティ 4: プロファイル一覧の完全性

*任意の*AWS 設定ファイルに対して、システムは全てのプロファイル名を抽出し、各プロファイル名を 1 行ずつ出力する

**検証: 要件 3.1, 3.2**

### プロパティ 5: unset コマンドの完全性

*全ての*unset コマンド出力は、以下の全ての環境変数を unset する: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN, AWS_REGION, AWS_DEFAULT_REGION, AWS_PROFILE, AWSOP_PROFILE, AWSOP_EXPIRATION

**検証: 要件 4.1.2**

### プロパティ 6: リージョン設定の優先順位

*任意の*プロファイルとリージョン指定に対して、--region オプションが指定された場合はそれを使用し、指定されない場合はプロファイルの region 設定を使用し、それもない場合はデフォルトリージョン（ap-northeast-1）を使用する

**検証: 要件 4.2.1, 4.2.2, 4.2.3**

### プロパティ 7: セッション名の生成

*任意の*実行に対して、--session-name が指定された場合はそれを使用し、指定されない場合は「awsop-<タイムスタンプ>」形式のセッション名を生成する

**検証: 要件 4.3.1, 4.3.2**

### プロパティ 8: ロール期間の検証

*任意の*ロール期間指定に対して、1 から 43200 秒の範囲内であれば受け入れ、範囲外であればエラーを返す

**検証: 要件 4.4.1, 4.4.3**

### プロパティ 9: 出力プロファイルの保護

*任意の*出力プロファイル名に対して、そのプロファイルが既に存在し `manager = awsop` プロパティがない場合はエラーを返し、プロパティがある場合は上書きを許可する

**検証: 要件 4.6.2, 4.6.3**

### プロパティ 10: 出力先の分離

*任意の*実行に対して、export コマンドは標準出力に出力され、ステータスメッセージとエラーメッセージは標準エラー出力に出力される

**検証: 要件 5.4, 8.2, 8.3**

### プロパティ 11: ログレベルの制御

*任意の*実行に対して、--info が指定された場合は INFO レベル以上のログを表示し、--debug が指定された場合は DEBUG レベル以上のログを表示し、指定されない場合は WARNING レベル以上のログのみを表示する

**検証: 要件 9.1, 9.2, 9.3**

### プロパティ 12: 設定ファイルの優先順位

*任意の*実行に対して、--config-file または --credentials-file が指定された場合はそれを使用し、指定されない場合はデフォルトの `~/.aws/config` と `~/.aws/credentials` を使用する

**検証: 要件 10.1, 10.2, 10.3**

### プロパティ 13: エラー時の終了コード

*任意の*エラーが発生した場合、システムは終了コード 1 で終了する

**検証: 要件 11.4**

### プロパティ 14: バージョン出力フォーマット

*全ての*バージョン表示は「awsop X.Y.Z」という形式で標準出力に出力される

**検証: 要件 12.2**

## エラーハンドリング

### エラーの種類

1. **設定エラー**

   - プロファイルが見つからない
   - role_arn が定義されていない
   - 設定ファイルの読み取りに失敗

2. **認証エラー**

   - 1Password CLI の実行に失敗
   - AssumeRole の実行に失敗
   - MFA 認証に失敗

3. **バリデーションエラー**

   - ロール期間が範囲外
   - 出力プロファイルが保護されている
   - 必要なコマンドが存在しない

4. **ファイル操作エラー**
   - 認証情報ファイルの書き込みに失敗
   - 設定ファイルの読み取りに失敗

### エラーハンドリング戦略

- 全てのエラーは標準エラー出力に赤色で表示
- エラーメッセージは日本語で、原因が明確に分かる内容
- 全てのエラーで終了コード 1 を返す
- スタックトレースは --debug オプション時のみ表示

## テスト戦略

### ユニットテスト

各コンポーネントの個別機能をテストする：

- **AWSConfigParser**: プロファイル設定の読み取り、プロファイル一覧の取得
- **OnePasswordClient**: コマンド存在確認、AWS コマンド実行
- **STSClient**: AssumeRole リクエストの構築
- **CredentialsWriter**: 認証情報の書き込み、プロファイル保護チェック
- **ConsoleUI**: メッセージ出力（stdout/stderr の分離）

### プロパティベーステスト

プロパティベーステストライブラリとして **Hypothesis** を使用する。各テストは最低 100 回の反復を実行する。

各正確性プロパティに対して、以下の形式でテストを実装する：

```python
from hypothesis import given, strategies as st

@given(st.text(min_size=1))
def test_property_1_profile_config_reading(profile_name: str):
    """Feature: awsop-cli-migration, Property 1: プロファイル設定の読み取り"""
    # テスト実装
    pass
```

テストタグの形式: `**Feature: awsop-cli-migration, Property {番号}: {プロパティ名}**`

### 統合テスト

エンドツーエンドのフローをテストする：

- プロファイル指定から認証情報出力までの完全なフロー
- 各オプションの組み合わせ
- エラーケースの処理

### テスト環境

- モック: 1Password CLI、AWS STS API
- テストフィクスチャ: サンプル AWS 設定ファイル
- 一時ディレクトリ: ファイル操作のテスト用

## 実装の詳細

### プロジェクト構造

```
awsop/
├── pyproject.toml
├── README.md
├── src/
│   └── awsop/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── app/
│       │   ├── __init__.py
│       │   ├── profile_manager.py
│       │   └── credentials_manager.py
│       ├── services/
│       │   ├── __init__.py
│       │   ├── aws_config.py
│       │   ├── onepassword.py
│       │   ├── aws_sts.py
│       │   └── credentials_writer.py
│       ├── ui/
│       │   ├── __init__.py
│       │   └── console.py
│       └── shell/
│           ├── __init__.py
│           └── wrapper.py
└── tests/
    ├── __init__.py
    ├── unit/
    │   ├── test_profile_manager.py
    │   ├── test_credentials_manager.py
    │   ├── test_aws_config.py
    │   ├── test_onepassword.py
    │   ├── test_aws_sts.py
    │   └── test_credentials_writer.py
    ├── property/
    │   ├── test_properties.py
    │   └── strategies.py
    └── integration/
        └── test_cli.py
```

### 依存関係

```toml
[project]
name = "awsop"
version = "1.0.0"
dependencies = [
    "typer>=0.9.0",
    "rich>=13.0.0",
    "boto3>=1.28.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "hypothesis>=6.82.0",
    "pytest-cov>=4.1.0",
]

[project.scripts]
awsop = "awsop.cli:app"
```

### シェルラッパー関数

`--init-shell` オプションで出力されるシェルラッパー関数：

```bash
# awsop シェルラッパー関数
function awsop() {
  local output
  output=$(command awsop "$@" 2>&1)
  local exit_code=$?

  if [[ $exit_code -eq 0 ]]; then
    # export コマンドを eval
    eval "$output"
  else
    # エラーメッセージを表示
    echo "$output" >&2
    return $exit_code
  fi
}

# zsh 補完（正規表現による部分一致）
_awsop() {
  local -a profiles
  if [[ -f ~/.aws/config ]]; then
    profiles=($(sed -nE 's/^\[(profile )?([^]]+)\]/\2/p' ~/.aws/config))
  fi

  # 正規表現による部分一致補完を有効化
  _describe 'profile' profiles
}
compdef _awsop awsop

# zsh の matcher-list 設定で部分一致を有効化
# ユーザーは .zshrc に以下を追加することを推奨:
# zstyle ':completion:*' matcher-list 'm:{a-z}={A-Z}' 'r:|[._-]=* r:|=*' 'l:|=* r:|=*'
```

### 1Password 統合

1Password CLI との統合は `op plugin run` コマンドを使用：

```python
def run_aws_command(self, command: list[str]) -> dict:
    """op plugin run 経由で AWS コマンドを実行"""
    full_command = ["op", "plugin", "run", "--", "aws"] + command
    result = subprocess.run(
        full_command,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)
```

### ログ設定

Python の標準 logging モジュールを使用：

```python
import logging

def setup_logging(info: bool = False, debug: bool = False):
    """ログレベルを設定"""
    if debug:
        level = logging.DEBUG
    elif info:
        level = logging.INFO
    else:
        level = logging.WARNING

    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )
```

## セキュリティ考慮事項

1. **認証情報の取り扱い**

   - 一時認証情報のみを標準出力に出力
   - 長期認証情報は 1Password のみに保存
   - ファイルに書き込む場合は `--output-profile` オプション使用時のみ

2. **ファイルパーミッション**

   - `~/.aws/credentials` への書き込み時は適切なパーミッション（600）を設定

3. **エラーメッセージ**

   - エラーメッセージに認証情報を含めない
   - デバッグログでも認証情報をマスク

4. **1Password 統合**
   - Touch ID による認証
   - MFA トークンの安全な取得

## パフォーマンス考慮事項

1. **起動時間**

   - 依存関係の遅延読み込み
   - 不要なモジュールのインポートを避ける

2. **1Password CLI 呼び出し**

   - 約 15 秒かかることを想定
   - スピナーで進行状況を表示

3. **ファイル I/O**
   - 設定ファイルの読み取りは最小限に
   - キャッシュは実装しない（要件により）

## 配布とインストール

### uv によるインストール

```bash
# PyPI からインストール
uv tool install awsop

# ローカルからインストール（開発時）
uv tool install -e .

# uvx で直接実行（インストール不要）
uvx awsop <profile>
```

### シェル統合のセットアップ

```bash
# .zshrc に追加
eval "$(awsop --init-shell)"
```

## 今後の拡張性

1. **キャッシュ機能**

   - 将来的に 1Password へのキャッシュ機能を追加可能
   - 現在の設計では実装しない

2. **他のシェルのサポート**

   - bash、fish のサポート追加
   - シェル検出の自動化

3. **プラグインシステム**

   - カスタム認証プロバイダーのサポート
   - カスタム出力フォーマット

4. **設定ファイル**
   - `~/.awsop/config` でデフォルト設定を管理
   - プロファイルごとの設定
