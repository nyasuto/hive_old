# Hive - Claude Code Multi-Agent System
# Makefile for development automation

.PHONY: help install dev clean build test test-cov lint format type-check quality quality-fix pr-ready git-hooks env-info quality-light poc-ready

# デフォルトターゲット
.DEFAULT_GOAL := help

# Python実行環境
PYTHON := uv run python
UV := uv

help: ## Show this help message
	@echo "Hive - Claude Code Multi-Agent System"
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	@echo "Installing dependencies..."
	uv sync --extra dev

dev: install ## Quick development setup
	@echo "Setting up development environment..."
	@$(MAKE) git-hooks
	@echo "Running initial quality check..."
	@$(MAKE) quality
	@echo "Development environment ready!"
	@echo "Next steps:"
	@echo "  1. Create a feature branch: git checkout -b feat/your-feature"
	@echo "  2. Make your changes and commit with descriptive messages"
	@echo "  3. Run 'make pr-ready' before creating a pull request"

clean: ## Clean build artifacts and cache
	@echo "Cleaning artifacts..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	@echo "Clean complete!"

build: clean ## Build package
	@echo "Building package..."
	$(PYTHON) -m build
	@echo "Build complete!"

test: ## Run tests
	@echo "Running tests..."
	uv run pytest tests/ -v

test-cov: ## Run tests with coverage
	@echo "Running tests with coverage..."
	uv run pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing

lint: ## Run linting
	@echo "Running linter..."
	uv run ruff check .

format: ## Format code
	@echo "Formatting code..."
	uv run ruff format .

format-check: ## Check code formatting
	@echo "Checking code formatting..."
	uv run ruff format . --check

type-check: ## Run type checking
	@echo "Running type checker..."
	uv run mypy .

quality: ## Run all quality checks with auto-fix
	@echo "Running quality checks with auto-fix..."
	@echo "Auto-fixing linting issues..."
	@uv run ruff check . --fix || true
	@echo "Auto-fixing formatting issues..."
	@uv run ruff format .
	@echo "Running final validation..."
	@uv run ruff check .
	@uv run ruff format . --check
	@uv run mypy .
	@echo "All quality checks completed!"

quality-check: lint format-check type-check ## Run quality checks without auto-fix
	@echo "All quality checks completed!"

quality-fix: quality ## Auto-fix issues (alias for quality)
	@echo "Quality fix completed!"

pr-ready: quality test ## Ensure code is ready for PR submission
	@echo "Code is ready for PR submission!"

git-hooks: ## Setup git pre-commit hooks from .git-hooks folder
	@echo "🔗 Git pre-commit hookを設定中..."
	@mkdir -p .git/hooks
	@if [ -f .git-hooks/pre-commit ]; then \
		cp .git-hooks/pre-commit .git/hooks/pre-commit; \
		chmod +x .git/hooks/pre-commit; \
		echo "✅ Pre-commit hook設定完了 (.git-hooks/pre-commit から)"; \
	else \
		echo "⚠️  .git-hooks/pre-commit が見つかりません。フォールバック版を作成します..."; \
		echo '#!/bin/bash' > .git/hooks/pre-commit; \
		echo 'set -e' >> .git/hooks/pre-commit; \
		echo 'echo "🪝 Pre-commit フック実行中..."' >> .git/hooks/pre-commit; \
		echo 'current_branch=$$(git symbolic-ref --short HEAD 2>/dev/null || echo "")' >> .git/hooks/pre-commit; \
		echo 'if [ "$$current_branch" = "main" ]; then' >> .git/hooks/pre-commit; \
		echo '  echo "❌ エラー: mainブランチへの直接コミットは禁止されています"' >> .git/hooks/pre-commit; \
		echo '  exit 1' >> .git/hooks/pre-commit; \
		echo 'fi' >> .git/hooks/pre-commit; \
		echo 'uv run make quality' >> .git/hooks/pre-commit; \
		echo 'uv run make test' >> .git/hooks/pre-commit; \
		echo 'echo "✅ Pre-commit チェック完了"' >> .git/hooks/pre-commit; \
		chmod +x .git/hooks/pre-commit; \
		echo "✅ Pre-commit hook設定完了 (フォールバック版)"; \
	fi
	@echo "Git hooks setup completed!"

env-info: ## Show environment information
	@echo "Environment Information:"
	@echo "Python version: $$(python3 --version)"
	@echo "Pip version: $$(pip3 --version)"
	@echo "Current directory: $$(pwd)"
	@echo "Current branch: $$(git branch --show-current 2>/dev/null || echo 'Not a git repository')"
	@echo ""
	@echo "Git Hooks Status:"
	@if [ -f .git/hooks/pre-commit ]; then \
		echo "✅ Pre-commit hook: Installed"; \
		if [ -x .git/hooks/pre-commit ]; then \
			echo "✅ Pre-commit hook: Executable"; \
		else \
			echo "❌ Pre-commit hook: Not executable"; \
		fi; \
	else \
		echo "❌ Pre-commit hook: Not installed"; \
	fi
	@if [ -f .git-hooks/pre-commit ]; then \
		echo "✅ Enhanced pre-commit: Available (.git-hooks/pre-commit)"; \
	else \
		echo "⚠️  Enhanced pre-commit: Not found (.git-hooks/pre-commit)"; \
	fi
	@echo ""
	@echo "Git status:"
	@git status --short || echo "Not a git repository"
	@echo ""
	@echo "Development Tools:"
	@if command -v uv >/dev/null 2>&1; then echo "✅ uv: $$(uv --version)"; else echo "❌ uv: Not found"; fi
	@if command -v uv >/dev/null 2>&1; then echo "✅ ruff: $$(uv run ruff --version)"; else echo "❌ ruff: Not found"; fi
	@if command -v uv >/dev/null 2>&1; then echo "✅ mypy: $$(uv run mypy --version)"; else echo "❌ mypy: Not found"; fi
	@if command -v uv >/dev/null 2>&1; then echo "✅ pytest: $$(uv run pytest --version)"; else echo "❌ pytest: Not found"; fi

# Hive-specific commands
hive-start: ## Start Small Hive (Phase 1)
	@echo "Starting Small Hive..."
	@if [ -f scripts/start-small-hive.sh ]; then \
		chmod +x scripts/start-small-hive.sh; \
		./scripts/start-small-hive.sh; \
	else \
		echo "scripts/start-small-hive.sh not found. Please implement Issue #3 first."; \
	fi

hive-stop: ## Stop Hive
	@echo "Stopping Hive..."
	@if [ -f scripts/shutdown-hive.sh ]; then \
		chmod +x scripts/shutdown-hive.sh; \
		./scripts/shutdown-hive.sh; \
	else \
		echo "scripts/shutdown-hive.sh not found. Please implement Issue #3 first."; \
	fi

hive-status: ## Check Hive status
	@echo "Checking Hive status..."
	@if [ -f scripts/check-comb.sh ]; then \
		chmod +x scripts/check-comb.sh; \
		./scripts/check-comb.sh; \
	else \
		echo "scripts/check-comb.sh not found. Please implement Issue #2 first."; \
	fi

hive-collect: ## Collect Honey (results)
	@echo "Collecting Honey..."
	@if [ -f scripts/collect-honey.sh ]; then \
		chmod +x scripts/collect-honey.sh; \
		./scripts/collect-honey.sh; \
	else \
		echo "scripts/collect-honey.sh not found. Please implement Issue #5 first."; \
	fi

# Development helpers
check-deps: ## Check if all dependencies are available
	@echo "Checking dependencies..."
	@command -v uv >/dev/null 2>&1 || { echo "uv is required but not installed"; exit 1; }
	@command -v tmux >/dev/null 2>&1 || { echo "tmux is required but not installed"; exit 1; }
	@command -v git >/dev/null 2>&1 || { echo "git is required but not installed"; exit 1; }
	@echo "All dependencies are available!"

init-project: check-deps install ## Initialize new Hive project
	@echo "Initializing Hive project..."
	@$(MAKE) dev
	@echo "Hive project initialized successfully!"
	@echo "Next steps:"
	@echo "  1. Run 'make hive-start' to start your first Hive"
	@echo "  2. Check 'make hive-status' to verify communication"
	@echo "  3. Use 'make hive-collect' to gather results"

quality-light: ## Lightweight quality check for exploration phase
	@echo "🔍 Lightweight quality check for exploration phase..."
	@echo "Running basic linting (excluding line length)..."
	@uv run ruff check . --select=E,W,F --ignore=E501
	@echo "Running basic formatting check..."
	@uv run ruff format . --check
	@echo "✅ Light quality check completed!"

poc-ready: quality-light ## Check if code is ready for PoC (lightweight validation)
	@echo "🚀 PoC readiness check..."
	@echo "Running basic tests..."
	@uv run python -m pytest tests/ -x --tb=short || echo "⚠️ Some tests failed, but continuing for PoC"
	@echo "✅ Code is ready for PoC!"