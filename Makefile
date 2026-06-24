.PHONY: help install start test clear

UV_SERVER = uv --directory server

help:  ## Show available commands
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*## "}; /^[a-zA-Z0-9_-]+:.*## / {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install development dependencies
	@echo "Installing development  dependencies..."
	$(UV_SERVER) sync --extra dev
	@clear

start: ## Start fastapi in dev mode
	@echo "Starting fastapi in dev mode..."
	$(UV_SERVER) run --extra dev fastapi dev --host 127.0.0.1 --port 3000

test: ## Run test suite
	@echo "Testing application..."
	$(UV_SERVER) run --extra dev pytest

clear:  ## Remove virtual environment
	@echo "Removing virtual environment..."
	rm -rf .venv
