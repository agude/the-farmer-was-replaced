# The Farmer Was Replaced Scripts

This repository tracks automation scripts from The Farmer Was Replaced. The
game runs a restricted Python-like language rather than CPython.

`Save0/` and `Save0 - Copy/` are independent save trees. Changes are not copied
between them automatically. Generated `save.json` and `__builtins__.py` files
remain local and untracked.

## Static checks

Install the managed Python interpreter and run all checks:

```sh
just sync
just check
```

Install the optional pre-commit hook with `just hooks-install`.

The checks run a constrained Ruff ruleset, check formatting for all Python
files, reject syntax unsupported by the game interpreter, verify that game
imports resolve within their save, and validate repository Agent Skills. Lint
autofixes remain limited to the CPython tools under `scripts/`. Static checks
do not replace testing in the game debugger or simulator.

GitHub Actions runs the same `just lint` recipe. This repository has no
continuous-deployment step because the active local game save cannot be chosen
or updated safely by hosted CI.
