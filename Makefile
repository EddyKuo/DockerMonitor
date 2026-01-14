# Makefile for DockerMonitor

.PHONY: help install install-dev test test-verbose test-coverage lint format clean run-tui run-status

help:
	@echo "DockerMonitor - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install       Install production dependencies"
	@echo "  make install-dev   Install development dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  make test          Run all tests"
	@echo "  make test-verbose  Run tests with verbose output"
	@echo "  make test-coverage Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint          Run linters (flake8, mypy)"
	@echo "  make format        Format code with black"
	@echo ""
	@echo "Running:"
	@echo "  make run-tui       Launch TUI interface"
	@echo "  make run-status    Get container status (table format)"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean         Remove generated files and caches"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -e .

test:
	pytest tests/

test-verbose:
	pytest -v tests/

test-coverage:
	pytest --cov=src --cov-report=html --cov-report=term tests/

lint:
	flake8 src/ tests/
	mypy src/

format:
	black src/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/
	rm -rf logs/*.log

run-tui:
	python -m src.main tui

run-status:
	python -m src.main status

run-status-json:
	python -m src.main status --format json

run-status-csv:
	python -m src.main status --format csv
