import os
import uhashlib
import ubinascii
from ucryptolib import aes

# Diffie-Hellman parameters
DH_P = 104729
DH_G = 2

# ESP private key
PRIVATE_KEY = 87321


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


def _hmac_sha256(key, message):
    block_size = 64
    if len(key) > block_size:
        h = uhashlib.sha256()
        h.update(key)
        key = h.digest()
    key = key + b'\x00' * (block_size - len(key))

    o_key_pad = bytes([k ^ 0x5c for k in key])
    i_key_pad = bytes([k ^ 0x36 for k in key])

    h_inner = uhashlib.sha256()
    h_inner.update(i_key_pad)
    h_inner.update(message)
    inner_hash = h_inner.digest()

    h_outer = uhashlib.sha256()
    h_outer.update(o_key_pad)
    h_outer.update(inner_hash)
    return h_outer.digest()


def get_public_key():
    return _mod_pow(DH_G, PRIVATE_KEY, DH_P)


def compute_shared_secret(peer_public_key):
    shared = _mod_pow(peer_public_key, PRIVATE_KEY, DH_P)
    h = uhashlib.sha256()
    h.update(str(shared).encode("utf-8"))
    return h.digest()


def encrypt(plaintext, aes_key):
    data = plaintext.encode("utf-8") if isinstance(plaintext, str) else plaintext
    padded = _pkcs7_pad(data)
    nonce = os.urandom(16)
    cipher = aes(aes_key, 2, nonce)
    ciphertext = cipher.encrypt(padded)

    tag = _hmac_sha256(aes_key, nonce + ciphertext)

    return (
        ubinascii.hexlify(ciphertext).decode(),
        ubinascii.hexlify(tag).decode(),
        ubinascii.hexlify(nonce).decode(),
    )


def decrypt(ciphertext_hex, tag_hex, nonce_hex, aes_key):
    ciphertext = ubinascii.unhexlify(ciphertext_hex)
    tag = ubinascii.unhexlify(tag_hex)
    nonce = ubinascii.unhexlify(nonce_hex)

    expected_tag = _hmac_sha256(aes_key, nonce + ciphertext)
    if tag != expected_tag:
        raise ValueError("Tag verification failed")

    cipher = aes(aes_key, 2, nonce)
    padded = cipher.decrypt(ciphertext)
    return _pkcs7_unpad(padded).decode("utf-8")
