# agentpack

Claude Codeを使ったAI支援開発のためのスターターテンプレート。

## 技術スタック

- Python 3.13+
- uv (パッケージ管理)
- MCP統合、devcontainer対応

## クイックスタート

```bash
python main.py
```

## 開発環境

**環境変数:**
- devcontainer: `.devcontainer/.env.example` → `.devcontainer/.env` にコピー
- ローカル: `mise.local.toml` に設定（gitignore済み）

## CLIツール

Bash使用時はモダンCLIを優先:
- `fd` > `tree`, `find`, `ls -R`
- `rg` > `grep`, `cat | grep`
- `sd` > `sed`, `awk`
- `jq` でJSON処理

## Python開発

**パッケージ管理 (uv):**
- `uv add package` - インストール
- `uv run tool` - ツール実行
- `pip`, `uv pip install` は使用禁止

**コード品質:**
- `uv run ruff format .` - フォーマット
- `uv run ruff check .` - リント
- `uv run ty check` - 型チェック

**テスト:**
- `uv run pytest`
- 非同期: `anyio` を使用

**pre-commit:**
- git commit時に自動実行
- Prettier (YAML/JSON), Ruff, ty (Python)
