#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Exercise game-dialect checks that CPython's parser accepts."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from check_game_code import check_file


EMPTY_MANIFEST = {"functions": {}, "enums": {}}


def get_messages(save_directory: Path, source: str) -> list[str]:
    path = save_directory / "subject.py"
    path.write_text(source, encoding="utf-8")
    return [finding.message for finding in check_file(path, EMPTY_MANIFEST)]


def test_triple_quoted_strings_are_rejected(save_directory: Path) -> None:
    messages = get_messages(
        save_directory,
        "\"\"\"Module docstring.\"\"\"\n\ndef example():\n    r'''Function docstring.'''\n",
    )

    expected = "unsupported game syntax: triple-quoted strings"
    if messages.count(expected) != 2:
        raise AssertionError(f"triple-quoted strings were not rejected: {messages}")


def test_comments_and_ordinary_strings_are_allowed(save_directory: Path) -> None:
    messages = get_messages(
        save_directory,
        '# A comment containing """ is not a string.\ndescription = "An ordinary string"\n',
    )

    if messages:
        raise AssertionError(f"valid comments or strings were rejected: {messages}")


def test_import_aliases_are_rejected(save_directory: Path) -> None:
    (save_directory / "dependency.py").write_text("VALUE = 1\n", encoding="utf-8")
    messages = get_messages(
        save_directory,
        "import dependency as renamed_dependency\nfrom dependency import VALUE as RENAMED_VALUE\n",
    )

    expected = "unsupported game syntax: import aliases"
    if messages.count(expected) != 2:
        raise AssertionError(f"import aliases were not rejected: {messages}")


def test_unaliased_imports_are_allowed(save_directory: Path) -> None:
    (save_directory / "dependency.py").write_text("VALUE = 1\n", encoding="utf-8")
    messages = get_messages(
        save_directory,
        "import dependency\nfrom dependency import VALUE\n",
    )

    if messages:
        raise AssertionError(f"valid imports were rejected: {messages}")


def main() -> None:
    with TemporaryDirectory() as temporary_directory:
        save_directory = Path(temporary_directory) / "SaveTest"
        save_directory.mkdir()

        test_triple_quoted_strings_are_rejected(save_directory)
        test_comments_and_ordinary_strings_are_allowed(save_directory)
        test_import_aliases_are_rejected(save_directory)
        test_unaliased_imports_are_allowed(save_directory)

    print("Passed game-code checker regression tests")


if __name__ == "__main__":
    main()
