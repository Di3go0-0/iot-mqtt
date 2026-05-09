import os
import uhashlib
import ubinascii
from ucryptolib import aes

# Diffie-Hellman parameters
DH_P = 104729
DH_G = 2

# ESP private key (hardcoded)
PRIVATE_KEY = 87321

# Server public key (pre-computed: pow(2, 52319, 104729))
PEER_PUBLIC_KEY = 19565


def _mod_pow(base, exp, mod):
    result = 1
    base = base % mod
    while exp > 0:
        if exp % 2 == 1:
            result = (result * base) % mod
        exp = exp >> 1
        base = (base * base) % mod
    return result


def _pkcs7_pad(data, block_size=16):
    pad_len = block_size - (len(data) % block_size)
    return data + bytes([pad_len] * pad_len)


def _pkcs7_unpad(data):
    pad_len = data[-1]
    return data[:-pad_len]


def init_crypto():
    public_key = _mod_pow(DH_G, PRIVATE_KEY, DH_P)
    shared_secret = _mod_pow(PEER_PUBLIC_KEY, PRIVATE_KEY, DH_P)

    h = uhashlib.sha256()
    h.update(str(shared_secret).encode("utf-8"))
    aes_key = h.digest()

    print("DH public key:", public_key)
    print("Shared secret establecido")

    return {"public_key": public_key, "aes_key": aes_key}


def encrypt_value(value, aes_key):
    plaintext = str(value).encode("utf-8")
    padded = _pkcs7_pad(plaintext)
    iv = os.urandom(16)
    cipher = aes(aes_key, 2, iv)
    ciphertext = cipher.encrypt(padded)
    return ubinascii.hexlify(iv).decode() + ":" + ubinascii.hexlify(ciphertext).decode()


def decrypt_value(encrypted_str, aes_key):
    iv_hex, ct_hex = encrypted_str.split(":")
    iv = ubinascii.unhexlify(iv_hex)
    ciphertext = ubinascii.unhexlify(ct_hex)
    cipher = aes(aes_key, 2, iv)
    padded = cipher.decrypt(ciphertext)
    plaintext = _pkcs7_unpad(padded)
    return plaintext.decode("utf-8")
