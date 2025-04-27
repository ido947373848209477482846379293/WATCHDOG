from customtkinter import *
import cv2
from PIL import Image, ImageTk
import socket
import struct
import threading
import time
import numpy
import base64

import constants
from encryption import *


class CameraWindow(CTk):
    def __init__(self):
        super().__init__()

        self.video_capture = cv2.VideoCapture(int(input("Enter camera num (test mode): ")))
        width, height = 800, 600
        self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        self.camera_label = CTkLabel(self, text="")
        self.camera_label.pack()

        self.show_camera_button = CTkButton(self, text="Show camera footage", command=self.show_camera_footage)
        self.show_camera_button.pack()

        self.mirrored = False
        self.mirror_button = CTkButton(self, text="Mirror footage", command=self.mirror_footage)
        self.mirror_button.pack()

    def mirror_footage(self):
        self.mirrored = not self.mirrored

    def show_camera_footage(self):
        # Capture the video frame by frame
        _, frame = self.video_capture.read()

        # Convert image from one color space to other
        opencv_image = cv2.cvtColor(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), cv2.COLOR_BGR2RGBA)

        if self.mirrored:
            opencv_image = numpy.flip(opencv_image, axis=1)

        # Capture the latest frame and transform to image
        captured_image = Image.fromarray(opencv_image)

        # Convert captured image to photo image
        photo_image = ImageTk.PhotoImage(image=captured_image)

        # Displaying photo image in the label
        self.camera_label.photo_image = photo_image

        # Configure image in the label
        self.camera_label.configure(image=photo_image)

        # Repeat the same process after every 10 milliseconds
        self.camera_label.after(10, self.show_camera_footage)

    def send_camera_footage(self, client_socket):
        while True: # TO DO: change this from while true
            # Read a frame from the camera
            ret, frame = self.video_capture.read()
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) # Turn frame black and white

            if self.mirrored:
                frame = numpy.flip(frame, axis=1)

            # Compress the frame using JPEG
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 50]
            _, encoded_frame = cv2.imencode('.jpg', frame, encode_param)

            # Convert the encoded frame to a byte array
            frame_bytes = encoded_frame.tobytes()

            # Pack the data size and frame data
            message_size = struct.pack("L", len(frame_bytes))
            client_socket.sendall(message_size + frame_bytes)

            conf = client_socket.recv(1024).decode()


def main(client_socket):
    camera_window = CameraWindow()
    camera_window.title("Camera")

    threading.Thread(target=camera_window.send_camera_footage, args=(client_socket,)).start()
    camera_window.mainloop()
