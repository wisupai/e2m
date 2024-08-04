.PHONY: format sort lint

# Variables
ISORT_OPTIONS = --profile black
PROJECT_NAME := e2m

# Default target
all: format sort lint

install:
	poetry install

install_all:
	poetry install

# Format code with ruff
format:
	poetry run ruff check . --fix $(RUFF_OPTIONS)

# Sort imports with isort
sort:
	poetry run isort . $(ISORT_OPTIONS)

# Lint code with ruff
lint:
	poetry run ruff check .

docs:
	cd docs && mintlify dev

build:
	poetry build

publish:
	poetry publish

clean:
	poetry run rm -rf dist

test:
	poetry run pytest tests
