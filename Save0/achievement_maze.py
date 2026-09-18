"""Pure disjoint layout for achievement maze workers."""

from achievement_config import MAZE_REGION_COLUMNS
from achievement_config import MAZE_REGION_COUNT
from achievement_config import MAZE_REGION_ROWS
from achievement_config import MAZE_REGION_SIZE
from navigation import move_to


MAZE_WORLD_WIDTH = MAZE_REGION_COLUMNS * MAZE_REGION_SIZE
MAZE_WORLD_HEIGHT = MAZE_REGION_ROWS * MAZE_REGION_SIZE
MAZE_REUSE_LIMIT = 300
MAZE_RECOVERY_ATTEMPTS = 2

MAZE_WORKER_COMPLETE = "complete"
MAZE_WORKER_RESOURCE_EXHAUSTED = "resource_exhausted"
MAZE_WORKER_RELOCATIONS_EXHAUSTED = "relocations_exhausted"
MAZE_WORKER_BLOCKED = "blocked"
MAZE_WORKER_TREASURE_MISSING = "treasure_missing"


def is_valid_maze_index(maze_index: int) -> bool:
    return maze_index >= 0 and maze_index < MAZE_REGION_COUNT


def get_maze_anchor(maze_index: int):
    if not is_valid_maze_index(maze_index):
        return None

    column = maze_index % MAZE_REGION_COLUMNS
    row = maze_index // MAZE_REGION_COLUMNS
    return column * MAZE_REGION_SIZE, row * MAZE_REGION_SIZE


def get_maze_bounds(maze_index: int):
    anchor = get_maze_anchor(maze_index)
    if anchor == None:
        return None

    anchor_x, anchor_y = anchor
    last_x = anchor_x + MAZE_REGION_SIZE - 1
    last_y = anchor_y + MAZE_REGION_SIZE - 1
    return anchor_x, anchor_y, last_x, last_y


def get_maze_bounds_for_creation(
    creation_x: int,
    creation_y: int,
    maze_size: int,
    world_size: int,
):
    if maze_size <= 0 or world_size < maze_size:
        return None
    if creation_x < 0 or creation_y < 0:
        return None
    if creation_x >= world_size or creation_y >= world_size:
        return None

    lower_x = creation_x - maze_size // 2
    lower_y = creation_y - maze_size // 2

    if lower_x < 0:
        lower_x = 0
    if lower_y < 0:
        lower_y = 0

    if lower_x + maze_size > world_size:
        lower_x = world_size - maze_size
    if lower_y + maze_size > world_size:
        lower_y = world_size - maze_size

    return (
        lower_x,
        lower_y,
        lower_x + maze_size - 1,
        lower_y + maze_size - 1,
    )


def get_safe_maze_creation_coordinate(
    lower_x: int,
    lower_y: int,
    maze_size: int,
    world_size: int,
):
    if maze_size <= 0 or lower_x < 0 or lower_y < 0:
        return None
    if lower_x + maze_size > world_size or lower_y + maze_size > world_size:
        return None

    return lower_x + maze_size // 2, lower_y + maze_size // 2


def get_maze_start_position(maze_index: int):
    bounds = get_maze_bounds(maze_index)
    if bounds == None:
        return None

    return get_safe_maze_creation_coordinate(
        bounds[0],
        bounds[1],
        MAZE_REGION_SIZE,
        MAZE_WORLD_WIDTH,
    )


def get_maze_index(x: int, y: int):
    if x < 0 or y < 0 or x >= MAZE_WORLD_WIDTH or y >= MAZE_WORLD_HEIGHT:
        return None

    column = x // MAZE_REGION_SIZE
    row = y // MAZE_REGION_SIZE
    maze_index = row * MAZE_REGION_COLUMNS + column

    if not is_valid_maze_index(maze_index):
        return None

    return maze_index


def is_maze_coordinate(x: int, y: int, maze_index: int) -> bool:
    return get_maze_index(x, y) == maze_index


def get_maze_worker_jobs(worker_count: int):
    if worker_count <= 0:
        return []

    if worker_count > MAZE_REGION_COUNT:
        worker_count = MAZE_REGION_COUNT

    jobs = []
    for maze_index in range(worker_count):
        start_x, start_y = get_maze_start_position(maze_index)
        jobs.append((maze_index, start_x, start_y))

    return jobs


def get_maze_directions():
    return [North, East, South, West]


def get_maze_probe_coordinates(world_size: int):
    if world_size <= 0:
        return []

    midpoint = world_size // 2
    candidates = [
        (0, 0),
        (world_size - 1, 0),
        (0, world_size - 1),
        (world_size - 1, world_size - 1),
        (midpoint, midpoint),
        (0, midpoint),
        (world_size - 1, midpoint),
        (midpoint, 0),
        (midpoint, world_size - 1),
    ]
    coordinates = []

    for coordinate in candidates:
        if coordinate not in coordinates:
            coordinates.append(coordinate)

    return coordinates


def get_opposite_direction(direction):
    if direction == North:
        return South

    if direction == East:
        return West

    if direction == South:
        return North

    return East


def get_neighbor_position(x: int, y: int, direction):
    if direction == North:
        return x, y + 1

    if direction == East:
        return x + 1, y

    if direction == South:
        return x, y - 1

    return x - 1, y


def add_maze_tile(maze_map, x: int, y: int) -> None:
    position = (x, y)
    if position in maze_map["edges"]:
        return

    maze_map["tiles"].append(position)
    maze_map["edges"][position] = {}


def record_maze_edge(maze_map, x: int, y: int, direction, neighbor_x: int, neighbor_y: int) -> None:
    position = (x, y)
    neighbor = (neighbor_x, neighbor_y)
    opposite = get_opposite_direction(direction)
    maze_map["edges"][position][direction] = neighbor
    maze_map["edges"][neighbor][opposite] = position


def map_maze(maze_index: int, start_x: int, start_y: int):
    bounds = get_maze_bounds(maze_index)
    if bounds == None:
        return None

    if not is_maze_coordinate(start_x, start_y, maze_index):
        return None

    maze_map = {"tiles": [], "edges": {}}
    add_maze_tile(maze_map, start_x, start_y)
    directions = get_maze_directions()
    stack = [(start_x, start_y, None, 0)]

    while len(stack) > 0:
        current_x, current_y, back_direction, direction_index = stack[len(stack) - 1]

        if direction_index >= len(directions):
            stack.pop()
            if len(stack) > 0 and not move(back_direction):
                return None
            continue

        direction = directions[direction_index]
        stack[len(stack) - 1] = (
            current_x,
            current_y,
            back_direction,
            direction_index + 1,
        )
        neighbor_x, neighbor_y = get_neighbor_position(current_x, current_y, direction)

        if not is_maze_coordinate(neighbor_x, neighbor_y, maze_index):
            continue

        if not move(direction):
            continue

        neighbor_position = (neighbor_x, neighbor_y)
        was_discovered = neighbor_position in maze_map["edges"]
        add_maze_tile(maze_map, neighbor_x, neighbor_y)
        record_maze_edge(maze_map, current_x, current_y, direction, neighbor_x, neighbor_y)

        if was_discovered:
            if not move(get_opposite_direction(direction)):
                return None
            continue

        stack.append((neighbor_x, neighbor_y, get_opposite_direction(direction), 0))

    return maze_map


def map_observed_maze_bounds():
    start_x = get_pos_x()
    start_y = get_pos_y()
    directions = get_maze_directions()
    visited = [(start_x, start_y)]
    stack = [(start_x, start_y, None, 0)]
    lower_x = start_x
    lower_y = start_y
    upper_x = start_x
    upper_y = start_y

    while len(stack) > 0:
        current_x, current_y, back_direction, direction_index = stack[len(stack) - 1]

        if direction_index >= len(directions):
            stack.pop()
            if len(stack) > 0 and not move(back_direction):
                return None
            continue

        direction = directions[direction_index]
        stack[len(stack) - 1] = (
            current_x,
            current_y,
            back_direction,
            direction_index + 1,
        )

        if not can_move(direction):
            continue
        if not move(direction):
            return None

        neighbor_x = get_pos_x()
        neighbor_y = get_pos_y()
        if neighbor_x < lower_x:
            lower_x = neighbor_x
        if neighbor_y < lower_y:
            lower_y = neighbor_y
        if neighbor_x > upper_x:
            upper_x = neighbor_x
        if neighbor_y > upper_y:
            upper_y = neighbor_y

        neighbor = (neighbor_x, neighbor_y)
        if neighbor in visited:
            if not move(get_opposite_direction(direction)):
                return None
            continue

        visited.append(neighbor)
        stack.append((neighbor_x, neighbor_y, get_opposite_direction(direction), 0))

    return lower_x, lower_y, upper_x, upper_y


def create_probe_maze(creation_x: int, creation_y: int, substance_cost: int) -> bool:
    move_to(creation_x, creation_y)
    clear()

    if get_ground_type() != Grounds.Soil:
        till()
    if not plant(Entities.Bush):
        return False

    return use_item(Items.Weird_Substance, substance_cost)


def run_maze_placement_probe() -> bool:
    world_size = get_world_size()
    substance_cost = get_reusable_maze_substance_cost()
    if world_size <= 0 or substance_cost <= 0:
        return False

    coordinates = get_maze_probe_coordinates(world_size)
    for index in range(len(coordinates)):
        creation_x, creation_y = coordinates[index]
        if num_items(Items.Weird_Substance) < substance_cost:
            return False
        if not create_probe_maze(creation_x, creation_y, substance_cost):
            return False

        bounds = map_observed_maze_bounds()
        if bounds == None:
            return False

        quick_print(
            "Maze probe creation=("
            + str(creation_x)
            + ","
            + str(creation_y)
            + ") bounds=("
            + str(bounds[0])
            + ","
            + str(bounds[1])
            + ","
            + str(bounds[2])
            + ","
            + str(bounds[3])
            + ")"
        )

    clear()
    return True


def find_shortest_path(maze_map, start_x: int, start_y: int, target_x: int, target_y: int):
    start = (start_x, start_y)
    target = (target_x, target_y)
    edges = maze_map["edges"]

    if start not in edges or target not in edges:
        return None

    if start == target:
        return []

    queue = [start]
    queue_index = 0
    parents = {start: None}
    parent_directions = {}
    directions = get_maze_directions()

    while queue_index < len(queue):
        current = queue[queue_index]
        queue_index += 1

        if current == target:
            break

        for direction in directions:
            if direction not in edges[current]:
                continue

            neighbor = edges[current][direction]
            if neighbor in parents:
                continue

            parents[neighbor] = current
            parent_directions[neighbor] = direction
            queue.append(neighbor)

    if target not in parents:
        return None

    path = []
    current = target
    while current != start:
        path.insert(0, parent_directions[current])
        current = parents[current]

    return path


def find_treasure_path(maze_map, start_x: int, start_y: int):
    treasure_x, treasure_y = measure()
    return find_shortest_path(maze_map, start_x, start_y, treasure_x, treasure_y)


def follow_maze_path(path) -> bool:
    for direction in path:
        if not move(direction):
            return False

    return True


def get_reusable_maze_substance_cost() -> int:
    maze_level = num_unlocked(Unlocks.Mazes)
    if maze_level <= 0:
        return 0

    return MAZE_REGION_SIZE * 2 ** (maze_level - 1)


def get_reusable_maze_substance_budget(relocation_limit: int):
    if relocation_limit < 0:
        return None

    substance_cost = get_reusable_maze_substance_cost()
    if substance_cost <= 0:
        return None

    return substance_cost * (relocation_limit + 1)


def can_fund_reusable_maze(relocation_limit: int) -> bool:
    budget = get_reusable_maze_substance_budget(relocation_limit)
    if budget == None:
        return False

    return num_items(Items.Weird_Substance) >= budget


def create_reusable_maze(maze_index: int, substance_cost: int) -> bool:
    start = get_maze_start_position(maze_index)
    if start == None:
        return False

    start_x, start_y = start
    move_to(start_x, start_y)

    current_entity = get_entity_type()
    if current_entity != None:
        if not can_harvest() or not harvest():
            return False

    if get_ground_type() != Grounds.Soil:
        till()

    if not plant(Entities.Bush):
        return False

    return use_item(Items.Weird_Substance, substance_cost)


def make_maze_worker_result(completed_relocations: int, reason):
    return {"completed": completed_relocations, "reason": reason}


def run_reusable_maze_worker(maze_index: int, relocation_limit=MAZE_REUSE_LIMIT):
    if not is_valid_maze_index(maze_index):
        return make_maze_worker_result(0, MAZE_WORKER_BLOCKED)

    budget = get_reusable_maze_substance_budget(relocation_limit)
    if budget == None or num_items(Items.Weird_Substance) < budget:
        return make_maze_worker_result(0, MAZE_WORKER_RESOURCE_EXHAUSTED)

    substance_cost = get_reusable_maze_substance_cost()
    if not create_reusable_maze(maze_index, substance_cost):
        return make_maze_worker_result(0, MAZE_WORKER_RESOURCE_EXHAUSTED)

    start_x, start_y = get_maze_start_position(maze_index)
    maze_map = map_maze(maze_index, start_x, start_y)
    if maze_map == None:
        return make_maze_worker_result(0, MAZE_WORKER_BLOCKED)

    current_x, current_y = start_x, start_y
    completed_relocations = 0

    for _relocation in range(relocation_limit):
        path_found = False
        for _recovery in range(MAZE_RECOVERY_ATTEMPTS + 1):
            path = find_treasure_path(maze_map, current_x, current_y)
            if path != None and follow_maze_path(path):
                path_found = True
                break

            current_x = get_pos_x()
            current_y = get_pos_y()
            maze_map = map_maze(maze_index, current_x, current_y)
            if maze_map == None:
                break

        if not path_found:
            if path == None:
                return make_maze_worker_result(
                    completed_relocations,
                    MAZE_WORKER_RELOCATIONS_EXHAUSTED,
                )
            return make_maze_worker_result(completed_relocations, MAZE_WORKER_BLOCKED)

        if get_entity_type() != Entities.Treasure:
            return make_maze_worker_result(
                completed_relocations,
                MAZE_WORKER_TREASURE_MISSING,
            )

        if not use_item(Items.Weird_Substance, substance_cost):
            return make_maze_worker_result(
                completed_relocations,
                MAZE_WORKER_RESOURCE_EXHAUSTED,
            )

        completed_relocations += 1
        current_x = get_pos_x()
        current_y = get_pos_y()

    # Harvesting away from the treasure removes an exhausted maze so the
    # worker can create its replacement in the same owned region.
    harvest()
    return make_maze_worker_result(completed_relocations, MAZE_WORKER_COMPLETE)


def report_maze_worker_failure(job, result) -> None:
    maze_index, _start_x, _start_y = job
    quick_print(
        "Maze worker "
        + str(maze_index)
        + " stopped after "
        + str(result["completed"])
        + " relocations: "
        + result["reason"]
    )


def run_maze_worker(job) -> bool:
    while True:
        result = run_reusable_maze_worker(job[0])
        if result["reason"] != MAZE_WORKER_COMPLETE:
            report_maze_worker_failure(job, result)
            return False


def start_maze_workers(jobs):
    parent_jobs = []
    worker_handles = []

    for index in range(len(jobs) - 1):
        worker = spawn_drone(run_maze_worker, jobs[index])
        if worker == None:
            parent_jobs.append(jobs[index])
        else:
            worker_handles.append(worker)

    parent_jobs.append(jobs[len(jobs) - 1])
    return parent_jobs, worker_handles


def run_maze_parent_jobs(parent_jobs):
    active_jobs = []
    for job in parent_jobs:
        active_jobs.append(job)

    while len(active_jobs) > 0:
        for index in range(len(active_jobs) - 1, -1, -1):
            job = active_jobs[index]
            result = run_reusable_maze_worker(job[0])
            if result["reason"] == MAZE_WORKER_COMPLETE:
                continue

            report_maze_worker_failure(job, result)
            active_jobs.pop(index)

    return False


def run_maze_workers() -> bool:
    jobs = get_maze_worker_jobs(max_drones())
    if len(jobs) == 0:
        return False

    parent_jobs, _worker_handles = start_maze_workers(jobs)
    return run_maze_parent_jobs(parent_jobs)
