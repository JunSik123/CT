import numpy as np
import cv2
from fastapi import UploadFile


def read_bgr(file: UploadFile):
    data = file.file.read()
    array = np.frombuffer(data, np.uint8)
    return cv2.imdecode(array, cv2.IMREAD_COLOR)
