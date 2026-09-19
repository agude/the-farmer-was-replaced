# Synchronized full-field pumpkin cycle for Pumpkin Master.

from achievement_config import DEBUG_OUTPUT
from navigation import move_to
from parallel_farming import dispatch_indexed_jobs
from planting import ensure_soil


def water_after_planting() -> None:
    if get_water() < 1 and num_items(Items.Water) > 0:
        use_item(Items.Water)


def plant_pumpkin_for_achievement() -> bool:
    ensure_soil()
    if not plant(Entities.Pumpkin):
        return False

    water_after_planting()
    return True


def maintain_pumpkin_tile() -> bool:
    entity = get_entity_type()

    if entity == Entities.Pumpkin:
        return can_harvest()

    if entity == Entities.Dead_Pumpkin or entity == None:
        if not plant_pumpkin_for_achievement():
            return None

        return False

    # Never harvest another crop while repairing the synchronized field.
    return None


def grow_pumpkin_row_job(row_y: int) -> bool:
    size = get_world_size()
    pending = []

    for x in range(size):
        pending.append(x)

    while len(pending) > 0:
        still_pending = []

        for index in range(len(pending)):
            x = pending[index]
            move_to(x, row_y)
            readiness = maintain_pumpkin_tile()

            if readiness == None:
                return False

            if not readiness:
                still_pending.append(x)

        pending = still_pending

    return True


def harvest_ready_field(size: int) -> bool:
    move_to(size - 1, size - 1)

    if not can_harvest():
        return False

    # Do not fertilize the final pumpkin harvest.
    harvest()
    return True


def report_phase_ticks(label, starting_tick) -> None:
    if DEBUG_OUTPUT:
        quick_print(label + " ticks " + str(get_tick_count() - starting_tick))


def farm_achievement_pumpkin_cycle() -> bool:
    size = get_world_size()
    rows = []

    for row_y in range(size):
        rows.append(row_y)

    planting_start = get_tick_count()
    results = dispatch_indexed_jobs(rows, grow_pumpkin_row_job)
    report_phase_ticks("Pumpkin planting/repair", planting_start)

    for result in results:
        if not result:
            return False

    harvest_start = get_tick_count()
    harvest_succeeded = harvest_ready_field(size)
    report_phase_ticks("Pumpkin harvest", harvest_start)
    return harvest_succeeded
