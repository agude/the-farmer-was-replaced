"""Finite full-field Dinosaur Master harvest burst."""

from achievement_config import ACHIEVEMENT_BONES_TARGET
from dinosaurs import get_full_run_cactus_cost
from dinosaurs import traverse_dinosaur_cycle


def get_achievement_apple_cost() -> int:
    cost = get_cost(Entities.Apple)

    if cost == None:
        return 0

    for item in cost:
        if item == Items.Cactus and cost[item] > 0:
            return cost[item]

    return 0


def can_start_dinosaur_run(size: int, apple_cost: int) -> bool:
    if size < 2 or size % 2 != 0:
        return False

    if num_unlocked(Unlocks.Dinosaurs) == 0:
        return False

    run_cost = get_full_run_cactus_cost(size, apple_cost)
    return num_items(Items.Cactus) >= run_cost


def fill_dinosaur_tail(size: int) -> bool:
    # The completed tail proves itself by blocking the next Hamiltonian move.
    return not traverse_dinosaur_cycle(size)


def run_achievement_dinosaur_once() -> bool:
    size = get_world_size()
    apple_cost = get_achievement_apple_cost()

    if apple_cost <= 0 or not can_start_dinosaur_run(size, apple_cost):
        return False

    starting_bones = num_items(Items.Bone)
    clear()
    change_hat(Hats.Dinosaur_Hat)

    if get_entity_type() != Entities.Apple:
        change_hat(Hats.Straw_Hat)
        return False

    if not fill_dinosaur_tail(size):
        change_hat(Hats.Straw_Hat)
        return False

    # Removing the hat credits the entire completed dinosaur tail at once.
    change_hat(Hats.Straw_Hat)
    return num_items(Items.Bone) - starting_bones >= ACHIEVEMENT_BONES_TARGET
