.PHONY: compare judge-only clean help

compare: ## Run the full matrix (corpus x candidates x judges) with keys from the Hermes pass store
	uv run python scripts/run_with_key.py

judge-only: ## Re-judge existing candidate outputs without re-running structure.py
	uv run python scripts/run_with_key.py --judge-only

clean: ## Remove generated result dirs, preserving the committed 2026-08-20 one
	find results -mindepth 1 -maxdepth 1 -type d ! -name '2026-08-20-summary-structuring' -exec rm -rf {} +

help: ## List available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "%-12s %s\n", $$1, $$2}'
