"""Run one reusable maze for the Recycling achievement."""

from achievement_maze import run_reusable_maze_worker


result = run_reusable_maze_worker(0, 300)
if result["completed"] == 300:
    quick_print("Recycling complete after 300 relocations")
else:
    quick_print(
        "Recycling stopped after " + str(result["completed"]) + " relocations: " + result["reason"]
    )
