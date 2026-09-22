import json as json_module
import socket
import time

import requests
from koskript import Errors

from .helpers import expect_map, expect_number, expect_string, type_name


def _perform(action, method, url, options):
    start = time.time()

    try:
        response = requests.request(method, url, **options)
    except requests.Timeout:
        raise Errors.RuntimeError(
            f"network.{action}() timed out after {options.get('timeout')} second(s)") from None
    except requests.RequestException as error:
        raise Errors.RuntimeError(f"network.{action}() failed: {error}") from None

    return {
        "ok": response.status_code < 400,
        "status": response.status_code,
        "reason": response.reason or "",
        "text": response.text,
        "url": response.url,
        "headers": dict(response.headers),
        "elapsed": time.time() - start,
    }


def _options(name, headers, params, data, payload, timeout):
    expect_number(name, timeout)

    if headers is not None:
        expect_map(name, headers)
    if params is not None:
        expect_map(name, params)
    if data is not None and not isinstance(data, (str, dict, list)):
        raise Errors.MismatchType(
            f"{name}() expected a string, map or array for data, got {type_name(data)}")

    return {"headers": headers, "params": params, "data": data, "json": payload, "timeout": timeout}


class Network:
    def request(method, url, headers=None, params=None, data=None, json=None, timeout=10):
        expect_string("network.request", method)
        expect_string("network.request", url)
        options = _options("network.request", headers, params, data, json, timeout)
        return _perform("request", method.upper(), url, options)

    def get(url, headers=None, timeout=10):
        expect_string("network.get", url)
        options = _options("network.get", headers, None, None, None, timeout)
        return _perform("get", "GET", url, options)

    def post(url, data=None, json=None, headers=None, timeout=10):
        expect_string("network.post", url)
        options = _options("network.post", headers, None, data, json, timeout)
        return _perform("post", "POST", url, options)

    def put(url, data=None, json=None, headers=None, timeout=10):
        expect_string("network.put", url)
        options = _options("network.put", headers, None, data, json, timeout)
        return _perform("put", "PUT", url, options)

    def patch(url, data=None, json=None, headers=None, timeout=10):
        expect_string("network.patch", url)
        options = _options("network.patch", headers, None, data, json, timeout)
        return _perform("patch", "PATCH", url, options)

    def delete(url, headers=None, timeout=10):
        expect_string("network.delete", url)
        options = _options("network.delete", headers, None, None, None, timeout)
        return _perform("delete", "DELETE", url, options)

    def head(url, headers=None, timeout=10):
        expect_string("network.head", url)
        options = _options("network.head", headers, None, None, None, timeout)
        return _perform("head", "HEAD", url, options)

    def get_json(url, headers=None, timeout=10):
        result = Network.get(url, headers, timeout)

        try:
            return json_module.loads(result["text"])
        except ValueError:
            raise Errors.RuntimeError(
                f"network.get_json() response from '{url}' is not valid JSON") from None

    def post_json(url, value, headers=None, timeout=10):
        result = Network.post(url, None, value, headers, timeout)

        try:
            return json_module.loads(result["text"])
        except ValueError:
            raise Errors.RuntimeError(
                f"network.post_json() response from '{url}' is not valid JSON") from None

    def download(url, path, timeout=60):
        expect_string("network.download", url)
        expect_string("network.download", path)
        expect_number("network.download", timeout)

        size = 0
        status = 0

        try:
            with requests.get(url, stream=True, timeout=timeout) as response:
                response.raise_for_status()
                status = response.status_code

                with open(path, "wb") as file:
                    for chunk in response.iter_content(chunk_size=65536):
                        file.write(chunk)
                        size += len(chunk)
        except requests.RequestException as error:
            raise Errors.RuntimeError(f"network.download() failed: {error}") from None
        except OSError as error:
            raise Errors.RuntimeError(
                f"network.download() failed: {error.strerror or error}") from None

        return {"ok": True, "path": path, "size": size, "status": status}

    def is_online(host="1.1.1.1", port=53, timeout=2):
        expect_string("network.is_online", host)
        expect_number("network.is_online", timeout)

        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            return False

    def port_open(host, port, timeout=1):
        expect_string("network.port_open", host)
        expect_number("network.port_open", timeout)

        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            return False

    def resolve(host):
        expect_string("network.resolve", host)

        try:
            return socket.gethostbyname(host)
        except OSError:
            return None

    def local_ip():
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            try:
                sock.connect(("8.8.8.8", 80))
                return sock.getsockname()[0]
            except OSError:
                return "127.0.0.1"

    def public_ip(timeout=5):
        expect_number("network.public_ip", timeout)

        try:
            response = requests.get("https://api.ipify.org", timeout=timeout)
            response.raise_for_status()
        except requests.RequestException:
            return None

        return response.text.strip()
