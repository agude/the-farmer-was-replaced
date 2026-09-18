"""Full-field cactus cycle for the Cactus Master achievement."""

from cactus import grow_cactus_row_job
from cactus import sort_cactus_column_job
from cactus import sort_cactus_row_job
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
    return grow_cactus_row_job(job)


def sort_full_field_row_job(job) -> bool:
    return sort_cactus_row_job(job)


def sort_full_field_column_job(job) -> bool:
    return sort_cactus_column_job(job)


def grow_full_field(size: int) -> bool:
    return run_phase(build_row_jobs(size), grow_full_field_row_job)


def sort_full_field(size: int) -> bool:
    if not run_phase(build_row_jobs(size), sort_full_field_row_job):
        return False

    return run_phase(build_column_jobs(size), sort_full_field_column_job)


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

    if not grow_full_field(size):
        return False

    if not sort_full_field(size):
        return False

    return harvest_full_field()
