"""Run one finite Dinosaur Master harvest burst."""

from achievement_dinosaur import run_achievement_dinosaur_once


if not run_achievement_dinosaur_once():
    quick_print("Dinosaur achievement run failed")
