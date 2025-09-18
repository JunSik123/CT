import os
from typing import List, Sequence, Tuple

import cv2
import numpy as np
import pytesseract
from dotenv import load_dotenv

load_dotenv()
TESSERACT_PATH = os.getenv("TESSERACT_PATH")
if TESSERACT_PATH:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

CONFUSION = {
    ("O", "0"): 0.2,
    ("0", "O"): 0.2,
    ("I", "1"): 0.2,
    ("1", "I"): 0.2,
    ("S", "5"): 0.3,
    ("5", "S"): 0.3,
    ("B", "8"): 0.3,
    ("8", "B"): 0.3,
    ("Z", "2"): 0.4,
    ("2", "Z"): 0.4,
}


def confusion_cost(a: str, b: str) -> float:
    if a == b:
        return 0.0
    return CONFUSION.get((a, b), 1.0)


def weighted_edit_distance(source: str, target: str) -> float:
    n, m = len(source), len(target)
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = float(i)
    for j in range(m + 1):
        dp[0][j] = float(j)

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost_sub = confusion_cost(source[i - 1], target[j - 1])
            dp[i][j] = min(
                dp[i - 1][j] + 1.0,
                dp[i][j - 1] + 1.0,
                dp[i - 1][j - 1] + cost_sub,
            )
    return dp[n][m]


def ocr_basic(image_bgr: np.ndarray) -> str:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    config = (
        "--psm 7 --oem 1 "
        "-c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    )
    text = pytesseract.image_to_string(thresh, config=config)
    return text.strip().replace(" ", "")


def lexicon_rank(
    ocr_text: str, lexicon: Sequence[str], topn: int = 10
) -> List[Tuple[str, float]]:
    if not lexicon:
        return []
    if not ocr_text:
        candidates = sorted(lexicon, key=lambda s: (len(s), s))[:topn]
        return [(candidate, 999.0) for candidate in candidates]

    scored: List[Tuple[str, float]] = []
    for candidate in lexicon:
        distance = weighted_edit_distance(ocr_text, candidate)
        scored.append((candidate, distance))
    scored.sort(key=lambda item: item[1])
    return scored[:topn]
