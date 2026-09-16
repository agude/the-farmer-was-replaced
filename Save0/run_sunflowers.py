from farm_config import (
    POWER_TARGET,
    SUNFLOWER_WATER_THRESHOLD,
)
from navigation import move_to
from sunflowers import (
    prepare_sunflower_tile,
    plant_sunflower,
    SUNFLOWER_MAX_PETALS,
    SUNFLOWER_MIN_PETALS,
    SUNFLOWER_MIN_REMAINING,
)
from watering import water_if_dry


def prepare_sunflower_tile_until_planted():
    # Prepare one tile without waiting for its sunflower to mature.
    while True:
        if prepare_sunflower_tile():
            return


def measure_sunflower_when_ready():
    # Poll one planted sunflower until it is mature, then measure it.
    while True:
        if can_harvest():
            return measure()

        water_if_dry(SUNFLOWER_WATER_THRESHOLD)


def get_full_farm_positions():
    # Return every tile in a continuous snake order.
    size = get_world_size()
    positions = []

    for x in range(size):
        if x % 2 == 0:
            for y in range(size):
                positions.append((x, y))
        else:
            for y in range(size - 1, -1, -1):
                positions.append((x, y))

    return positions


def grow_sunflower_row_until_ready():
    # Plant the row first so all tiles grow while the drone is moving.
    size = get_world_size()
    row_y = get_pos_y()

    positions_by_petals = []

    for _ in range(SUNFLOWER_MAX_PETALS - SUNFLOWER_MIN_PETALS + 1):
        positions_by_petals.append([])

    for x in range(size):
        move_to(x, row_y)

        prepare_sunflower_tile_until_planted()

    # Only after the row is planted do we wait and measure each flower.
    for x in range(size):
        move_to(x, row_y)
        petals = measure_sunflower_when_ready()
        positions_by_petals[petals - SUNFLOWER_MIN_PETALS].append((x, row_y))

    return positions_by_petals


def combine_row_measurements(row_measurements):
    # Merge worker-local petal buckets without rescanning the farm.
    positions_by_petals = []

    for _ in range(SUNFLOWER_MAX_PETALS - SUNFLOWER_MIN_PETALS + 1):
        positions_by_petals.append([])

    for row in row_measurements:
        for petals in range(len(positions_by_petals)):
            for position in row[petals]:
                positions_by_petals[petals].append(position)

    return positions_by_petals


def grow_full_farm_with_drones() -> None:
    # Use one worker per row; on a 32x32 farm this uses all 32 drones.
    workers = []
    row_measurements = []
    size = get_world_size()
    move_to(0, 0)

    for row in range(size - 1):
        worker = spawn_drone(grow_sunflower_row_until_ready)

        if worker == None:
            # Fall back to the current drone if the worker limit is reached.
            row_measurements.append(grow_sunflower_row_until_ready())
        else:
            workers.append(worker)

        move_to(0, row + 1)

    row_measurements.append(grow_sunflower_row_until_ready())

    for worker in workers:
        row_measurements.append(wait_for(worker))

    return combine_row_measurements(row_measurements)


def harvest_positions(positions) -> None:
    # Harvest one worker's share of a single petal tier.
    for i in range(len(positions)):
        x, y = positions[i]
        move_to(x, y)
        harvest()


def take_positions(positions, count):
    # Copy a prefix without relying on Python slice syntax.
    selected = []

    for i in range(len(positions)):
        if i >= count:
            break

        selected.append(positions[i])

    return selected


def run_position_task_in_parallel(positions, task) -> None:
    # Dispatch a position task across all available drones.
    if len(positions) == 0:
        return

    worker_count = max_drones() - num_drones()

    if worker_count <= 0:
        task(positions)
        return

    if worker_count > len(positions):
        worker_count = len(positions)

    chunk_size = (len(positions) + worker_count - 1) // worker_count
    workers = []
    size = get_world_size()
    move_to(size // 2, size // 2)

    for start in range(0, len(positions), chunk_size):
        chunk = []

        for i in range(start, start + chunk_size):
            if i >= len(positions):
                break

            chunk.append(positions[i])

        worker = spawn_drone(task, chunk)

        if worker == None:
            # Keep this tier safe even if the cap changes while dispatching.
            task(chunk)
        else:
            workers.append(worker)

    for worker in workers:
        wait_for(worker)


def harvest_tier_in_parallel(positions) -> None:
    # Equal-petal harvests may overlap; wait before starting the next tier.
    run_position_task_in_parallel(positions, harvest_positions)


def replant_positions(positions) -> None:
    # Plant one worker's share after the full harvest phase is complete.
    for i in range(len(positions)):
        x, y = positions[i]
        move_to(x, y)
        plant_sunflower()


def replant_positions_in_parallel(positions) -> None:
    # Replanting is independent, so it can use the same worker dispatcher.
    run_position_task_in_parallel(positions, replant_positions)


def harvest_tiers_in_parallel(positions_by_petals, harvest_count):
    # Finish each tier completely before touching a lower-petal tier.
    harvested_positions = []
    harvested_count = 0

    for petals in range(SUNFLOWER_MAX_PETALS, SUNFLOWER_MIN_PETALS - 1, -1):
        positions = positions_by_petals[petals - SUNFLOWER_MIN_PETALS]
        remaining = harvest_count - harvested_count

        if remaining <= 0:
            return harvested_positions

        if len(positions) > remaining:
            positions = take_positions(positions, remaining)

        harvest_tier_in_parallel(positions)

        for position in positions:
            harvested_positions.append(position)

        harvested_count += len(positions)

    return harvested_positions


def harvest_power_cycle() -> None:
    # Grow and measure in parallel, then harvest in global petal order.
    positions = get_full_farm_positions()
    positions_by_petals = grow_full_farm_with_drones()

    harvest_count = len(positions) - SUNFLOWER_MIN_REMAINING
    harvested_positions = harvest_tiers_in_parallel(
        positions_by_petals,
        harvest_count,
    )
    replant_positions_in_parallel(harvested_positions)


def stockpile_power() -> None:
    # Run optimized, drone-assisted cycles until the power target is met.
    while num_items(Items.Power) < POWER_TARGET:
        harvest_power_cycle()


stockpile_power()
