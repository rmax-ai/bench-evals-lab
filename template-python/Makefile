.PHONY: run test clean

run:
	python3 scripts/run.py

test:
	@if command -v pytest >/dev/null 2>&1; then pytest; else echo "pytest unavailable; skipping tests"; fi

clean:
	rm -rf results/
