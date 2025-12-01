# 実装計画

- [x] 1. バージョン取得ロジックの実装

  - `src/awsop/__init__.py`を修正して`importlib.metadata`を使用
  - ハードコードされた`__version__ = "1.0.0"`を削除
  - `importlib.metadata.version("awsop")`を使用して動的に取得
  - `PackageNotFoundError`をキャッチして"unknown"を返すフォールバック処理を実装
  - _要件: 1.1, 1.2, 1.3, 2.1, 2.2, 3.1, 3.2, 3.3, 3.4_

- [x] 1.1 Property 1 のプロパティベーステストを実装

  - **Property 1: バージョン文字列の型保証**
  - **検証: 要件 2.4**
  - インストール済み環境とフォールバック環境の両方で`__version__`が文字列型であることを検証
  - Hypothesis を使用して最低 100 回の反復を実行
  - テストファイル: `tests/property/test_version_type.py`

- [x] 1.2 Edge Case 1 のテストを実装

  - **Edge Case 1: パッケージ未インストール時のフォールバック**
  - **検証: 要件 3.1, 3.2, 3.3, 3.4**
  - `importlib.metadata.version`をモックして`PackageNotFoundError`を発生させる
  - `__version__`が"unknown"になることを確認
  - 例外が伝播しないことを確認
  - テストファイル: `tests/unit/test_version_fallback.py`

- [x] 2. CLI バージョン表示の動作確認

  - `src/awsop/cli.py`のインポート部分を確認（変更不要のはず）
  - `awsop -v`と`awsop --version`が正しく動作することを確認
  - _要件: 4.1, 4.2, 4.3, 4.4, 6.1, 6.2, 6.3_

- [x] 2.1 Example 2 と Example 3 のテストを実装

  - **Example 2: CLI バージョン表示（-v）**
  - **Example 3: CLI バージョン表示（--version）**
  - **検証: 要件 4.1, 4.2**
  - `awsop -v`が"awsop X.Y.Z"形式で出力することを確認
  - `awsop --version`が同じ出力をすることを確認
  - 終了コードが 0 であることを確認
  - テストファイル: `tests/integration/test_version_display.py`

- [x] 3. インストール済み環境でのバージョン取得テスト

  - パッケージがインストールされている状態で`__version__`が正しい値を返すことを確認
  - `pyproject.toml`のバージョンと一致することを確認
  - _要件: 2.2, 5.1, 5.2, 5.3, 5.4_

- [x] 3.1 Example 1 のテストを実装

  - **Example 1: インストール済み環境でのバージョン取得**
  - **検証: 要件 2.2**
  - `__version__`が`pyproject.toml`で定義されたバージョンと一致することを確認
  - テストファイル: `tests/unit/test_version_installed.py`

- [x] 4. 最終チェックポイント - すべてのテストが通ることを確認
  - すべてのテストが通ることを確認し、質問があればユーザーに尋ねる
