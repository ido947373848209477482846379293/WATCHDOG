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

# CONSTANTS & IMPORTANT VARIABLES
num_of_cameras = count_connected_cameras()
curr_camera = 0

# Define a video capture object
vid = cv2.VideoCapture(curr_camera)

# Declare the width and height in variables
width, height = 800, 600

# Set the width and height
vid.set(cv2.CAP_PROP_FRAME_WIDTH, width)
vid.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

def switch_between_cameras():
	global curr_camera, vid
	curr_camera = (curr_camera + 1) % num_of_cameras
	try:
		# Define a video capture object
		vid = cv2.VideoCapture(curr_camera)

		# Declare the width and height in variables
		width, height = 800, 600

		# Set the width and height
		vid.set(cv2.CAP_PROP_FRAME_WIDTH, width)
		vid.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

	except Exception as e:
		print(e)