.PHONY: compare clean help

compare: ## Run every configured video and model comparison
	uv run python scripts/compare.py

clean: ## Remove generated result directories, preserving committed artifacts
	find results -mindepth 1 -maxdepth 1 -type d ! -name '2026-08-15-openwiki-analysis' -exec rm -rf {} +

help: ## List available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "%-12s %s\n", $$1, $$2}'
