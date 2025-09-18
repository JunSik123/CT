from typing import Optional, Tuple

import cv2
import numpy as np
from skimage.feature import local_binary_pattern


def load_image(path: str, max_side: int = 512) -> Optional[np.ndarray]:
    data = np.fromfile(path, dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if image is None:
        return None
    height, width = image.shape[:2]
    scale = max_side / max(height, width)
    if scale < 1.0:
        image = cv2.resize(
            image,
            (int(width * scale), int(height * scale)),
            interpolation=cv2.INTER_AREA,
        )
    return image


def segment_pill(image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(
        blur, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV
    )
    contours, _ = cv2.findContours(
        thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    if not contours:
        mask = np.ones(gray.shape, np.uint8) * 255
        return image, mask
    contour = max(contours, key=cv2.contourArea)
    mask = np.zeros(gray.shape, np.uint8)
    cv2.drawContours(mask, [contour], -1, 255, -1)
    return image, mask


def feat_color_hist(image: np.ndarray, mask: np.ndarray, bins: int = 16) -> np.ndarray:
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2Lab)
    histograms = []
    for channel in cv2.split(lab):
        hist = cv2.calcHist([channel], [0], mask, [bins], [0, 256])
        hist = cv2.normalize(hist, None).flatten()
        histograms.append(hist)
    return np.concatenate(histograms).astype(np.float32)


def feat_shape(image: np.ndarray, mask: np.ndarray) -> np.ndarray:
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return np.zeros(10, np.float32)
    contour = max(contours, key=cv2.contourArea)
    moments = cv2.moments(contour)
    hu = cv2.HuMoments(moments).flatten()
    hu = -np.sign(hu) * np.log10(np.abs(hu) + 1e-12)
    x, y, width, height = cv2.boundingRect(contour)
    ratio = np.array([width / max(height, 1)], dtype=np.float32)
    area = np.array(
        [cv2.contourArea(contour) / (image.shape[0] * image.shape[1])],
        dtype=np.float32,
    )
    return np.concatenate([hu.astype(np.float32), ratio, area])


def feat_texture(image: np.ndarray, mask: np.ndarray, P: int = 8, R: int = 1) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    lbp = local_binary_pattern(gray, P=P, R=R, method="uniform").astype(np.uint8)
    lbp[mask == 0] = 0
    hist, _ = np.histogram(lbp[mask > 0], bins=np.arange(0, P + 3), density=True)
    return hist.astype(np.float32)


def feat_orb_embed(
    image: np.ndarray, mask: np.ndarray, max_keypoints: int = 200
) -> np.ndarray:
    orb = cv2.ORB_create(nfeatures=max_keypoints)
    keypoints, descriptors = orb.detectAndCompute(image, mask)
    if descriptors is None:
        return np.zeros(64, np.float32)
    mean = descriptors.mean(axis=0)
    std = descriptors.std(axis=0)
    return np.concatenate([mean, std]).astype(np.float32)


def extract_all_features(path: str):
    image = load_image(path)
    if image is None:
        return None
    image, mask = segment_pill(image)
    color = feat_color_hist(image, mask)
    shape = feat_shape(image, mask)
    texture = feat_texture(image, mask)
    embed = feat_orb_embed(image, mask)
    return color, shape, texture, embed
