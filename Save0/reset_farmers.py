# Bounded producers used only by reset progression.

from achievement_maze import MAZE_WORKER_COMPLETE
from achievement_maze import get_reusable_maze_substance_budget
from achievement_maze import run_reusable_maze_worker
from dinosaurs import get_apple_cactus_cost
from dinosaurs import get_full_run_cactus_cost
from dinosaurs import run_dinosaur_once
from navigation import move_to
from planting import ensure_ground_for_entity


MAX_INPUT_DEPTH = 4
MAX_CROP_WAIT_CHECKS = 1000000
MAX_STAGNANT_CROP_WAIT_CHECKS = 1000


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


def get_producer_positions():
    world_size = get_world_size()
    positions = []

    for y in range(world_size):
        if y % 2 == 0:
            for x in range(world_size):
                positions.append((x, y))
        else:
            for x in range(world_size - 1, -1, -1):
                positions.append((x, y))

    return positions


def wait_for_crop(entity) -> bool:
    starting_tick = get_tick_count()
    last_tick = starting_tick
    stagnant_checks = 0

    for _check in range(MAX_CROP_WAIT_CHECKS):
        if get_entity_type() != entity:
            return False
        if can_harvest():
            return True
        water_crop_if_available()

        do_a_flip()
        current_tick = get_tick_count()
        if current_tick == last_tick:
            stagnant_checks += 1
        else:
            last_tick = current_tick
            stagnant_checks = 0

        if stagnant_checks >= MAX_STAGNANT_CROP_WAIT_CHECKS:
            quick_print("Reset producer clock stopped while waiting for " + str(entity))
            return False

    quick_print("Reset producer crop did not mature: " + str(entity))
    return False


def water_crop_if_available() -> None:
    if num_unlocked(Unlocks.Watering) == 0:
        return
    if get_water() >= 0.2 or num_items(Items.Water) <= 0:
        return

    use_item(Items.Water)


def wait_for_fertilizer() -> bool:
    last_tick = get_tick_count()
    stagnant_checks = 0

    for _check in range(MAX_CROP_WAIT_CHECKS):
        if num_items(Items.Fertilizer) > 0:
            return True

        do_a_flip()
        current_tick = get_tick_count()
        if current_tick == last_tick:
            stagnant_checks += 1
        else:
            last_tick = current_tick
            stagnant_checks = 0

        if stagnant_checks >= MAX_STAGNANT_CROP_WAIT_CHECKS:
            quick_print("Reset producer clock stopped while waiting for Fertilizer")
            return False

    quick_print("Reset producer fertilizer did not replenish")
    return False


def prepare_crop(entity, input_depth: int, harvest_ready: bool = True) -> bool:
    current_entity = get_entity_type()
    if current_entity == entity:
        if can_harvest():
            if not harvest_ready:
                return True
            return harvest()

        if not harvest_ready:
            return True
        return wait_for_crop(entity) and harvest()

    # Dead pumpkins disappear when the replacement plant is placed.
    if current_entity != None and current_entity != Entities.Dead_Pumpkin:
        if not wait_for_crop(current_entity) or not harvest():
            return False
        if get_entity_type() != None:
            return False

    if not ensure_planting_inputs(entity, 1, input_depth):
        return False
    if not ensure_ground_for_entity(entity):
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
    positions = get_producer_positions()
    if len(positions) == 0:
        return False

    position_index = 0
    while num_items(item) < target_amount:
        x, y = positions[position_index]
        position_index = (position_index + 1) % len(positions)
        move_to(x, y)
        if not prepare_crop(entity, input_depth):
            return False

    return True


def farm_weird_substance(required_amount: int) -> bool:
    if num_unlocked(Unlocks.Fertilizer) == 0:
        return False

    target_amount = num_items(Items.Weird_Substance) + required_amount
    positions = get_producer_positions()
    if len(positions) == 0:
        return False

    position_index = 0
    while num_items(Items.Weird_Substance) < target_amount:
        x, y = positions[position_index]
        position_index = (position_index + 1) % len(positions)
        move_to(x, y)

        if not prepare_crop(Entities.Grass, 0, False):
            return False
        if not wait_for_crop(Entities.Grass):
            return False
        if not wait_for_fertilizer():
            return False
        if not use_item(Items.Fertilizer):
            return False
        if not harvest():
            return False

    return True


def farm_gold(required_amount: int, input_depth: int) -> bool:
    if num_unlocked(Unlocks.Mazes) == 0:
        return False
    if required_amount <= 0:
        return True

    target_gold = num_items(Items.Gold) + required_amount
    while num_items(Items.Gold) < target_gold:
        substance_budget = get_reusable_maze_substance_budget(1)
        if substance_budget == None:
            return False

        if num_items(Items.Weird_Substance) < substance_budget:
            missing_substance = substance_budget - num_items(Items.Weird_Substance)
            if input_depth >= MAX_INPUT_DEPTH or not farm_weird_substance(missing_substance):
                return False

        if not ensure_planting_inputs(Entities.Bush, 1, input_depth):
            return False

        before_gold = num_items(Items.Gold)
        result = run_reusable_maze_worker(0, 1)
        if result["reason"] != MAZE_WORKER_COMPLETE:
            return False
        if num_items(Items.Gold) <= before_gold:
            return False

    return True


def farm_bones(required_amount: int, input_depth: int) -> bool:
    if num_unlocked(Unlocks.Dinosaurs) == 0 or get_world_size() < 2:
        return False
    if required_amount <= 0:
        return True

    world_size = get_world_size()
    if world_size % 2:
        return False

    apple_cost = get_apple_cactus_cost()
    if apple_cost <= 0:
        return False

    cactus_budget = get_full_run_cactus_cost(world_size, apple_cost)
    target_bones = num_items(Items.Bone) + required_amount

    while num_items(Items.Bone) < target_bones:
        if num_items(Items.Cactus) < cactus_budget:
            missing_cactus = cactus_budget - num_items(Items.Cactus)
            if input_depth >= MAX_INPUT_DEPTH or not farm_crop(
                Items.Cactus,
                Entities.Cactus,
                Unlocks.Cactus,
                missing_cactus,
                input_depth + 1,
            ):
                return False

        before_bones = num_items(Items.Bone)
        move_to(0, 0)
        if not run_dinosaur_once(world_size):
            return False
        if num_items(Items.Bone) <= before_bones:
            return False

    return True


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
        return farm_gold(required_amount, input_depth)

    if item == Items.Bone:
        return farm_bones(required_amount, input_depth)

    return False
