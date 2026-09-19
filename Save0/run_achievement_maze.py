# Continuously run parallel reusable mazes for Maze Master.

from achievement_maze import run_maze_workers
from achievement_metrics import get_elapsed_time
from achievement_metrics import get_item_delta
from achievement_metrics import get_items_per_minute
from achievement_metrics import start_item_measurement
from achievement_metrics import start_time_measurement


starting_gold = start_item_measurement(Items.Gold)
starting_time = start_time_measurement()


while True:
    if not run_maze_workers():
        produced_gold = get_item_delta(Items.Gold, starting_gold)
        elapsed_seconds = get_elapsed_time(starting_time)
        gold_per_minute = get_items_per_minute(produced_gold, elapsed_seconds)
        quick_print(
            "Maze achievement workers stopped after "
            + str(produced_gold)
            + " gold and "
            + str(elapsed_seconds)
            + " seconds at "
            + str(gold_per_minute)
            + " gold/min"
        )
        break
