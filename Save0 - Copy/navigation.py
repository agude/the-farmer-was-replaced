def distance_to(target_x: int, target_y: int) -> int:
	size = get_world_size()

	dx = target_x - get_pos_x()
	if dx < 0:
		dx = -dx

	dy = target_y - get_pos_y()
	if dy < 0:
		dy = -dy

	if size - dx < dx:
		dx = size - dx

	if size - dy < dy:
		dy = size - dy

	return dx + dy


def move_to(target_x: int, target_y: int) -> None:
	size = get_world_size()

	current_x = get_pos_x()

	east_steps = (target_x - current_x) % size
	west_steps = (current_x - target_x) % size

	if east_steps <= west_steps:
		for _ in range(east_steps):
			move(East)
	else:
		for _ in range(west_steps):
			move(West)

	current_y = get_pos_y()

	north_steps = (target_y - current_y) % size
	south_steps = (current_y - target_y) % size

	if north_steps <= south_steps:
		for _ in range(north_steps):
			move(North)
	else:
		for _ in range(south_steps):
			move(South)