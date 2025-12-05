# 設計書

## 概要

本設計書は、awsop に AWS マネジメントコンソールをブラウザで開く機能を追加するための設計を定義します。この機能は、既存の awsume-console-plugin の実装を参考にしながら、awsop のアーキテクチャに統合します。

主な機能：

- `-c`オプションで AWS コンソールをブラウザで開く
- `-c <service>`で特定のサービスページを開く
- `--console-link`で URL のみを出力
- リージョン別のドメイン処理（標準、GovCloud、中国）
- サービス名の短縮形サポート

## アーキテクチャ

### システム構成

```
┌─────────────────┐
│   CLI Layer     │  cli.py: コマンドライン引数の解析
│   (cli.py)      │  新規オプション: -c, --console-link
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Application    │  新規: ConsoleManager
│     Layer       │  既存: CredentialsManager, ProfileManager
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Services      │  新規: ConsoleService
│     Layer       │  既存: OnePasswordClient, STSClient
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   External      │  AWS Federation Endpoint
│   Services      │  ブラウザ (webbrowser module)
└─────────────────┘
```

### レイヤー間の責務

1. **CLI レイヤー** (`cli.py`)

   - コンソール関連オプションの追加と解析
   - 既存のプロファイル処理フローへの統合
   - エラーハンドリングとユーザーフィードバック

2. **アプリケーションレイヤー** (`app/console_manager.py`)

   - コンソール URL 生成のオーケストレーション
   - 認証情報の取得と変換
   - ブラウザ起動の制御

3. **サービスレイヤー** (`services/console_service.py`)
   - AWS Federation Endpoint との通信
   - サインイントークンの取得
   - URL 生成ロジック

## コンポーネントとインターフェース

### 1. ConsoleService (新規)

AWS Federation Endpoint との通信を担当するサービスクラス。

```python
class ConsoleService:
    """AWSコンソールURL生成サービス"""

    def get_signin_token(
        self,
        access_key_id: str,
        secret_access_key: str,
        session_token: str,
        amazon_domain: str
    ) -> str:
        """
        AWS Federation Endpointからサインイントークンを取得

        Args:
            access_key_id: アクセスキーID
            secret_access_key: シークレットアクセスキー
            session_token: セッショントークン
            amazon_domain: Amazonドメイン

        Returns:
            str: サインイントークン

        Raises:
            RuntimeError: トークン取得に失敗した場合
        """

    def generate_console_url(
        self,
        signin_token: str,
        destination_url: str,
        amazon_domain: str
    ) -> str:
        """
        コンソールURLを生成

        Args:
            signin_token: サインイントークン
            destination_url: デスティネーションURL
            amazon_domain: Amazonドメイン

        Returns:
            str: 完全なコンソールURL
        """

    def get_amazon_domain(self, region: str) -> str:
        """
        リージョンから適切なAmazonドメインを取得

        Args:
            region: AWSリージョン

        Returns:
            str: Amazonドメイン (aws.amazon.com, amazonaws-us-gov.com, amazonaws.cn)
        """

    def build_destination_url(
        self,
        service: str,
        region: str,
        amazon_domain: str
    ) -> str:
        """
        サービス名からデスティネーションURLを構築

        Args:
            service: サービス名または短縮名
            region: AWSリージョン
            amazon_domain: Amazonドメイン

        Returns:
            str: デスティネーションURL
        """
```

### 2. ConsoleManager (新規)

コンソール起動のオーケストレーションを担当するマネージャークラス。

```python
class ConsoleManager:
    """コンソール起動管理クラス"""

    def __init__(
        self,
        console_service: Optional[ConsoleService] = None,
        credentials_manager: Optional[CredentialsManager] = None
    ):
        """
        コンソールマネージャーを初期化

        Args:
            console_service: コンソールサービス（テスト用）
            credentials_manager: 認証情報マネージャー（テスト用）
        """

    def open_console(
        self,
        credentials: Credentials,
        service: str = "console",
        open_browser: bool = True
    ) -> str:
        """
        AWSコンソールを開く

        Args:
            credentials: AWS認証情報
            service: サービス名（デフォルト: "console"）
            open_browser: ブラウザを開くかどうか

        Returns:
            str: 生成されたコンソールURL

        Raises:
            RuntimeError: URL生成またはブラウザ起動に失敗した場合
        """
```

### 3. CLI レイヤーの拡張

既存の`cli.py`に以下のオプションを追加：

```python
console: bool = typer.Option(
    False, "--console", "-c", help="Open AWS console in browser"
)
console_service: Optional[str] = typer.Option(
    None, "--console-service", help="AWS service to open (e.g., s3, lambda)"
)
console_link: bool = typer.Option(
    False, "--console-link", help="Print console URL without opening browser"
)
```

## データモデル

### サービスマッピング

サービスの短縮名から実際のコンソール URL へのマッピング。

```python
SERVICE_MAPPING = {
    # 一般的な短縮形
    'api': 'apigateway',
    'c9': 'cloud9',
    'cfn': 'cloudformation',
    'cw': 'cloudwatch',
    'ddb': 'dynamodb',
    'eb': 'elasticbeanstalk',
    'ec': 'elasticache',
    'es': 'elasticsearch',
    'gd': 'guardduty',
    'k8s': 'eks',
    'l': 'lambda',
    'logs': 'https://console.{amazon_domain}/cloudwatch/home?region={region}#logsV2:log-groups',
    'r53': 'route53',
    'secret': 'secretsmanager',
    'sfn': 'states',
    'ssm': 'systems-manager',
    # ... その他のマッピング
}
```

### URL テンプレート

サービス URL は以下の変数をサポート：

- `{region}`: AWS リージョン
- `{amazon_domain}`: Amazon ドメイン

例：

```
https://console.{amazon_domain}/cloudwatch/home?region={region}#logsV2:log-groups
```

## Correctness Properties

_プロパティとは、システムのすべての有効な実行において真であるべき特性または動作です。プロパティは、人間が読める仕様と機械で検証可能な正確性保証の橋渡しとなります。_

### プロパティ反映

prework 分析を確認した結果、以下の冗長性を特定しました：

1. **ドメイン決定のプロパティ (4.1, 4.2, 4.3)**: これらは 1 つの包括的なプロパティ「リージョンからドメインへのマッピング」にまとめます
2. **URL 出力のプロパティ (3.3, 3.4)**: これらは出力フォーマットの 1 つのプロパティにまとめます
3. **サービスマッピングのプロパティ (6.2, 6.3)**: これらは重複しており、1 つにまとめます

### コアプロパティ

**プロパティ 1: サインイントークン取得の一貫性**

*任意の*有効な一時認証情報（AccessKeyId、SecretAccessKey、SessionToken）に対して、システムは AWS Federation Endpoint を呼び出し、これらの認証情報を使用してサインイントークンを取得する

**検証: 要件 1.2, 1.3**

**プロパティ 2: リージョンの URL 反映**

*任意の*AWS リージョンに対して、生成されるコンソール URL はそのリージョンをパラメータとして含む

**検証: 要件 1.4**

**プロパティ 3: サービスマッピングの変換**

*任意の*サービスマッピングに存在する短縮名に対して、システムは対応する完全なサービス名または URL パスに変換する

**検証: 要件 2.2, 6.2, 6.3**

**プロパティ 4: 未知のサービス名の透過的処理**

*任意の*サービスマッピングに存在しないサービス名に対して、システムはそのサービス名をそのまま URL パスとして使用する

**検証: 要件 2.3**

**プロパティ 5: テンプレート変数の置換**

*任意の*テンプレート変数（{region}、{amazon_domain}）を含む URL に対して、システムは適切な値で置換する

**検証: 要件 2.4, 4.5**

**プロパティ 6: 完全な URL の透過的処理**

*任意の*完全な URL（http://または https://で始まる）に対して、システムはその URL をデスティネーションとして使用する

**検証: 要件 2.5**

**プロパティ 7: URL 出力フォーマット**

*任意の*生成されたコンソール URL に対して、`--console-link`オプション使用時は標準出力に改行なしで出力し、情報メッセージは標準エラー出力に出力する

**検証: 要件 3.3, 3.4**

**プロパティ 8: 完全な認証済み URL 生成**

*任意の*有効な認証情報に対して、生成される URL はサインイントークンとデスティネーション URL を含む完全な認証済み URL である

**検証: 要件 3.5**

**プロパティ 9: リージョンベースのドメイン決定**

*任意の*AWS リージョンに対して、システムは以下のルールで Amazon ドメインを決定する：

- `us-gov-`で始まる場合: `amazonaws-us-gov.com`
- `cn-`で始まる場合: `amazonaws.cn`
- その他の場合: `aws.amazon.com`

**検証: 要件 4.1, 4.2, 4.3**

**プロパティ 10: ドメインの一貫性**

*任意の*リージョンに対して、Federation Endpoint とコンソール URL で使用される Amazon ドメインは同一である

**検証: 要件 4.4**

**プロパティ 11: リージョンオプションの優先**

_任意の_`--region`オプションで指定されたリージョンに対して、システムはそのリージョンのコンソール URL を生成する

**検証: 要件 7.1**

**プロパティ 12: マッピングテンプレートの処理**

*任意の*完全な URL を値として持つサービスマッピングエントリに対して、システムはその URL をテンプレートとして使用し、変数を置換する

**検証: 要件 6.4**

## エラーハンドリング

### エラーの種類と処理

1. **認証情報取得エラー**

   - 原因: 1Password 認証失敗、プロファイル不存在
   - 処理: エラーメッセージを表示し、終了コード 1 で終了
   - 要件: 5.1

2. **サインイントークン取得エラー**

   - 原因: ネットワークエラー、無効な認証情報、API エラー
   - 処理: 詳細なエラーメッセージを表示し、終了コード 1 で終了
   - 要件: 5.2, 5.4

3. **ブラウザ起動エラー**

   - 原因: ブラウザが見つからない、起動失敗
   - 処理: エラーメッセージと URL を表示し、ユーザーが手動でアクセスできるようにする
   - 要件: 5.3

4. **デバッグモード**
   - すべてのエラーでスタックトレースを含む詳細情報を表示
   - 要件: 5.5

### エラーメッセージの設計

```python
# 認証情報取得エラー
"認証情報の取得に失敗しました: {詳細}"

# サインイントークン取得エラー
"AWSコンソールURLの生成に失敗しました: {詳細}"

# ブラウザ起動エラー
"ブラウザの起動に失敗しました: {詳細}\n以下のURLを手動で開いてください:\n{url}"

# ネットワークエラー
"AWS Federation Endpointへの接続に失敗しました: {詳細}"
```

## テスト戦略

### 二重テストアプローチ

本機能では、ユニットテストとプロパティベーステストの両方を使用します：

- **ユニットテスト**: 特定の例、エッジケース、エラー条件を検証
- **プロパティベーステスト**: すべての入力に対して成り立つべき普遍的なプロパティを検証

両者は補完的であり、包括的なカバレッジを提供します。

### プロパティベーステスト

**使用ライブラリ**: Hypothesis (Python)

**設定**:

- 各プロパティテストは最低 100 回の反復を実行
- 各テストには設計書のプロパティ番号を明示的に参照するコメントを付与
- フォーマット: `**Feature: console-browser-launch, Property {number}: {property_text}**`

**テスト対象プロパティ**:

1. **プロパティ 1**: サインイントークン取得の一貫性

   - 戦略: ランダムな認証情報を生成
   - 検証: Federation Endpoint 呼び出しに正しいパラメータが渡される

2. **プロパティ 2**: リージョンの URL 反映

   - 戦略: ランダムな AWS リージョンを生成
   - 検証: 生成された URL にリージョンが含まれる

3. **プロパティ 3**: サービスマッピングの変換

   - 戦略: マッピングに存在するすべての短縮名を使用
   - 検証: 正しい完全名または URL パスに変換される

4. **プロパティ 4**: 未知のサービス名の透過的処理

   - 戦略: ランダムな文字列を生成
   - 検証: そのまま URL パスとして使用される

5. **プロパティ 5**: テンプレート変数の置換

   - 戦略: テンプレート変数を含む URL とランダムなリージョン/ドメインを生成
   - 検証: すべての変数が適切に置換される

6. **プロパティ 6**: 完全な URL の透過的処理

   - 戦略: ランダムな完全な URL を生成
   - 検証: そのままデスティネーションとして使用される

7. **プロパティ 7**: URL 出力フォーマット

   - 戦略: ランダムな URL を生成
   - 検証: 標準出力に改行なしで出力される

8. **プロパティ 8**: 完全な認証済み URL 生成

   - 戦略: ランダムな認証情報を生成
   - 検証: URL が必要な要素（サインイントークン、デスティネーション）を含む

9. **プロパティ 9**: リージョンベースのドメイン決定

   - 戦略: 各タイプのリージョン（標準、GovCloud、中国）を生成
   - 検証: 正しいドメインが選択される

10. **プロパティ 10**: ドメインの一貫性

    - 戦略: ランダムなリージョンを生成
    - 検証: Federation Endpoint とコンソール URL で同じドメインが使用される

11. **プロパティ 11**: リージョンオプションの優先

    - 戦略: ランダムなリージョンを生成
    - 検証: 指定されたリージョンが URL に反映される

12. **プロパティ 12**: マッピングテンプレートの処理
    - 戦略: 完全な URL を含むマッピングエントリを使用
    - 検証: テンプレート変数が適切に置換される

### ユニットテスト

以下の特定のシナリオとエッジケースをカバー：

1. **基本的なコンソール起動** (要件 1.1)

   - 正常系: プロファイル指定でコンソールが開く
   - ブラウザ起動のモック

2. **サービス指定でのコンソール起動** (要件 2.1)

   - 特定のサービス名で URL が生成される

3. **コンソール URL の出力** (要件 3.1, 3.2)

   - `--console-link`オプションで URL のみ出力
   - ブラウザが開かないことを確認

4. **エラーケース** (要件 5.1-5.5)

   - 認証情報取得失敗
   - サインイントークン取得失敗
   - ブラウザ起動失敗
   - ネットワークエラー
   - デバッグモードでのスタックトレース表示

5. **既存オプションとの統合** (要件 7.2-7.5)

   - `--role-arn`との組み合わせ
   - `--source-profile`との組み合わせ
   - `--debug`オプションでの詳細ログ
   - 複数オプションの組み合わせ

6. **UI フィードバック** (要件 8.1-8.5)

   - スピナー表示
   - 成功メッセージ
   - エラーメッセージ
   - 情報メッセージの標準エラー出力

7. **サービスマッピング初期化** (要件 6.1)
   - 一般的なサービスの短縮名が定義されている

### テスト実行

```bash
# すべてのテストを実行
uv run pytest tests/

# プロパティテストのみ実行
uv run pytest tests/property/test_console_service.py

# ユニットテストのみ実行
uv run pytest tests/unit/test_console_manager.py

# 統合テストのみ実行
uv run pytest tests/integration/test_console_integration.py

# カバレッジレポート付き
uv run pytest --cov=src/awsop --cov-report=html
```

## 実装の詳細

### Federation Endpoint API

AWS Federation Endpoint は 2 段階のプロセスでコンソール URL を生成します：

1. **サインイントークンの取得**

   ```
   GET https://signin.{amazon_domain}/federation?Action=getSigninToken&Session={session_json}
   ```

   Session JSON フォーマット:

   ```json
   {
     "sessionId": "ACCESS_KEY_ID",
     "sessionKey": "SECRET_ACCESS_KEY",
     "sessionToken": "SESSION_TOKEN"
   }
   ```

2. **コンソール URL の生成**
   ```
   https://signin.{amazon_domain}/federation?Action=login&Issuer=&Destination={destination_url}&SigninToken={signin_token}
   ```

### URL 構造

生成されるコンソール URL の構造：

```
https://signin.{amazon_domain}/federation
  ?Action=login
  &Issuer=
  &Destination=https://console.{amazon_domain}/{service}/home?region={region}
  &SigninToken={token}
```

### デスティネーション URL のパターン

1. **デフォルト（コンソールホーム）**

   ```
   https://console.{amazon_domain}/console/home?region={region}
   ```

2. **特定のサービス**

   ```
   https://console.{amazon_domain}/{service}/home?region={region}
   ```

3. **カスタム URL（マッピングから）**

   ```
   https://console.{amazon_domain}/cloudwatch/home?region={region}#logsV2:log-groups
   ```

4. **完全な URL**
   ```
   https://quicksight.aws.amazon.com
   ```

### ブラウザ起動

Python の`webbrowser`モジュールを使用：

```python
import webbrowser

# デフォルトブラウザで開く
webbrowser.open(url)
```

エラーハンドリング：

- ブラウザが見つからない場合: URL を表示してユーザーに手動で開くよう促す
- 起動失敗の場合: エラーメッセージと URL を表示

## セキュリティ考慮事項

1. **一時認証情報の使用**

   - サインイントークンは一時的なもの
   - 長期認証情報は使用しない

2. **URL の取り扱い**

   - 生成された URL にはサインイントークンが含まれる
   - ログ出力時は注意が必要（デバッグモードのみ）

3. **ネットワーク通信**

   - HTTPS 通信のみ使用
   - 証明書検証を有効化

4. **エラーメッセージ**
   - 機密情報を含まないようにする
   - デバッグモード以外では詳細を隠す

## パフォーマンス考慮事項

1. **ネットワークレイテンシ**

   - Federation Endpoint 呼び出しは 1 回のみ
   - タイムアウト設定: 30 秒

2. **ブラウザ起動**

   - 非同期で起動（ブロックしない）
   - 起動完了を待たない

3. **キャッシング**
   - サインイントークンはキャッシュしない（セキュリティ上の理由）
   - サービスマッピングは静的データとして保持

## 依存関係

### 新規依存関係

なし（標準ライブラリのみ使用）

### 使用する標準ライブラリ

- `urllib.parse`: URL エンコーディング
- `urllib.request`: HTTP 通信
- `webbrowser`: ブラウザ起動
- `json`: JSON 処理

### 既存の依存関係

- `boto3`: AWS SDK（既存）
- `typer`: CLI フレームワーク（既存）
- `rich`: UI 表示（既存）
- `hypothesis`: プロパティベーステスト（既存）

## 互換性

### Python バージョン

- Python 3.11 以上（既存の要件と同じ）

### AWS リージョン

- すべての AWS リージョンをサポート
- GovCloud、中国リージョンを含む

### ブラウザ

- システムのデフォルトブラウザを使用
- macOS、Linux、Windows をサポート

## 今後の拡張性

1. **カスタムブラウザコマンド**

   - 設定ファイルでブラウザコマンドをカスタマイズ可能にする
   - 例: `browser_command = "open -a 'Google Chrome' {url}"`

2. **サービスマッピングのカスタマイズ**

   - ユーザー定義のサービスマッピングをサポート
   - 設定ファイルで追加マッピングを定義

3. **コンソールセッションの永続化**

   - 生成された URL を履歴として保存
   - 最近使用したサービスへのクイックアクセス

4. **複数ブラウザプロファイル**
   - 異なる AWS アカウントを異なるブラウザプロファイルで開く
   - プロファイルごとのブラウザ設定
