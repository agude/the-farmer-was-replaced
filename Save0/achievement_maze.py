"""Pure disjoint layout for achievement maze workers."""

from achievement_config import MAZE_REGION_COLUMNS
from achievement_config import MAZE_REGION_COUNT
from achievement_config import MAZE_REGION_ROWS
from achievement_config import MAZE_REGION_SIZE


MAZE_WORLD_WIDTH = MAZE_REGION_COLUMNS * MAZE_REGION_SIZE
MAZE_WORLD_HEIGHT = MAZE_REGION_ROWS * MAZE_REGION_SIZE


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


def get_maze_start_position(maze_index: int):
    anchor = get_maze_anchor(maze_index)
    if anchor == None:
        return None

    return anchor


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
