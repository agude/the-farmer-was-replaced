# Continuously run the Carrot Master polyculture cycle.

from achievement_metrics import get_item_delta
from achievement_metrics import start_item_measurement
from achievement_polyculture import CARROT_MODE
from achievement_polyculture import can_fund_carrot_startup
from achievement_polyculture import run_polculture_workers


starting_carrots = start_item_measurement(Items.Carrot)
world_size = get_world_size()
startup_ready = can_fund_carrot_startup(world_size)


while True:
    if not startup_ready:
        quick_print("Carrot achievement startup preflight failed")
        break

    if not run_polculture_workers(world_size, CARROT_MODE):
        produced_carrots = get_item_delta(Items.Carrot, starting_carrots)
        quick_print("Carrot achievement cycle failed after " + str(produced_carrots) + " carrots")
        break
