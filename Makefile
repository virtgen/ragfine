# =========================
#  RAGFINE Development Makefile
# =========================

PYTHON      := python3
POETRY      := poetry
PYTEST      := pytest
SRC_DIR     := ragfine
TEST_DIR    := tests

# Default target
.PHONY: help
help:
	@echo "Ragfine development commands:"
	@echo "  make install        - install dev dependencies"
	@echo "  make test           - run all tests"
	@echo "  make test-fast      - run tests without slow/async ones"
	@echo "  make coverage       - run tests with coverage report"
	@echo "  make lint           - check code style with ruff & mypy"
	@echo "  make clean          - remove cache and temporary files"
	@echo "  make format         - auto-format code with black & isort"

# --------------------------
#  Setup / install
# --------------------------

.PHONY: install
install:
	@echo "Installing development dependencies..."
	$(POETRY) install --with dev

# --------------------------
#  Tests
# --------------------------

.PHONY: test
test:
	@echo "Running all tests..."
	$(POETRY) run $(PYTEST) -q $(TEST_DIR) -s

.PHONY: test-fast
test-fast:
	@echo "Running quick tests..."
	$(POETRY) run $(PYTEST) -q $(TEST_DIR) -m "not slow" -s

.PHONY: coverage
coverage:
	@echo "Running tests with coverage..."
	$(POETRY) run pytest --cov=$(SRC_DIR) --cov-report=term-missing $(TEST_DIR)

# --------------------------
#  Linting / Formatting
# --------------------------

.PHONY: lint
lint:
	@echo "Linting code..."
	$(POETRY) run ruff check $(SRC_DIR) $(TEST_DIR)
	$(POETRY) run mypy $(SRC_DIR)

.PHONY: format
format:
	@echo "Formatting code..."
	$(POETRY) run black $(SRC_DIR) $(TEST_DIR)
	$(POETRY) run isort $(SRC_DIR) $(TEST_DIR)

# --------------------------
#  Clean
# --------------------------

.PHONY: clean
clean:
	@echo "Cleaning build and cache files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	rm -rf .mypy_cache .ruff_cache .coverage coverage.xml dist build *.egg-info