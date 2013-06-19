SALT_LENGTH = 32
DERIVATION_ROUNDS = 1337
BLOCK_SIZE = 16
KEY_SIZE = 32


def encrypt(password, plaintext):
    import hashlib
    import os
    from Crypto.Cipher import AES
    mode = AES.MODE_CBC
    salt = os.urandom(SALT_LENGTH)
    _iv = os.urandom(BLOCK_SIZE)
    padding_length = 16 - (len(plaintext) % 16)
    padded_plaintext = plaintext + chr(padding_length) * padding_length
    derived_key = password
    for _ in range(0, DERIVATION_ROUNDS):
        derived_key = hashlib.sha256('%s%s' % (str(derived_key),
                                               str(salt))).digest()
    derived_key = derived_key[:KEY_SIZE]
    cipher_spec = AES.new(derived_key, mode, _iv)
    ciphertext = cipher_spec.encrypt(padded_plaintext)
    ciphertext = ciphertext + _iv + salt
    return ciphertext.encode("hex")


def decrypt(password, ciphertext):
    """
    Using Hashlib and AES we will attempt password decryption
    """
    import hashlib
    from Crypto.Cipher import AES
    mode = AES.MODE_CBC
    decoded_ciphertext = ciphertext.decode("hex")
    start_iv = len(decoded_ciphertext) - BLOCK_SIZE - SALT_LENGTH
    start_salt = len(decoded_ciphertext) - SALT_LENGTH
    data, _iv, salt = (decoded_ciphertext[:start_iv],
                       decoded_ciphertext[start_iv:start_salt],
                       decoded_ciphertext[start_salt:])
    derived_key = password
    for _ in range(0, DERIVATION_ROUNDS):
        derived_key = hashlib.sha256('%s%s' % (str(derived_key),
                                               str(salt))).digest()
    derived_key = derived_key[:KEY_SIZE]
    cipher_spec = AES.new(derived_key, mode, _iv)
    plaintext_with_padding = cipher_spec.decrypt(data)
    padding_length = ord(plaintext_with_padding[-1])
    plaintext = plaintext_with_padding[:-padding_length]
    return plaintext
