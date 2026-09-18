"""Rehearse the reset progression in an isolated simulation."""

SIMULATION_FILE = "reset_progression"
SIMULATION_UNLOCKS = {}
SIMULATION_ITEMS = {}
SIMULATION_GLOBALS = {}
SIMULATION_SEED = 17
SIMULATION_SPEEDUP = 256


simulation_runtime = simulate(
    SIMULATION_FILE,
    SIMULATION_UNLOCKS,
    SIMULATION_ITEMS,
    SIMULATION_GLOBALS,
    SIMULATION_SEED,
    SIMULATION_SPEEDUP,
)
quick_print(simulation_runtime)
