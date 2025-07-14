# Hive - Claude Code Multi-Agent System
# Makefile for development automation

.PHONY: help install dev clean build test test-cov lint format type-check quality quality-fix pr-ready git-hooks env-info

# デフォルトターゲット
.DEFAULT_GOAL := help

# カラー定義
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
RED := \033[31m
RESET := \033[0m

# Python実行環境
PYTHON := python3
PIP := pip3

help: ## Show this help message
	@echo "$(BLUE)Hive - Claude Code Multi-Agent System$(RESET)"
	@echo "$(YELLOW)Available commands:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-15s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	@echo "$(BLUE)Installing dependencies...$(RESET)"
	$(PIP) install -r requirements.txt
	$(PIP) install -e ".[dev]"

dev: install ## Quick development setup
	@echo "$(BLUE)Setting up development environment...$(RESET)"
	@$(MAKE) git-hooks
	@echo "$(BLUE)Running initial quality check...$(RESET)"
	@$(MAKE) quality
	@echo "$(GREEN)Development environment ready!$(RESET)"
	@echo "$(YELLOW)Next steps:$(RESET)"
	@echo "  1. Create a feature branch: git checkout -b feat/your-feature"
	@echo "  2. Make your changes and commit with descriptive messages"
	@echo "  3. Run 'make pr-ready' before creating a pull request"

clean: ## Clean build artifacts and cache
	@echo "$(BLUE)Cleaning artifacts...$(RESET)"
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
	@echo "$(GREEN)Clean complete!$(RESET)"

build: clean ## Build package
	@echo "$(BLUE)Building package...$(RESET)"
	$(PYTHON) -m build
	@echo "$(GREEN)Build complete!$(RESET)"

test: ## Run tests
	@echo "$(BLUE)Running tests...$(RESET)"
	pytest tests/ -v

test-cov: ## Run tests with coverage
	@echo "$(BLUE)Running tests with coverage...$(RESET)"
	pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing

lint: ## Run linting
	@echo "$(BLUE)Running linter...$(RESET)"
	ruff check .

format: ## Format code
	@echo "$(BLUE)Formatting code...$(RESET)"
	ruff format .
	black .

type-check: ## Run type checking
	@echo "$(BLUE)Running type checker...$(RESET)"
	mypy .

quality: lint type-check ## Run all quality checks
	@echo "$(GREEN)All quality checks completed!$(RESET)"

quality-fix: ## Auto-fix issues where possible
	@echo "$(BLUE)Auto-fixing code issues...$(RESET)"
	ruff check . --fix
	ruff format .
	black .
	@$(MAKE) quality

pr-ready: quality test ## Ensure code is ready for PR submission
	@echo "$(GREEN)Code is ready for PR submission!$(RESET)"

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
		echo 'make quality' >> .git/hooks/pre-commit; \
		echo 'make test' >> .git/hooks/pre-commit; \
		echo 'echo "✅ Pre-commit チェック完了"' >> .git/hooks/pre-commit; \
		chmod +x .git/hooks/pre-commit; \
		echo "✅ Pre-commit hook設定完了 (フォールバック版)"; \
	fi
	@echo "$(GREEN)Git hooks setup completed!$(RESET)"

env-info: ## Show environment information
	@echo "$(BLUE)Environment Information:$(RESET)"
	@echo "Python version: $$(python3 --version)"
	@echo "Pip version: $$(pip3 --version)"
	@echo "Current directory: $$(pwd)"
	@echo "Current branch: $$(git branch --show-current 2>/dev/null || echo 'Not a git repository')"
	@echo ""
	@echo "$(BLUE)Git Hooks Status:$(RESET)"
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
	@echo "$(BLUE)Git status:$(RESET)"
	@git status --short || echo "Not a git repository"
	@echo ""
	@echo "$(BLUE)Development Tools:$(RESET)"
	@if command -v ruff >/dev/null 2>&1; then echo "✅ ruff: $$(ruff --version)"; else echo "❌ ruff: Not found"; fi
	@if command -v mypy >/dev/null 2>&1; then echo "✅ mypy: $$(mypy --version)"; else echo "❌ mypy: Not found"; fi
	@if command -v black >/dev/null 2>&1; then echo "✅ black: $$(black --version)"; else echo "❌ black: Not found"; fi
	@if command -v pytest >/dev/null 2>&1; then echo "✅ pytest: $$(pytest --version)"; else echo "❌ pytest: Not found"; fi

# Hive-specific commands
hive-start: ## Start Small Hive (Phase 1)
	@echo "$(BLUE)Starting Small Hive...$(RESET)"
	@if [ -f scripts/start-small-hive.sh ]; then \
		chmod +x scripts/start-small-hive.sh; \
		./scripts/start-small-hive.sh; \
	else \
		echo "$(RED)scripts/start-small-hive.sh not found. Please implement Issue #3 first.$(RESET)"; \
	fi

hive-stop: ## Stop Hive
	@echo "$(BLUE)Stopping Hive...$(RESET)"
	@if [ -f scripts/shutdown-hive.sh ]; then \
		chmod +x scripts/shutdown-hive.sh; \
		./scripts/shutdown-hive.sh; \
	else \
		echo "$(RED)scripts/shutdown-hive.sh not found. Please implement Issue #3 first.$(RESET)"; \
	fi

hive-status: ## Check Hive status
	@echo "$(BLUE)Checking Hive status...$(RESET)"
	@if [ -f scripts/check-comb.sh ]; then \
		chmod +x scripts/check-comb.sh; \
		./scripts/check-comb.sh; \
	else \
		echo "$(RED)scripts/check-comb.sh not found. Please implement Issue #2 first.$(RESET)"; \
	fi

hive-collect: ## Collect Honey (results)
	@echo "$(BLUE)Collecting Honey...$(RESET)"
	@if [ -f scripts/collect-honey.sh ]; then \
		chmod +x scripts/collect-honey.sh; \
		./scripts/collect-honey.sh; \
	else \
		echo "$(RED)scripts/collect-honey.sh not found. Please implement Issue #5 first.$(RESET)"; \
	fi

# Development helpers
check-deps: ## Check if all dependencies are available
	@echo "$(BLUE)Checking dependencies...$(RESET)"
	@command -v python3 >/dev/null 2>&1 || { echo "$(RED)python3 is required but not installed$(RESET)"; exit 1; }
	@command -v tmux >/dev/null 2>&1 || { echo "$(RED)tmux is required but not installed$(RESET)"; exit 1; }
	@command -v git >/dev/null 2>&1 || { echo "$(RED)git is required but not installed$(RESET)"; exit 1; }
	@echo "$(GREEN)All dependencies are available!$(RESET)"

init-project: check-deps install ## Initialize new Hive project
	@echo "$(BLUE)Initializing Hive project...$(RESET)"
	@$(MAKE) dev
	@echo "$(GREEN)Hive project initialized successfully!$(RESET)"
	@echo "$(YELLOW)Next steps:$(RESET)"
	@echo "  1. Run 'make hive-start' to start your first Hive"
	@echo "  2. Check 'make hive-status' to verify communication"
	@echo "  3. Use 'make hive-collect' to gather results"