import socket, select
import sqlite3
import threading
import db
import struct
import pickle
import random
import time


class Client:
    def __init__(self, client_socket):
        self.client_socket = client_socket

    def get_socket(self):
        return self.client_socket


class User(Client):
    def __init__(self, client_socket, user_id):
        super().__init__(client_socket)
        self.user_id = user_id
        self.current_camera_id = None
        self.ready_for_pic = True


class Camera(Client):
    def __init__(self, client_socket, camera_id):
        super().__init__(client_socket)
        self.camera_id = camera_id


server = socket.socket()
server.bind(('0.0.0.0', 1729))
server.listen(10)
clients = []
users = []
cameras = []
db_lock = threading.Lock()


def handle_client(client_socket):
    message = client_socket.recv(1024).decode()

    if message == "register":
        client_socket.send("Register attempted detected, go on...".encode())
        register_info = client_socket.recv(1024).decode().split(", ") # 0 - username, 1 - password, 2 - account_type

        try:
            db_lock.acquire()
            db.create_new_account(register_info[0], register_info[1])
            db_lock.release()

            if register_info[2] == "User":
                client_socket.send("Phone number needed".encode())
                phone_num = client_socket.recv(1024).decode()
                db_lock.acquire()
                db.create_new_user(register_info[0], phone_num)
                db_lock.release()
                client_socket.send("User account created successfully".encode())

                user = User(client_socket, db.get_user_id(register_info[0]))
                users.append(user)
                handle_user(user)

            elif register_info[2] == "Camera":
                db_lock.acquire()
                db.create_new_camera(register_info[0])
                db_lock.release()
                client_socket.send("Camera account created successfully".encode())

                camera = Camera(client_socket, db.get_camera_id(register_info[0]))
                cameras.append(camera)
                handle_camera(camera)

        except sqlite3.IntegrityError as e:
            client_socket.send("Attempted username is taken".encode())
            db_lock.release()
            handle_client(client_socket)


    elif message == "login":
        client_socket.send("Login attempted detected, go on...".encode())
        login_info = client_socket.recv(1024).decode().split(", ")  # 0 - username, 1 - password

        try:
            db_lock.acquire()
            db.login(login_info[0], login_info[1])
            account_type = db.get_account_type(login_info[0])
            db_lock.release()

            if account_type == "User":
                user = User(client_socket, db.get_user_id(login_info[0]))
                for u in users:
                    if u.user_id == user.user_id:
                        db_lock.acquire()
                        raise Exception("User already logged in")
                client_socket.send("User logged in successfully".encode())
                users.append(user)
                handle_user(user)

            elif account_type == "Camera":
                camera = Camera(client_socket, db.get_camera_id(login_info[0]))
                for c in cameras:
                    if c.camera_id == camera.camera_id:
                        db_lock.acquire()
                        raise Exception("Camera already logged in")
                client_socket.send("Camera logged in successfully".encode())
                cameras.append(camera)
                handle_camera(camera)

        except Exception as e:
            client_socket.send(f"{e}".encode())
            db_lock.release()
            handle_client(client_socket)
    else:
        pass


def handle_user(user):
    while True:
        request = user.client_socket.recv(1024).decode()


        if "ready_for_pic" in request:
            user.ready_for_pic = True

        elif "switch_camera_request" in request:
            print(request)
            curr_camera = False

            for camera in cameras:
                if camera.camera_id == user.current_camera_id:
                    curr_camera = True
                    index = cameras.index(camera)
                    print(f"index: {index}")

                    if len(cameras) - 1 > index:
                        user.current_camera_id = cameras[index+1].camera_id

                    elif len(cameras) - 1 == index:
                        if index > 0:
                            user.current_camera_id = cameras[0].camera_id

                    break


            if not curr_camera:
                try:
                    user.current_camera_id = cameras[0].camera_id
                except IndexError:
                    print("There aren't any cameras")

            print(user.current_camera_id)




def handle_camera(camera):
    while True:
        received_data = b""
        payload_size = struct.calcsize("L")

        # Receive and assemble the data until the payload size is reached
        while len(received_data) < payload_size:
            received_data += camera.client_socket.recv(4096)

        # Extract the packed message size
        packed_msg_size = received_data[:payload_size]
        received_data = received_data[payload_size:]
        msg_size = struct.unpack("L", packed_msg_size)[0]

        # Receive and assemble the frame data until the complete frame is received
        while len(received_data) < msg_size:
            received_data += camera.client_socket.recv(4096)

        # Extract the frame data
        frame_data = received_data[:msg_size]
        received_data = received_data[msg_size:]

        # Deserialize the received frame
        received_frame = pickle.loads(frame_data)

        camera.client_socket.send("lorem ipsum".encode())

        for user in users:
            if user.current_camera_id == camera.camera_id and user.ready_for_pic == True:
                user.ready_for_pic = False
                serialized_frame = pickle.dumps(received_frame)
                message_size = struct.pack("L", len(serialized_frame))
                user.client_socket.sendall(message_size + serialized_frame)



if __name__ == "__main__":
    db.main()

    while True:                                                                     #wlist- רשימת כל הלקוחות שאליהם השרת שלח מידע
        rlist, wlist, xlist = select.select([server]+clients, clients, [])     #rlist - כל הלקוחות שמהם השרת עושה ריד
        for client in rlist:                                                        #xlist- כל הלקוחות שהתקשורות איתם קרסה
            if client is server:
                print('new client has joined the chat')
                c, address = client.accept()
                clients.append(c)
                client_thread = threading.Thread(target=handle_client, args=(c,)).start()
            else:
                # message = client.recv(1024).decode()
                pass
