PY := python

.PHONY: help install run test lint types check

help:
	@echo "make install     install dev tooling"
	@echo "make run CH=01   run a chapter (needs ANTHROPIC_API_KEY)"
	@echo "make test        run the test suite (no API key needed)"
	@echo "make check       lint + types + tests"

install:
	$(PY) -m pip install -e ".[dev]"

# Run a single chapter against the real API, e.g. `make run CH=01`
run:
	@test -n "$(CH)" || (echo "usage: make run CH=01" && exit 1)
	@f=$$(ls chapters/$(CH)_*.py 2>/dev/null | head -1); \
	 test -n "$$f" || (echo "no chapter matching chapters/$(CH)_*.py" && exit 1); \
	 echo "running $$f"; $(PY) "$$f"

test:
	$(PY) -m pytest

lint:
	$(PY) -m ruff check .
	$(PY) -m ruff format --check .

types:
	$(PY) -m mypy

check: lint types test
