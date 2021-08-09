import re
import time

import yaml


def print_t(text, nowrap=False, logger=None):
    full_text = "\r" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + " " + text
    print(
        f"{full_text: <75}",
        end="" if nowrap else "\n",
    )
    if logger != None:
        log_text = (
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + " " + text + "\n"
        )
        logger.write(log_text)


def size_G(size_str):
    size = re.match("(\d+(?:\.\d+)?)[\n\s]*([KMGT])?i?B", size_str).groups()
    if size[1] == None:
        return float(size[0]) / 1073741824
    elif size[1] == "K":
        return float(size[0]) / 1048576
    elif size[1] == "M":
        return float(size[0]) / 1024
    elif size[1] == "G":
        return float(size[0])
    else:
        return float(size[0]) * 1024


def filter_regexp(torrent, patterns):
    for pattern in patterns:
        if re.search(pattern, torrent["title"]) != None:
            return True
    return False


def filter_size(torrent, ranges):
    for range in ranges:
        if range[0] <= torrent["size"] <= range[1]:
            return True
    return False


def yaml_read(file_name):
    try:
        with open(file_name, "r", encoding="utf-8") as file:
            return yaml.load(file, yaml.FullLoader)
    except FileNotFoundError:
        return {}


def yaml_dump(data, file_name):
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
