import socket
import pickle
import struct
from customtkinter import *
from PIL import Image, ImageTk
import numpy
import threading
import time
import cv2


class UserWindow(CTk):
    def __init__(self, client_socket):
        super().__init__()
        self.client_socket = client_socket
        self.image_to_display_in_numpy_array = numpy.array(Image.open("no_video.jpg"))

        self.camera_label = CTkLabel(self, text="")
        self.camera_label.pack()

        self.switch_camera_button = CTkButton(self, text=f"Switch camera", command=self.switch_camera_request_start_thread)
        self.switch_camera_button.pack()

        threading.Thread(target=self.receive_camera_footage).start()
        self.show_camera_footage()

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

            # Deserialize the received frame
            received_frame = pickle.loads(frame_data)

            # Decode the JPEG byte data back into the frame (image)
            nparr = numpy.frombuffer(received_frame, numpy.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)  # Decodes the byte data to a color image

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
