from cactus import farm_cactus_cycle
from carrots import farm_carrot_cycle
from farm_config import (
    CACTUS_REVERSE_SORT,
    POWER_TARGET,
)
from hay import farm_hay_cycle
from maze import farm_mazes, get_maze_substance_cost
from pumpkins import farm_pumpkin_cycle
from resource_costs import (
    can_afford_cost,
    get_planting_budget,
    get_required_inventory,
    get_top_hat_cost,
)
from sunflowers import farm_sunflower_cycle
from trees import farm_tree_cycle


POWER_LOW_WATERMARK = POWER_TARGET // 10
POWER_HIGH_WATERMARK = POWER_TARGET
POWER_OBSERVED_CONSUMPTION = 0
NO_PROGRESS_LIMIT = 2


def get_cost_amount(cost, item) -> int:
    if item in cost:
        return cost[item]

    return 0


def needs_item(cost, item) -> bool:
    return num_items(item) < get_cost_amount(cost, item)


def get_power_low_watermark() -> int:
    return POWER_LOW_WATERMARK + POWER_OBSERVED_CONSUMPTION


def get_power_target(cost) -> int:
    target = get_cost_amount(cost, Items.Power)

    if target < POWER_HIGH_WATERMARK:
        target = POWER_HIGH_WATERMARK

    return target + POWER_OBSERVED_CONSUMPTION


def is_power_stockpile_complete(cost) -> bool:
    return num_items(Items.Power) >= get_power_target(cost)


def merge_costs(first_cost, second_cost):
    # Combine live budgets for mixed tree and bush rows.
    if first_cost == None or second_cost == None:
        return None

    merged = {}

    for item in first_cost:
        merged[item] = first_cost[item]

    for item in second_cost:
        if item in merged:
            merged[item] = merged[item] + second_cost[item]
        else:
            merged[item] = second_cost[item]

    return merged


def get_entity_cycle_budget(entity, width, height):
    return get_planting_budget(entity, width, height)


def get_tree_cycle_budget(width, height):
    tree_tiles = 0
    bush_tiles = 0

    for x in range(width):
        for y in range(height):
            if (x + y) % 2:
                tree_tiles += 1
            else:
                bush_tiles += 1

    tree_budget = get_entity_cycle_budget(Entities.Tree, tree_tiles, 1)
    bush_budget = get_entity_cycle_budget(Entities.Bush, bush_tiles, 1)
    return merge_costs(tree_budget, bush_budget)


def get_missing_input(cycle_budget, protected_cost):
    required = get_required_inventory(cycle_budget, protected_cost)

    if required == None:
        return None

    for item in required:
        if num_items(item) < required[item]:
            return item

    return None


def can_run_budget(cycle_budget, protected_cost) -> bool:
    if cycle_budget == None:
        return False

    return can_afford_cost(cycle_budget, protected_cost)


def can_run_sunflowers(cost, size) -> bool:
    budget = get_entity_cycle_budget(Entities.Sunflower, size, size)
    return can_run_budget(budget, cost)


def can_run_carrots(cost, size) -> bool:
    budget = get_entity_cycle_budget(Entities.Carrot, size, size)
    return can_run_budget(budget, cost)


def can_run_pumpkins(cost, size) -> bool:
    budget = get_entity_cycle_budget(Entities.Pumpkin, size, size)
    return can_run_budget(budget, cost)


def can_run_cactus(cost, size) -> bool:
    budget = get_entity_cycle_budget(Entities.Cactus, size, size)
    return can_run_budget(budget, cost)


def can_run_trees(cost, size) -> bool:
    budget = get_tree_cycle_budget(size, size)
    return can_run_budget(budget, cost)


def can_run_maze(cost) -> bool:
    maze_cost = get_maze_substance_cost()

    if maze_cost <= 0:
        return False

    gold_target = get_cost_amount(cost, Items.Gold)
    substance_reserve = get_cost_amount(cost, Items.Weird_Substance)
    return num_items(Items.Gold) < gold_target and num_items(Items.Weird_Substance) >= (
        maze_cost + substance_reserve
    )


def run_cactus_action(cost, size) -> bool:
    weird_target = get_cost_amount(cost, Items.Weird_Substance)

    return farm_cactus_cycle(
        0,
        0,
        size,
        size,
        CACTUS_REVERSE_SORT,
        weird_target,
        0,
        True,
    )


def run_item_producer(item, cost, blocked_item=None) -> bool:
    # Produce one missing resource, recursively funding its next input.
    if item == blocked_item:
        quick_print("Top Hat producer dependency cycle")
        return False

    size = get_world_size()

    if item == Items.Hay:
        return farm_hay_cycle()

    if item == Items.Wood:
        if can_run_trees(cost, size):
            return farm_tree_cycle()

        budget = get_tree_cycle_budget(size, size)
        missing_item = get_missing_input(budget, cost)
        if missing_item == None:
            quick_print("Wood cycle is not affordable")
            return False

        return run_item_producer(missing_item, cost, item)

    if item == Items.Carrot:
        if can_run_carrots(cost, size):
            return farm_carrot_cycle()

        budget = get_entity_cycle_budget(Entities.Carrot, size, size)
        missing_item = get_missing_input(budget, cost)
        if missing_item == None:
            quick_print("Carrot cycle is not affordable")
            return False

        return run_item_producer(missing_item, cost, item)

    if item == Items.Pumpkin:
        if can_run_pumpkins(cost, size):
            return farm_pumpkin_cycle()

        budget = get_entity_cycle_budget(Entities.Pumpkin, size, size)
        missing_item = get_missing_input(budget, cost)
        if missing_item == None:
            quick_print("Pumpkin cycle is not affordable")
            return False

        return run_item_producer(missing_item, cost, item)

    if item == Items.Cactus:
        if can_run_cactus(cost, size):
            return run_cactus_action(cost, size)

        budget = get_entity_cycle_budget(Entities.Cactus, size, size)
        missing_item = get_missing_input(budget, cost)
        if missing_item == None:
            quick_print("Cactus cycle is not affordable")
            return False

        return run_item_producer(missing_item, cost, item)

    if item == Items.Power:
        if can_run_sunflowers(cost, size):
            return farm_sunflower_cycle()

        budget = get_entity_cycle_budget(Entities.Sunflower, size, size)
        missing_item = get_missing_input(budget, cost)
        if missing_item == None:
            quick_print("Power cycle is not affordable")
            return False

        return run_item_producer(missing_item, cost, item)

    if item == Items.Weird_Substance:
        if num_items(Items.Fertilizer) <= 0:
            quick_print("Missing fertilizer for Weird Substance")
            return False

        if can_run_cactus(cost, size):
            return run_cactus_action(cost, size)

        budget = get_entity_cycle_budget(Entities.Cactus, size, size)
        missing_item = get_missing_input(budget, cost)
        if missing_item == None:
            quick_print("Weird Substance cycle is not affordable")
            return False

        return run_item_producer(missing_item, cost, item)

    if item == Items.Gold:
        if can_run_maze(cost):
            return farm_mazes(
                get_cost_amount(cost, Items.Gold),
                get_cost_amount(cost, Items.Weird_Substance),
            )

        if num_items(Items.Fertilizer) > 0:
            return run_item_producer(Items.Weird_Substance, cost, item)

        quick_print("Gold cycle is waiting for Weird Substance")
        return False

    quick_print("No Top Hat producer for required item")
    return False


def run_selected_producer(item, cost) -> bool:
    # Keep producer failures visible to the next planner iteration.
    result = run_item_producer(item, cost)

    if not result:
        quick_print("Top Hat producer failed for " + str(item))

    return result


def perform_next_action(cost) -> bool:
    # Select one bounded action using current protected balances.
    power_target = get_power_target(cost)

    if num_items(Items.Power) < get_power_low_watermark():
        return run_selected_producer(Items.Power, cost)

    if num_items(Items.Power) < power_target:
        return run_selected_producer(Items.Power, cost)

    if needs_item(cost, Items.Cactus) or needs_item(cost, Items.Weird_Substance):
        if needs_item(cost, Items.Cactus):
            return run_selected_producer(Items.Cactus, cost)

        return run_selected_producer(Items.Weird_Substance, cost)

    if needs_item(cost, Items.Gold):
        return run_selected_producer(Items.Gold, cost)

    if (
        is_power_stockpile_complete(cost)
        and not needs_item(cost, Items.Cactus)
        and not needs_item(cost, Items.Gold)
        and needs_item(cost, Items.Carrot)
    ):
        return run_selected_producer(Items.Carrot, cost)

    if needs_item(cost, Items.Wood):
        return run_selected_producer(Items.Wood, cost)

    if needs_item(cost, Items.Hay):
        return run_selected_producer(Items.Hay, cost)

    quick_print("Top Hat planner has no selected action")
    return False


def get_inventory_snapshot(cost):
    # Track all production resources plus any live-cost keys.
    snapshot = []
    tracked_items = [
        Items.Hay,
        Items.Wood,
        Items.Carrot,
        Items.Pumpkin,
        Items.Cactus,
        Items.Power,
        Items.Weird_Substance,
        Items.Gold,
        Items.Fertilizer,
    ]

    for item in tracked_items:
        snapshot.append((item, num_items(item)))

    for item in cost:
        if item not in tracked_items:
            snapshot.append((item, num_items(item)))

    return snapshot


def get_snapshot_amount(snapshot, item) -> int:
    for snapshot_item, amount in snapshot:
        if snapshot_item == item:
            return amount

    return 0


def record_power_consumption(before, after) -> None:
    # Retain the largest observed net power drop as a future reserve.
    global POWER_OBSERVED_CONSUMPTION

    before_power = get_snapshot_amount(before, Items.Power)
    after_power = get_snapshot_amount(after, Items.Power)
    consumption = before_power - after_power

    if consumption > POWER_OBSERVED_CONSUMPTION:
        POWER_OBSERVED_CONSUMPTION = consumption


def farm_top_hat() -> bool:
    # Reconcile live costs one bounded action at a time before unlocking.
    if num_unlocked(Unlocks.Top_Hat) > 0:
        return True

    cost = get_top_hat_cost()

    if cost == None:
        quick_print("Top Hat cost unavailable")
        return False

    no_progress_count = 0

    while True:
        cost = get_top_hat_cost()

        if cost == None:
            quick_print("Top Hat cost unavailable")
            return False

        if can_afford_cost(cost):
            if unlock(Unlocks.Top_Hat):
                return True

            quick_print("Top Hat unlock failed")
            return False

        before = get_inventory_snapshot(cost)
        perform_next_action(cost)

        refreshed_cost = get_top_hat_cost()
        if refreshed_cost == None:
            quick_print("Top Hat cost unavailable")
            return False

        after = get_inventory_snapshot(refreshed_cost)
        record_power_consumption(before, after)

        if before == after:
            no_progress_count += 1
        else:
            no_progress_count = 0

        if no_progress_count >= NO_PROGRESS_LIMIT:
            quick_print("Top Hat planner made no progress")
            return False
