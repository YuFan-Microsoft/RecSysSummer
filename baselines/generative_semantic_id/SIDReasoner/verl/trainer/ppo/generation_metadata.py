from typing import Any

import numpy as np


def copy_reward_models_for_generation(
    non_tensor_batch: dict[str, Any],
    expected_size: int,
) -> np.ndarray:
    """Copy batch-aligned reward metadata for target-aware rollout selection."""
    reward_models = non_tensor_batch.get("reward_model")
    if reward_models is None:
        raise ValueError("Best-of-N SID sampling requires reward_model metadata")
    if len(reward_models) != expected_size:
        raise ValueError(
            "Best-of-N SID sampling requires reward_model metadata aligned with the generation batch"
        )
    return reward_models.copy()