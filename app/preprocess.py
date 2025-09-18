import cv2
import numpy as np


def align_pair(reference: np.ndarray, moving: np.ndarray) -> np.ndarray:
    orb = cv2.ORB_create(1000)
    keypoints_ref, descriptors_ref = orb.detectAndCompute(reference, None)
    keypoints_mov, descriptors_mov = orb.detectAndCompute(moving, None)
    if descriptors_ref is None or descriptors_mov is None:
        return moving

    matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = matcher.match(descriptors_ref, descriptors_mov)
    matches = sorted(matches, key=lambda m: m.distance)[:200]
    if len(matches) < 10:
        return moving

    src = np.float32([keypoints_ref[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
    dst = np.float32([keypoints_mov[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
    matrix, _ = cv2.estimateAffinePartial2D(dst, src)
    if matrix is None:
        return moving

    height, width = reference.shape[:2]
    return cv2.warpAffine(moving, matrix, (width, height))


def flash_only(flash_on: np.ndarray, flash_off: np.ndarray):
    if flash_on.shape != flash_off.shape:
        flash_off = cv2.resize(flash_off, (flash_on.shape[1], flash_on.shape[0]))
    aligned_off = align_pair(flash_on, flash_off)
    difference = cv2.absdiff(flash_on, aligned_off)
    albedo = aligned_off.copy()
    spec = cv2.cvtColor(difference, cv2.COLOR_BGR2GRAY)
    spec = cv2.normalize(spec, None, 0, 255, cv2.NORM_MINMAX)
    spec = cv2.GaussianBlur(spec, (0, 0), 1.0)
    spec = cv2.addWeighted(
        spec,
        2.0,
        cv2.Laplacian(spec, cv2.CV_16S, ksize=3).astype(np.uint8),
        -0.5,
        0,
    )
    return albedo, spec


def flatten_placeholder(image: np.ndarray, spec_map: np.ndarray | None = None) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if spec_map is not None:
        mix = cv2.addWeighted(gray, 0.7, spec_map, 0.3, 0)
    else:
        mix = gray
    mix = cv2.equalizeHist(mix)
    return mix
