# Repository Instructions

## Runtime

Treat files under `Save*/` as The Farmer Was Replaced programs, not ordinary
Python. Follow `.agents/skills/farmer-was-replaced-python/SKILL.md` when reading
or changing them. Treat each save directory independently and do not edit
generated save-state files unless explicitly requested.

## Validation

Run `just check` before committing. It is the complete local equivalent of CI.

Ruff is limited to defect-oriented rules. Do not run Ruff formatting or
autofixes on `Save*/`, and do not enable `SIM`, `RUF`, `UP`, or `C4`: those
rules can recommend syntax that the game interpreter does not support. The
`format` recipe changes only the CPython tooling under `scripts/`. Update the
explicit `builtins` list in `ruff.toml` when game code starts using another
injected API name.

This repository is a script collection. It intentionally has no package,
type-check, test, coverage, build, release, or deployment jobs. Behavioral
validation happens in the game debugger or simulator. Python 3.12 is pinned
only to run repository tooling; it is not the game runtime.
