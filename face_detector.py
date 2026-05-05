import cv2
import numpy as np
import mediapipe as mp
import os

# ✅ Initialize MediaPipe FaceMesh
mp_face_mesh = mp.solutions.face_mesh

# ✅ Main detection function
def detect_face_shape(image_path):
    img = cv2.imread(image_path)
    if img is None:
        return "No face detected"

    with mp_face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5
    ) as face_mesh:
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)
        if not results.multi_face_landmarks:
            return "No face detected"

        h, w, _ = img.shape
        landmarks = results.multi_face_landmarks[0]
        xs = [lm.x * w for lm in landmarks.landmark]
        ys = [lm.y * h for lm in landmarks.landmark]

        face_width = max(xs) - min(xs)
        face_height = max(ys) - min(ys)
        ratio = face_height / face_width

        if ratio > 1.45:
            return "Oblong"
        elif ratio > 1.25:
            return "Oval"
        elif ratio > 1.1:
            return "Round"
        elif ratio > 0.95:
            return "Square"
        else:
            return "Heart"
