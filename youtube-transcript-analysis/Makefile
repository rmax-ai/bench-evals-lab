.PHONY: compare judge clean help

compare: ## Run transcript, analysis, and judge over every configured pair
	uv run python scripts/compare.py

judge: ## Judge existing analysis artifacts without re-running analyses
	uv run python scripts/compare.py --judge-only

clean: ## Remove generated result directories, preserving committed artifacts
	find results -mindepth 1 -maxdepth 1 -type d ! -name '2026-08-15-openwiki-analysis' ! -name '2026-08-16-openwiki-analysis' -exec rm -rf {} +

help: ## List available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "%-12s %s\n", $$1, $$2}'
