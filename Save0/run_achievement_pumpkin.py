# Continuously run the full-field Pumpkin Master cycle.

from achievement_metrics import get_item_delta
from achievement_metrics import start_item_measurement
from achievement_pumpkin import farm_achievement_pumpkin_cycle


starting_pumpkins = start_item_measurement(Items.Pumpkin)


while True:
    if not farm_achievement_pumpkin_cycle():
        produced_pumpkins = get_item_delta(Items.Pumpkin, starting_pumpkins)
        quick_print(
            "Pumpkin achievement cycle failed after " + str(produced_pumpkins) + " pumpkins"
        )
        break
