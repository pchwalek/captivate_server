from cryptography.fernet import Fernet


key = b'1UmspHQ7FFAa9uQpst6DUE2qFgDJ8uQZkvo_pzlfcNs='

def do_encrypt(message):
    global key

    f = Fernet(key)

    # print("encrypt input")
    # print(message)

    try:
        if isinstance(message, (bytes)):
            encrypted_message = f.encrypt(message)
        elif isinstance(message, (str)):
            encrypted_message = f.encrypt(bytes(message, 'utf-8'))
        else:
            raise Exception('input to \"do_encrypt()\" not byte or string type')
    except Exception as inst:
        print(inst)
    #
    # print("encrypted")
    # print(encrypted_message)

    return encrypted_message

def do_decrypt(ciphertext):
    global key

    # print("decrypt input")
    # print(ciphertext)

    f = Fernet(key)
    decrypted_message = f.decrypt(ciphertext)

    # print("decrypted")
    # print(decrypted_message)

    return decrypted_message
