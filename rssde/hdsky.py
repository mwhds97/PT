#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import time

import feedparser
import yaml
from deluge_client import DelugeRPCClient


def print_t(text, eol="\n", sol="\x1b[2K"):
    print(
        sol + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + " " + text, end=eol
    )


def size_G(size_str):
    size = re.match(r"(.*) ([KMGT])?i?B", size_str).groups()
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


def NewClient(config):
    client = DelugeRPCClient(
        config["host"].split(":")[0],
        int(config["host"].split(":")[1]),
        config["user"],
        config["pass"],
        True,
        False,
    )
    return client


with open("hdsky.yaml", "r") as f:
    config = yaml.load(f, yaml.FullLoader)
client = NewClient(config)
client.connect()
while True:
    try:
        torrents = client.call(
            "core.get_torrents_status",
            {},
            ["hash", "total_size", "seeding_time", "tracker_status"],
        )
        print_t("连接正常", "\r")
        currentTotalSize = 0
        for t in list(torrents.values()):
            if (
                t["seeding_time"] >= config["str"] * t["total_size"] / 1073741824 * 60
                or "registered" in t["tracker_status"]
            ):
                client.call("core.remove_torrent", t["hash"], True)
                print_t("删除种子（{}GB）".format("%.2f" % (t["total_size"] / 1073741824)))
            else:
                currentTotalSize += t["total_size"] / 1073741824
        feed = feedparser.parse(config["rss"])
        entries = [
            {
                "time": time.mktime(time.gmtime()) - time.mktime(f["published_parsed"]),
                "size": size_G(re.match(r"^.*\[(.*)\]$", f["title"]).groups()[0]),
                "link": f["links"][1]["href"],
            }
            for f in feed["entries"]
        ]
        entries = list(
            filter(
                lambda e: e["time"] <= config["publish"]
                and config["size"][0] <= e["size"] <= config["size"][1],
                entries,
            )
        )
        entries.sort(key=lambda e: e["size"], reverse=True)
        for e in entries:
            if currentTotalSize + e["size"] <= config["space"]:
                try:
                    client.call(
                        "core.add_torrent_url",
                        e["link"],
                        {"download_location": config["path"]},
                    )
                    currentTotalSize += e["size"]
                    print_t(
                        "添加种子（{}GB），总体积 {}GB".format(
                            "%.2f" % e["size"], "%.2f" % currentTotalSize
                        )
                    )
                except Exception as e:
                    if not "Torrent already in session" in repr(e):
                        raise Exception
        time.sleep(config["interval"])
    except KeyboardInterrupt:
        client.disconnect()
        break
    except:
        print_t("出现异常，尝试重连", "\r")
        try:
            client.disconnect()
            client = NewClient(config)
            client.connect()
            time.sleep(10)
        except KeyboardInterrupt:
            client.disconnect()
            break
        except:
            pass
