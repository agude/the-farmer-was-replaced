"""Pure coordinate layout for achievement polyculture workers."""

from navigation import move_to
from planting import ensure_ground_for_entity


HAY_MODE = "Hay"
CARROT_MODE = "Carrot"

PRIMARY_ROLE = "primary"
COMPANION_ROLE = "companion"
GUARD_ROLE = "guard"

TEMPLATE_SIZE = 8
MAX_TRANSACTION_ATTEMPTS = 3
MAX_PRIMARY_WAIT_CHECKS = 1000000
MAX_STAGNANT_PRIMARY_CHECKS = 1000


def is_supported_mode(mode) -> bool:
    return mode == HAY_MODE or mode == CARROT_MODE


def get_region_anchor(x: int, y: int):
    return (x // TEMPLATE_SIZE) * TEMPLATE_SIZE, (y // TEMPLATE_SIZE) * TEMPLATE_SIZE


def get_primary_position(x: int, y: int):
    anchor_x, anchor_y = get_region_anchor(x, y)
    center_offset = TEMPLATE_SIZE // 2 - 1
    return anchor_x + center_offset, anchor_y + center_offset


def get_primary_supply_position(primary_x: int, primary_y: int):
    anchor_x, anchor_y = get_region_anchor(primary_x, primary_y)
    guard_offset = TEMPLATE_SIZE - 1
    return anchor_x + guard_offset, anchor_y + guard_offset


def is_primary_tile(x: int, y: int, mode) -> bool:
    center_offset = TEMPLATE_SIZE // 2 - 1
    return (
        is_supported_mode(mode)
        and x % TEMPLATE_SIZE == center_offset
        and y % TEMPLATE_SIZE == center_offset
    )


def is_template_companion_tile(x: int, y: int, mode) -> bool:
    if not is_supported_mode(mode):
        return False

    local_x = x % TEMPLATE_SIZE
    local_y = y % TEMPLATE_SIZE
    center_offset = TEMPLATE_SIZE // 2 - 1
    distance = abs(local_x - center_offset) + abs(local_y - center_offset)
    return distance > 0 and distance <= 3


def get_layout_role(x: int, y: int, mode):
    if is_primary_tile(x, y, mode):
        return PRIMARY_ROLE

    if is_template_companion_tile(x, y, mode):
        return COMPANION_ROLE

    return GUARD_ROLE


def get_primary_owner(x: int, y: int, mode):
    if not is_supported_mode(mode) or x < 0 or y < 0:
        return None

    return get_primary_position(x, y)


def is_supply_tile(x: int, y: int, mode) -> bool:
    if not is_supported_mode(mode) or x < 0 or y < 0:
        return False

    guard_offset = TEMPLATE_SIZE - 1
    return x % TEMPLATE_SIZE == guard_offset and y % TEMPLATE_SIZE == guard_offset


def get_supply_owner(x: int, y: int, mode):
    if not is_supply_tile(x, y, mode):
        return None

    return get_primary_position(x, y)


def is_allowed_companion_coordinate(
    x: int,
    y: int,
    primary_x: int,
    primary_y: int,
    mode,
) -> bool:
    if not is_template_companion_tile(x, y, mode):
        return False

    return get_primary_owner(x, y, mode) == (primary_x, primary_y)


def get_primary_positions(world_size: int, mode):
    positions = []

    for x in range(world_size):
        for y in range(world_size):
            if is_primary_tile(x, y, mode):
                positions.append((x, y))

    return positions


def get_companion_positions_for_primary(
    primary_x: int,
    primary_y: int,
    world_size: int,
    mode,
):
    positions = []

    anchor_x, anchor_y = get_region_anchor(primary_x, primary_y)

    for x in range(anchor_x, anchor_x + TEMPLATE_SIZE):
        for y in range(anchor_y, anchor_y + TEMPLATE_SIZE):
            if x >= world_size or y >= world_size:
                continue

            if is_allowed_companion_coordinate(x, y, primary_x, primary_y, mode):
                positions.append((x, y))

    return positions


def get_primary_entity(mode):
    if mode == HAY_MODE:
        return Entities.Grass

    if mode == CARROT_MODE:
        return Entities.Carrot

    return None


def water_after_planting() -> bool:
    if get_water() >= 1 or num_items(Items.Water) <= 0:
        return True

    return use_item(Items.Water)


def is_supported_companion_entity(entity) -> bool:
    return (
        entity == Entities.Grass
        or entity == Entities.Bush
        or entity == Entities.Tree
        or entity == Entities.Carrot
    )


def plant_entity_for_transaction(entity) -> bool:
    if not ensure_ground_for_entity(entity):
        return False

    if not plant(entity):
        return False

    return water_after_planting()


def report_input_replenishment_failure(primary_x: int, primary_y: int, item) -> bool:
    quick_print(
        "Polyculture input replenishment failed: primary=("
        + str(primary_x)
        + ","
        + str(primary_y)
        + ") item="
        + str(item)
        + " phase=input-replenishment"
    )
    return False


def plant_hay_supply(primary_x: int, primary_y: int) -> bool:
    supply_x, supply_y = get_primary_supply_position(primary_x, primary_y)
    move_to(supply_x, supply_y)

    current_entity = get_entity_type()
    if current_entity == Entities.Grass and get_ground_type() == Grounds.Grassland:
        return True

    if current_entity != None:
        # An unguarded harvest intentionally removes a conflicting supply crop.
        harvest()
        if get_entity_type() != None:
            return False

    if not ensure_ground_for_entity(Entities.Grass):
        return False
    return plant(Entities.Grass)


def replenish_hay(primary_x: int, primary_y: int, missing_amount: int) -> bool:
    target_amount = num_items(Items.Hay) + missing_amount

    while num_items(Items.Hay) < target_amount:
        if not plant_hay_supply(primary_x, primary_y):
            return False
        if not wait_for_primary(Entities.Grass) or not harvest():
            return False

    move_to(primary_x, primary_y)
    return True


def validate_primary_cost(primary_x: int, primary_y: int, cost) -> bool:
    if cost == None:
        return report_input_replenishment_failure(primary_x, primary_y, None)

    for item in cost:
        amount = cost[item]
        if amount == None or amount < 0:
            return report_input_replenishment_failure(primary_x, primary_y, item)
        if num_items(item) >= amount:
            continue
        if item != Items.Hay:
            return report_input_replenishment_failure(primary_x, primary_y, item)

    return True


def ensure_primary_inputs(primary_x: int, primary_y: int, primary_entity) -> bool:
    cost = get_cost(primary_entity)
    if not validate_primary_cost(primary_x, primary_y, cost):
        return False

    for item in cost:
        missing_amount = cost[item] - num_items(item)
        if missing_amount <= 0:
            continue
        if not replenish_hay(primary_x, primary_y, missing_amount):
            return report_input_replenishment_failure(primary_x, primary_y, item)

    move_to(primary_x, primary_y)
    refreshed_cost = get_cost(primary_entity)
    if not validate_primary_cost(primary_x, primary_y, refreshed_cost):
        return False

    for item in refreshed_cost:
        if num_items(item) < refreshed_cost[item]:
            return report_input_replenishment_failure(primary_x, primary_y, item)

    return True


def plant_primary_for_transaction(primary_x: int, primary_y: int, primary_entity) -> bool:
    if primary_entity == Entities.Carrot and not ensure_primary_inputs(
        primary_x,
        primary_y,
        primary_entity,
    ):
        return False

    return plant_entity_for_transaction(primary_entity)


def establish_primary(primary_x: int, primary_y: int, primary_entity) -> bool:
    current_entity = get_entity_type()

    if current_entity == primary_entity:
        return True

    if current_entity != None:
        return False

    return plant_primary_for_transaction(primary_x, primary_y, primary_entity)


def get_transaction_companion(primary_x: int, primary_y: int, mode):
    companion = get_companion()

    if companion == None:
        return None

    companion_entity = companion[0]
    companion_x, companion_y = companion[1]

    if not is_supported_companion_entity(companion_entity):
        return False

    if not is_allowed_companion_coordinate(
        companion_x,
        companion_y,
        primary_x,
        primary_y,
        mode,
    ):
        return False

    return companion_entity, companion_x, companion_y


def wait_for_primary(primary_entity) -> bool:
    starting_tick = get_tick_count()
    last_tick = starting_tick
    stagnant_checks = 0

    for _check in range(MAX_PRIMARY_WAIT_CHECKS):
        if get_entity_type() != primary_entity:
            return False
        if can_harvest():
            return True

        current_tick = get_tick_count()
        if current_tick == last_tick:
            stagnant_checks += 1
        else:
            last_tick = current_tick
            stagnant_checks = 0

        if stagnant_checks >= MAX_STAGNANT_PRIMARY_CHECKS:
            return False

    return False


def wait_for_companion_entity(entity) -> bool:
    for _check in range(MAX_TRANSACTION_ATTEMPTS):
        if get_entity_type() == entity:
            return True

    return False


def wait_for_companion_harvest(entity) -> bool:
    starting_tick = get_tick_count()
    last_tick = starting_tick
    stagnant_checks = 0

    for _check in range(MAX_PRIMARY_WAIT_CHECKS):
        if get_entity_type() != entity:
            return False
        if can_harvest():
            return True

        current_tick = get_tick_count()
        if current_tick == last_tick:
            stagnant_checks += 1
        else:
            last_tick = current_tick
            stagnant_checks = 0

        if stagnant_checks >= MAX_STAGNANT_PRIMARY_CHECKS:
            return False

    return False


def replace_companion_entity(entity) -> bool:
    current_entity = get_entity_type()

    if current_entity == entity:
        return True

    if current_entity != None:
        # An unguarded harvest intentionally removes an unready old companion.
        harvest()

        if get_entity_type() != None:
            return False

    if not ensure_ground_for_entity(entity):
        return False

    if not plant(entity):
        return False

    return water_after_planting()


def report_transaction_failure(
    primary_x: int,
    primary_y: int,
    companion_x,
    companion_y,
    expected_entity,
    observed_entity,
    phase,
) -> bool:
    quick_print(
        "Polyculture transaction failed: primary=("
        + str(primary_x)
        + ","
        + str(primary_y)
        + ") companion=("
        + str(companion_x)
        + ","
        + str(companion_y)
        + ") expected="
        + str(expected_entity)
        + " observed="
        + str(observed_entity)
        + " phase="
        + phase
    )
    return False


def perform_polculture_transaction(primary_x: int, primary_y: int, mode) -> bool:
    if not is_primary_tile(primary_x, primary_y, mode):
        return report_transaction_failure(
            primary_x,
            primary_y,
            None,
            None,
            get_primary_entity(mode),
            None,
            "primary-position",
        )

    primary_entity = get_primary_entity(mode)

    for _attempt in range(MAX_TRANSACTION_ATTEMPTS):
        move_to(primary_x, primary_y)

        if not establish_primary(primary_x, primary_y, primary_entity):
            return report_transaction_failure(
                primary_x,
                primary_y,
                None,
                None,
                primary_entity,
                get_entity_type(),
                "primary-setup",
            )

        companion = get_transaction_companion(primary_x, primary_y, mode)

        if companion == None:
            if not can_harvest() or not harvest():
                return report_transaction_failure(
                    primary_x,
                    primary_y,
                    None,
                    None,
                    None,
                    get_entity_type(),
                    "companion-request",
                )
            continue

        if not companion:
            if not can_harvest() or not harvest():
                return report_transaction_failure(
                    primary_x,
                    primary_y,
                    None,
                    None,
                    None,
                    get_entity_type(),
                    "companion-request",
                )
            continue

        companion_entity, companion_x, companion_y = companion
        move_to(companion_x, companion_y)

        if not replace_companion_entity(companion_entity):
            return report_transaction_failure(
                primary_x,
                primary_y,
                companion_x,
                companion_y,
                companion_entity,
                get_entity_type(),
                "companion-setup",
            )

        if not wait_for_companion_entity(companion_entity):
            return report_transaction_failure(
                primary_x,
                primary_y,
                companion_x,
                companion_y,
                companion_entity,
                get_entity_type(),
                "companion-readiness",
            )

        move_to(primary_x, primary_y)

        if not wait_for_primary(primary_entity):
            return report_transaction_failure(
                primary_x,
                primary_y,
                companion_x,
                companion_y,
                companion_entity,
                get_entity_type(),
                "primary-readiness",
            )

        if not harvest():
            return report_transaction_failure(
                primary_x,
                primary_y,
                companion_x,
                companion_y,
                companion_entity,
                get_entity_type(),
                "primary-harvest",
            )

        if mode == CARROT_MODE:
            move_to(companion_x, companion_y)

            if not wait_for_companion_harvest(companion_entity) or not harvest():
                return report_transaction_failure(
                    primary_x,
                    primary_y,
                    companion_x,
                    companion_y,
                    companion_entity,
                    get_entity_type(),
                    "companion-harvest",
                )

            move_to(primary_x, primary_y)

        if not plant_primary_for_transaction(primary_x, primary_y, primary_entity):
            return report_transaction_failure(
                primary_x,
                primary_y,
                companion_x,
                companion_y,
                companion_entity,
                get_entity_type(),
                "primary-replant",
            )

        return True

    return report_transaction_failure(
        primary_x,
        primary_y,
        None,
        None,
        primary_entity,
        get_entity_type(),
        "retry-limit",
    )


def get_polculture_worker_jobs(world_size: int, mode):
    positions = get_primary_positions(world_size, mode)
    capacity = max_drones()

    if capacity <= 0:
        capacity = 1

    if len(positions) < capacity:
        capacity = len(positions)

    jobs = []
    for index in range(capacity):
        primary_x, primary_y = positions[index]
        jobs.append((primary_x, primary_y, mode))

    return jobs


def get_carrot_startup_requirements(world_size: int):
    jobs = get_polculture_worker_jobs(world_size, CARROT_MODE)
    if len(jobs) == 0:
        return None

    primary_cost = get_cost(Entities.Carrot)
    companion_costs = [
        get_cost(Entities.Grass),
        get_cost(Entities.Bush),
        get_cost(Entities.Tree),
        get_cost(Entities.Carrot),
    ]
    if primary_cost == None:
        return None

    for companion_cost in companion_costs:
        if companion_cost == None:
            return None

    worker_count = len(jobs)
    required = get_carrot_transaction_requirements(primary_cost, companion_costs)

    for item in primary_cost:
        required[item] = required[item] + primary_cost[item]

    for item in required:
        required[item] = required[item] * worker_count

    return required


def get_carrot_transaction_requirements(primary_cost, companion_costs):
    required = {}
    companion_requirements = {}

    for item in primary_cost:
        required[item] = primary_cost[item]

    for companion_cost in companion_costs:
        for item in companion_cost:
            companion_amount = companion_cost[item]
            if (
                item not in companion_requirements
                or companion_amount > companion_requirements[item]
            ):
                companion_requirements[item] = companion_amount

    for item in companion_requirements:
        if item in required:
            required[item] = required[item] + companion_requirements[item]
        else:
            required[item] = companion_requirements[item]

    return required


def can_fund_carrot_startup(world_size: int) -> bool:
    required = get_carrot_startup_requirements(world_size)
    if required == None:
        return False

    for item in required:
        if num_items(item) < required[item]:
            return False

    return True


def run_polculture_worker_for_cycles(job, cycle_count: int) -> bool:
    primary_x, primary_y, mode = job

    for _cycle in range(cycle_count):
        if not perform_polculture_transaction(primary_x, primary_y, mode):
            return False

    return True


def run_polculture_worker(job) -> bool:
    primary_x, primary_y, mode = job

    while True:
        if not perform_polculture_transaction(primary_x, primary_y, mode):
            quick_print("Polyculture worker failed")
            return False


def start_polculture_workers(jobs):
    parent_jobs = []
    worker_handles = []

    for index in range(len(jobs) - 1):
        worker = spawn_drone(run_polculture_worker, jobs[index])

        if worker == None:
            parent_jobs.append(jobs[index])
        else:
            worker_handles.append(worker)

    parent_jobs.append(jobs[len(jobs) - 1])
    return parent_jobs, worker_handles


def run_polculture_workers(world_size: int, mode) -> bool:
    jobs = get_polculture_worker_jobs(world_size, mode)

    if len(jobs) == 0:
        return False

    parent_jobs, _worker_handles = start_polculture_workers(jobs)

    while True:
        for index in range(len(parent_jobs)):
            primary_x, primary_y, primary_mode = parent_jobs[index]

            if not perform_polculture_transaction(primary_x, primary_y, primary_mode):
                return False
