ruff_version := "0.16.0"
python_version := "3.12.3"

default:
    @just --list

# Install the Python interpreter used by repository checks. Ruff remains a
# pinned, isolated uvx tool because this repository is not a Python package.
sync:
    uv python install {{python_version}}

# Run every read-only static check used by CI.
lint:
    uvx ruff@{{ruff_version}} check .
    uvx ruff@{{ruff_version}} format --check .
    uv run scripts/check_game_code.py
    uv run scripts/check_skills.py

format:
    uvx ruff@{{ruff_version}} format .
    uvx ruff@{{ruff_version}} check --fix scripts

check: lint

hooks-install:
    ln -sf ../../bin/pre-commit.sh .git/hooks/pre-commit
