from customtkinter import *
import socket
import threading
from win32api import MessageBox
from win32con import MB_OK, MB_ICONINFORMATION
import constants
from encryption import *
import os
import win32file
import cv2
from PIL import Image, ImageTk
import struct
import time
import numpy


class App(CTk):
    def __init__(self):
        super().__init__()
        self.iconbitmap("watchdog.ico")
        self.geometry("600x600")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.login_frame = LoginFrame(app=self)
        self.login_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self.register_frame = RegisterFrame(app=self)
        self.register_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self.user_frame = UserFrame(app=self)
        self.user_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self.camera_selection_frame = CameraSelectionFrame(app=self)
        self.camera_selection_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self.camera_frame = CameraFrame(app=self)
        self.camera_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        # The frame we are starting with
        self.show_login_frame()

    def show_login_frame(self):
        self.title("WATCHDOG - Login")
        self.login_frame.lift()

    def show_register_frame(self):
        self.title("WATCHDOG - Register")
        self.register_frame.lift()

    def show_user_frame(self):
        self.title("WATCHDOG - User")
        self.user_frame.start_receiving_footage()
        self.user_frame.lift()

    def show_camera_selection_frame(self):
        self.title("WATCHDOG - Camera Selection")
        self.camera_selection_frame.update_camera_indexes()
        self.camera_selection_frame.lift()

    def show_camera_frame(self, camera_index=0):
        self.title("WATCHDOG - Camera")
        self.camera_frame.start_sending_camera_footage(camera_index)
        self.camera_frame.lift()


class LoginFrame(CTkFrame):
    def __init__(self, app):
        super().__init__(app)
        self.app = app

        self.username_entry = CTkEntry(self, font=("Arial", 12), placeholder_text="Enter username")
        self.username_entry.pack(pady=5)

        self.password_entry = CTkEntry(self, font=("Arial", 12), placeholder_text="Enter password", show="*")
        self.password_entry.pack(pady=5)

        self.login_btn = CTkButton(self, text="Log In", command=self.login_to_account_thread_start,
                                   font=("Consolas", 14, "bold"), height=40, width=200)
        self.login_btn.pack(pady=20)

        self.register_button = CTkButton(self, text="Register", command=self.app.show_register_frame)
        self.register_button.pack()

    def login_to_account_thread_start(self):
        threading.Thread(target=self.login_to_account).start()

    def login_to_account(self):
        client_socket.send("login".encode())
        print(client_socket.recv(1024).decode())

        client_socket.send(rsa_encrypt(constants.client_to_server_public_key,
                                       f"{self.username_entry.get()}, {self.password_entry.get()}").encode())
        answer = client_socket.recv(1024).decode()

        if "Wrong password" in answer:
            MessageBox(0, "Wrong password", 'Error', MB_OK | MB_ICONINFORMATION)
        elif "No such username" in answer:
            MessageBox(0, "No such username", 'Error', MB_OK | MB_ICONINFORMATION)
        elif "already logged in" in answer:
            MessageBox(0, answer, 'Error', MB_OK | MB_ICONINFORMATION)
        else:
            MessageBox(0, answer, 'Success', MB_OK | MB_ICONINFORMATION)

            if answer.split()[0] == "User":
                self.app.show_user_frame()
            elif answer.split()[0] == "Camera":
                self.app.show_camera_selection_frame()
            else:
                print("wtf")


class RegisterFrame(CTkFrame):
    def __init__(self, app):
        super().__init__(app)
        self.app = app

        self.username_entry = CTkEntry(self, font=("Arial", 12), placeholder_text="Enter username")
        self.username_entry.pack(pady=5)

        self.password_entry = CTkEntry(self, font=("Arial", 12), placeholder_text="Enter password")
        self.password_entry.pack(pady=5)

        self.account_type = CTkOptionMenu(self, values=["User", "Camera"])
        self.account_type.pack()

        self.register_btn = CTkButton(self, text="Register", command=self.register_account_thread_start,
                                      font=("Consolas", 14, "bold"), height=40, width=200)
        self.register_btn.pack(pady=20)

        self.login_button = CTkButton(self, text="Login", command=self.app.show_login_frame)
        self.login_button.pack()

    def register_account_thread_start(self):
        threading.Thread(target=self.register_account).start()

    def register_account(self):
        client_socket.send("register".encode())
        print(client_socket.recv(1024).decode())

        client_socket.send(rsa_encrypt(constants.client_to_server_public_key,
                                       f"{self.username_entry.get()}, {self.password_entry.get()}, {self.account_type.get()}").encode())
        answer = client_socket.recv(1024).decode()

        if answer == "Attempted username is taken":
            MessageBox(0, answer, 'Error', MB_OK | MB_ICONINFORMATION)

        elif answer == "verification code needed":
            dialog = CTkInputDialog(text="Start your chat with @WatchdogCameraBot on Telegram and get your verification code", title="Verify your account")
            client_socket.send(rsa_encrypt(constants.client_to_server_public_key, f"{dialog.get_input()}").encode())
            MessageBox(0, client_socket.recv(1024).decode(), 'Success', MB_OK | MB_ICONINFORMATION)

            self.app.show_user_frame()

        elif answer == "Camera account created successfully":
            MessageBox(0, answer, 'Success', MB_OK | MB_ICONINFORMATION)

            self.app.show_camera_selection_frame()
        else:
            print("How did we get here")


class UserFrame(CTkFrame):
    def __init__(self, app):
        super().__init__(app)
        self.app = app

        self.camera_title = CTkLabel(self, text="Camera -999")
        self.camera_title.pack()

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


    def start_receiving_footage(self):
        self.switch_camera_request_start_thread()
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
            if ".jpg" in f[8] and "screenshot" in f[8]:
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
        client_socket.send("alert".encode())

    def sub_start_thread(self):
        threading.Thread(target=self.subscribe_to_camera).start()

    def subscribe_to_camera(self):
        client_socket.send("subscribe_to_camera".encode())

    def switch_camera_request_start_thread(self):
        threading.Thread(target=self.switch_camera_request).start()

    def switch_camera_request(self):
        client_socket.send("switch_camera_request".encode())

    def receive_camera_footage(self):
        while True:
            received_data = b""
            payload_size = struct.calcsize("L")

            # Receive and assemble the data until the payload size is reached
            while len(received_data) < payload_size:
                received_data += client_socket.recv(4096)

            # Extract the packed message size
            packed_msg_size = received_data[:payload_size]
            received_data = received_data[payload_size:]
            msg_size = struct.unpack("L", packed_msg_size)[0]

            # Receive and assemble the frame data until the complete frame is received
            while len(received_data) < msg_size:
                received_data += client_socket.recv(4096)

            # Extract the frame data
            frame_data = received_data[:msg_size]

            # Decode the JPEG byte data back into the frame (image)
            nparr = numpy.frombuffer(frame_data, numpy.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)  # Decodes the byte data to a color image

            if self.mirrored:
                frame = numpy.flip(frame, axis=1)

            # put the received frame in a global variable that's displaying the image in customtkinter
            self.image_to_display_in_numpy_array = frame

            client_socket.send("ready_for_pic".encode())

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
        self.camera_label.after(1, self.show_camera_footage)


class CameraSelectionFrame(CTkFrame):
    def __init__(self, app):
        super().__init__(app)
        self.app = app

        self.camera_active = False
        self.video_capture = None

        self.camera_index = CTkOptionMenu(self, values=list(map(lambda x: f"Camera {x}", self.count_connected_cameras())))
        self.camera_index.pack()

        self.test_camera_button = CTkButton(self, text="Test selected camera", command=self.start_camera)
        self.test_camera_button.pack()

        self.camera_label = CTkLabel(self, text="")
        self.camera_label.pack()

        self.select_camera_button = CTkButton(self, text="Select this camera", command=self.stop_camera)
        self.select_camera_button.pack()

    def update_camera_indexes(self):
        self.camera_index.configure(values =list(map(lambda x: f"Camera {x}", self.count_connected_cameras())))
    def start_camera(self):
        self.camera_active = False
        time.sleep(0.1)
        camera_index = int(self.camera_index.get()[-2:])
        self.camera_active = True
        self.video_capture = cv2.VideoCapture(camera_index)
        width, height = 400, 300
        self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        threading.Thread(target=self.test_camera, args=(camera_index,)).start()

    def stop_camera(self):
        if self.camera_active:
            self.camera_active = False
            self.video_capture.release()
        self.app.show_camera_frame(int(self.camera_index.get()[-2:]))

    def test_camera(self, camera_index):
        if not self.camera_active:
            return

        try:
            # Capture the video frame by frame
            _, frame = self.video_capture.read()

            # Convert image from one color space to other
            opencv_image = cv2.cvtColor(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), cv2.COLOR_BGR2RGBA)

            # Capture the latest frame and transform to image
            captured_image = Image.fromarray(opencv_image)

            # Convert captured image to photo image
            photo_image = ImageTk.PhotoImage(image=captured_image)

            # Displaying photo image in the label
            self.camera_label.photo_image = photo_image

            # Configure image in the label
            self.camera_label.configure(image=photo_image)

            # Repeat the same process after every 10 milliseconds
            self.camera_label.after(1, lambda: self.test_camera(camera_index))
        except Exception as e:
            print(e)
            image = Image.open("no_video.jpg")
            photo_image = ImageTk.PhotoImage(image)
            self.camera_label.photo_image = photo_image
            self.camera_label.configure(image=photo_image)

    def count_connected_cameras(self):
        camera_count = 0
        looking_for_cameras = True
        cameras_indexes = []

        while looking_for_cameras:
            cap = cv2.VideoCapture(camera_count)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    cameras_indexes.append(camera_count)
                else:
                    print(f"Camera at index {camera_count} is in use or not returning frames")
                cap.release()
            else:
                cap.release()
                looking_for_cameras = False

            camera_count += 1

        return cameras_indexes


class CameraFrame(CTkFrame):
    def __init__(self, app):
        super().__init__(app)
        self.app = app

        self.encryption_key = None
        self.video_capture = None

        self.camera_label = CTkLabel(self, text="Camera hidden for you")
        self.camera_label.pack()

        self.showing_camera = False
        self.camera_loop_id = None  # Store after() loop ID

        self.show_camera_button = CTkButton(self, text="Show camera footage", command=self.toggle_camera_footage)
        self.show_camera_button.pack()

        self.mirrored = False
        self.mirror_button = CTkButton(self, text="Mirror footage", command=self.mirror_footage)
        self.mirror_button.pack()


    def start_sending_camera_footage(self, camera_index):
        self.encryption_key = os.urandom(16)
        client_socket.send(rsa_encrypt(constants.client_to_server_public_key, self.encryption_key.hex()).encode())

        self.video_capture = cv2.VideoCapture(camera_index)
        width, height = 400, 300
        self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        threading.Thread(target=self.send_camera_footage).start()

    def mirror_footage(self):
        self.mirrored = not self.mirrored

    def toggle_camera_footage(self):
        if not self.showing_camera:
            self.showing_camera = True
            self.camera_label.configure(text="")
            self.show_camera_button.configure(text="Hide camera footage")
            self.show_camera_footage()
        else:
            self.showing_camera = False
            self.show_camera_button.configure(text="Show camera footage")
            if self.camera_loop_id is not None:
                self.after_cancel(self.camera_loop_id)
            # Clear the image from the label
            self.camera_label.configure(image=None, text="Camera hidden for you")
            self.camera_label.photo_image = None

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
        #self.camera_label.after(1, self.show_camera_footage)

        if self.showing_camera:
            self.camera_loop_id = self.camera_label.after(1, self.show_camera_footage)

    def send_camera_footage(self):
        while True: # TO DO: change this from while true
            # Read a frame from the camera
            ret, frame = self.video_capture.read()
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) # Turn frame black and white

            if self.mirrored:
                frame = numpy.flip(frame, axis=1)

            # Compress the frame using JPEG
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 30]
            _, encoded_frame = cv2.imencode('.jpg', frame, encode_param)

            # Convert the encoded frame to a byte array
            frame_bytes = encoded_frame.tobytes()

            # Pack the data size and frame data
            message_size = struct.pack("L", len(frame_bytes))
            client_socket.sendall(message_size + frame_bytes)

            # Image received confirmation -> send next one
            client_socket.recv(1024)


if __name__ == "__main__":
    # Establish connection to the server
    client_socket = socket.socket()
    client_socket.connect(("127.0.0.1", 1729))

    # Create App
    root = App()
    root.mainloop()
