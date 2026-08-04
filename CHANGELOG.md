# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0](https://github.com/sakai-classmethod/awsop/compare/v1.0.0...v1.1.0) (2026-08-04)


### Features

* add awsop CLI usage skill guide ([a24d8d6](https://github.com/sakai-classmethod/awsop/commit/a24d8d65e0ddeea6c1125d0f7a3b28358833845e))
* add awsop CLI usage skill guide ([6392798](https://github.com/sakai-classmethod/awsop/commit/63927987ddb7d5a0c97e3e721d3870e39668cfbd))
* support role durations over 1 hour by bypassing MFA session role chaining ([6263581](https://github.com/sakai-classmethod/awsop/commit/62635812c0ca0d82dd0a62aaa4ceb443657be32e))
* support role durations over 1 hour by bypassing MFA session role chaining ([ee5ff51](https://github.com/sakai-classmethod/awsop/commit/ee5ff517751475ced1806cd6b61758350e77eafd))

## 1.0.0 (2026-06-27)


### ⚠ BREAKING CHANGES

* installation method changed from `uv tool install` to `go install ./cmd/awsop/`. Shell integration (`eval "$(awsop --init-shell)"`) remains unchanged.

### Features

* add credentials cache to skip 1Password when env creds are valid ([c590023](https://github.com/sakai-classmethod/awsop/commit/c59002367655c7b79ea3cbcf1f5fe22554c6d760))
* **cli:** control show-commands output behavior ([34f2e9d](https://github.com/sakai-classmethod/awsop/commit/34f2e9dc4188bc63155b05a9ac5aa79438632f75))
* **cli:** control show-commands output behavior ([e6c9295](https://github.com/sakai-classmethod/awsop/commit/e6c9295b8424b4fe37d8d60b55a6cf06d44041ab))
* **credentials:** add cache to skip 1Password ([a427dbf](https://github.com/sakai-classmethod/awsop/commit/a427dbf70ee912b1f7c653c81a887fa30620d81f))
* **credentials:** remove AWS_PROFILE environment variable management ([918bf38](https://github.com/sakai-classmethod/awsop/commit/918bf385a85be71b0d4c685eace1cb9d861e3ef6))
* **credentials:** remove AWS_PROFILE environment variable management ([fa70d56](https://github.com/sakai-classmethod/awsop/commit/fa70d568cfec29d7535bd62c293a892de32f9f03))
* **version:** implement dynamic version retrieval from pyproject.toml ([c5ab425](https://github.com/sakai-classmethod/awsop/commit/c5ab4257fcbea0b9f5676d111cb47967c8b7270d))
* **version:** implement dynamic version retrieval from pyproject.toml ([28d3b45](https://github.com/sakai-classmethod/awsop/commit/28d3b4582990e442c3ae7ef495deacd7a4f28026))


### Bug Fixes

* **cli:** support -h short option and fix help display in shell wrapper ([42cd7ed](https://github.com/sakai-classmethod/awsop/commit/42cd7edbdd7e861ed97922260d86e373730361d4))
* **cli:** support -h short option and fix help display in shell wrapper ([3205e11](https://github.com/sakai-classmethod/awsop/commit/3205e11dc6d2e3bc7f8bb82eaae644b3c720b9ea))
* **ui:** escape Rich markup in credential expiry message ([21157a7](https://github.com/sakai-classmethod/awsop/commit/21157a7b97b6871da2ccf0cf8bdf0e2bc693e25a))


### Code Refactoring

* rewrite CLI from Python to Go ([fc63f7b](https://github.com/sakai-classmethod/awsop/commit/fc63f7bbfcf7a6b88a072bd002b29f9dda1668be))

## [Unreleased]

### Added

- pyproject.toml からの動的バージョン取得機能
  - `__version__` を pyproject.toml から自動的に読み取るように変更
  - バージョン情報の一元管理を実現
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

[Unreleased]: https://github.com/sakai-classmethod/awsop/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/sakai-classmethod/awsop/releases/tag/v1.0.0
