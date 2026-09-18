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
