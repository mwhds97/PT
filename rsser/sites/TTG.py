import math
import random
import re
import time

import feedparser
import requests
from bs4 import BeautifulSoup

from utils import *


def TTG(config: dict) -> dict:
    response = requests.get(
        config["rss"],
        proxies=config["proxies"],
        timeout=config["rss_timeout"],
    )
    if response.status_code == 200:
        feed = feedparser.parse(response.text)
    else:
        raise Exception
    torrents = {}
    for entry in feed["entries"]:
        title_size = re.match(r"(.+) (\d+(?:\.\d+)? \w+?)$", entry["title"]).groups()
        torrents[re.search(r"id=(\d+)", entry["link"]).group(1)] = {
            "site": "TTG",
            "title": title_size[0],
            "size": size_G(title_size[1]),
            "publish_time": time.mktime(entry["published_parsed"]) - time.timezone,
            "link": entry["links"][1]["href"],
        }
    if config["web"] == []:
        return {
            "[TTG]"
            + id: {
                **torrent,
                **{
                    "free": False,
                    "free_end": None,
                    "hr": None,
                    "downloaded": False,
                    "seeder": -1,
                    "leecher": -1,
                    "snatch": -1,
                },
            }
            for id, torrent in torrents.items()
        }
    """ web_info_all = {}
    for index, url in enumerate(config["web"]):
        response = requests.get(
            url,
            headers={"User-Agent": config["user_agent"]},
            cookies=config["cookies"],
            proxies=config["proxies"],
            timeout=config["web_timeout"],
        )
        if response.status_code == 200:
            soup = BeautifulSoup(response.content.decode("utf-8"), "lxml")
            rows = soup.find("table", id="torrent_table").find_all(
                "tr", recursive=False
            )
            if rows == []:
                raise Exception
            for row in rows[1:]:
                cols = row.find_all("td", recursive=False)
                if len(cols) >= 10:
                    id = re.search(r'tid="(\d+)"', str(cols[1])).group(1)
                    web_info = {
                        "free": False,
                        "free_end": None,
                        "hr": None,
                        "downloaded": False,
                        "seeder": -1,
                        "leecher": -1,
                        "snatch": -1,
                    }
                    if cols[1].find("img", alt="free") is not None:
                        web_info["free"] = True
                        free_end = re.search(
                            r"javascript:alert.+(\d{4}年\d{2}月\d{2}日\d{2}点\d{2}分)",
                            str(cols[1]),
                        )
                        web_info["free_end"] = (
                            None
                            if free_end is None
                            else time.mktime(
                                time.strptime(free_end.group(1), "%Y年%m月%d日%H点%M分")
                            )
                            - time.timezone
                            - config["timezone"] * 3600
                        )
                    if cols[1].find("img", title="Hit and Run") is not None:
                        web_info["hr"] = (
                            86400
                            if re.search(r"第\d+[集话話周週]|EP?\d+(?!-)", str(cols[1]))
                            is not None
                            else 216000
                        )
                    if cols[1].find("div", class_="process") is not None:
                        web_info["downloaded"] = True
                    web_info["snatch"] = int(re.sub("\D", "", cols[7].text))
                    seeder_leecher = re.sub("[^\d/]", "", cols[8].text).split("/")
                    web_info["seeder"] = int(seeder_leecher[0])
                    web_info["leecher"] = int(seeder_leecher[1])
                    web_info_all[id] = web_info
        else:
            raise Exception
        if index < len(config["web"]) - 1:
            time.sleep(eval(str(config["web_interval"])))
    for id in web_info_all:
        torrents[id] = (
            {**torrents[id], **web_info_all[id]} if id in torrents else web_info_all[id]
        ) """
    return {
        "[TTG]" + id: torrent
        for id, torrent in torrents.items()
        if "downloaded" in torrent
    }
