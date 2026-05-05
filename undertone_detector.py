import cv2
import numpy as np
from PIL import Image

def get_dominant_color(image):
    img = np.array(image)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    img = cv2.resize(img, (100, 100))
    pixels = img.reshape(-1, 3)
    counts = {}

    for pixel in pixels:
        key = tuple(pixel)
        counts[key] = counts.get(key, 0) + 1

    dominant = max(counts, key=counts.get)
    return dominant


def classify_undertone(bgr):
    b, g, r = bgr
    hsv = cv2.cvtColor(np.uint8([[[b, g, r]]]), cv2.COLOR_BGR2HSV)[0][0]
    h, s, v = hsv

    if (0 <= h <= 25) or (h >= 330):
        return "Warm"
    elif 150 <= h <= 270:
        return "Cool"
    else:
        return "Neutral"


def get_suggested_colors(undertone):
    if undertone == "Warm":
        return {
            "Coral": "#FF7F50",
            "Peach": "#FFE5B4",
            "Gold": "#FFD700",
            "Olive": "#808000",
            "Warm Red": "#FF4500"
        }

    elif undertone == "Cool":
        return {
            "Berry": "#8A2BE2",
            "Silver": "#C0C0C0",
            "Emerald": "#50C878",
            "Sapphire": "#0F52BA",
            "Cool Pink": "#FF69B4"
        }

    else:
        return {
            "Chocolate brown": "#7B3F00",
            "Teal": "#008080",
            "Lavender": "#E6E6FA",
            "Champagne": "#F7E7CE",
            "Soft Rose": "#F4C2C2"
        }


def get_bad_colors(undertone):
    if undertone == "Warm":
        return {
            "Icy Blue": "#99CCFF",
            "Magenta": "#FF00FF",
            "Pure White": "#FFFFFF",
            "Cool Gray": "#A9A9A9",
            "Lavender": "#E6E6FA"
        }

    elif undertone == "Cool":
        return {
            "Mustard": "#FFDB58",
            "Pumpkin": "#FF7518",
            "Olive": "#808000",
            "Tan": "#D2B48C",
            "Warm Brown": "#A0522D"
        }

    else:
        return {
            "Neon Green": "#39FF14",
            "Neon Pink": "#FF6EC7",
            "Pale Pastels": "#FEFFBF",
            "Burnt Orange": "#CC5500",
            "Bright Yellow": "#FFFF00"
        }


def detect_undertone(image_file):
    image = Image.open(image_file).convert("RGB")
    dominant_color = get_dominant_color(image)
    undertone = classify_undertone(dominant_color)
    good_colors = get_suggested_colors(undertone)
    bad_colors = get_bad_colors(undertone)
    return undertone, good_colors, bad_colors
