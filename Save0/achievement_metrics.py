"""Import-safe measurements for achievement runner throughput."""


def start_item_measurement(item) -> int:
    # Capture the inventory balance before the runner starts producing.
    return num_items(item)


def get_item_delta(item, starting_amount: int) -> int:
    # Subtract the starting balance so existing inventory is not counted.
    return num_items(item) - starting_amount


def start_time_measurement():
    # Capture the game clock at the same boundary as the item measurement.
    return get_time()


def get_elapsed_time(starting_time):
    # Treat clock wrap and a stalled clock as zero usable elapsed time.
    elapsed_time = get_time() - starting_time

    if elapsed_time <= 0:
        return 0

    return elapsed_time


def get_items_per_minute(item_delta: int, elapsed_time) -> float:
    # Avoid a division by zero when a measurement window has no duration.
    if elapsed_time <= 0:
        return 0

    return item_delta * 60 / elapsed_time
