import base64
import binascii
import hashlib
import hmac as hmac_module
import secrets
import string as string_module
import urllib.parse
import uuid as uuid_module

from koskript import Errors

from .helpers import expect_int, expect_string, guard


def _digest(algorithm):
    if algorithm not in hashlib.algorithms_available or algorithm.startswith("shake"):
        raise Errors.RuntimeError(f"codec() unknown hash algorithm '{algorithm}'")
    return algorithm


class Codec:
    def base64_encode(text):
        expect_string("codec.base64_encode", text)
        return base64.b64encode(text.encode("utf-8")).decode("ascii")

    def base64_decode(text):
        expect_string("codec.base64_decode", text)

        with guard("codec.base64_decode", binascii.Error):
            return base64.b64decode(text, validate=True).decode("utf-8", errors="replace")

    def base64_url_encode(text):
        expect_string("codec.base64_url_encode", text)
        return base64.urlsafe_b64encode(text.encode("utf-8")).decode("ascii")

    def base64_url_decode(text):
        expect_string("codec.base64_url_decode", text)

        with guard("codec.base64_url_decode", binascii.Error):
            return base64.urlsafe_b64decode(text).decode("utf-8", errors="replace")

    def hex_encode(text):
        expect_string("codec.hex_encode", text)
        return text.encode("utf-8").hex()

    def hex_decode(text):
        expect_string("codec.hex_decode", text)

        with guard("codec.hex_decode", ValueError):
            return bytes.fromhex(text).decode("utf-8", errors="replace")

    def url_encode(text):
        expect_string("codec.url_encode", text)
        return urllib.parse.quote(text, safe="")

    def url_decode(text):
        expect_string("codec.url_decode", text)
        return urllib.parse.unquote(text)

    def hash(text, algorithm="sha256"):
        expect_string("codec.hash", text)
        expect_string("codec.hash", algorithm)
        return hashlib.new(_digest(algorithm), text.encode("utf-8")).hexdigest()

    def hash_file(path, algorithm="sha256"):
        expect_string("codec.hash_file", path)
        expect_string("codec.hash_file", algorithm)
        hasher = hashlib.new(_digest(algorithm))

        with guard("codec.hash_file"):
            with open(path, "rb") as file:
                for chunk in iter(lambda: file.read(65536), b""):
                    hasher.update(chunk)

        return hasher.hexdigest()

    def sign(text, key, algorithm="sha256"):
        expect_string("codec.sign", text)
        expect_string("codec.sign", key)
        expect_string("codec.sign", algorithm)
        return hmac_module.new(
            key.encode("utf-8"), text.encode("utf-8"), _digest(algorithm)).hexdigest()

    def equals(left, right):
        return secrets.compare_digest(str(left), str(right))

    def uuid():
        return str(uuid_module.uuid4())

    def uuid5(text):
        expect_string("codec.uuid5", text)
        return str(uuid_module.uuid5(uuid_module.NAMESPACE_URL, text))

    def token(length=32):
        expect_int("codec.token", length)
        return secrets.token_hex((length + 1) // 2)[:length]

    def password(length=16, symbols=True):
        expect_int("codec.password", length)
        alphabet = string_module.ascii_letters + string_module.digits

        if symbols:
            alphabet += "!@#$%^&*()-_=+"

        return "".join(secrets.choice(alphabet) for _ in range(length))
