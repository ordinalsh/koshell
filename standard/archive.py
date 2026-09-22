import os
import tarfile
import zipfile
from datetime import datetime

from koskript import Errors

from .helpers import expect_array, expect_string, guard

_ZIP_COMPRESSION = {
    "stored": zipfile.ZIP_STORED,
    "deflated": zipfile.ZIP_DEFLATED,
    "bzip2": zipfile.ZIP_BZIP2,
    "lzma": zipfile.ZIP_LZMA,
}

_TAR_COMPRESSION = {
    "none": "w",
    "gz": "w:gz",
    "bz2": "w:bz2",
    "xz": "w:xz",
}


def _sources(source):
    if isinstance(source, str):
        return [source]

    expect_array("archive", source)
    return [str(item) for item in source]


def _zip_mode(compression):
    if compression not in _ZIP_COMPRESSION:
        raise Errors.MismatchType(
            "archive() expected compression 'stored', 'deflated', 'bzip2' or 'lzma'")

    return _ZIP_COMPRESSION[compression]


def _tar_mode(path, compression):
    if compression is None:
        lower = path.lower()
        if lower.endswith((".tar.bz2", ".tbz2")):
            compression = "bz2"
        elif lower.endswith((".tar.xz", ".txz")):
            compression = "xz"
        elif lower.endswith((".tar",)):
            compression = "none"
        else:
            compression = "gz"

    if compression not in _TAR_COMPRESSION:
        raise Errors.MismatchType(
            "archive() expected compression 'none', 'gz', 'bz2' or 'xz'")

    return _TAR_COMPRESSION[compression]


def _require(name, path):
    if not os.path.exists(path):
        raise Errors.RuntimeError(f"{name}() path does not exist: {path}")


def _is_tar(path):
    try:
        return tarfile.is_tarfile(path)
    except OSError:
        return False


def _add_zip_path(archive, path):
    if os.path.isdir(path):
        count = 0
        base = os.path.dirname(os.path.abspath(path))
        for root, dirs, files in os.walk(path):
            for name in files:
                full = os.path.join(root, name)
                archive.write(full, os.path.relpath(full, base))
                count += 1
        return count

    archive.write(path, os.path.basename(path))
    return 1


def _add_tar_path(archive, path):
    if os.path.isdir(path):
        count = 0
        for root, dirs, files in os.walk(path):
            for name in files:
                full = os.path.join(root, name)
                archive.add(full, arcname=os.path.relpath(full, os.path.dirname(os.path.abspath(path))))
                count += 1
        return count

    archive.add(path, arcname=os.path.basename(path))
    return 1


class Archive:
    def zip_create(path, source, compression="deflated"):
        expect_string("archive.zip_create", path)
        mode = _zip_mode(compression)
        entries = 0

        with guard("archive.zip_create", zipfile.BadZipFile):
            with zipfile.ZipFile(path, "w", compression=mode) as archive:
                for item in _sources(source):
                    entries += _add_zip_path(archive, item)

        return {"path": path, "entries": entries}

    def zip_add(path, source):
        expect_string("archive.zip_add", path)
        entries = 0

        with guard("archive.zip_add", zipfile.BadZipFile):
            with zipfile.ZipFile(path, "a") as archive:
                for item in _sources(source):
                    entries += _add_zip_path(archive, item)

        return {"path": path, "entries": entries}

    def zip_extract(path, destination="."):
        expect_string("archive.zip_extract", path)
        expect_string("archive.zip_extract", destination)

        with guard("archive.zip_extract", zipfile.BadZipFile):
            with zipfile.ZipFile(path) as archive:
                names = archive.namelist()
                archive.extractall(destination)

        return names

    def zip_list(path):
        expect_string("archive.zip_list", path)

        with guard("archive.zip_list", zipfile.BadZipFile):
            with zipfile.ZipFile(path) as archive:
                return [
                    {
                        "name": info.filename,
                        "size": info.file_size,
                        "compressed": info.compress_size,
                        "modified": datetime(*info.date_time).timestamp(),
                        "dir": info.is_dir(),
                    }
                    for info in archive.infolist()
                ]

    def tar_create(path, source, compression=None):
        expect_string("archive.tar_create", path)
        mode = _tar_mode(path, compression)
        entries = 0

        with guard("archive.tar_create", tarfile.TarError):
            with tarfile.open(path, mode) as archive:
                for item in _sources(source):
                    entries += _add_tar_path(archive, item)

        return {"path": path, "entries": entries}

    def tar_extract(path, destination="."):
        expect_string("archive.tar_extract", path)
        expect_string("archive.tar_extract", destination)

        with guard("archive.tar_extract", tarfile.TarError):
            with tarfile.open(path) as archive:
                names = archive.getnames()
                try:
                    archive.extractall(destination, filter="data")
                except TypeError:
                    archive.extractall(destination)

        return names

    def tar_list(path):
        expect_string("archive.tar_list", path)

        with guard("archive.tar_list", tarfile.TarError):
            with tarfile.open(path) as archive:
                return [
                    {
                        "name": member.name,
                        "size": member.size,
                        "compressed": None,
                        "modified": member.mtime,
                        "dir": member.isdir(),
                    }
                    for member in archive.getmembers()
                ]

    def pack(path, source):
        expect_string("archive.pack", path)
        lower = path.lower()

        if lower.endswith(".zip"):
            return Archive.zip_create(path, source)

        if lower.endswith((".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tbz2", ".tar.xz", ".txz")):
            return Archive.tar_create(path, source)

        raise Errors.RuntimeError(
            f"archive.pack() cannot detect the archive format of '{path}'")

    def unpack(path, destination="."):
        expect_string("archive.unpack", path)
        expect_string("archive.unpack", destination)
        _require("archive.unpack", path)

        if zipfile.is_zipfile(path):
            return Archive.zip_extract(path, destination)

        if _is_tar(path):
            return Archive.tar_extract(path, destination)

        raise Errors.RuntimeError(f"archive.unpack() '{path}' is not a zip or tar archive")

    def contains(path, member):
        expect_string("archive.contains", path)
        expect_string("archive.contains", member)
        _require("archive.contains", path)

        if zipfile.is_zipfile(path):
            with guard("archive.contains", zipfile.BadZipFile):
                with zipfile.ZipFile(path) as archive:
                    return member in archive.namelist()

        if _is_tar(path):
            with guard("archive.contains", tarfile.TarError):
                with tarfile.open(path) as archive:
                    return member in archive.getnames()

        raise Errors.RuntimeError(f"archive.contains() '{path}' is not a zip or tar archive")

    def read(path, member):
        expect_string("archive.read", path)
        expect_string("archive.read", member)
        _require("archive.read", path)

        if zipfile.is_zipfile(path):
            with guard("archive.read", zipfile.BadZipFile, KeyError):
                with zipfile.ZipFile(path) as archive:
                    return archive.read(member).decode("utf-8", errors="replace")

        if _is_tar(path):
            with guard("archive.read", tarfile.TarError, KeyError):
                with tarfile.open(path) as archive:
                    extracted = archive.extractfile(member)

                    if extracted is None:
                        raise Errors.RuntimeError(
                            f"archive.read() member '{member}' not found in '{path}'")

                    return extracted.read().decode("utf-8", errors="replace")

        raise Errors.RuntimeError(f"archive.read() '{path}' is not a zip or tar archive")
