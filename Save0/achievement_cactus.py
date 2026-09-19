# Full-field cactus cycle for the Cactus Master achievement.

from achievement_config import DEBUG_OUTPUT
from cactus import maintain_cactus_tile
from navigation import move_to
from parallel_farming import dispatch_indexed_jobs


def build_row_jobs(size: int):
    jobs = []

    for row_y in range(size):
        jobs.append((row_y, 0, 0, size, size, False))

    return jobs


def build_column_jobs(size: int):
    jobs = []

    for column_x in range(size):
        jobs.append((column_x, 0, 0, size, size, False))

    return jobs


def run_phase(jobs, task) -> bool:
    results = dispatch_indexed_jobs(jobs, task)

    for result in results:
        if not result:
            return False

    return True


def grow_full_field_row_job(job) -> bool:
    row_y, start_x, _start_y, width, _height, _reverse = job
    pending = []

    for offset in range(width):
        pending.append(start_x + offset)

    while len(pending) > 0:
        move_to(pending[0], row_y)
        still_pending = []
        previous_x = pending[0]

        for index in range(len(pending)):
            x = pending[index]

            if index > 0:
                for _step in range(x - previous_x):
                    if not move(East):
                        return False

            readiness = maintain_cactus_tile()

            if readiness == None:
                return False

            if not readiness:
                still_pending.append(x)

            previous_x = x

        pending = still_pending

    move_to(start_x, row_y)
    return True


def measure_adjacent(direction):
    current_size = measure()
    neighbor_size = measure(direction)
    return current_size, neighbor_size


def should_swap_forward(current_size, neighbor_size, reverse: bool) -> bool:
    if reverse:
        return current_size < neighbor_size

    return current_size > neighbor_size


def should_swap_backward(current_size, neighbor_size, reverse: bool) -> bool:
    if reverse:
        return current_size > neighbor_size

    return current_size < neighbor_size


def sort_lane(
    start_x: int,
    start_y: int,
    length: int,
    forward_direction,
    backward_direction,
    reverse: bool,
) -> bool:
    if length <= 0:
        return False

    left = 0
    right = length - 1
    move_to(start_x, start_y)

    while left < right:
        swapped = False

        for offset in range(left, right):
            current_size, neighbor_size = measure_adjacent(forward_direction)

            if should_swap_forward(current_size, neighbor_size, reverse):
                swap(forward_direction)
                swapped = True

            if offset < right - 1 and not move(forward_direction):
                return False

        right -= 1

        if not swapped:
            move_to(start_x, start_y)
            return True

        swapped = False

        for offset in range(right, left, -1):
            current_size, neighbor_size = measure_adjacent(backward_direction)

            if should_swap_backward(current_size, neighbor_size, reverse):
                swap(backward_direction)
                swapped = True

            if offset > left + 1 and not move(backward_direction):
                return False

        left += 1

        if not swapped:
            move_to(start_x, start_y)
            return True

    move_to(start_x, start_y)
    return True


def sort_full_field_row_job(job) -> bool:
    row_y, start_x, _start_y, width, _height, reverse = job
    return sort_lane(start_x, row_y, width, East, West, reverse)


def sort_full_field_column_job(job) -> bool:
    column_x, start_x, start_y, _width, height, reverse = job
    return sort_lane(column_x, start_y, height, North, South, reverse)


def grow_full_field(size: int) -> bool:
    return run_phase(build_row_jobs(size), grow_full_field_row_job)


def sort_full_field(size: int) -> bool:
    return sort_full_field_rows(size) and sort_full_field_columns(size)


def sort_full_field_rows(size: int) -> bool:
    return run_phase(build_row_jobs(size), sort_full_field_row_job)


def sort_full_field_columns(size: int) -> bool:
    if not run_phase(build_column_jobs(size), sort_full_field_column_job):
        return False

    return True


def report_phase_ticks(label, starting_tick) -> None:
    if DEBUG_OUTPUT:
        quick_print(label + " ticks " + str(get_tick_count() - starting_tick))


def harvest_full_field() -> bool:
    move_to(0, 0)

    if not can_harvest():
        return False

    # Do not fertilize the chain harvest: infection reduces its yield.
    harvest()
    return True


def farm_achievement_cactus_cycle() -> bool:
    size = get_world_size()

    if size <= 0:
        return False

    planting_start = get_tick_count()
    planting_succeeded = grow_full_field(size)
    report_phase_ticks("Cactus planting", planting_start)

    if not planting_succeeded:
        return False

    row_sort_start = get_tick_count()
    row_sort_succeeded = sort_full_field_rows(size)
    report_phase_ticks("Cactus row-sort", row_sort_start)

    if not row_sort_succeeded:
        return False

    column_sort_start = get_tick_count()
    column_sort_succeeded = sort_full_field_columns(size)
    report_phase_ticks("Cactus column-sort", column_sort_start)

    if not column_sort_succeeded:
        return False

    harvest_start = get_tick_count()
    harvest_succeeded = harvest_full_field()
    report_phase_ticks("Cactus harvest", harvest_start)

    return harvest_succeeded
