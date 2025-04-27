import socket
import struct
import time

from customtkinter import *
from PIL import Image, ImageTk
import numpy
import threading
import cv2
import os
import win32file
import base64

import constants
from encryption import *


class UserWindow(CTk):
    def __init__(self, client_socket):
        super().__init__()
        self.client_socket = client_socket
        self.image_to_display_in_numpy_array = numpy.array(Image.open("no_video.jpg"))

        self.camera_label = CTkLabel(self, text="")
        self.camera_label.pack()

        self.switch_camera_button = CTkButton(self, text=f"Switch camera", command=self.switch_camera_request_start_thread)
        self.switch_camera_button.pack()

        self.screenshot_button = CTkButton(self, text=f"Screenshot", command=self.screenshot_start_thread)
        self.screenshot_button.pack()

        self.subscribe_button = CTkButton(self, text=f"Subscribe to camera", command=self.sub_start_thread)
        self.subscribe_button.pack()

        self.alert_button = CTkButton(self, text=f"Alert all camera subscribers", command=self.alert_start_thread)
        self.alert_button.pack()

        self.mirrored = False
        self.mirror_button = CTkButton(self, text="Mirror footage", command=self.mirror_footage)
        self.mirror_button.pack()

        threading.Thread(target=self.receive_camera_footage).start()
        self.show_camera_footage()

    def mirror_footage(self):
        self.mirrored = not self.mirrored

    def screenshot_start_thread(self):
        threading.Thread(target=self.screenshot).start()

    def screenshot(self):
        image = Image.fromarray(self.image_to_display_in_numpy_array)

        screenshots_folder = os.getcwd()
        path = os.path.join(screenshots_folder, '*')
        file_name = None

        files = win32file.FindFilesW(path)
        for f in files:
            if ".jpg" in f[8] and "no_video" not in f[8]:
                file_name = f[8]

        if file_name is None:
            file_name = "screenshot0.jpg"
        else:
            file_name = "screenshot" + str(int(file_name.split('.')[0].split('screenshot')[1]) + 1) + ".jpg"

        image.save(file_name)

        toplevel = CTkToplevel(self)
        toplevel.title(file_name)

        photo_image = ImageTk.PhotoImage(image=image)
        image_label = CTkLabel(toplevel, text="", image=photo_image)
        image_label.pack()

    def alert_start_thread(self):
        threading.Thread(target=self.alert_camera_subscribers).start()

    def alert_camera_subscribers(self):
        self.client_socket.send("alert".encode())

    def sub_start_thread(self):
        threading.Thread(target=self.subscribe_to_camera).start()

    def subscribe_to_camera(self):
        self.client_socket.send("subscribe_to_camera".encode())

    def switch_camera_request_start_thread(self):
        threading.Thread(target=self.switch_camera_request).start()

    def switch_camera_request(self):
        self.client_socket.send("switch_camera_request".encode())

    def receive_camera_footage(self):
        while True:
            received_data = b""
            payload_size = struct.calcsize("L")

            # Receive and assemble the data until the payload size is reached
            while len(received_data) < payload_size:
                received_data += self.client_socket.recv(4096)

            # Extract the packed message size
            packed_msg_size = received_data[:payload_size]
            received_data = received_data[payload_size:]
            msg_size = struct.unpack("L", packed_msg_size)[0]

            # Receive and assemble the frame data until the complete frame is received
            while len(received_data) < msg_size:
                received_data += self.client_socket.recv(4096)

            # Extract the frame data
            frame_data = received_data[:msg_size]
            received_data = received_data[msg_size:]

            # Decode the JPEG byte data back into the frame (image)
            nparr = numpy.frombuffer(frame_data, numpy.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)  # Decodes the byte data to a color image

            if self.mirrored:
                frame = numpy.flip(frame, axis=1)

            # put the received frame in a global variable that's displaying the image in customtkinter
            self.image_to_display_in_numpy_array = frame

            self.client_socket.send("ready_for_pic".encode())

    def show_camera_footage(self):
        # Capture the latest frame and transform to image
        captured_image = Image.fromarray(self.image_to_display_in_numpy_array)

        # Convert captured image to PhotoImage
        photo_image = ImageTk.PhotoImage(image=captured_image)

        # Displaying PhotoImage in the label
        self.camera_label.photo_image = photo_image

        # Configure image in the label
        self.camera_label.configure(image=photo_image)

        # Repeat the same process after every 10 milliseconds
        self.camera_label.after(10, self.show_camera_footage)


def main(client_socket):
    user_window = UserWindow(client_socket)
    user_window.title("User")

    user_window.mainloop()
