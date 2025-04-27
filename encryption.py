import functools


def rsa_encrypt(pk, plaintext):
    key, n = pk

    #Convert each letter in the plaintext to numbers based on the character using a^b mod m
    cipher = [(ord(char) ** key) % n for char in plaintext]
    #Return the array of bytes
    return functools.reduce(lambda x, y: f"{x},{y}", cipher)

def rsa_decrypt(pk, ciphertext):
    #Unpack the key into its components
    key, n = pk
    #Generate the plaintext based on the ciphertext and key using a^b mod m
    plain = [chr((char ** key) % n) for char in list(map(lambda x: int(x), ciphertext.split(",")))]
    #Return the array of bytes as a string
    return ''.join(plain)
