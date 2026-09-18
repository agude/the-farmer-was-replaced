"""Continuously run the Hay Master polyculture cycle."""

from achievement_metrics import get_item_delta
from achievement_metrics import start_item_measurement
from achievement_polyculture import HAY_MODE
from achievement_polyculture import run_polculture_workers


starting_hay = start_item_measurement(Items.Hay)
world_size = get_world_size()


while True:
    if not run_polculture_workers(world_size, HAY_MODE):
        produced_hay = get_item_delta(Items.Hay, starting_hay)
        quick_print("Hay achievement cycle failed after " + str(produced_hay) + " hay")
        break
