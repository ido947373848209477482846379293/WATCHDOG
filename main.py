"""
import cv2

def count_connected_cameras():
	camera_count = 0
	looking_for_cameras = True

	while looking_for_cameras:
		cap = cv2.VideoCapture(camera_count)  # Try to open the camera at index i
		if cap.isOpened():  # Check if the camera is successfully opened
			print(f"Camera found at index {camera_count}")
			camera_count += 1
			cap.release()  # Release the camera after checking
		else:
			looking_for_cameras = False

	return camera_count

print(count_connected_cameras())
"""

import cv2
import numpy as np

# Read input image
img = cv2.imread('no_video.jpg')

# Mirror in x direction (flip horizontally)
imgX = np.flip(img, axis=1)
# imgX = imgX = img[:, ::-1, :]
print(type(imgX))

# Outputs
cv2.imshow('imgX', imgX)
cv2.waitKey(0)