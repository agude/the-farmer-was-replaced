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


def append_unlock_steps(plan, unlock_target, reason, prerequisites) -> None:
    target_level = get_target_level(unlock_target)
    for level in range(1, target_level + 1):
        level_reason = reason
        if level > 1:
            level_reason = reason + " (level " + str(level) + ")"

        level_prerequisites = prerequisites
        if level > 1:
            level_prerequisites = []
        plan.append((unlock_target, level, level_reason, level_prerequisites))


def get_unlock_plan():
    plan = []
    append_unlock_steps(plan, Unlocks.Variables, "Track reset state with variables", [])
    append_unlock_steps(
        plan,
        Unlocks.Operators,
        "Compare live inventory and unlock levels",
        [Unlocks.Variables],
    )
    append_unlock_steps(
        plan, Unlocks.Senses, "Read the farm state before planting", [Unlocks.Operators]
    )
    append_unlock_steps(
        plan, Unlocks.Loops, "Repeat bounded production and purchase attempts", [Unlocks.Operators]
    )
    append_unlock_steps(
        plan, Unlocks.Functions, "Reuse bounded reset-safe producers", [Unlocks.Loops]
    )
    append_unlock_steps(
        plan, Unlocks.Lists, "Store explicit progression queues", [Unlocks.Functions]
    )
    append_unlock_steps(plan, Unlocks.Dictionaries, "Store live multi-item costs", [Unlocks.Lists])
    append_unlock_steps(plan, Unlocks.Import, "Load reset-safe shared farmers", [Unlocks.Functions])
    append_unlock_steps(plan, Unlocks.Timing, "Measure bounded reset stages", [Unlocks.Functions])
    append_unlock_steps(plan, Unlocks.Utilities, "Use reusable game utilities", [Unlocks.Functions])
    append_unlock_steps(plan, Unlocks.Costs, "Read unlock costs at runtime", [Unlocks.Variables])
    append_unlock_steps(
        plan,
        Unlocks.Simulation,
        "Rehearse progression without live mutation",
        [Unlocks.Costs],
    )
    append_unlock_steps(
        plan, Unlocks.Grass, "Start the first bounded resource producer", [Unlocks.Variables]
    )
    append_unlock_steps(
        plan, Unlocks.Plant, "Enable crop planting for resource producers", [Unlocks.Grass]
    )
    append_unlock_steps(
        plan, Unlocks.Expand, "Open enough tiles for reset-safe batches", [Unlocks.Plant]
    )
    append_unlock_steps(
        plan, Unlocks.Trees, "Produce Wood for later unlocks", [Unlocks.Plant, Unlocks.Expand]
    )
    append_unlock_steps(
        plan, Unlocks.Carrots, "Produce Carrots for later unlocks", [Unlocks.Plant, Unlocks.Expand]
    )
    append_unlock_steps(
        plan, Unlocks.Watering, "Maintain water-dependent crops", [Unlocks.Plant, Unlocks.Expand]
    )
    append_unlock_steps(
        plan, Unlocks.Pumpkins, "Produce Pumpkin batches", [Unlocks.Watering, Unlocks.Expand]
    )
    append_unlock_steps(
        plan,
        Unlocks.Cactus,
        "Produce Cactus and Weird Substance inputs",
        [Unlocks.Plant, Unlocks.Expand],
    )
    append_unlock_steps(
        plan,
        Unlocks.Sunflowers,
        "Produce Power for accelerated stages",
        [Unlocks.Watering, Unlocks.Expand],
    )
    append_unlock_steps(
        plan,
        Unlocks.Polyculture,
        "Enable Hay and Carrot companion yields",
        [Unlocks.Carrots, Unlocks.Trees],
    )
    append_unlock_steps(
        plan,
        Unlocks.Megafarm,
        "Enable parallel reset-safe workers",
        [Unlocks.Expand, Unlocks.Polyculture],
    )
    append_unlock_steps(
        plan, Unlocks.Mazes, "Enable reusable maze gold production", [Unlocks.Plant, Unlocks.Expand]
    )
    append_unlock_steps(
        plan, Unlocks.Dinosaurs, "Enable bounded bone production", [Unlocks.Mazes, Unlocks.Cactus]
    )
    append_unlock_steps(
        plan, Unlocks.Fertilizer, "Enable Weird Substance production", [Unlocks.Cactus]
    )
    append_unlock_steps(
        plan, Unlocks.Speed, "Accelerate the remaining reset stages", [Unlocks.Expand]
    )
    append_unlock_steps(
        plan, Unlocks.Hats, "Enable achievement and reset hat changes", [Unlocks.Plant]
    )
    append_unlock_steps(
        plan,
        Unlocks.Leaderboard,
        "Finish reset progression",
        [Unlocks.Simulation, Unlocks.Megafarm, Unlocks.Dinosaurs],
    )
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

        quick_print(reason + ": " + status)
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
