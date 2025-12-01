# Python 実行環境ルール

## パッケージ管理と Python 実行

- **必須**: すべての Python 実行には`uv`を使用すること
- **禁止**: `pip`の使用は厳禁

## 具体的な使用方法

### パッケージのインストール

```bash
uv pip install <package-name>
```

### Python スクリプトの実行

```bash
uv run python <script.py>
```

### 仮想環境での実行

```bash
uv venv
source .venv/bin/activate  # macOS/Linux
uv pip install -r requirements.txt
```

### プロジェクトの依存関係管理

```bash
uv sync
```

## 理由

このプロジェクトでは、高速で信頼性の高い Python パッケージマネージャーである`uv`を標準として採用しています。一貫性を保つため、`pip`の使用は避けてください。
