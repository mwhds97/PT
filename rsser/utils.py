import re
import time
from io import TextIOWrapper
from typing import Union

import yaml


def print_t(text: str, nowrap: bool = False, logger: Union[TextIOWrapper, None] = None):
    full_text = "\r" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + " " + text
    print(
        f"{full_text: <75}",
        end="" if nowrap else "\n",
    )
    if logger is not None:
        log_text = (
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + " " + text + "\n"
        )
        logger.write(log_text)


def size_G(size_str: str) -> float:
    size = re.match(r"(\d+(?:\.\d+)?)[\n\s]*([KMGT])?i?B", size_str).groups()
    if size[1] is None:
        return float(size[0]) / 1073741824
    elif size[1] == "K":
        return float(size[0]) / 1048576
    elif size[1] == "M":
        return float(size[0]) / 1024
    elif size[1] == "G":
        return float(size[0])
    else:
        return float(size[0]) * 1024


def yaml_read(file_name: str) -> Union[dict, list]:
    try:
        with open(file_name, "r", encoding="utf-8") as file:
            return yaml.load(file, yaml.FullLoader)
    except Exception:
        return {}


def yaml_dump(data: Union[dict, list], file_name: str):
    with open(file_name, "w", encoding="utf-8", newline="\n") as file:
        yaml.dump(
            data,
            file,
            default_flow_style=False,
            allow_unicode=True,
            line_break="\n",
            encoding="utf-8",
            sort_keys=False,
        )


def compare_version(ver_a: str, ver_b: str) -> bool:
    ver_a = [int(n) for n in re.sub(r"[^\d\.]", "", ver_a).split(".") if n != ""]
    ver_b = [int(n) for n in re.sub(r"[^\d\.]", "", ver_b).split(".") if n != ""]
    for i in range(min(len(ver_a), len(ver_b))):
        if ver_a[i] > ver_b[i]:
            return True
        if ver_a[i] < ver_b[i]:
            return False
    if len(ver_a) >= len(ver_b):
        return True
    return False
