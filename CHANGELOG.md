# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- zsh シェル補完機能の拡張
  - コマンドラインオプションの補完をサポート
  - `-` で始まる入力時に、すべての利用可能なオプションを説明付きで表示
  - 文脈認識型の補完（オプション補完とプロファイル補完を自動切り替え）
  - `--source-profile` と `--output-profile` の後でプロファイル名を補完
  - 部分一致によるフィルタリング機能
  - 既存のプロファイル補完機能との完全な後方互換性

### Changed

- シェルラッパー関数の補完ロジックを改善
  - オプションリストに短縮形と長形式の両方を含める
  - 各オプションに日本語の説明を追加
  - より直感的な補完体験を提供

## [1.0.0] - 2024-12-01

### Added

- 初回リリース
- 1Password CLI 連携による AWS 認証情報管理
- AWS STS AssumeRole のサポート
- シェル統合（zsh）
- Rich UI による視覚的なフィードバック
- プロファイル管理機能
- 以下のオプションをサポート：
  - `--list-profiles`: プロファイル一覧表示
  - `--show-commands`: export コマンド表示
  - `--unset`: 環境変数クリア
  - `--init-shell`: シェルラッパー関数出力
  - `--region`: リージョン指定
  - `--session-name`: セッション名指定
  - `--role-duration`: ロール期間指定
  - `--mfa-token`: MFA トークン指定
  - `--output-profile`: 認証情報ファイルへの書き込み
  - `--role-arn`: 直接ロール ARN 指定
  - `--source-profile`: ソースプロファイル指定
  - `--external-id`: 外部 ID 指定
  - `--config-file`: カスタム設定ファイル指定
  - `--credentials-file`: カスタム認証情報ファイル指定
  - `--info`: INFO レベルログ
  - `--debug`: DEBUG レベルログ
- 包括的なテストスイート：
  - ユニットテスト
  - プロパティベーステスト（Hypothesis）
  - 統合テスト

### Security

- 長期認証情報を平文で保存しない設計
- 1Password による安全な認証情報管理
- Touch ID による MFA 認証

[Unreleased]: https://github.com/yourusername/awsop/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/yourusername/awsop/releases/tag/v1.0.0
