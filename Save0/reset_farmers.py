"""Bounded producers used only by reset progression."""

from achievement_dinosaur import run_achievement_dinosaur_once
from achievement_maze import MAZE_WORKER_COMPLETE
from achievement_maze import run_reusable_maze_worker
from navigation import move_to


MAX_PRODUCER_CYCLES = 256
MAX_INPUT_DEPTH = 4


def get_crop_spec(item):
    if item == Items.Hay:
        return Entities.Grass, None

    if item == Items.Wood:
        return Entities.Bush, Unlocks.Plant

    if item == Items.Carrot:
        return Entities.Carrot, Unlocks.Carrots

    if item == Items.Pumpkin:
        return Entities.Pumpkin, Unlocks.Pumpkins

    if item == Items.Cactus:
        return Entities.Cactus, Unlocks.Cactus

    if item == Items.Power:
        return Entities.Sunflower, Unlocks.Sunflowers

    return None


def ensure_planting_inputs(entity, planting_count: int, input_depth: int) -> bool:
    cost = get_cost(entity)
    if cost == None:
        return True

    for item in cost:
        amount = cost[item]
        if amount == None or amount < 0:
            return False

        required_amount = amount * planting_count
        if num_items(item) >= required_amount:
            continue
        if input_depth >= MAX_INPUT_DEPTH or not produce_item(
            item,
            required_amount - num_items(item),
            input_depth + 1,
        ):
            return False

    return True


def prepare_crop(entity, input_depth: int) -> bool:
    current_entity = get_entity_type()
    if current_entity == entity:
        if can_harvest():
            return harvest()

        if num_unlocked(Unlocks.Watering) > 0 and get_water() < 0.2:
            use_item(Items.Water)
        return True

    if current_entity != None:
        if not can_harvest() or not harvest():
            return False

    if entity == Entities.Grass:
        if get_ground_type() == Grounds.Soil:
            till()
    elif get_ground_type() != Grounds.Soil:
        till()

    if not ensure_planting_inputs(entity, 1, input_depth):
        return False

    return plant(entity)


def farm_crop(item, entity, unlock_target, required_amount: int, input_depth: int) -> bool:
    if entity != Entities.Grass and num_unlocked(Unlocks.Plant) == 0:
        return False
    if unlock_target != None and num_unlocked(unlock_target) == 0:
        return False
    if get_world_size() < 1 or required_amount <= 0:
        return False

    target_amount = num_items(item) + required_amount
    move_to(0, 0)

    for _cycle in range(MAX_PRODUCER_CYCLES):
        if num_items(item) >= target_amount:
            return True
        if not prepare_crop(entity, input_depth):
            return False

    return num_items(item) >= target_amount


def farm_weird_substance(required_amount: int) -> bool:
    if num_unlocked(Unlocks.Fertilizer) == 0 or num_items(Items.Fertilizer) <= 0:
        return False

    target_amount = num_items(Items.Weird_Substance) + required_amount
    move_to(0, 0)

    for _cycle in range(MAX_PRODUCER_CYCLES):
        if num_items(Items.Weird_Substance) >= target_amount:
            return True

        if not prepare_crop(Entities.Grass, 0):
            return False
        if not can_harvest():
            continue
        if not use_item(Items.Fertilizer):
            return False
        if not harvest():
            return False

    return num_items(Items.Weird_Substance) >= target_amount


def farm_gold(required_amount: int) -> bool:
    if num_unlocked(Unlocks.Mazes) == 0:
        return False

    starting_gold = num_items(Items.Gold)
    result = run_reusable_maze_worker(0, 1)
    if result["reason"] != MAZE_WORKER_COMPLETE:
        return False

    return num_items(Items.Gold) >= starting_gold + required_amount


def farm_bones(required_amount: int) -> bool:
    if num_unlocked(Unlocks.Dinosaurs) == 0 or get_world_size() < 2:
        return False

    starting_bones = num_items(Items.Bone)
    if not run_achievement_dinosaur_once():
        return False

    return num_items(Items.Bone) >= starting_bones + required_amount


def produce_item(item, required_amount: int, input_depth=0) -> bool:
    if required_amount <= 0:
        return True
    if input_depth > MAX_INPUT_DEPTH:
        return False

    crop_spec = get_crop_spec(item)
    if crop_spec != None:
        entity, unlock_target = crop_spec
        return farm_crop(item, entity, unlock_target, required_amount, input_depth)

    if item == Items.Weird_Substance:
        return farm_weird_substance(required_amount)

    if item == Items.Gold:
        return farm_gold(required_amount)

    if item == Items.Bone:
        return farm_bones(required_amount)

    return False
