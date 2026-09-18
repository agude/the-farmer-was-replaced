#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Verify the shared achievement runner contract."""

from __future__ import annotations

import sys
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE_DIRECTORY))

import achievement_config  # noqa: E402


EXPECTED_TARGETS = {
    "ACHIEVEMENT_HAY_TARGET": 200000000,
    "ACHIEVEMENT_CARROT_TARGET": 200000000,
    "ACHIEVEMENT_PUMPKIN_TARGET": 20000000,
    "ACHIEVEMENT_CACTUS_TARGET": 20000000,
    "ACHIEVEMENT_BONES_TARGET": 1000000,
    "ACHIEVEMENT_GOLD_TARGET": 2000000,
}


def test_targets_match_plan() -> None:
    for name, expected in EXPECTED_TARGETS.items():
        actual = getattr(achievement_config, name)
        if actual != expected:
            raise AssertionError(f"{name} changed: expected {expected}, got {actual}")


def test_debug_and_benchmark_modes_default_to_disabled() -> None:
    if achievement_config.DEBUG_OUTPUT:
        raise AssertionError("achievement debug output must default to disabled")
    if achievement_config.BENCHMARK_MODE:
        raise AssertionError("achievement benchmark mode must default to disabled")


def test_maze_layout_contract() -> None:
    if achievement_config.MAZE_REGION_SIZE != 4:
        raise AssertionError("maze regions must start at 4x4")
    if achievement_config.MAZE_REGION_COLUMNS != 8:
        raise AssertionError("maze layout must have eight columns")
    if achievement_config.MAZE_REGION_ROWS != 4:
        raise AssertionError("maze layout must have four rows")
    if achievement_config.MAZE_REGION_COUNT != 32:
        raise AssertionError("maze layout must expose 32 regions")


def test_farm_config_has_no_achievement_settings() -> None:
    farm_config_source = (SAVE_DIRECTORY / "farm_config.py").read_text()
    if "ACHIEVEMENT_" in farm_config_source:
        raise AssertionError("achievement settings leaked into farm_config.py")


def main() -> None:
    test_targets_match_plan()
    test_debug_and_benchmark_modes_default_to_disabled()
    test_maze_layout_contract()
    test_farm_config_has_no_achievement_settings()
    print("Passed achievement target, mode, maze layout, and config isolation tests")


if __name__ == "__main__":
    main()
