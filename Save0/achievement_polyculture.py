"""Pure coordinate layout for achievement polyculture workers."""

from navigation import move_to


HAY_MODE = "Hay"
CARROT_MODE = "Carrot"

PRIMARY_ROLE = "primary"
COMPANION_ROLE = "companion"
GUARD_ROLE = "guard"

TEMPLATE_SIZE = 8
MAX_TRANSACTION_ATTEMPTS = 3


def is_supported_mode(mode) -> bool:
    return mode == HAY_MODE or mode == CARROT_MODE


def get_region_anchor(x: int, y: int):
    return (x // TEMPLATE_SIZE) * TEMPLATE_SIZE, (y // TEMPLATE_SIZE) * TEMPLATE_SIZE


def get_primary_position(x: int, y: int):
    anchor_x, anchor_y = get_region_anchor(x, y)
    center_offset = TEMPLATE_SIZE // 2 - 1
    return anchor_x + center_offset, anchor_y + center_offset


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


def is_supported_companion_entity(entity) -> bool:
    return (
        entity == Entities.Grass
        or entity == Entities.Bush
        or entity == Entities.Tree
        or entity == Entities.Carrot
    )


def plant_entity_for_transaction(entity) -> bool:
    if entity == Entities.Grass:
        if get_ground_type() != Grounds.Grassland:
            till()
    elif get_ground_type() != Grounds.Soil:
        till()

    return plant(entity)


def establish_primary(primary_entity) -> bool:
    current_entity = get_entity_type()

    if current_entity == primary_entity:
        return True

    if current_entity != None:
        return False

    return plant_entity_for_transaction(primary_entity)


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


def wait_for_primary() -> bool:
    for _check in range(MAX_TRANSACTION_ATTEMPTS * 10000):
        if can_harvest():
            return True

    return False


def perform_polculture_transaction(primary_x: int, primary_y: int, mode) -> bool:
    if not is_primary_tile(primary_x, primary_y, mode):
        return False

    primary_entity = get_primary_entity(mode)

    for _attempt in range(MAX_TRANSACTION_ATTEMPTS):
        move_to(primary_x, primary_y)

        if not establish_primary(primary_entity):
            return False

        companion = get_transaction_companion(primary_x, primary_y, mode)

        if companion == None:
            return False

        if not companion:
            if not can_harvest() or not harvest():
                return False
            continue

        companion_entity, companion_x, companion_y = companion
        move_to(companion_x, companion_y)

        if get_entity_type() != None and get_entity_type() != companion_entity:
            return False

        if get_entity_type() == None and not plant_entity_for_transaction(companion_entity):
            return False

        move_to(primary_x, primary_y)

        if not wait_for_primary():
            return False

        if not harvest():
            return False

        return plant_entity_for_transaction(primary_entity)

    return False


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
    required = {}
    for item in (Items.Hay, Items.Wood):
        primary_amount = 0
        if item in primary_cost:
            primary_amount = primary_cost[item]

        companion_amount = 0
        for companion_cost in companion_costs:
            if item in companion_cost and companion_cost[item] > companion_amount:
                companion_amount = companion_cost[item]

        required[item] = (primary_amount + companion_amount) * worker_count

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
