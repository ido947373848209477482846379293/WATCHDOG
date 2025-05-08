import sqlite3
import hashlib
from encryption import *
import constants
import functools
import random


def main():
    conn = sqlite3.connect("watchdog.db")
    conn.execute("PRAGMA foreign_keys = ON;")

    # create Account table
    conn.execute(''' CREATE TABLE IF NOT EXISTS Account
                       ( name TEXT NOT NULL UNIQUE PRIMARY KEY,
                        password TEXT NOT NULL) ''')

    # create User table
    conn.execute(''' CREATE TABLE IF NOT EXISTS User
                     ( id INTEGER PRIMARY KEY AUTOINCREMENT,
                       name TEXT NOT NULL,
                       chat_id TEXT NOT NULL,
                       FOREIGN KEY(name) REFERENCES Account(name)) ''')

    # create Camera table
    conn.execute(''' CREATE TABLE IF NOT EXISTS Camera
                     ( id INTEGER PRIMARY KEY AUTOINCREMENT,
                       name TEXT NOT NULL,
                       linked_users TEXT NOT NULL, 
                       FOREIGN KEY(name) REFERENCES Account(name)) ''')

    # create / delete and create Telegram chat ID to verification code table
    conn.execute('''DROP TABLE IF EXISTS ChatIDs''')
    conn.execute(''' CREATE TABLE IF NOT EXISTS ChatIDs
                     ( chat_id TEXT NOT NULL,
                       verif_code TEXT NOT NULL ) ''')

    conn.close()


def create_new_account(name, password):
    conn = sqlite3.connect("watchdog.db")
    result = None

    try:
        conn.execute('''
                       INSERT INTO Account (name, password)
                       VALUES(?,?)
                       ''', [rsa_encrypt(constants.server_to_db_public_key, name), hash_password(password)])
    except sqlite3.IntegrityError as e:
        result = e

    conn.commit()
    conn.close()

    if result is not None:
        raise result


def create_new_user(name, chat_id):
    conn = sqlite3.connect("watchdog.db")

    conn.execute("INSERT INTO User (name, chat_id) VALUES (?, ?)",
                 [rsa_encrypt(constants.server_to_db_public_key, name), rsa_encrypt(constants.server_to_db_public_key, chat_id)])

    conn.commit()
    conn.close()


def create_new_camera(name):
    conn = sqlite3.connect("watchdog.db")

    conn.execute("INSERT INTO Camera (name, linked_users) VALUES (?, ?)",
                 [rsa_encrypt(constants.server_to_db_public_key, name), ""])

    conn.commit()
    conn.close()


def create_new_chat_id_verif_code(chat_id, verif_code):
    conn = sqlite3.connect("watchdog.db")

    conn.execute("INSERT INTO ChatIDs (chat_id, verif_code) VALUES (?, ?)",
                 [rsa_encrypt(constants.server_to_db_public_key, chat_id), rsa_encrypt(constants.server_to_db_public_key, verif_code)])

    conn.commit()
    conn.close()


def login(name, password):
    result = None
    conn = sqlite3.connect("watchdog.db")
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM Account WHERE name = ?', (rsa_encrypt(constants.server_to_db_public_key, name),))
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


def get_chat_id_from_verif_code(verif_code):
    conn = sqlite3.connect("watchdog.db")
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM ChatIDs WHERE verif_code = ?', (rsa_encrypt(constants.server_to_db_public_key, verif_code),))
    chat_id = rsa_decrypt(constants.server_to_db_private_key, cursor.fetchone()[0])

    conn.close()
    return chat_id

def get_chat_id(name):
    conn = sqlite3.connect("watchdog.db")
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM User WHERE name = ?', (rsa_encrypt(constants.server_to_db_public_key, name),))
    chat_id = rsa_decrypt(constants.server_to_db_private_key, cursor.fetchone()[2])

    conn.close()
    return chat_id


def get_user_id(name):
    conn = sqlite3.connect("watchdog.db")
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM User WHERE name = ?', (rsa_encrypt(constants.server_to_db_public_key, name),))
    uid = cursor.fetchone()[0]

    conn.close()
    return uid


def get_camera_id(name):
    conn = sqlite3.connect("watchdog.db")
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM Camera WHERE name = ?', (rsa_encrypt(constants.server_to_db_public_key, name),))
    cid = cursor.fetchone()[0]

    conn.close()
    return cid


def get_account_type(name):
    conn = sqlite3.connect("watchdog.db")
    cursor = conn.cursor()
    result = ""

    cursor.execute('SELECT * FROM User WHERE name = ?', (rsa_encrypt(constants.server_to_db_public_key, name),))
    info = cursor.fetchone()

    if info is not None:
        result = "User"
    else:
        result = "Camera"

    conn.close()
    return result


def get_camera_subscriptions(cid):
    conn = sqlite3.connect("watchdog.db")
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM Camera WHERE id = ?', (cid,))
    linked_users = cursor.fetchone()[2]
    if linked_users == '':
        subs = []
    else:
        subs = rsa_decrypt(constants.server_to_db_private_key, linked_users).split(',')

    conn.close()
    return subs


def subscribe_to_camera(username, cid):
    subs = get_camera_subscriptions(cid)
    print(subs)
    subs.append(username)
    subs = list(set(subs))
    subs_to_db = functools.reduce(lambda x, y: f"{x},{y}", subs)
    print(subs_to_db)

    conn = sqlite3.connect("watchdog.db")
    cursor = conn.cursor()

    cursor.execute('UPDATE Camera SET linked_users = ? WHERE id = ?', (rsa_encrypt(constants.server_to_db_public_key, subs_to_db), cid))
    conn.commit()
    conn.close()


def hash_password(password):
    password_hash = hashlib.sha256(b"arbitrary" + password.encode()).hexdigest()
    return password_hash

if __name__ == "__main__":
    main()
