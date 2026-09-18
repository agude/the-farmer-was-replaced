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


def get_unlock_plan():
    return [
        (Unlocks.Variables, "Track reset state with variables", []),
        (Unlocks.Operators, "Compare live inventory and unlock levels", [Unlocks.Variables]),
        (Unlocks.Senses, "Read the farm state before planting", [Unlocks.Operators]),
        (Unlocks.Loops, "Repeat bounded production and purchase attempts", [Unlocks.Operators]),
        (Unlocks.Functions, "Reuse bounded reset-safe producers", [Unlocks.Loops]),
        (Unlocks.Lists, "Store explicit progression queues", [Unlocks.Functions]),
        (Unlocks.Dictionaries, "Store live multi-item costs", [Unlocks.Lists]),
        (Unlocks.Import, "Load reset-safe shared farmers", [Unlocks.Functions]),
        (Unlocks.Timing, "Measure bounded reset stages", [Unlocks.Functions]),
        (Unlocks.Utilities, "Use reusable game utilities", [Unlocks.Functions]),
        (Unlocks.Costs, "Read unlock costs at runtime", [Unlocks.Variables]),
        (Unlocks.Simulation, "Rehearse progression without live mutation", [Unlocks.Costs]),
        (Unlocks.Grass, "Start the first bounded resource producer", [Unlocks.Variables]),
        (Unlocks.Plant, "Enable crop planting for resource producers", [Unlocks.Grass]),
        (Unlocks.Expand, "Open enough tiles for reset-safe batches", [Unlocks.Plant]),
        (Unlocks.Trees, "Produce Wood for later unlocks", [Unlocks.Plant, Unlocks.Expand]),
        (Unlocks.Carrots, "Produce Carrots for later unlocks", [Unlocks.Plant, Unlocks.Expand]),
        (Unlocks.Watering, "Maintain water-dependent crops", [Unlocks.Plant, Unlocks.Expand]),
        (Unlocks.Pumpkins, "Produce Pumpkin batches", [Unlocks.Watering, Unlocks.Expand]),
        (
            Unlocks.Cactus,
            "Produce Cactus and Weird Substance inputs",
            [Unlocks.Plant, Unlocks.Expand],
        ),
        (
            Unlocks.Sunflowers,
            "Produce Power for accelerated stages",
            [Unlocks.Watering, Unlocks.Expand],
        ),
        (
            Unlocks.Polyculture,
            "Enable Hay and Carrot companion yields",
            [Unlocks.Carrots, Unlocks.Trees],
        ),
        (
            Unlocks.Megafarm,
            "Enable parallel reset-safe workers",
            [Unlocks.Expand, Unlocks.Polyculture],
        ),
        (Unlocks.Mazes, "Enable reusable maze gold production", [Unlocks.Plant, Unlocks.Expand]),
        (Unlocks.Dinosaurs, "Enable bounded bone production", [Unlocks.Mazes, Unlocks.Cactus]),
        (Unlocks.Fertilizer, "Enable Weird Substance production", [Unlocks.Cactus]),
        (Unlocks.Speed, "Accelerate the remaining reset stages", [Unlocks.Expand]),
        (Unlocks.Hats, "Enable achievement and reset hat changes", [Unlocks.Plant]),
        (
            Unlocks.Leaderboard,
            "Finish reset progression",
            [Unlocks.Simulation, Unlocks.Megafarm, Unlocks.Dinosaurs],
        ),
    ]


def get_plan_unlocks(plan):
    unlocks = []
    for unlock, _reason, _prerequisites in plan:
        unlocks.append(unlock)
    return unlocks


def validate_unlock_plan(plan) -> bool:
    planned_unlocks = get_plan_unlocks(plan)

    for index in range(len(planned_unlocks)):
        for later_index in range(index + 1, len(planned_unlocks)):
            if planned_unlocks[index] == planned_unlocks[later_index]:
                return False

    remaining = []
    for entry in plan:
        remaining.append(entry)

    resolved = []
    while len(remaining) > 0:
        resolved_one = False
        next_remaining = []

        for unlock, _reason, prerequisites in remaining:
            prerequisites_ready = True
            for prerequisite in prerequisites:
                if prerequisite in planned_unlocks and prerequisite not in resolved:
                    prerequisites_ready = False

            if prerequisites_ready:
                resolved.append(unlock)
                resolved_one = True
            else:
                next_remaining.append((unlock, _reason, prerequisites))

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


def unlock_one(unlock_target, prerequisites=None):
    if num_unlocked(unlock_target) > 0:
        return make_unlock_result(unlock_target, UNLOCK_ALREADY_COMPLETE)

    if prerequisites != None and not prerequisites_are_ready(prerequisites):
        return make_unlock_result(unlock_target, UNLOCK_MISSING_PREREQUISITE)

    for _attempt in range(MAX_UNLOCK_ATTEMPTS):
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
                return make_unlock_result(unlock_target, UNLOCK_NO_PROGRESS)
            continue

        if unlock(unlock_target) and num_unlocked(unlock_target) > 0:
            return make_unlock_result(unlock_target, UNLOCK_SUCCESS)

        if num_unlocked(unlock_target) > 0:
            return make_unlock_result(unlock_target, UNLOCK_SUCCESS)

        return make_unlock_result(unlock_target, UNLOCK_PURCHASE_FAILED)

    return make_unlock_result(unlock_target, UNLOCK_NO_PROGRESS)


def run_reset_progression() -> bool:
    if num_unlocked(Unlocks.Leaderboard) > 0:
        return True

    plan = get_unlock_plan()
    if not validate_unlock_plan(plan):
        quick_print("Reset unlock plan contains a dependency cycle")
        return False

    for unlock_target, reason, prerequisites in plan:
        result = unlock_one(unlock_target, prerequisites)
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
