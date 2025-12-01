# awsop

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 目次

- [プロジェクトの説明](#プロジェクトの説明)
- [対象ユーザー](#対象ユーザー)
- [前提条件](#前提条件)
- [インストール](#インストール)
- [使用方法](#使用方法)
  - [シェル統合のセットアップ](#シェル統合のセットアップ)
  - [awsop の実行](#awsop-の実行)
  - [トラブルシューティング](#トラブルシューティング)
- [貢献ガイドライン](#貢献ガイドライン)
- [追加ドキュメント](#追加ドキュメント)
- [サポート](#サポート)
- [ライセンス](#ライセンス)

## プロジェクトの説明

awsop を使うと、1Password に保存された AWS 認証情報を使って、安全かつ簡単に AWS アカウント間を切り替えられます。

従来の AWS 認証情報管理ツールとは異なり、awsop は長期認証情報を平文ファイルに保存しません。代わりに、1Password CLI と Touch ID を使用して、必要な時にだけ一時認証情報を取得します。これにより、セキュリティポリシーを遵守しながら、快適な開発体験を実現できます。

シェル統合により、`eval "$(awsop production)"` と入力するだけで、本番環境の認証情報が環境変数に設定されます。Rich UI が視覚的なフィードバックを提供するため、現在どのアカウントで作業しているかを常に把握できます。

![awsop demo](docs/images/demo.gif)

### 主な特徴

- **セキュアな認証**: 1Password と Touch ID による MFA 認証で、長期認証情報を平文で保存しない
- **シンプルな操作**: `eval "$(awsop profile-name)"` だけで認証情報を設定
- **視覚的なフィードバック**: Rich UI によるスピナーと色付きメッセージで状態を明確に表示
- **柔軟な設定**: リージョン、セッション名、ロール期間など、豊富なオプションで様々なシナリオに対応
- **プロファイル管理**: `~/.aws/config` からプロファイルを読み取り、複数アカウントを簡単に管理
- **デバッグサポート**: 詳細なログ出力で問題を素早く特定

## 対象ユーザー

このプロジェクトは、以下のような方を対象としています：

- **AWS を日常的に使用する開発者**: 複数の AWS アカウント間を頻繁に切り替える必要がある方
- **セキュリティを重視する組織**: 長期認証情報の平文保存を禁止しているチーム
- **1Password を使用している方**: すでに 1Password で認証情報を管理している方
- **ジャンプアカウント運用をしている方**: MFA 必須の環境で AssumeRole を使用している方

awsop は、セキュリティポリシーを遵守しながら、快適な AWS 開発体験を実現したい方に最適です

## 前提条件

awsop を使用する前に、以下を準備してください：

- **Python 3.11 以上**: Python がインストールされていることを確認してください
- **uv パッケージマネージャー**: Python パッケージの管理に使用します（[インストール方法](https://github.com/astral-sh/uv)）
- **1Password CLI**: `op` コマンドがインストールされている必要があります（[インストール方法](https://developer.1password.com/docs/cli/)）
- **AWS 設定ファイル**: `~/.aws/config` にプロファイル設定が必要です
- **1Password アカウント**: AWS 認証情報が 1Password に保存されている必要があります

### 1Password CLI のインストール

```bash
# macOS (Homebrew)
brew install 1password-cli

# インストール後、1Password にサインイン
op signin
```

### uv のインストール

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# または Homebrew
brew install uv
```

## インストール

### awsop のインストール

awsop をインストールするには、以下のコマンドを実行します：

```bash
# PyPI からインストール（推奨）
uv tool install awsop
```

開発版をインストールする場合：

```bash
# リポジトリをクローン
git clone <repository-url>
cd awsop

# 開発モードでインストール
uv tool install -e .
```

インストールせずに試したい場合は、`uvx` を使用できます：

```bash
# インストール不要で直接実行
uvx awsop --help
```

## 使用方法

awsop を使い始めるには、まずシェル統合をセットアップします。

### シェル統合のセットアップ

1. **シェルラッパー関数を追加**

   `.zshrc` ファイルに以下を追加します：

   ```bash
   eval "$(awsop --init-shell)"
   ```

2. **設定を再読み込み**

   ```bash
   source ~/.zshrc
   ```

   これで、`awsop` コマンドが環境変数を直接設定できるようになります。

### awsop の実行

1. **利用可能なプロファイルを確認**

   ```bash
   awsop --list-profiles
   ```

   `~/.aws/config` に定義されているすべてのプロファイルが表示されます。

2. **プロファイルを指定して認証情報を取得**

   ```bash
   awsop production
   ```

   1Password で Touch ID 認証が求められます。認証が成功すると、以下の環境変数が設定されます：

   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_SESSION_TOKEN`
   - `AWS_REGION`
   - `AWS_PROFILE`
   - `AWSOP_EXPIRATION`

3. **認証情報を確認**

   ```bash
   echo $AWS_PROFILE
   # => production

   aws sts get-caller-identity
   ```

4. **認証情報をクリア**

   作業が終わったら、認証情報をクリアします：

   ```bash
   awsop --unset
   ```

### 高度な使用方法

#### リージョンを指定

```bash
# 東京リージョン（デフォルト）
awsop production

# 米国西部リージョン
awsop production --region us-west-2
```

#### ロール期間を指定

```bash
# デフォルト（1時間）
awsop production

# 2時間
awsop production --role-duration 7200
```

#### 認証情報をファイルに書き込む

```bash
# ~/.aws/credentials に書き込む
awsop production --output-profile prod-temp

# 他のツールから使用
export AWS_PROFILE=prod-temp
terraform plan
```

#### 直接ロール ARN を指定

```bash
# プロファイルを使わずにロールを引き受ける
awsop --role-arn arn:aws:iam::123456789012:role/MyRole
```

詳細な使用例については、[EXAMPLES.md](EXAMPLES.md) を参照してください。

### 利用可能なオプション

| オプション         | 短縮形 | 説明                                       |
| ------------------ | ------ | ------------------------------------------ |
| `--list-profiles`  | `-l`   | 利用可能なプロファイル一覧を表示           |
| `--show-commands`  | `-s`   | export コマンドを表示（eval せずに確認）   |
| `--unset`          | `-u`   | 環境変数をクリア                           |
| `--region`         | -      | AWS リージョンを指定                       |
| `--session-name`   | -      | AssumeRole のセッション名を指定            |
| `--role-duration`  | -      | ロールの有効期間（秒）を指定               |
| `--output-profile` | `-o`   | 認証情報を `~/.aws/credentials` に書き込む |
| `--role-arn`       | -      | 直接ロール ARN を指定                      |
| `--info`           | -      | INFO レベルのログを表示                    |
| `--debug`          | -      | DEBUG レベルのログを表示                   |
| `--version`        | `-v`   | バージョン情報を表示                       |
| `--help`           | `-h`   | ヘルプを表示                               |

すべてのオプションの詳細については、`awsop --help` を実行してください

### トラブルシューティング

よくある問題と解決方法：

<table>
  <tr>
    <td><strong>問題</strong></td>
    <td><strong>解決方法</strong></td>
  </tr>
  <tr>
    <td>1Password CLI が見つからない</td>
    <td>
      <code>which op</code> でインストールを確認してください。<br>
      インストールされていない場合: <code>brew install 1password-cli</code>
    </td>
  </tr>
  <tr>
    <td>プロファイルが見つからない</td>
    <td>
      <code>awsop --list-profiles</code> で利用可能なプロファイルを確認してください。<br>
      <code>~/.aws/config</code> にプロファイルが定義されているか確認してください。
    </td>
  </tr>
  <tr>
    <td>AssumeRole が失敗する</td>
    <td>
      <code>awsop production --debug</code> で詳細ログを確認してください。<br>
      <code>role_arn</code> が正しく設定されているか確認してください。<br>
      IAM ロールの信頼ポリシーが正しいか確認してください。
    </td>
  </tr>
  <tr>
    <td>認証情報の有効期限が切れた</td>
    <td>
      <code>echo $AWSOP_EXPIRATION</code> で有効期限を確認してください。<br>
      <code>awsop production</code> で認証情報を再取得してください。<br>
      長時間の作業には <code>--role-duration 7200</code> を使用してください。
    </td>
  </tr>
  <tr>
    <td>出力プロファイルが保護されている</td>
    <td>
      別のプロファイル名を使用するか、<code>~/.aws/credentials</code> に<br>
      <code>manager = awsop</code> を手動で追加してください。
    </td>
  </tr>
  <tr>
    <td>Touch ID 認証が表示されない</td>
    <td>
      <code>op signin</code> で 1Password にサインインしているか確認してください。<br>
      1Password アプリが起動しているか確認してください。
    </td>
  </tr>
</table>

その他のトラブルシューティング情報：

- [よくある質問（FAQ）](docs/FAQ.md)
- [詳細な使用例](EXAMPLES.md)
- [開発者ガイド](CONTRIBUTING.md)

## 貢献ガイドライン

awsop プロジェクトへの貢献を歓迎します！貢献方法については、[CONTRIBUTING.md](CONTRIBUTING.md) をご覧ください。

貢献の前に：

- Issue を作成して、変更内容を議論してください
- テストを書いてください
- コーディング規約に従ってください
- コミットメッセージは明確に書いてください

## 追加ドキュメント

詳細な情報については、以下のドキュメントを参照してください：

- [詳細な使用例](EXAMPLES.md) - 様々なシナリオでの使用方法
- [開発者ガイド](CONTRIBUTING.md) - 開発環境のセットアップとテスト方法
- [変更履歴](CHANGELOG.md) - バージョンごとの変更内容
- [設計書](.kiro/specs/awsop-cli-migration/design.md) - システムアーキテクチャと設計
- [要件定義](.kiro/specs/awsop-cli-migration/requirements.md) - 機能要件

## サポート

問題が発生した場合や質問がある場合は、以下の方法でサポートを受けられます：

- **Issue トラッカー**: [GitHub Issues](https://github.com/yourusername/awsop/issues) でバグ報告や機能リクエストを作成
- **ディスカッション**: [GitHub Discussions](https://github.com/yourusername/awsop/discussions) で質問や議論
- **メール**: support@example.com

## ライセンス

awsop は [MIT License](LICENSE) の下でライセンスされています。

---

**バージョン**: 1.0.0  
**最終更新**: 2024-12-01

> このプロジェクトは [The Good Docs Project](https://thegooddocsproject.dev/) のテンプレートを参考にしています
