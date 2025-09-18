import numpy as np


def _normalize01(values: np.ndarray) -> np.ndarray:
    if values.size == 0:
        return values
    minimum = float(np.min(values))
    maximum = float(np.max(values))
    if maximum - minimum < 1e-9:
        return np.ones_like(values)
    return (values - minimum) / (maximum - minimum)


def fuse_scores(
    ann_distances: list[float], ocr_costs: list[float], w_ann: float = 0.5, w_ocr: float = 0.5
) -> np.ndarray:
    ann_array = np.asarray(ann_distances, dtype=np.float32)
    ocr_array = np.asarray(ocr_costs, dtype=np.float32)
    ann_similarity = 1.0 - _normalize01(ann_array)
    ocr_similarity = 1.0 - _normalize01(ocr_array)
    return w_ann * ann_similarity + w_ocr * ocr_similarity
