import os
import hashlib
import hmac
from Crypto.Cipher import AES

# DH parameters (must match server and ESP)
DH_P = 104729
DH_G = 2

# Bot private key (different from ESP and server)
PRIVATE_KEY = 63147


def get_public_key():
    return pow(DH_G, PRIVATE_KEY, DH_P)


def compute_shared_secret(peer_public_key):
    shared = pow(peer_public_key, PRIVATE_KEY, DH_P)
    return hashlib.sha256(str(shared).encode("utf-8")).digest()


def _pkcs7_pad(data, block_size=16):
    pad_len = block_size - (len(data) % block_size)
    return data + bytes([pad_len] * pad_len)


def _pkcs7_unpad(data):
    pad_len = data[-1]
    return data[:-pad_len]


def encrypt(plaintext, aes_key):
    data = plaintext.encode("utf-8") if isinstance(plaintext, str) else plaintext
    padded = _pkcs7_pad(data)
    nonce = os.urandom(16)

    cipher = AES.new(aes_key, AES.MODE_CBC, nonce)
    ciphertext = cipher.encrypt(padded)

    tag = hmac.new(aes_key, nonce + ciphertext, hashlib.sha256).digest()

    return ciphertext.hex(), tag.hex(), nonce.hex()


def decrypt(ciphertext_hex, tag_hex, nonce_hex, aes_key):
    ciphertext = bytes.fromhex(ciphertext_hex)
    tag = bytes.fromhex(tag_hex)
    nonce = bytes.fromhex(nonce_hex)

    expected_tag = hmac.new(aes_key, nonce + ciphertext, hashlib.sha256).digest()
    if not hmac.compare_digest(tag, expected_tag):
        raise ValueError("Tag verification failed")

    cipher = AES.new(aes_key, AES.MODE_CBC, nonce)
    padded = cipher.decrypt(ciphertext)
    return _pkcs7_unpad(padded).decode("utf-8")
