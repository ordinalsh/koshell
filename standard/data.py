import csv
import json

from .helpers import expect_array, expect_string, guard


def _convert(value):
    text = str(value).strip()

    try:
        return int(text)
    except ValueError:
        pass

    try:
        return float(text)
    except ValueError:
        return value


def _convert_row(row, types):
    if not types:
        return dict(row)
    return {key: _convert(value) for key, value in row.items()}


class Data:
    def read_json(path):
        expect_string("data.read_json", path)

        with guard("data.read_json", ValueError):
            with open(path, "r", encoding="utf-8") as file:
                return json.load(file)

    def write_json(path, value, indent=2):
        expect_string("data.write_json", path)

        with guard("data.write_json", ValueError, TypeError):
            with open(path, "w", encoding="utf-8") as file:
                json.dump(value, file, indent=indent, ensure_ascii=False)

        return path

    def read_lines(path):
        expect_string("data.read_lines", path)

        with guard("data.read_lines", UnicodeDecodeError):
            with open(path, "r", encoding="utf-8") as file:
                return file.read().splitlines()

    def write_lines(path, lines, append=False):
        expect_string("data.write_lines", path)
        expect_array("data.write_lines", lines)
        mode = "a" if append else "w"

        with guard("data.write_lines"):
            with open(path, mode, encoding="utf-8") as file:
                for line in lines:
                    file.write(f"{line}\n")

        return path

    def read_csv(path, headers=True, types=False):
        expect_string("data.read_csv", path)
        rows = []

        with guard("data.read_csv", csv.Error):
            with open(path, "r", encoding="utf-8", newline="") as file:
                if headers:
                    for row in csv.DictReader(file):
                        rows.append(_convert_row(row, types))
                else:
                    for row in csv.reader(file):
                        rows.append([_convert(value) for value in row] if types else row)

        return rows

    def write_csv(path, rows, append=False):
        expect_string("data.write_csv", path)
        expect_array("data.write_csv", rows)
        mode = "a" if append else "w"

        with guard("data.write_csv", csv.Error):
            with open(path, mode, encoding="utf-8", newline="") as file:
                if not rows:
                    return path

                if isinstance(rows[0], dict):
                    writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
                    if not append:
                        writer.writeheader()
                    for row in rows:
                        writer.writerow(row)
                else:
                    writer = csv.writer(file)
                    for row in rows:
                        writer.writerow(expect_array("data.write_csv", row))

        return path
