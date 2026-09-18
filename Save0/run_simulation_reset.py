"""Run the ten required seeded Fastest Reset simulations."""

SIMULATION_FILE = "reset_progression"
SIMULATION_UNLOCKS = {}
SIMULATION_ITEMS = {}
SIMULATION_GLOBALS = {}
SIMULATION_SEEDS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
SIMULATION_SPEEDUP = 256


for simulation_seed in SIMULATION_SEEDS:
    simulation_runtime = simulate(
        SIMULATION_FILE,
        SIMULATION_UNLOCKS,
        SIMULATION_ITEMS,
        SIMULATION_GLOBALS,
        simulation_seed,
        SIMULATION_SPEEDUP,
    )
    quick_print(str(simulation_seed) + ": " + str(simulation_runtime))
