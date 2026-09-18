"""Import-safe reset progression controller contracts."""

from reset_farmers import produce_item

MAX_UNLOCK_ATTEMPTS = 3

UNLOCK_SUCCESS = "success"
UNLOCK_ALREADY_COMPLETE = "already_complete"
UNLOCK_MISSING_PREREQUISITE = "missing_prerequisite"
UNLOCK_MISSING_COST = "missing_cost"
UNLOCK_INVALID_COST = "invalid_cost"
UNLOCK_NO_PROGRESS = "no_progress"
UNLOCK_PURCHASE_FAILED = "purchase_failed"
UNLOCK_CYCLE = "cycle"


def get_target_level(unlock_target) -> int:
    if unlock_target == Unlocks.Expand:
        return 7
    if unlock_target == Unlocks.Speed:
        return 5
    if unlock_target == Unlocks.Grass:
        return 4
    if unlock_target == Unlocks.Trees:
        return 5
    if unlock_target == Unlocks.Carrots:
        return 6
    if unlock_target == Unlocks.Watering:
        return 6
    if unlock_target == Unlocks.Pumpkins:
        return 5
    if unlock_target == Unlocks.Cactus:
        return 3
    if unlock_target == Unlocks.Polyculture:
        return 2
    if unlock_target == Unlocks.Megafarm:
        return 4
    if unlock_target == Unlocks.Mazes:
        return 4
    if unlock_target == Unlocks.Dinosaurs:
        return 5
    if unlock_target == Unlocks.Fertilizer:
        return 4

    return 1


def append_route_step(plan, unlock_target, target_level, reason, prerequisites) -> None:
    plan.append((unlock_target, target_level, reason, prerequisites))


def get_unlock_plan():
    """Return the farm-only reset milestones in measured purchase order."""
    plan = []
    route = [
        (Unlocks.Speed, 1, "Accelerate the remaining reset stages", []),
        (Unlocks.Plant, 1, "Enable crop planting for resource producers", []),
        (Unlocks.Expand, 1, "Open enough tiles for reset-safe batches", [Unlocks.Plant]),
        (Unlocks.Expand, 2, "Open enough tiles for reset-safe batches", []),
        (Unlocks.Speed, 2, "Accelerate the remaining reset stages", []),
        (Unlocks.Carrots, 1, "Produce Carrots for later unlocks", [Unlocks.Plant, Unlocks.Expand]),
        (Unlocks.Grass, 2, "Start the first bounded resource producer", [Unlocks.Plant]),
        (Unlocks.Trees, 1, "Produce Wood for later unlocks", [Unlocks.Plant, Unlocks.Expand]),
        (Unlocks.Trees, 2, "Produce Wood for later unlocks", []),
        (Unlocks.Expand, 3, "Open enough tiles for reset-safe batches", []),
        (Unlocks.Carrots, 2, "Produce Carrots for later unlocks", []),
        (Unlocks.Speed, 3, "Accelerate the remaining reset stages", []),
        (Unlocks.Expand, 4, "Open enough tiles for reset-safe batches", []),
        (Unlocks.Watering, 1, "Maintain water-dependent crops", [Unlocks.Plant, Unlocks.Expand]),
        (Unlocks.Watering, 2, "Maintain water-dependent crops", []),
        (Unlocks.Carrots, 3, "Produce Carrots for later unlocks", []),
        (Unlocks.Grass, 3, "Start the first bounded resource producer", []),
        (Unlocks.Sunflowers, 1, "Produce Power for accelerated stages", [Unlocks.Watering]),
        (Unlocks.Fertilizer, 1, "Enable Weird Substance production", [Unlocks.Sunflowers]),
        (Unlocks.Watering, 3, "Maintain water-dependent crops", []),
        (Unlocks.Speed, 4, "Accelerate the remaining reset stages", []),
        (Unlocks.Pumpkins, 1, "Produce Pumpkin batches", [Unlocks.Watering, Unlocks.Expand]),
        (Unlocks.Watering, 4, "Maintain water-dependent crops", []),
        (
            Unlocks.Polyculture,
            1,
            "Enable Hay and Carrot companion yields",
            [Unlocks.Carrots, Unlocks.Trees],
        ),
        (Unlocks.Speed, 5, "Accelerate the remaining reset stages", []),
        (Unlocks.Expand, 5, "Open enough tiles for reset-safe batches", []),
        (Unlocks.Fertilizer, 2, "Enable Weird Substance production", []),
        (
            Unlocks.Mazes,
            1,
            "Enable reusable maze gold production",
            [Unlocks.Plant, Unlocks.Expand],
        ),
        (
            Unlocks.Megafarm,
            1,
            "Enable parallel reset-safe workers",
            [Unlocks.Expand, Unlocks.Polyculture],
        ),
        (Unlocks.Trees, 3, "Produce Wood for later unlocks", []),
        (Unlocks.Trees, 4, "Produce Wood for later unlocks", []),
        (Unlocks.Carrots, 4, "Produce Carrots for later unlocks", []),
        (Unlocks.Watering, 5, "Maintain water-dependent crops", []),
        (Unlocks.Pumpkins, 2, "Produce Pumpkin batches", []),
        (Unlocks.Pumpkins, 3, "Produce Pumpkin batches", []),
        (Unlocks.Expand, 6, "Open enough tiles for reset-safe batches", []),
        (
            Unlocks.Cactus,
            1,
            "Produce Cactus and Weird Substance inputs",
            [Unlocks.Plant, Unlocks.Expand],
        ),
        (Unlocks.Dinosaurs, 1, "Enable bounded bone production", [Unlocks.Mazes, Unlocks.Cactus]),
        (Unlocks.Dinosaurs, 2, "Enable bounded bone production", []),
        (Unlocks.Polyculture, 2, "Enable Hay and Carrot companion yields", []),
        (Unlocks.Mazes, 2, "Enable reusable maze gold production", []),
        (Unlocks.Mazes, 3, "Enable reusable maze gold production", []),
        (Unlocks.Megafarm, 2, "Enable parallel reset-safe workers", []),
        (Unlocks.Megafarm, 3, "Enable parallel reset-safe workers", []),
        (Unlocks.Grass, 4, "Start the first bounded resource producer", []),
        (Unlocks.Trees, 5, "Produce Wood for later unlocks", []),
        (Unlocks.Fertilizer, 3, "Enable Weird Substance production", []),
        (Unlocks.Fertilizer, 4, "Enable Weird Substance production", []),
        (Unlocks.Watering, 6, "Maintain water-dependent crops", []),
        (Unlocks.Carrots, 5, "Produce Carrots for later unlocks", []),
        (Unlocks.Carrots, 6, "Produce Carrots for later unlocks", []),
        (Unlocks.Pumpkins, 4, "Produce Pumpkin batches", []),
        (Unlocks.Pumpkins, 5, "Produce Pumpkin batches", []),
        (Unlocks.Expand, 7, "Open enough tiles for reset-safe batches", []),
        (Unlocks.Megafarm, 4, "Enable parallel reset-safe workers", []),
        (Unlocks.Cactus, 2, "Produce Cactus and Weird Substance inputs", []),
        (Unlocks.Cactus, 3, "Produce Cactus and Weird Substance inputs", []),
        (Unlocks.Dinosaurs, 3, "Enable bounded bone production", []),
        (Unlocks.Dinosaurs, 4, "Enable bounded bone production", []),
        (Unlocks.Dinosaurs, 5, "Enable bounded bone production", []),
        (Unlocks.Mazes, 4, "Enable reusable maze gold production", []),
        (Unlocks.Leaderboard, 1, "Finish reset progression", [Unlocks.Megafarm, Unlocks.Dinosaurs]),
    ]
    for unlock_target, target_level, reason, prerequisites in route:
        append_route_step(plan, unlock_target, target_level, reason, prerequisites)
    return plan


def unpack_plan_entry(entry):
    if len(entry) == 3:
        unlock_target, reason, prerequisites = entry
        return unlock_target, 1, reason, prerequisites

    return entry


def get_plan_unlocks(plan):
    unlocks = []
    for entry in plan:
        unlock_target, _target_level, _reason, _prerequisites = unpack_plan_entry(entry)
        if unlock_target not in unlocks:
            unlocks.append(unlock_target)
    return unlocks


def validate_unlock_plan(plan) -> bool:
    planned_unlocks = get_plan_unlocks(plan)

    remaining = []
    last_levels = {}
    for entry in plan:
        unlock, target_level, _reason, _prerequisites = unpack_plan_entry(entry)
        if target_level <= 0:
            return False
        if unlock in last_levels and target_level != last_levels[unlock] + 1:
            return False
        last_levels[unlock] = target_level
        remaining.append(entry)

    resolved = []
    while len(remaining) > 0:
        resolved_one = False
        next_remaining = []

        for entry in remaining:
            unlock, _target_level, _reason, prerequisites = unpack_plan_entry(entry)
            prerequisites_ready = True
            for prerequisite in prerequisites:
                if prerequisite in planned_unlocks and prerequisite not in resolved:
                    prerequisites_ready = False

            if prerequisites_ready:
                if unlock not in resolved:
                    resolved.append(unlock)
                resolved_one = True
            else:
                next_remaining.append(entry)

        if not resolved_one:
            return False

        remaining = next_remaining

    return True


def get_live_unlock_cost(unlock_target):
    cost = get_cost(unlock_target)
    if cost == None:
        return None

    for item in cost:
        amount = cost[item]
        if amount == None or amount < 0:
            return None

    return cost


def get_missing_cost_item(cost):
    for item in cost:
        if num_items(item) < cost[item]:
            return item

    return None


def make_unlock_result(unlock_target, status):
    return {"unlock": unlock_target, "status": status}


def prerequisites_are_ready(prerequisites) -> bool:
    for prerequisite in prerequisites:
        if num_unlocked(prerequisite) <= 0:
            return False

    return True


def report_reset_failure(unlock_target, target_level, reason, status, starting_time) -> None:
    cost = get_live_unlock_cost(unlock_target)
    missing_item = None
    if cost != None:
        missing_item = get_missing_cost_item(cost)
    elapsed_time = get_time() - starting_time
    if elapsed_time < 0:
        elapsed_time = 0

    quick_print(
        reason
        + ": "
        + status
        + " unlock="
        + str(unlock_target)
        + " level="
        + str(num_unlocked(unlock_target))
        + "/"
        + str(target_level)
        + " missing="
        + str(missing_item)
        + " elapsed="
        + str(elapsed_time)
        + " seconds"
    )


def unlock_one(unlock_target, prerequisites=None, target_level=1):
    if num_unlocked(unlock_target) >= target_level:
        return make_unlock_result(unlock_target, UNLOCK_ALREADY_COMPLETE)

    if prerequisites != None and not prerequisites_are_ready(prerequisites):
        return make_unlock_result(unlock_target, UNLOCK_MISSING_PREREQUISITE)

    attempts_without_progress = 0
    while num_unlocked(unlock_target) < target_level:
        if attempts_without_progress >= MAX_UNLOCK_ATTEMPTS:
            return make_unlock_result(unlock_target, UNLOCK_NO_PROGRESS)

        cost = get_live_unlock_cost(unlock_target)
        if cost == None:
            return make_unlock_result(unlock_target, UNLOCK_MISSING_COST)

        missing_item = get_missing_cost_item(cost)
        if missing_item != None:
            before_amount = num_items(missing_item)
            required_amount = cost[missing_item] - before_amount
            if not produce_item(missing_item, required_amount):
                return make_unlock_result(unlock_target, UNLOCK_NO_PROGRESS)
            if num_items(missing_item) <= before_amount:
                attempts_without_progress += 1
            else:
                attempts_without_progress = 0
            continue

        before_level = num_unlocked(unlock_target)
        unlock(unlock_target)
        current_level = num_unlocked(unlock_target)
        if current_level >= target_level:
            return make_unlock_result(unlock_target, UNLOCK_SUCCESS)
        if current_level <= before_level:
            return make_unlock_result(unlock_target, UNLOCK_PURCHASE_FAILED)
        attempts_without_progress = 0

    return make_unlock_result(unlock_target, UNLOCK_SUCCESS)


def run_reset_progression() -> bool:
    if num_unlocked(Unlocks.Leaderboard) > 0:
        return True

    starting_time = get_time()
    plan = get_unlock_plan()
    if not validate_unlock_plan(plan):
        quick_print("Reset unlock plan contains a dependency cycle")
        return False

    for entry in plan:
        unlock_target, target_level, reason, prerequisites = unpack_plan_entry(entry)
        result = unlock_one(unlock_target, prerequisites, target_level)
        status = result["status"]
        if status == UNLOCK_SUCCESS or status == UNLOCK_ALREADY_COMPLETE:
            continue

        report_reset_failure(unlock_target, target_level, reason, status, starting_time)
        return False

    return num_unlocked(Unlocks.Leaderboard) > 0


def is_blank_reset_environment() -> bool:
    return (
        get_world_size() == 1
        and num_unlocked(Unlocks.Grass) == 0
        and num_unlocked(Unlocks.Plant) == 0
    )


if __name__ == "__main__":
    if is_blank_reset_environment():
        run_reset_progression()
    else:
        quick_print("Reset progression requires a blank simulation")
