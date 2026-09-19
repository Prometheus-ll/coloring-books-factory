"""
Converts an image into clean black-and-white coloring-book line art. Meant
to run on the flat, bold-outlined cartoon illustrations generate_book.py
now asks for (see coloring_page_prompt) - a much easier source to extract
clean lines from than a photorealistic one, since there's far less fine
texture/shading fighting the edge detection.

Settings below are lighter than an earlier version tuned against
photorealistic output, on the reasoning that a flatter source needs less
smoothing to begin with - not yet verified against a live-generated flat
cartoon image (that needs an actual Pollinations call, which isn't
possible to test from here). If pages come out too sparse or too
scribbly, this is the one function to retune.
"""

import cv2
import numpy as np
from PIL import Image


def to_coloring_page(img: Image.Image, line_thickness: int = 2) -> Image.Image:
    arr = np.array(img.convert("RGB"))
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)

    smoothed = cv2.bilateralFilter(gray, d=11, sigmaColor=100, sigmaSpace=100)
    smoothed = cv2.medianBlur(smoothed, 5)

    edges = cv2.Canny(smoothed, threshold1=50, threshold2=140)

    # Canny's lines are thin and pencil-like - thicken them into bold,
    # marker-friendly coloring-book outlines.
    kernel = np.ones((line_thickness, line_thickness), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=1)

    # Canny gives white edges on a black background; coloring pages need
    # the opposite - black lines on white.
    inverted = cv2.bitwise_not(edges)

    return Image.fromarray(inverted).convert("RGB")
