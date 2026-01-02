# Agentpack v0.1 設計ドキュメント

## 概要

Agentpackは、`agentpack.yml`をSSoT（Single Source of Truth）として、Claude CodeとCodex CLIの運用差分を吸収し、CLAUDE.md/AGENTS.md等を一貫生成するCLIツール。

### 主要ユースケース

1. **チーム配布** - 新メンバーが`agentpack generate --write`を実行して、すぐにClaude Code/Codexを使える状態にする
2. **テンプレート再利用** - 複数プロジェクトで統一したagentpack.ymlテンプレートを使い回す（v0.1はコピー運用）

---

## v0.1 スコープ

### コマンド

```
agentpack init [--template <source>] [--stack <id>] [directory]
agentpack generate [--write] [--stack <id>]
```

### 受け入れ条件

1. `agentpack init`でdevcontainer + agentpack.ymlスケルトンを取得できる
2. `agentpack generate`でCLAUDE.md/AGENTS.mdを再現性高く生成できる
3. stackごとにdeps/lint/typecheck/test/runが必ず提示される
4. MCP定義から`.claude/settings.json`と`codex.config.toml`を生成できる
5. http MCPの接続先をファイアウォール（init-firewall.sh）に自動追加できる（失敗時はwarning）

### v0.1で対象外（v0.2以降）

- Skills整合チェック
- Drift/Lint
- 推定補完
- Hooks/Subagents生成
- Doctor

---

## コマンド仕様

### `agentpack init`

```
agentpack init [--template <source>] [--stack <id>] [directory]
```

**引数・オプション：**
- `directory`: 初期化先ディレクトリ（デフォルト: カレント）
- `--template`: テンプレートソース（デフォルト: `github:agentpack/template-default`）
- `--stack`: 使用するstack（python, node, rust, go等）

**動作：**
1. テンプレートリポジトリから`.devcontainer/`をダウンロード
2. `agentpack.yml`のスケルトンを生成（--stackで指定されたstackを含む）
3. 既存ファイルがある場合は上書き確認（`--force`で強制上書き）

**テンプレートソース形式：**
```
github:owner/repo          # GitHubリポジトリ
github:owner/repo@branch   # 特定ブランチ
github:owner/repo#subdir   # サブディレクトリ
```

**生成されるファイル：**
```
.devcontainer/
  devcontainer.json
  Dockerfile
  init-firewall.sh
  .env.example
agentpack.yml              # スケルトン
```

### `agentpack generate`

```
agentpack generate [--write] [--stack <id>]
```

**オプション：**
- `--write`: 実際にファイルを更新（なければdry-run表示）
- `--stack`: 使用するstack（autoの場合はdetectで自動選択）

**生成物：**
```
CLAUDE.md              # Claude Code用ドキュメント
AGENTS.md              # Codex用ドキュメント
.claude/settings.json  # MCP設定（mcpServers）
codex.config.toml      # Codex用MCP設定
```

**devcontainer更新（付随動作）：**

1. **ファイアウォール更新：**
   - `init-firewall.sh`が存在する場合、http MCPのドメインを追加

2. **環境変数更新：**
   - `.env.example`に必要な環境変数をプレースホルダーとして追記
   - `devcontainer.json`に`.env`読み込み設定を追加（未設定の場合）

**失敗時の挙動：**
- devcontainer関連の更新が失敗してもwarningを出力し、generate自体は続行

**決定的生成：**
- 同じ`agentpack.yml`からは常に同じ出力
- タイムスタンプやランダム値は含めない

---

## Manifestフォーマット（agentpack.yml）

```yaml
version: "1"

project:
  name: "my-app"
  description: "プロジェクト概要"

stack: python

stacks:
  python:
    deps: "uv sync"
    lint: "uv run ruff check ."
    typecheck: "uv run ty check"
    test: "uv run pytest"
    run: "uv run python main.py"

mcp:
  servers:
    memory:
      transport: stdio
      command: ["npx", "@anthropic/mcp-memory"]
      env:
        MEMORY_PATH: "${workspaceFolder}/.memory"
    external-api:
      transport: http
      url: "https://api.example.com/mcp"
      env:
        API_KEY: "${env:EXAMPLE_API_KEY}"

workflows:
  - name: "開発フロー"
    steps:
      - "uv run ruff format . && uv run ruff check ."
      - "uv run pytest"

pre_commit: ["prettier", "ruff", "ty"]

custom_content: |
  ## クイックスタート

  ```bash
  python main.py
  ```

  ## CLIツール

  - `fd` > `find`
  - `rg` > `grep`
```

---

## 出力ファイルフォーマット

### CLAUDE.md / AGENTS.md

```markdown
# {project.name}

{project.description}

## Commands

- **deps**: `{stack.deps}`
- **lint**: `{stack.lint}`
- **typecheck**: `{stack.typecheck}`
- **test**: `{stack.test}`
- **run**: `{stack.run}`

## Workflows

### {workflow.name}
1. `{workflow.steps[0]}`
2. `{workflow.steps[1]}`

## Pre-commit

- {pre_commit[0]}
- {pre_commit[1]}
- ...

{custom_content}
```

### .claude/settings.json

```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["@anthropic/mcp-memory"],
      "env": {
        "MEMORY_PATH": "${workspaceFolder}/.memory"
      }
    }
  }
}
```

### codex.config.toml

Codexの設定フォーマットに準拠（要調査）

---

## アーキテクチャ

### ディレクトリ構成

```
src/agentpack/
  __init__.py
  cli.py              # CLIエントリポイント（cyclopts使用）
  manifest/
    loader.py         # YAML読み込み・バリデーション
    schema.py         # Pydanticモデル定義
  generators/
    claude_md.py      # CLAUDE.md生成
    agents_md.py      # AGENTS.md生成
    settings.py       # .claude/settings.json生成
    codex_config.py   # codex.config.toml生成
  devcontainer/
    firewall.py       # init-firewall.sh更新
    env.py            # .env.example更新
  init/
    template.py       # テンプレートダウンロード
```

### 依存ライブラリ

```
cyclopts    - CLI
pydantic    - バリデーション
pyyaml      - YAML読み込み
httpx       - HTTP（テンプレートDL）
```

### テンプレート生成方式

f-string/format を使用（Jinja2は使用しない）

---

## テスト戦略

### テストの種類

1. **スナップショットテスト（メイン）**
   - 入力: `agentpack.yml`のフィクスチャ
   - 出力: 生成されたCLAUDE.md/AGENTS.md等
   - ツール: `pytest` + `syrupy`（スナップショット）

2. **ユニットテスト**
   - Manifestのバリデーション
   - 各ジェネレータの個別テスト

3. **統合テスト**
   - `agentpack init` / `agentpack generate` のE2E
   - 一時ディレクトリで実行

### ディレクトリ構成

```
tests/
  fixtures/
    minimal.yml
    full.yml
    python-stack.yml
  snapshots/
  test_manifest.py
  test_generators.py
  test_cli.py
```

---

## 設計決定の記録

| 項目 | 決定 | 理由 |
|-----|------|------|
| CLIライブラリ | cyclopts | 軽量、Pydantic統合、click依存なし |
| YAMLライブラリ | pyyaml | 読み込みのみで十分 |
| HTTPライブラリ | httpx | モダン、同期/非同期両対応 |
| バリデーション | pydantic | エコシステム充実、cyclopts統合 |
| テンプレート生成 | f-string | シンプル、依存なし |
| CLAUDE.md/AGENTS.md | 完全分離 | Claude Code専用 / Codex専用 |
| Skills | 存在チェックのみ（v0.1） | 将来的に生成・lint追加 |
| テンプレート継承 | コピー運用（v0.1） | 将来的にextends追加 |
| ランタイムバージョン | 扱わない | シンプルに保つ |

---

## 今後の拡張（v0.2以降）

- Skills整合チェック（Phase 1）
- Drift/Lint（Phase 2）
- 推定補完（Phase 3）
- MCP詳細設定（Phase 4）
- Hooks/Subagents生成（Phase 5）
- Doctor（Phase 6）
- テンプレート継承（extends）
- Skills生成・lint
- 出力ターゲット選択（claude/codex）
