"""Finite operations submitted to leaderboard simulations."""

from achievement_cactus import farm_achievement_cactus_cycle


CACTUS_LEADERBOARD_TARGET = 33554432


def run_leaderboard_cactus() -> bool:
    while num_items(Items.Cactus) < CACTUS_LEADERBOARD_TARGET:
        if not farm_achievement_cactus_cycle():
            return False

    return True


if __name__ == "__main__":
    run_leaderboard_cactus()
