---
status: in_progress
created: "2026-09-18T19:20:09.521219+00:00"
updated: "2026-09-18T20:34:21.975431+00:00"
started: "2026-09-18T19:20:16.268118+00:00"
approach: Work through plan.md in order, completing each task with focused validation and an atomic commit.
criteria:
  - All required plan tasks are implemented or have recorded evidence
  - just check passes after the final implementation
  - Each implementation task has an atomic commit
files:
  - plan.md
  - Save0
  - scripts
  - justfile
---

# Implement achievement runner plan

Task 29 static implementation complete: added reset_farmers.py with bounded single-tile Hay/Wood/Carrot/Pumpkin/Cactus/Power producers, recursive planting-input safeguards, Weird Substance handling, and explicit Gold/Bone maze/dinosaur stages. Wired reset_progression.py to the producer hook and added precondition/dispatch tests; full just check passed. Full blank-reset progression and ten-seed validation remain live/simulation work for Tasks 30-31.

## Notes

### 2026-09-18T19:22:12.581052+00:00

Task 1 complete: added Save0/achievement_config.py with the six exact timed targets, disabled debug/benchmark defaults, and 4x4 x 8 x 4 maze layout constants; added scripts/test_achievement_config.py and included achievement-config-test in just check. Focused test and full just check passed with UV_CACHE_DIR and UV_TOOL_DIR redirected to /tmp.

### 2026-09-18T19:23:53.749005+00:00

Task 2 complete: added import-safe achievement_metrics helpers for inventory baselines/deltas, elapsed game time, and per-minute rates. Negative deltas preserve consumed inputs; clock wrap and non-positive elapsed time return safe zero values. Added focused harness and just check recipe; full just check passed.

### 2026-09-18T19:25:17.684261+00:00

Task 3 runner infrastructure complete: extended scripts/test_runners.py with an import-side-effect guard for registered implementation modules and preserved the continuous-runner failure-exit checks. Future achievement entry points must be registered as introduced; circular-import and stack-overflow entry points will remain parse-only.

### 2026-09-18T19:27:35.519694+00:00

Task 4 complete: added run_achievement_healer.py with item preflight, isolated empty-cross search, grass planting, fertilizer use, Weird Substance cure, and direct failure diagnostics. Added static Healer acceptance tests, registered it as a finite runner, and full just check passed. In-game unlock still requires game-side validation.

### 2026-09-18T19:29:28.985020+00:00

Task 5 complete: added the isolated two-module achievement_import_cycle_a/b graph and run_achievement_import.py trigger. Helpers perform no game work; static tests verify exact cycle edges, entry-point trigger, and no production imports. Registered the entry point as parse-only. Full just check passed.

### 2026-09-18T19:30:33.510598+00:00

Task 6 complete: added run_achievement_stack_overflow.py with direct unbounded recursion and an explicit intentional-runtime-error comment. Added parse-only static tests, forbade field/inventory actions, and full just check passed; the file is never imported or executed by CPython.

### 2026-09-18T19:35:04.834020+00:00

Task 7 complete: added import-safe achievement_cactus.py for explicit 0..size-1 full-field growth, row-sort barrier, column-sort barrier, and exactly one unfertilized chain harvest. The deterministic harness proves soil/maturity preconditions, sorted/reverse/diagonal inputs, ten seeded random 32x32 inputs, and spawn fallback lane coverage. Full just check passed; in-game throughput remains for Tasks 8-9.

### 2026-09-18T19:39:37.983084+00:00

Task 8 complete in static/debug scope: replaced achievement cactus sort hot loops with one current/neighbor measurement pair per comparison, shrinking cocktail bounds, direct lane movement, and documented lane return to its start. Added separate planting, row-sort, column-sort, and harvest tick diagnostics gated by DEBUG_OUTPUT; the deterministic 32x32 harness verifies direct movement, measurement pairing, lane returns, and correctness. Full just check passed; live tick totals remain to be recorded during in-game validation.

### 2026-09-18T19:41:26.954378+00:00

Task 9 static implementation complete: added run_achievement_cactus.py as a selectable continuous wrapper that captures its own cactus baseline and reports the produced delta only on cycle failure. Registered it in the runner harness, forbade runner-side fertilizing, and full just check passed. Cactus Master last-60-second rate, cycle ticks, and Big Farmer progress require in-game validation and are not claimed.

### 2026-09-18T19:44:07.305552+00:00

Task 10 complete: added import-safe achievement_pumpkin.py with one row job per world row, unresolved-position retention, direct empty/dead Pumpkin replacement, one post-plant water action when available, explicit worker failure propagation, row barrier, and one unfertilized bulk harvest. Focused harness covers reduced drone capacity, dead repair, watering, and failed-row harvest blocking. Full just check passed; Task 11 still requires consecutive in-game throughput validation.

### 2026-09-18T19:46:14.842780+00:00

Task 11 static implementation complete: added run_achievement_pumpkin.py with its own Pumpkin baseline and failure delta, registered it as a continuous runner, and added debug timing labels separating planting/repair from final harvest. The harness proves two consecutive cycles without clear() and validates the runner boundary; full just check passed. Pumpkin Master rate and Big Pumpkin Farmer closure still require in-game validation.

### 2026-09-18T19:46:37.243455+00:00

Task 12 deferred by its explicit condition: no in-game Pumpkin Master result is available yet, so the full-field design has not been shown to miss and no 6x6 fallback was added. Revisit only after live Stats/rate validation.

### 2026-09-18T19:49:00.456180+00:00

Task 13 complete: added achievement_dinosaur.py and finite run_achievement_dinosaur.py. Preflight checks even world size, Dinosaur unlock, live Apple cactus cost, and full-run cactus inventory before clear(); the existing Hamiltonian cycle fills the tail until its expected blocking move, then one Straw Hat change credits and verifies the bone delta. Harness covers preflight isolation, missing Apple hat restoration, exact success sequence, and finite runner boundary. Full just check passed; live one-million-bone result remains in-game validation.

### 2026-09-18T19:50:54.304712+00:00

Task 14 complete: added pure achievement_polyculture.py coordinate predicates for shared Hay and Carrot modes using disjoint 4x4 primary regions, three owned companion slots, and explicit guard tiles. Harness validates one role per coordinate and ownership/coverage for 8x8, 16x16, and 32x32 worlds. Full just check passed.

### 2026-09-18T19:53:58.354675+00:00

Task 15 complete: implemented perform_polculture_transaction in achievement_polyculture.py. It establishes a mode-specific primary, reads and validates the documented get_companion() tuple, rejects or bounded-rerolls invalid own-primary requests, plants only owned companion targets with entity-specific ground conversion, waits for maturity, harvests once, and restores the primary. Harness covers all four companion types, ground rules, failed planting, out-of-region requests, and reroll ownership. Full just check passed.

### 2026-09-18T19:56:51.175847+00:00

Task 16 complete: added persistent polyculture worker scheduling with an 8x8 sparse template, capacity bounded by max_drones(), stable tuple-owned regions, persistent child workers, parent-owned fallback jobs when spawn fails, and no shared mutable correctness globals or farm-wide dispatch joins. The CPython scheduler harness runs 1,000 transactions and verifies capacity/fallback ownership. Full just check passed.

### 2026-09-18T20:00:56.100330+00:00

Follow-up correction: centered each 8x8 primary at its region's (3,3) offset, classified the complete 24-tile Manhattan-radius-three companion set, and fixed companion enumeration to use region anchors. Updated layout and transaction harnesses; full just check passed.

### 2026-09-18T20:03:00.394057+00:00

Task 17 static implementation complete: added run_achievement_hay.py with Hay baseline/delta reporting over persistent polyculture workers, registered the runner, and added hot-loop/ mode/failure boundary coverage. Full just check passed. Candidate-template/worker benchmark and Hay Master throughput still require identical-seed simulation and live in-game Stats validation.

### 2026-09-18T20:05:52.712505+00:00

Task 18 static implementation complete: added live worst-case Hay/Wood startup budgeting for the Carrot polyculture workers, a preflight-gated run_achievement_carrots.py entry point with Carrot delta diagnostics, runner registration, and exact/underfunded budget tests. Full just check passed. Five-seed template/worker benchmarking and Carrot Master throughput/Big Carrot Farmer closure remain live validation.

### 2026-09-18T20:07:51.017378+00:00

Task 19 complete: added import-safe achievement_maze.py with 32 deterministic disjoint 4x4 regions, anchor/start/bounds/owner helpers, and prefix worker selection capped at 32. Added coverage and non-overlap tests for every worker count from 1 through 32; full just check passed.

### 2026-09-18T20:10:46.213579+00:00

Task 20 complete: extended achievement_maze.py with bounded iterative DFS mapping, game-compatible list/dictionary graph storage, BFS shortest-path search, measured treasure lookup, and move-result-checked path following. Mapping tests cover loop-free branches, dead ends, later-added edges, unreachable targets, and blocked cached moves; full just check passed.

### 2026-09-18T20:13:47.892265+00:00

Task 21 complete: added reusable maze worker logic with exact creation-plus-relocation Weird Substance budgeting, one-time mapping, measured treasure paths, bounded remapping after blocked moves, 300-success limit, and result reasons distinguishing completion, resource exhaustion, relocation exhaustion, and blocking. Harness covers exact 300 reuse, post-success counting, exhaustion, recovery, and no-action preflight; full just check passed.

### 2026-09-18T20:15:12.536521+00:00

Task 22 complete: added finite run_achievement_recycling.py that invokes one maze worker at region 0 with the 300-relocation limit and prints exactly one completion or failure diagnostic. Registered the imported finite runner and added isolation tests excluding unrelated gold farming; full just check passed.

### 2026-09-18T20:17:16.973889+00:00

Task 23 complete: added persistent achievement maze workers and manager with stable region-owned jobs, bounded max-drone startup, child spawn fallback to parent jobs, independent parent failure removal, completion-driven maze replacement, and visible failure diagnostics. Scheduler harness covers spawn fallback, healthy-job isolation, replacement, and no shared/barrier state; full just check passed.

### 2026-09-18T20:19:27.931836+00:00

Task 24 static implementation complete: added run_achievement_maze.py with Gold delta and elapsed-time failure diagnostics over the parallel manager, registered its continuous runner, and added hot-loop isolation checks. Full just check passed. Five-seed benchmark reporting, startup-versus-steady mapping measurements, Maze Master throughput, and Big Gold Farmer closure still require live validation.

### 2026-09-18T20:23:01.377635+00:00

Task 25 static implementation complete: added import-safe leaderboard_runs.py with the achievement cactus cycle and exact 33,554,432 termination target, plus run_leaderboard_cactus.py launcher using the leaderboard_runs window and configurable speedup. Harness covers target termination, cycle failure, import isolation, board selection, filename, and speedup; full just check passed. Actual leaderboard completion and Competitive Farming unlock remain in-game validation.

### 2026-09-18T20:23:19.203242+00:00

Task 26 deferred: cumulative achievement closure, Top Hat validation, remaining unlock purchases, and What? unlock require live game execution and live get_cost/unlock-tree results; repository checks cannot establish them.

### 2026-09-18T20:25:15.947601+00:00

Task 27 complete: added run_simulate_fastest_reset.py as a separate rehearsal launcher with empty unlocks/items/globals, fixed seed 17, configurable speedup 256, and one printed simulated runtime. Static tests verify the six simulate arguments, empty start state, no nested/live operations, and one output; full just check passed.

### 2026-09-18T20:28:23.631692+00:00

Task 28 complete: added import-safe reset_progression.py with explicit unlock reasons/prerequisites, dependency-cycle detection, live cost validation, bounded unlock_one() retries, producer progress proofs, purchase failure diagnostics, and Leaderboard success check. Harness covers direct/multi-item cycles, changing costs, overshoot, failed purchases, missing prerequisites, and no-progress exits; full just check passed.

### 2026-09-18T20:32:04.194633+00:00

Task 29 static implementation complete: added reset_farmers.py with bounded single-tile Hay/Wood/Carrot/Pumpkin/Cactus/Power producers, recursive planting-input safeguards, Weird Substance handling, and explicit Gold/Bone maze/dinosaur stages. Wired reset_progression.py to the producer hook and added precondition/dispatch tests; full just check passed. Full blank-reset progression and ten-seed validation remain live/simulation work for Tasks 30-31.

### 2026-09-18T20:34:21.975417+00:00

Task 30 static implementation complete: added the Leaderboard early-success return and blank-world guard to reset_progression.py, plus run_leaderboard_reset.py targeting the guarded reset_progression window. Harness covers immediate Leaderboard termination, no nested leaderboard call, blank-state guard, board selection, window name, and speedup; full just check passed. Ten-seed simulation, real Fastest Reset acceptance, and Full Automation unlock remain live validation.
