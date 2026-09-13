#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Validate tracked The Farmer Was Replaced source files."""

from __future__ import annotations

import argparse
import ast
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


UNSUPPORTED_NODES: dict[type[ast.AST], str] = {
    ast.AsyncFor: "async for loops",
    ast.AsyncFunctionDef: "async functions",
    ast.AsyncWith: "async context managers",
    ast.Await: "await expressions",
    ast.ClassDef: "classes",
    ast.DictComp: "dictionary comprehensions",
    ast.GeneratorExp: "generator expressions",
    ast.IfExp: "ternary expressions",
    ast.Lambda: "lambdas",
    ast.ListComp: "list comprehensions",
    ast.SetComp: "set comprehensions",
    ast.Starred: "starred expressions",
}


@dataclass(frozen=True, order=True)
class Finding:
    path: Path
    line: int
    column: int
    message: str

    def render(self, root: Path) -> str:
        try:
            display_path = self.path.relative_to(root)
        except ValueError:
            display_path = self.path

        return f"{display_path}:{self.line}:{self.column}: {self.message}"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check game scripts for syntax unsupported by the game interpreter."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Files or save directories to check; defaults to tracked Save* Python files.",
    )
    return parser.parse_args()


def tracked_game_files(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--", "*.py"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )

    return sorted(
        root / relative_path
        for relative_path in result.stdout.splitlines()
        if Path(relative_path).name != "__builtins__.py"
        and any(part.startswith("Save") for part in Path(relative_path).parts)
    )


def expand_paths(paths: list[Path], root: Path) -> list[Path]:
    if not paths:
        return tracked_game_files(root)

    files: set[Path] = set()
    for path in paths:
        resolved_path = path if path.is_absolute() else root / path
        if resolved_path.is_dir():
            files.update(resolved_path.rglob("*.py"))
        else:
            files.add(resolved_path)

    return sorted(path for path in files if path.name != "__builtins__.py")


def find_save_directory(path: Path) -> Path | None:
    for directory in path.parents:
        if directory.name.startswith("Save"):
            return directory
    return None


def module_exists(save_directory: Path, module_name: str) -> bool:
    module_path = save_directory.joinpath(*module_name.split("."))
    return (
        module_path.with_suffix(".py").is_file()
        or (module_path / "__init__.py").is_file()
    )


def import_findings(path: Path, tree: ast.AST) -> list[Finding]:
    findings: list[Finding] = []
    save_directory = find_save_directory(path)
    if save_directory is None:
        return [Finding(path, 1, 1, "file is not inside a Save* directory")]

    for node in ast.walk(tree):
        modules: list[str] = []
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                findings.append(
                    Finding(
                        path,
                        node.lineno,
                        node.col_offset + 1,
                        "relative imports are unsupported",
                    )
                )
                continue
            if node.module:
                modules = [node.module]

        for module_name in modules:
            if not module_exists(save_directory, module_name):
                findings.append(
                    Finding(
                        path,
                        node.lineno,
                        node.col_offset + 1,
                        f"import {module_name!r} does not resolve inside {save_directory.name}",
                    )
                )

    return findings


def dialect_findings(path: Path, tree: ast.AST) -> list[Finding]:
    findings: list[Finding] = []

    for node in ast.walk(tree):
        unsupported_feature = UNSUPPORTED_NODES.get(type(node))
        if unsupported_feature:
            findings.append(
                Finding(
                    path,
                    getattr(node, "lineno", 1),
                    getattr(node, "col_offset", 0) + 1,
                    f"unsupported game syntax: {unsupported_feature}",
                )
            )

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            arguments = node.args
            if arguments.vararg or arguments.kwarg or arguments.kwonlyargs:
                findings.append(
                    Finding(
                        path,
                        node.lineno,
                        node.col_offset + 1,
                        "unsupported game syntax: variadic or keyword-only parameters",
                    )
                )

        if isinstance(node, ast.Call) and node.keywords:
            findings.append(
                Finding(
                    path,
                    node.lineno,
                    node.col_offset + 1,
                    "unsupported game syntax: named or expanded keyword arguments",
                )
            )

    return findings


def check_file(path: Path) -> list[Finding]:
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as error:
        return [Finding(path, 1, 1, f"cannot read file: {error}")]

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as error:
        return [
            Finding(
                path,
                error.lineno or 1,
                error.offset or 1,
                f"Python parser error: {error.msg}",
            )
        ]

    return dialect_findings(path, tree) + import_findings(path, tree)


def main() -> int:
    arguments = parse_arguments()
    root = Path.cwd().resolve()

    try:
        files = expand_paths(arguments.paths, root)
    except subprocess.CalledProcessError as error:
        print(f"failed to list tracked files: {error}", file=sys.stderr)
        return 2

    if not files:
        print("no game Python files found", file=sys.stderr)
        return 2

    findings = sorted(finding for path in files for finding in check_file(path))
    if findings:
        for finding in findings:
            print(finding.render(root))
        print(f"Found {len(findings)} game-code error(s).")
        return 1

    print(f"Checked {len(files)} game files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
