# Hive - Claude Code Multi-Agent System 開発ガイド

## 🐝 プロジェクト概要

**Hive**は、Claude Codeを複数並列実行し、各インスタンスに専門的な役割を与えて協調的にタスクを遂行するマルチエージェントシステムです。Python、Shell、tmuxを使用してAIチームを組織化し、大規模プロジェクトの効率的な開発を実現します。

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


**Commit Types:** feat, fix, docs, style, refactor, test, chore, ci

### Required Development Workflow

1. Create feature branch from main
2. Make changes
3. **Run quality checks and auto-fix:**
   ```bash
   make quality  # Auto-fix linting + formatting + type check
   ```
4. **Check for auto-fix changes and commit if needed:**
   ```bash
   # Check if quality fixes created changes
   if [ -n "$(git status --porcelain)" ]; then
     git add .
     git commit -m "style: Auto-fix code formatting and linting issues

   🤖 Generated with [Claude Code](https://claude.ai/code)

   Co-Authored-By: Claude <noreply@anthropic.com>"
   fi
   ```
5. Make your actual feature/fix commits
6. Push branch to remote
7. Create Pull Request with descriptive title and body
8. Wait for CI checks to pass
9. Merge via GitHub interface (not locally)

### Pull Request Guidelines

#### PR Title Format

** PR は日本語で記述する **


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
make quality      # Run all quality checks with auto-fix
make test         # Run test suite

# Hive-specific
./scripts/start-hive.sh --size=small  # Start basic Hive
./scripts/check-comb.sh               # Check communication
./scripts/collect-honey.sh            # Collect results
```

### 🔄 Standard Development Workflow

**推奨する開発フローの詳細手順:**

```bash
# 1. Feature branch作成
git checkout main
git pull origin main
git checkout -b feat/issue-X-description

# 2. 変更作業
# ... コード変更 ...

# 3. 品質チェック・自動修正
make quality

# 4. 自動修正があった場合の専用コミット
if [ -n "$(git status --porcelain)" ]; then
  git add .
  git commit -m "style: Auto-fix code formatting and linting issues

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
fi

# 5. 実際の変更をコミット
git add .
git commit -m "feat: 新機能の実装

詳細な説明...

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# 6. PR作成
git push -u origin feat/issue-X-description
gh pr create --title "feat: 新機能の実装" --body "..."
```

### 🎯 Quality Commands Reference

- **`make quality`**: 自動修正 + 検証 (推奨)
- **`make quality-check`**: 検証のみ (CI用)
- **`make quality-fix`**: quality のエイリアス
- **`make pr-ready`**: quality + test (PR準備)

---
