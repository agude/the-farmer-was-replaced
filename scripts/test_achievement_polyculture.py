#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Verify the shared Hay and Carrot polyculture coordinate layout."""

from __future__ import annotations

import sys
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE_DIRECTORY))

import achievement_polyculture as layout  # noqa: E402


def test_every_coordinate_has_one_role() -> None:
    for world_size in (8, 16, 32):
        for mode in (layout.HAY_MODE, layout.CARROT_MODE):
            roles = []

            for x in range(world_size):
                for y in range(world_size):
                    role = layout.get_layout_role(x, y, mode)
                    if role not in (
                        layout.PRIMARY_ROLE,
                        layout.COMPANION_ROLE,
                        layout.GUARD_ROLE,
                    ):
                        raise AssertionError(f"unclassified coordinate {(x, y)}: {role}")
                    roles.append(role)

            if len(roles) != world_size * world_size:
                raise AssertionError("layout does not cover the complete world")


def test_modes_share_coordinates_but_not_layout_state() -> None:
    for world_size in (8, 16, 32):
        hay_positions = layout.get_primary_positions(world_size, layout.HAY_MODE)
        carrot_positions = layout.get_primary_positions(world_size, layout.CARROT_MODE)

        if hay_positions != carrot_positions:
            raise AssertionError("Hay and Carrot modes do not share primary coordinates")

        for x in range(world_size):
            for y in range(world_size):
                if layout.get_layout_role(x, y, layout.HAY_MODE) != layout.get_layout_role(
                    x, y, layout.CARROT_MODE
                ):
                    raise AssertionError("Hay and Carrot modes diverged in coordinate roles")


def test_companion_slots_are_owned_and_guards_are_rejected() -> None:
    for world_size in (8, 16, 32):
        for primary_x, primary_y in layout.get_primary_positions(world_size, layout.HAY_MODE):
            companions = layout.get_companion_positions_for_primary(
                primary_x,
                primary_y,
                world_size,
                layout.HAY_MODE,
            )
            if len(companions) != 3:
                raise AssertionError("each primary region must expose three companion slots")

            for x, y in companions:
                if not layout.is_allowed_companion_coordinate(
                    x,
                    y,
                    primary_x,
                    primary_y,
                    layout.HAY_MODE,
                ):
                    raise AssertionError("companion slot was not owned by its primary")

            guard_x = primary_x + 2
            guard_y = primary_y
            if layout.is_allowed_companion_coordinate(
                guard_x,
                guard_y,
                primary_x,
                primary_y,
                layout.HAY_MODE,
            ):
                raise AssertionError("guard tile was accepted as a companion target")

        for x in range(world_size):
            for y in range(world_size):
                owner = layout.get_primary_owner(x, y, layout.HAY_MODE)
                if owner != layout.get_primary_position(x, y):
                    raise AssertionError("coordinate owner is not deterministic")


def test_primary_regions_do_not_overlap() -> None:
    for world_size in (8, 16, 32):
        positions = layout.get_primary_positions(world_size, layout.CARROT_MODE)

        for index in range(len(positions)):
            first_x, first_y = positions[index]
            for second_index in range(index + 1, len(positions)):
                second_x, second_y = positions[second_index]
                distance = abs(first_x - second_x) + abs(first_y - second_y)
                if distance < layout.TEMPLATE_SIZE:
                    raise AssertionError("primary regions are not separated")


def main() -> None:
    test_every_coordinate_has_one_role()
    test_modes_share_coordinates_but_not_layout_state()
    test_companion_slots_are_owned_and_guards_are_rejected()
    test_primary_regions_do_not_overlap()
    print("Passed 8x8, 16x16, and 32x32 Hay/Carrot polyculture layout tests")


if __name__ == "__main__":
    main()
