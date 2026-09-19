# Run the disabled maze-placement diagnostic when explicitly enabled.

from achievement_config import ENABLE_MAZE_PLACEMENT_PROBE
from achievement_maze import run_maze_placement_probe


if ENABLE_MAZE_PLACEMENT_PROBE:
    if not run_maze_placement_probe():
        quick_print("Maze placement probe failed")
