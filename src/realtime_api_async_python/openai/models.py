from enum import Enum


class ModelName(str, Enum):
    state_of_the_art_model = "state_of_the_art_model"
    reasoning_model = "reasoning_model"
    base_model = "base_model"
    fast_model = "fast_model"


# Mapping from enum options to model IDs
model_name_to_id = {
    ModelName.state_of_the_art_model: "o1-preview",
    ModelName.reasoning_model: "o1-mini",
    ModelName.base_model: "gpt-4o-2024-08-06",
    ModelName.fast_model: "gpt-4o-mini",
}

def get_model_canonical_name(key: str):
    result = model_name_to_id.get("ModelName." + key, model_name_to_id[ModelName.base_model])
    return result