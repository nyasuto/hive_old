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

#### PR Description Template

**すべての PR は以下のシンプルなテンプレートを使用する：**

```markdown
## 概要

この PR の内容と目的を簡潔に説明

## 変更内容

- 主要な変更点
- 技術的改善
- バグ修正や新機能

## テスト

- テストカバレッジ情報
- 動作確認方法

Closes #[issue_number]
```

#### PR Content Requirements

1. **Issue 連携**: 必ず `Closes #X` で Issue とリンク
2. **明確な説明**: 何を変更し、なぜ変更したかを説明
3. **テスト情報**: テストカバレッジと動作確認手順を含む
4. **簡潔性**: 必要最小限の情報に集中

### Pre-commit Hook Setup

- Run `make git-hooks` to setup automatic quality checks
- Prevents committing code that fails quality standards
- Saves time by catching issues early

---

## Code Quality Standards

### Quality Check Integration

Quality checks should be:

- **Automated** through Makefile targets or shell scripts
- **Consistent** across all development environments
- **Enforceable** through pre-commit hooks and CI/CD
- **Fast** to encourage frequent use

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

---

## Testing Standards

### Test Organization

- Unit tests for individual components
- Integration tests for system interactions
- Mocking external dependencies to avoid platform issues
- Clear test naming: `test_<function>_<scenario>_<expected_result>`

### CI Test Environment

- Mock platform-specific dependencies for cross-platform compatibility
- Use consistent test databases/fixtures
- Parallel test execution where possible
- Clear error reporting and debugging information

---

## Hive-Specific Development Guidelines

### Worker Development

- Each Worker should have clearly defined responsibilities
- Worker prompts should be maintained in `workers/prompts/`
- Test Worker interactions through the Comb communication system
- Document Worker capabilities and limitations

### Comb Communication System

- Use structured JSON for all inter-Worker communication
- Implement proper error handling for communication failures
- Test message routing and delivery mechanisms
- Monitor communication patterns for optimization

### Script Development

- All scripts should include proper error handling
- Use consistent logging across all scripts
- Test scripts in isolated tmux environments
- Document script dependencies and requirements

### tmux Integration

- Test multi-pane layouts thoroughly
- Handle tmux session management gracefully
- Implement proper cleanup on script exit
- Document tmux version requirements

---

## Error Handling and Debugging

### Logging Standards

- Structured logging with appropriate levels
- Context-rich error messages for debugging
- Avoid logging sensitive information
- Performance-conscious logging (lazy evaluation)

### Error Recovery

- Graceful degradation for non-critical failures
- Clear error messages for users
- Retry mechanisms with exponential backoff
- Circuit breaker patterns for external services

---

## Documentation Standards

### Code Documentation

- Clear docstrings for all Python functions and classes
- Type hints for better IDE support
- README with setup and usage instructions
- CHANGELOG for version tracking

### Process Documentation

- This CLAUDE.md file for development standards
- Contributing guidelines for external contributors
- Architecture decision records (ADRs) for major decisions
- Troubleshooting guides for common issues

---

## Security Considerations

### Secrets Management

- Never commit secrets to version control
- Use environment variables for configuration
- Scan for accidentally committed secrets

### Multi-Agent Security

- Validate all inter-Worker communications
- Implement proper access controls for shared resources
- Monitor for unusual Worker behavior patterns
- Secure temporary file handling in Comb system

### Claude Code Security

- Follow Anthropic's usage guidelines
- Implement proper API rate limiting
- Handle API failures gracefully
- Monitor token usage across multiple instances

---

## Performance Optimization

### Resource Management

- Monitor memory usage across multiple Claude instances
- Implement proper cleanup of temporary files
- Optimize file I/O in Comb communication system
- Balance Worker workloads effectively

### Scalability Considerations

- Design for horizontal scaling of Workers
- Implement efficient task distribution algorithms
- Monitor system performance under load
- Plan for graceful degradation strategies

---

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