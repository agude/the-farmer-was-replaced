from farm_config import GOLD_TARGET, WEIRD_SUBSTANCE_RESERVE


def get_maze_substance_cost() -> int:
    # Return the full-field cost, or zero when mazes are unavailable.
    maze_level = num_unlocked(Unlocks.Mazes)

    if maze_level == 0:
        return 0

    world_size = get_world_size()
    return world_size * 2 ** (maze_level - 1)


def can_fund_maze(substance_cost: int) -> bool:
    # Keep the configured Weird Substance reserve untouched.
    return num_items(Items.Weird_Substance) >= (substance_cost + WEIRD_SUBSTANCE_RESERVE)


def create_maze(substance_cost: int) -> bool:
    # Turn the current tile into a fresh full-field maze.
    if get_ground_type() != Grounds.Soil:
        till()

    if not plant(Entities.Bush):
        return False

    return use_item(Items.Weird_Substance, substance_cost)


def solve_maze() -> bool:
    # Follow the right wall through a fresh maze without crossing hedges.
    directions = [North, East, South, West]
    facing = 0

    while get_entity_type() != Entities.Treasure:
        right = (facing + 1) % 4

        if move(directions[right]):
            facing = right
            continue

        if move(directions[facing]):
            continue

        left = (facing - 1) % 4

        if move(directions[left]):
            facing = left
            continue

        reverse = (facing + 2) % 4

        if not move(directions[reverse]):
            return False

        facing = reverse

    if get_entity_type() != Entities.Treasure:
        return False

    harvest()
    return True


def farm_mazes() -> None:
    # Create fresh mazes until the gold target or resource reserve is reached.
    if num_items(Items.Gold) >= GOLD_TARGET:
        return

    substance_cost = get_maze_substance_cost()

    if substance_cost == 0:
        return

    if not can_fund_maze(substance_cost):
        return

    clear()

    while num_items(Items.Gold) < GOLD_TARGET:
        if not can_fund_maze(substance_cost):
            return

        if not create_maze(substance_cost):
            return

        if not solve_maze():
            return
