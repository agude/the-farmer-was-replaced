from farm_config import (
    ENABLE_WEIRD_SUBSTANCE_PRODUCTION,
    FERTILIZER_RESERVE,
    WEIRD_SUBSTANCE_TARGET,
)


def should_produce_weird_substance() -> bool:
    if not ENABLE_WEIRD_SUBSTANCE_PRODUCTION:
        return False

    if num_items(Items.Weird_Substance) >= WEIRD_SUBSTANCE_TARGET:
        return False

    return num_items(Items.Fertilizer) > FERTILIZER_RESERVE


def fertilize_before_harvest() -> bool:
    if not should_produce_weird_substance():
        return False

    return use_item(Items.Fertilizer)
