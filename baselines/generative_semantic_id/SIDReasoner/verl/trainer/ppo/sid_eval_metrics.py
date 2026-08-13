import re


def count_unique_first_sid_tokens(predictions: list[str], cutoff: int = 10) -> int:
    """Count unique first-level SID tokens in the leading predictions."""
    if cutoff < 1:
        raise ValueError("SID diversity cutoff must be positive")
    leading_predictions = predictions[:cutoff]
    if not leading_predictions:
        raise ValueError("At least one SID prediction is required")

    first_tokens = []
    for prediction in leading_predictions:
        sid_tokens = re.findall(r"<[^>]+>", str(prediction))
        if not sid_tokens:
            raise ValueError(f"Prediction does not contain a SID token: {prediction!r}")
        first_tokens.append(sid_tokens[0])
    return len(set(first_tokens))