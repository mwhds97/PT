#!/usr/bin/env python3
#coding=utf-8

import re
import time

import feedparser
import requests
import yaml
from bs4 import BeautifulSoup
from deluge_client import DelugeRPCClient


def print_t(text, eol="\n", sol="\x1b[2K"):
    print(
        sol + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + " " + text, end=eol
    )


def size_G(size_str):
    size = re.match(r"(\d+(?:\.\d+)?)[\n\s]*([KMGT])?i?B", size_str).groups()
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
    return DelugeRPCClient(
        config["host"].split(":")[0],
        int(config["host"].split(":")[1]),
        config["user"],
        config["pass"],
        True,
        False,
    )


def RemoveTorrent(torrent, info):
    if torrent["hash"] in eod:
        del eod[torrent["hash"]]
    client.call("core.remove_torrent", torrent["hash"], True)
    print_t("删除种子（{:.2f}GB），原因：{}".format(torrent["total_size"] / 1073741824, info))


with open("hdsky.yaml", "r") as f:
    config = yaml.load(f, yaml.FullLoader)
client = NewClient(config)
client.connect()
eod = {}
while True:
    try:
        feed = feedparser.parse(config["rss"])
        entries = [
            {
                "id": re.search(r"id=(\d+)", f["link"]).group(1),
                "hash": f["id"],
                "time": time.mktime(time.gmtime()) - time.mktime(f["published_parsed"]),
                "size": size_G(re.search(r"\[(.*)\]$", f["title"]).group(1)),
                "link": f["links"][1]["href"],
                "free": False,
                "end": None,
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
        if config["free"]:
            response = requests.get(
                "https://hdsky.me/torrents.php",
                headers={
                    "user-agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36"
                },
                cookies=config["cookie"],
                timeout=15,
            )
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "lxml")
                rows = soup.find_all("tr", class_="progresstr")
                for r in rows:
                    id = re.search("id=(\d+)\D", str(r)).group(1)
                    for e in entries:
                        if e["id"] == id:
                            if 'alt="Free"' in str(r) and not "即将结束" in str(r):
                                e["free"] = True
                                end = re.search(r"<b><span title=\"(.*?)\"", str(r))
                                e["end"] = (
                                    None
                                    if end == None
                                    else time.mktime(
                                        time.strptime(end.group(1), "%Y-%m-%d %H:%M:%S")
                                    )
                                )
                                if e["hash"] in eod:
                                    eod[e["hash"]] = e["end"]
                            else:
                                if e["hash"] in eod:
                                    eod[e["hash"]] = 0
                            break
            entries = list(filter(lambda e: e["free"], entries))
    except:
        pass
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
                config["free"]
                and t["seeding_time"] == 0
                and eod[t["hash"]] != None
                and eod[t["hash"]] - time.mktime(time.localtime()) <= config["interval"]
            ):
                RemoveTorrent(t, "免费到期")
            elif t["seeding_time"] >= config["str"] * t["total_size"] / 1073741824 * 60:
                RemoveTorrent(t, "做种时间达到要求")
            elif "registered" in t["tracker_status"]:
                RemoveTorrent(t, "种子被撤回")
            else:
                currentTotalSize += t["total_size"] / 1073741824
        for e in entries:
            if config["free"] and e["free"] or not config["free"]:
                if currentTotalSize + e["size"] <= config["space"]:
                    try:
                        if config["free"]:
                            eod[e["hash"]] = e["end"]
                        client.call(
                            "core.add_torrent_url",
                            e["link"],
                            {"download_location": config["path"]},
                        )
                        currentTotalSize += e["size"]
                        print_t(
                            "添加种子（{:.2f}GB），总体积 {:.2f}GB".format(
                                e["size"], currentTotalSize
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
