# Hive - Claude Code Multi-Agent System 開発ガイド

## 🐝 プロジェクト概要

**Hive**は、Claude Codeを複数並列実行し、各インスタンスに専門的な役割を与えて協調的にタスクを遂行するマルチエージェントシステムです。Python、Shell、tmuxを使用してAIチームを組織化し、大規模プロジェクトの効率的な開発を実現します。

---

## 🛠️ 開発ツール

**Python + Shell スクリプト環境のため、以下のコマンドを使用：**

### Essential 開発コマンド

**Core Development Commands:**

- **Quick start:** `make help` または `./scripts/start-hive.sh --help` - Show all available commands
- **Code quality:** `make quality` - Run all quality checks (lint + format + type-check)
- **Auto-fix:** `make quality-fix` - Auto-fix issues where possible
- **Development:** `make dev` - Quick setup and run cycle
- **PR preparation:** `make pr-ready` - Ensure code is ready for submission
- **Git hooks:** `make git-hooks` - Setup pre-commit hooks

### Individual Quality Targets

- `make lint` または `ruff check .` - Run linting
- `make format` または `ruff format .` - Format code  
- `make type-check` または `mypy .` - Type checking
- `make test` または `pytest` - Run tests
- `make test-cov` または `pytest --cov` - Run tests with coverage

### Development Lifecycle

- `make install` または `pip install -r requirements.txt` - Install dependencies
- `make build` - Build package
- `make clean` - Clean artifacts
- `make env-info` - Show environment information

---

## 🔄 Pull Request Creation Rule

**CRITICAL: コード変更後は必ずPull Requestを作成する**

### 必須フロー
1. コード変更完了
2. 品質チェック実行 (`npm run quality`)
3. 変更をコミット
4. **Pull Request作成** (絶対に忘れてはいけない)
5. ⚠️ **ユーザーによる承認・マージ待ち** (Claude Codeはマージしない)

### PR作成チェックリスト
- [ ] すべてのコード変更が完了している
- [ ] 品質チェックが通っている
- [ ] 適切なブランチ名になっている
- [ ] PR説明が適切に記載されている
- [ ] 関連するIssueが参照されている
- [ ] ユーザーに承認・マージを依頼

## GitHub Issue Management Rules

### 🔴 CRITICAL: Issue Language Requirement

**ALL GitHub issues MUST be written in 日本語 - This is a project rule.**

### Required Issue Format

All issues must follow this template:

```markdown
## 🎯 [ISSUE_TYPE]: [BRIEF_DESCRIPTION]

### **Priority: [CRITICAL/HIGH/MEDIUM/LOW]**

**Impact:** [IMPACT_SCOPE]

**Component:** [RELATED_COMPONENTS]

**Files:** [RELATED_FILES]

### Problem Description

[Detailed problem description and background]

### Recommended Solution

[Detailed solution to implement]

### Acceptance Criteria

- [ ] [Specific completion condition 1]
- [ ] [Specific completion condition 2]

**[Value explanation to project]**
```

### Required Label System

All issues MUST have both Priority and Type labels:

#### Priority Labels

- `priority: critical` - Critical (app crashes, security issues)
- `priority: high` - High (core features, important bugs)
- `priority: medium` - Medium (improvements, minor bugs)
- `priority: low` - Low (future features, documentation)

#### Type Labels

- `type: feature` - New feature
- `type: bug` - Bug fix
- `type: enhancement` - Enhancement to existing feature
- `type: docs` - Documentation
- `type: test` - Test related
- `type: refactor` - Code refactoring
- `type: ci/cd` - CI/CD pipeline
- `type: security` - Security related

---

## Git Workflow and Branch Management

### Core Git Rules

- **NEVER commit directly to main branch**
- Always create feature branches for changes
- Create Pull Requests for ALL changes, regardless of size
- All commits must follow conventional commit format
- Include issue references in PR descriptions: `Closes #X`

### Branch Naming Convention

Use descriptive, consistent branch names:

- Feature: `feat/issue-X-feature-name`
- Bug fix: `fix/issue-X-description`
- Hotfix: `hotfix/X-description`
- Test: `test/X-description`
- Docs: `docs/X-description`
- CI/CD: `ci/X-description` or `cicd/X-description`
- Refactor: `refactor/X-description`
- Performance: `perf/X-description`
- Security: `security/X-description`
- Dependencies: `deps/X-description`

### Commit Message Format

```
<type>: <description>

<optional body explaining what and why>

<optional footer with issue references>

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Commit Types:** feat, fix, docs, style, refactor, test, chore, ci

### Required Development Workflow

1. Create feature branch from main
2. Make changes
3. **Run quality checks before commit:**
   - `make quality` (comprehensive checks)
   - OR `make quality-fix` (auto-fix + check)
4. Commit only after all checks pass
5. Push branch to remote
6. Create Pull Request with descriptive title and body
7. Wait for CI checks to pass
8. Merge via GitHub interface (not locally)

### Pull Request Guidelines

#### PR Title Format

**PR タイトルは日本語で記述し、以下の形式に従う：**

```
<type>: <brief description in 日本語>
```

**Examples:**

- `feat: Phase 2.0 アセンブリコード生成器実装`
- `fix: GitHub Actions CI失敗の修正`
- `docs: API仕様書の更新`
- `refactor: パーサーモジュールのリファクタリング`


### Essential Quality Tools

**Python-specific tools:**

- **Linting:** `ruff` (fast Python linter)
- **Formatting:** `ruff format` or `black` (code formatting)
- **Type Checking:** `mypy` (static type checking)
- **Testing:** `pytest` with coverage reporting

**Shell-specific tools:**

- **Linting:** `shellcheck` (shell script analysis)
- **Formatting:** `shfmt` (shell script formatting)

### CI/CD Integration

- All quality checks must pass in CI before merge
- Separate CI jobs for different check types (lint, test, type-check)
- Coverage reporting and tracking
- Security scanning where applicable



## GitHub Integration with MCP Tools

### 🔧 MCP Tool Usage for GitHub Access

**ALWAYS use MCP tools when accessing GitHub** - This provides better integration and functionality.

#### Preferred GitHub Access Methods

1. **WebFetch Tool for GitHub URLs**

```
Use WebFetch tool to access GitHub pages:
- Pull requests: https://github.com/owner/repo/pull/123
- Issues: https://github.com/owner/repo/issues/123
- Commits: https://github.com/owner/repo/commit/hash
- Releases: https://github.com/owner/repo/releases
```

2. **GitHub CLI Integration**

```bash
# Use gh command via Bash tool for GitHub operations
gh pr view 123 # View pull request details
gh issue view 123 # View issue details
gh pr create # Create pull requests
gh issue create # Create issues
gh repo view # View repository information
```

3. **WebFetch Prompt Guidelines**

```
When using WebFetch for GitHub URLs, use specific prompts:
- "Extract pull request details including title, status, description, comments, and reviews"
- "Get issue information including labels, assignees, status, and discussion"
- "Summarize commit details including changes, files modified, and commit message"
```

#### GitHub Access Workflow

1. **Always try MCP tools first** before manual URL construction
2. **Use WebFetch** for viewing GitHub content (PRs, issues, commits)
3. **Use Bash + gh command** for GitHub operations (create, update, merge)
4. **Verify results** by re-fetching the updated content via MCP

### MCP Tool Benefits for GitHub

- **Real-time data**: Always gets current GitHub state
- **Rich content**: Extracts formatted information and metadata
- **Integrated workflow**: Seamless integration with development process
- **Error handling**: Better error messages and retry capabilities

---

## Hive Project Specific Notes

### Project Language
**プロジェクト言語**: 日本語
**Build System**: Make + Python + Shell scripts
**Primary Tech Stack**: Python 3.9+, tmux, Claude Code API

### Environment Setup
```bash
# Required tools
python --version  # 3.9+
tmux -V          # 3.0+
make --version   # Build automation

# Optional but recommended  
ruff --version   # Python linting/formatting
mypy --version   # Type checking
pytest --version # Testing
```

### Quick Start Commands
```bash
# Initial setup
make install

# Development workflow
make dev          # Start development environment
make quality      # Run all quality checks
make test         # Run test suite

# Hive-specific
./scripts/start-hive.sh --size=small  # Start basic Hive
./scripts/check-comb.sh               # Check communication
./scripts/collect-honey.sh            # Collect results
```

---

# important-instruction-reminders

Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.