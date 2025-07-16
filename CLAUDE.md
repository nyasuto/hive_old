# Hive - Claude Code Multi-Agent System 開発ガイド

## 🐝 プロジェクト概要

**Hive**は、Claude Codeを複数並列実行し、各インスタンスに専門的な役割を与えて協調的にタスクを遂行するマルチエージェントシステムです。Python、Shell、tmuxを使用してAIチームを組織化し、大規模プロジェクトの効率的な開発を実現します。

---

## 🛠️ 開発ツール

### Essential 開発コマンド

#### 🔍 探索・実験フェーズ (現在)
- **`make quality-light`**: 軽量品質チェック (探索用)
- **`make poc-ready`**: PoCレディネスチェック (実験用)
- **`make test`**: テスト実行

#### 🚀 安定化フェーズ (PoC完成後)
- **`make quality`**: 自動修正 + 検証 (推奨)
- **`make quality-check`**: 検証のみ (CI用)
- **`make pr-ready`**: quality + test (PR準備)

---

## 🔄 Standard Development Workflow

```bash
# 1. Feature branch作成
git checkout main && git pull origin main
git checkout -b feat/issue-X-description

# 2. 変更作業
# ... コード変更 ...

# 3. 品質チェック・自動修正 (フェーズに応じて選択)
make quality-light  # 探索・実験フェーズ
# make quality      # 安定化フェーズ

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

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# 6. PR作成
git push -u origin feat/issue-X-description
gh pr create --title "feat: 新機能の実装" --body "..."
```

---

## Git Workflow Rules

### Core Rules
- **NEVER commit directly to main branch**
- Always create feature branches
- Create Pull Requests for ALL changes
- All commits must follow conventional commit format

### Branch Naming
- Feature: `feat/issue-X-feature-name`
- Bug fix: `fix/issue-X-description`
- Docs: `docs/X-description`

### Commit Format
```
<type>: <description>

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types:** feat, fix, docs, style, refactor, test, chore, ci

---

## Issue Management

### Issue Language
**ALL GitHub issues MUST be written in 日本語**

### PR Title Format
```
<type>: <brief description in 日本語>
```

### PR Template
```markdown
## 概要
この PR の内容と目的を簡潔に説明

## 変更内容
- 主要な変更点
- 技術的改善

## テスト
- テストカバレッジ情報
- 動作確認方法

Closes #[issue_number]
```

---

## Project Specific

### Tech Stack
- **Language**: Python 3.9+
- **Build System**: Make + Shell scripts
- **Communication**: tmux + Claude Code API
- **Project Language**: 日本語

### Quick Commands
```bash
# Setup
make install && make dev

# Quality
make quality          # Auto-fix + check
make pr-ready         # Full validation

# Hive operations
./scripts/start-hive.sh --size=small
./scripts/check-comb.sh
./scripts/collect-honey.sh
```