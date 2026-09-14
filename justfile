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
    uv run scripts/sync_game_api.py --check
    uvx ruff@{{ruff_version}} check .
    uvx ruff@{{ruff_version}} format --check .
    uv run scripts/check_game_code.py
    uv run scripts/check_skills.py

format:
    uvx ruff@{{ruff_version}} format .
    uvx ruff@{{ruff_version}} check --fix scripts

# Refresh committed API metadata after the game regenerates its editor stub.
api-sync:
    uv run scripts/sync_game_api.py

# Run the CPython cactus-sort harness against simulated game operations.
cactus-test:
    uv run scripts/test_cactus_sort.py

check: lint

hooks-install:
    ln -sf ../../bin/pre-commit.sh .git/hooks/pre-commit
