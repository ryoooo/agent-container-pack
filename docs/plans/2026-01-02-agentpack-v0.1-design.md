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
6. Skills（required）のfrontmatter形式を検証できる
7. 変数参照`${VAR}`が`.devcontainer/.env`に存在するか検証できる

### v0.1で対象外（v0.2以降）

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
AGENTS.md              # Codex用ドキュメント（CLAUDE.mdと同一内容）
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

## Stack選択ロジック

### detect.any

各stackに`detect.any`を定義し、ファイル存在チェックで自動選択：

```yaml
stacks:
  python:
    detect:
      any: ["pyproject.toml", "requirements.txt"]
  node:
    detect:
      any: ["package.json"]
```

### 選択ルール

**single-stack（docs.mode: single-stack）：**
- `--stack`指定あり: 指定されたstackを使用
- `--stack auto`または未指定:
  - detect一致が1件: それを採用
  - detect一致が複数: エラー（曖昧）
  - detect一致が0件: エラー（対象不明）

**multi-stack（docs.mode: multi-stack）：**
- detect一致のstackを列挙し、ドキュメント内でセクション分けして併記
- 一致が0件の場合はエラー

---

## Manifestフォーマット（agentpack.yml）

```yaml
version: "1"

project:
  name: "my-app"
  description: "プロジェクト概要"

docs:
  mode: single-stack        # single-stack | multi-stack
  defaultStack: auto        # auto | <stack-id>
  maxLines: 250             # 肥大化warning基準

stack: python               # 使用するstack（single-stack時）

stacks:
  python:
    detect:
      any: ["pyproject.toml", "requirements.txt"]
    deps: "uv sync"
    lint: "uv run ruff check ."
    typecheck: "uv run ty check"
    test: "uv run pytest"
    run: "uv run python main.py"
    skills:
      required: ["python-dev"]

skills:
  root: ".claude/skills"    # デフォルト

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

safety:
  preset: default           # default | none
  custom:                   # 追加ルール（オプション）
    - "本番DBに直接接続しない"

custom_content: |
  ## クイックスタート

  ```bash
  python main.py
  ```

  ## CLIツール

  - `fd` > `find`
  - `rg` > `grep`
```

### Safetyプリセット

**preset: default** の内容：
1. secrets禁止（API_KEY等を直書きしない）
2. 破壊操作は段階的に: dry-run → diff → apply

---

## Skills仕様

### 位置

`skills.root`で指定（デフォルト: `.claude/skills`）

### 構造

```
.claude/skills/<skill-id>/SKILL.md
```

### 検証（v0.1）

[agentskills.io仕様](https://agentskills.io/specification)に準拠：

**frontmatter必須フィールド：**
- `name`: 1-64文字、小文字英数字+ハイフン、親ディレクトリ名と一致
- `description`: 1-1024文字

```yaml
---
name: python-dev
description: Python開発のベストプラクティスと手順
---

## 目的
...
```

**検証内容：**
- SKILL.mdの存在チェック
- frontmatterのname, descriptionの存在と形式
- nameとディレクトリ名の一致（v0.2で追加予定）

---

## 変数参照

### 形式

MCP設定内で`${VAR}`または`${env:VAR}`形式で環境変数を参照可能。

### 検証

- 生成時に展開しない（そのまま出力）
- `.devcontainer/.env`に変数が定義されているかチェック
- 未定義の場合はwarning

---

## 出力ファイルフォーマット

### CLAUDE.md / AGENTS.md

両ファイルは**同一内容**で生成。

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

## Safety

- secrets禁止（API_KEY等を直書きしない）
- 破壊操作は段階的に: dry-run → diff → apply
{safety.custom}

{custom_content}
```

### multi-stack時の構造

```markdown
# {project.name}

{project.description}

## Python

### Commands
...

## Node

### Commands
...
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

**STDIOサーバ：**
```toml
[mcp_servers.memory]
command = "npx"
args = ["@anthropic/mcp-memory"]
env = { "MEMORY_PATH" = "${workspaceFolder}/.memory" }
```

**HTTPサーバ：**
```toml
[mcp_servers.external-api]
url = "https://api.example.com/mcp"
```

**v0.1でサポートするフィールド：**
- `command`, `args`, `env`, `cwd`（STDIO）
- `url`（HTTP）

**v0.2以降で追加予定：**
- `startup_timeout_sec`, `tool_timeout_sec`
- `enabled_tools`, `disabled_tools`
- `bearer_token_env_var`, `http_headers`

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
    markdown.py       # CLAUDE.md/AGENTS.md生成（共通）
    settings.py       # .claude/settings.json生成
    codex_config.py   # codex.config.toml生成
  validators/
    skills.py         # Skills検証
    env.py            # 環境変数検証
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
   - Skills検証
   - 環境変数検証

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
    multi-stack.yml
  snapshots/
  test_manifest.py
  test_generators.py
  test_validators.py
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
| CLAUDE.md/AGENTS.md | 同一内容 | シンプルに保つ |
| multi-stack | 対応 | モノレポ対応 |
| Safety | プリセット＋カスタム | 柔軟性と簡便さのバランス |
| Skills検証 | frontmatter検証 | agentskills.io仕様準拠 |
| 変数参照検証 | .devcontainer/.env | devcontainer環境を想定 |
| codex.config.toml | 基本フィールドのみ | 必要に応じて拡張 |
| テンプレート継承 | コピー運用（v0.1） | 将来的にextends追加 |
| ランタイムバージョン | 扱わない | シンプルに保つ |

---

## 今後の拡張（v0.2以降）

- Drift/Lint
- 推定補完
- MCP詳細設定（タイムアウト、ツール制限等）
- Hooks/Subagents生成
- Doctor
- テンプレート継承（extends）
- Skills完全検証（name/ディレクトリ一致、行数警告）
- 出力ターゲット選択（claude/codex）
