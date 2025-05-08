import socket, select
import sqlite3
import threading
import constants
import db
import struct
from encryption import *
import telegram_bot


class Client:
    def __init__(self, client_socket, name):
        self.client_socket = client_socket
        self.name = name


class User(Client):
    def __init__(self, client_socket, username, user_id, chat_id):
        super().__init__(client_socket, username)
        self.user_id = user_id
        self.current_camera_id = None
        self.chat_id = chat_id
        self.ready_for_pic = False


class Camera(Client):
    def __init__(self, client_socket, camera_name, camera_id):
        super().__init__(client_socket, camera_name)
        self.camera_id = camera_id
        self.encryption_key = None


server = socket.socket()
server.bind(('0.0.0.0', 1729))
server.listen(10)
clients = []
users = []
cameras = []
db_lock = threading.Lock()
camera_sub_lock = threading.Lock()


def handle_client(client_socket):
    message = client_socket.recv(1024).decode()

    if message == "register":
        client_socket.send("Register attempted detected, go on...".encode())
        register_info = rsa_decrypt(constants.client_to_server_private_key, client_socket.recv(1024).decode()).split(", ") # 0 - username, 1 - password, 2 - account_type

        try:
            db_lock.acquire()
            db.create_new_account(register_info[0], register_info[1])
            db_lock.release()

            if register_info[2] == "User":
                client_socket.send("verification code needed".encode())
                verif_code = rsa_decrypt(constants.client_to_server_private_key, client_socket.recv(1024).decode())
                chat_id = ""
                try:
                    chat_id = db.get_chat_id_from_verif_code(verif_code)
                except Exception as e:
                    print(e)

                db_lock.acquire()
                db.create_new_user(register_info[0], chat_id)
                db_lock.release()
                client_socket.send("User account created successfully".encode())

                user = User(client_socket, register_info[0], db.get_user_id(register_info[0]), chat_id)
                users.append(user)
                handle_user(user)

            elif register_info[2] == "Camera":
                db_lock.acquire()
                db.create_new_camera(register_info[0])
                db_lock.release()
                client_socket.send("Camera account created successfully".encode())

                camera = Camera(client_socket, register_info[0],db.get_camera_id(register_info[0]))
                cameras.append(camera)
                handle_camera(camera)

        except sqlite3.IntegrityError:
            client_socket.send("Attempted username is taken".encode())
            db_lock.release()
            handle_client(client_socket)


    elif message == "login":
        client_socket.send("Login attempted detected, go on...".encode())
        login_info = rsa_decrypt(constants.client_to_server_private_key, client_socket.recv(1024).decode()).split(", ")  # 0 - username, 1 - password

        try:
            db_lock.acquire()
            db.login(login_info[0], login_info[1])
            account_type = db.get_account_type(login_info[0])
            db_lock.release()

            if account_type == "User":
                user = User(client_socket, login_info[0], db.get_user_id(login_info[0]), db.get_chat_id(login_info[0]))
                for u in users:
                    if u.user_id == user.user_id:
                        db_lock.acquire()
                        raise Exception("User already logged in")
                client_socket.send("User logged in successfully".encode())
                users.append(user)
                handle_user(user)

            elif account_type == "Camera":
                camera = Camera(client_socket, login_info[0], db.get_camera_id(login_info[0]))
                for cam in cameras:
                    if cam.camera_id == camera.camera_id:
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
    user.ready_for_pic = True
    while True:
        request = user.client_socket.recv(1024).decode()

        if "ready_for_pic" in request:
            user.ready_for_pic = True

        if "subscribe_to_camera" in request:
            print(request)
            camera_sub_lock.acquire()
            db.subscribe_to_camera(user.name, user.current_camera_id)
            camera_sub_lock.release()

        if "alert" in request:
            print(request)
            camera_sub_lock.acquire()
            subs = db.get_camera_subscriptions(user.current_camera_id)
            camera_sub_lock.release()

            threading.Thread(target=send_alert_messages, args=(subs, user.name, user.current_camera_id)).start()

        if "switch_camera_request" in request:
            print(request)
            switch_camera(user)

def switch_camera(user):
    curr_camera = False
    print("start here")

    for camera in cameras:
        if camera.camera_id == user.current_camera_id:
            curr_camera = True
            index = cameras.index(camera)

            if len(cameras) - 1 > index:
                user.current_camera_id = cameras[index + 1].camera_id
                print("case 1")
                #user.client_socket.send(get_camera_info(user).encode())

            elif len(cameras) - 1 == index:
                if index > 0:
                    user.current_camera_id = cameras[0].camera_id
                    print("case 2")
                    #user.client_socket.send(get_camera_info(user).encode())

            break

    if not curr_camera:
        try:
            user.current_camera_id = cameras[0].camera_id
            print("case 3")
            #user.client_socket.send(get_camera_info(user).encode())
        except IndexError:
            print("There aren't any cameras")
            #user.client_socket.send("no_cameras".encode())

def get_camera_info(user):
    for cam in cameras:
        if user.current_camera_id == cam.camera_id:
            camera_sub_lock.acquire()
            subs = db.get_camera_subscriptions(user.current_camera_id)
            camera_sub_lock.release()
            print(f"{cam.name} {cam.camera_id} {user.name in subs}")
            return f"{cam.name} {cam.camera_id} {user.name in subs}"

def send_alert_messages(subs, alerter_name, camera_id):
    print(subs)
    for sub in subs:
        if True: # sub != alerter_name
            chat_id = int(db.get_chat_id(sub))
            print(chat_id)
            try:
                telegram_bot.send_telegram_message(chat_id, f"User {alerter_name} has decided to alert all users of the camera with the id of {camera_id} ")
            except Exception as e:
                print(e)

def handle_camera(camera):
    camera.encryption_key = rsa_decrypt(constants.client_to_server_private_key, camera.client_socket.recv(1024).decode())
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

        #total_received = payload_size + len(frame_data)
        #print(f"Total bytes received including header: {total_received} bytes")

        camera.client_socket.send("lorem ipsum".encode())

        for user in users:
            if user.current_camera_id == camera.camera_id and user.ready_for_pic == True:
                user.ready_for_pic = False
                message_size = struct.pack("L", len(frame_data))
                user.client_socket.sendall(message_size + frame_data)



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
