PORT = 8000

.PHONY: help install start test clear

help:  ## Show available commands
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*## "}; /^[a-zA-Z0-9_-]+:.*## / {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install development dependencies
	@echo "Installing development  dependencies..."
	uv sync --group dev
	@clear

start: ## Start fastapi in dev mode
	@echo "Starting fastapi in dev mode..."
	uv run --group dev fastapi dev --host 0.0.0.0 --port $(PORT)

test: ## Run test suite
	@echo "Testing application..."
	uv run --group dev pytest

clear:  ## Remove virtual environment
	@echo "Removing virtual environment..."
	rm -rf .venv
