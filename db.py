import sqlite3
import hashlib


def main():
    conn = sqlite3.connect("watchdog.db")
    conn.execute("PRAGMA foreign_keys = ON;")

    # create ACCOUNT table
    conn.execute(''' CREATE TABLE IF NOT EXISTS Account
                       ( name TEXT NOT NULL UNIQUE PRIMARY KEY,
                        password TEXT NOT NULL) ''')

    # create User table
    conn.execute(''' CREATE TABLE IF NOT EXISTS User
                     ( id INTEGER PRIMARY KEY AUTOINCREMENT,
                       name TEXT NOT NULL,
                       phone_number TEXT NOT NULL,
                       FOREIGN KEY(name) REFERENCES Account(name)) ''')

    # create Camera table
    conn.execute(''' CREATE TABLE IF NOT EXISTS Camera
                     ( id INTEGER PRIMARY KEY AUTOINCREMENT,
                       name TEXT NOT NULL,
                       linked_users TEXT NOT NULL, 
                       FOREIGN KEY(name) REFERENCES Account(name)) ''')

    conn.close()


def create_new_account(name, password):
    conn = sqlite3.connect("watchdog.db")
    result = None

    try:
        conn.execute('''
                       INSERT INTO Account (name, password)
                       VALUES(?,?)
                       ''', [name, hash_password(password)])
    except sqlite3.IntegrityError as e:
        result = e

    conn.commit()
    conn.close()

    if result is not None:
        raise result


def create_new_user(name, phone_num):
    conn = sqlite3.connect("watchdog.db")

    conn.execute("INSERT INTO User (name, phone_number) VALUES (?, ?)",
                 [name, phone_num])

    conn.commit()
    conn.close()


def create_new_camera(name):
    conn = sqlite3.connect("watchdog.db")

    conn.execute("INSERT INTO Camera (name, linked_users) VALUES (?, ?)",
                 [name, ""])

    conn.commit()
    conn.close()


def login(name, password):
    result = None
    conn = sqlite3.connect("watchdog.db")
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM Account WHERE name = ?', (name,))
    account = cursor.fetchone()

    if account:
        if account[1] == hash_password(password):
            pass # Password matches (hashed password matches hashed password)
        else:
            result = Exception("Wrong password")
    else:
        result = Exception("No such username")

    conn.close()

    if result is not None:
        raise result


def get_user_id(name):
    conn = sqlite3.connect("watchdog.db")
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM User WHERE name = ?', (name,))
    uid = cursor.fetchone()[0]

    conn.close()
    return uid


def get_camera_id(name):
    conn = sqlite3.connect("watchdog.db")
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM Camera WHERE name = ?', (name,))
    cid = cursor.fetchone()[0]

    conn.close()
    return cid


def get_account_type(name):
    conn = sqlite3.connect("watchdog.db")
    cursor = conn.cursor()
    result = ""

    cursor.execute('SELECT * FROM User WHERE name = ?', (name,))
    info = cursor.fetchone()

    if info is not None:
        result = "User"
    else:
        result = "Camera"

    conn.close()
    return result


def hash_password(password):
    password_hash = hashlib.sha256(b"salt" + password.encode()).hexdigest()
    return password_hash

if __name__ == "__main__":
    main()
