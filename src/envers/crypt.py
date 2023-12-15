"""Functions for cryptography."""
from __future__ import annotations

import base64
import os

from typing import cast

import typer

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

SALT_LENGTH = 16


def create_fernet_key(password: str, salt: bytes) -> bytes:
    """Create a Fernet key."""
    # Use PBKDF2HMAC to derive a Fernet-compatible key from the user password
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend(),
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


def get_password() -> str:
    """Prompt a password."""
    return cast(str, typer.prompt("Enter your password", hide_input=True))


def generate_salt() -> bytes:
    """Generate a salt in byte format."""
    return os.urandom(SALT_LENGTH)


def encrypt_data(data: str, password: str = "") -> str:
    """Encrypt the given data."""
    if not password:
        password = get_password()

    salt = generate_salt()
    salt_hex = salt.hex()
    key = create_fernet_key(password, salt)
    cipher_suite = Fernet(key)

    encrypted = cipher_suite.encrypt(data.encode("utf-8")).decode("utf-8")
    return salt_hex + encrypted


def decrypt_data(data: str, password: str = "") -> str:
    """Decrypt the given data."""
    if not password:
        password = get_password()

    HEX_SALT_LENGTH = SALT_LENGTH * 2

    salt_hex, data_clean = data[:HEX_SALT_LENGTH], data[HEX_SALT_LENGTH:]
    salt = bytes.fromhex(salt_hex)

    key = create_fernet_key(password, salt)
    cipher_suite = Fernet(key)

    return cipher_suite.decrypt(data_clean.encode("utf-8")).decode("utf-8")
