from customtkinter import *
import socket
import threading
from win32api import MessageBox
from win32con import MB_OK, MB_ICONINFORMATION
import camera
import constants
import user
from encryption import *


class LoginOrRegisterWindow(CTk):
    def __init__(self):
        super().__init__()

        self.login_button = CTkButton(self, text="Login", command=lambda: create_login_window(self))
        self.login_button.pack()

        self.register_button = CTkButton(self, text="Register", command=lambda: create_register_window(self))
        self.register_button.pack()


class LoginWindow(CTk):
    def __init__(self):
        super().__init__()

        self.username_entry = CTkEntry(self, font=("Arial", 12), placeholder_text="Enter username")
        self.username_entry.pack(pady=5)

        self.password_entry = CTkEntry(self, font=("Arial", 12), placeholder_text="Enter password", show="*")
        self.password_entry.pack(pady=5)

        self.login_btn = CTkButton(self, text="Log In", command=self.login_to_account_thread_start, font=("Consolas", 14, "bold"), height=40, width=200)
        self.login_btn.pack(pady=20)

        self.register_button = CTkButton(self, text="Register", command=lambda: create_register_window(self))
        self.register_button.pack()

    def login_to_account_thread_start(self):
        threading.Thread(target=self.login_to_account).start()

    def login_to_account(self):
        client_socket.send("login".encode())
        print(client_socket.recv(1024).decode())

        client_socket.send(rsa_encrypt(constants.client_to_server_public_key, f"{self.username_entry.get()}, {self.password_entry.get()}").encode())
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
                launch_program_btn = CTkButton(self, text="Launch program", command=lambda: create_user_window(self))
                launch_program_btn.pack()
            elif answer.split()[0] == "Camera":
                launch_program_btn = CTkButton(self, text="Launch program", command=lambda: create_camera_window(self))
                launch_program_btn.pack()
            else:
                print("wtf")



class RegisterWindow(CTk):
    def __init__(self):
        super().__init__()

        self.username_entry = CTkEntry(self, font=("Arial", 12), placeholder_text="Enter username")
        self.username_entry.pack(pady=5)

        self.password_entry = CTkEntry(self, font=("Arial", 12), placeholder_text="Enter password")
        self.password_entry.pack(pady=5)

        self.account_type = CTkOptionMenu(self, values=["User", "Camera"])
        self.account_type.pack()

        self.register_btn = CTkButton(self, text="Register", command=self.register_account_thread_start, font=("Consolas", 14, "bold"), height=40, width=200)
        self.register_btn.pack(pady=20)

        self.login_button = CTkButton(self, text="Login", command=lambda: create_login_window(self))
        self.login_button.pack()

    def register_account_thread_start(self):
        threading.Thread(target=self.register_account).start()

    def register_account(self):
        client_socket.send("register".encode())
        print(client_socket.recv(1024).decode())

        client_socket.send(rsa_encrypt(constants.client_to_server_public_key, f"{self.username_entry.get()}, {self.password_entry.get()}, {self.account_type.get()}").encode())
        answer = client_socket.recv(1024).decode()

        if answer == "Attempted username is taken":
            MessageBox(0, answer, 'Error', MB_OK | MB_ICONINFORMATION)
        elif answer == "verification code needed":
            dialog = CTkInputDialog(text="Message @WatchdogCameraBot on Telegram and get your verification code", title="Verify your account")
            client_socket.send(rsa_encrypt(constants.client_to_server_public_key, f"{dialog.get_input()}").encode())
            MessageBox(0, client_socket.recv(1024).decode(), 'Success', MB_OK | MB_ICONINFORMATION)

            launch_program_btn = CTkButton(self, text="Launch program", command=lambda: create_user_window(self))
            launch_program_btn.pack()

        elif answer == "Camera account created successfully":
            MessageBox(0, answer, 'Success', MB_OK | MB_ICONINFORMATION)

            launch_program_btn = CTkButton(self, text="Launch program", command=lambda: create_camera_window(self))
            launch_program_btn.pack()
        else:
            while True:
                print("How did we get here")

def create_login_window(ctk_window):
    # Destroy old window
    ctk_window.destroy()

    # Create a new window
    login_window = LoginWindow()
    login_window.title("Log In")  # Window title
    login_window.geometry("320x400")  # Window size
    login_window.mainloop()

def create_register_window(ctk_window):
    # Destroy old window
    ctk_window.destroy()

    # Create a new window
    register_window = RegisterWindow()
    register_window.title("Register")  # Window title
    register_window.geometry("320x400")  # Window size
    register_window.mainloop()

def create_user_window(ctk_window):
    ctk_window.destroy()
    user.main(client_socket)

def create_camera_window(ctk_window):
    ctk_window.destroy()
    camera.main(client_socket)

def main():
    # Create a new window
    login_or_register_window = LoginOrRegisterWindow()
    login_or_register_window.title("Login or Register")  # Window title
    login_or_register_window.geometry("320x400")  # Window size

    login_or_register_window.mainloop()

if __name__ == "__main__":
    # Establish connection to the server
    client_socket = socket.socket()
    client_socket.connect(("127.0.0.1", 1729))

    main()
