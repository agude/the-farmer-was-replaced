"""Continuously run the full-field Cactus Master cycle."""

from achievement_cactus import farm_achievement_cactus_cycle
from achievement_metrics import get_item_delta
from achievement_metrics import start_item_measurement


starting_cactus = start_item_measurement(Items.Cactus)


while True:
    if not farm_achievement_cactus_cycle():
        produced_cactus = get_item_delta(Items.Cactus, starting_cactus)
        quick_print("Cactus achievement cycle failed after " + str(produced_cactus) + " cactus")
        break
