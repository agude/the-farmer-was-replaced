def water_if_dry(water_threshold: float = 0.2) -> None:
	if get_water() < water_threshold:
		use_item(Items.Water)