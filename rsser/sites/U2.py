import math
import random
import re
import time

import feedparser
import requests
from bs4 import BeautifulSoup

from utils import *


def U2(config: dict) -> dict:
    response = requests.get(
        config["rss"],
        proxies=config["proxies"],
        timeout=config["rss_timeout"],
    )
    if response.status_code == 200:
        feed = feedparser.parse(response.text)
    else:
        raise Exception
    torrents = {
        re.search(r"id=(\d+)", entry["link"]).group(1): {
            "site": "U2",
            "title": re.match(r"(.+)\[.+\]$", entry["title"]).group(1),
            "size": size_G(re.search(r"\[([\w\.\s]+)\]$", entry["title"]).group(1)),
            "publish_time": time.mktime(entry["published_parsed"]) - time.timezone,
            "link": entry["links"][1]["href"],
        }
        for entry in feed["entries"]
    }
    if config["web"] == []:
        return {
            "[U2]"
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
    web_info_all = {}
    for index, url in enumerate(config["web"]):
        response = requests.get(
            url,
            headers={"User-Agent": config["user_agent"]},
            cookies=config["cookies"],
            proxies=config["proxies"],
            timeout=config["web_timeout"],
        )
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "lxml")
            rows = soup.find("table", class_="torrents").find_all("tr", recursive=False)
            if rows == []:
                raise Exception
            for row in rows[1:]:
                cols = row.find_all("td", recursive=False)
                if len(cols) >= 8:
                    id = re.search(r"id=(\d+)", str(cols[1])).group(1)
                    web_info = {
                        "publish_time": -1,
                        "free": False,
                        "free_end": None,
                        "hr": None,
                        "downloaded": False,
                        "seeder": -1,
                        "leecher": -1,
                        "snatch": -1,
                    }
                    if (
                        re.search(r'class="pro_\S*free', str(cols[1])) is not None
                        or re.search(
                            r'class="pro_custom.+class="arrowdown.+0\.00X',
                            str(cols[1]),
                        )
                        is not None
                    ):
                        web_info["free"] = True
                        free_end = re.search(
                            r'<time title="\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*"',
                            str(cols[1]),
                        )
                        web_info["free_end"] = (
                            None
                            if free_end is None
                            else time.mktime(
                                time.strptime(free_end.group(1), "%Y-%m-%d %H:%M:%S")
                            )
                            - time.timezone
                            - config["timezone"] * 3600
                        )
                    web_info["publish_time"] = (
                        time.mktime(
                            time.strptime(
                                re.search(
                                    r"(\d{4}-\d{2}-\d{2}.*\d{2}:\d{2}:\d{2})",
                                    str(cols[3]),
                                ).group(1),
                                "%Y-%m-%d %H:%M:%S",
                            )
                        )
                        - time.timezone
                        - config["timezone"] * 3600
                    )
                    web_info["seeder"] = int(re.sub("\D", "", cols[5].text))
                    web_info["leecher"] = int(re.sub("\D", "", cols[6].text))
                    web_info["snatch"] = int(re.sub("\D", "", cols[7].text))
                    if re.search(r"snatchhlc", str(cols[7])) is not None:
                        web_info["downloaded"] = True
                    web_info_all[id] = web_info
        else:
            raise Exception
        if index < len(config["web"]) - 1:
            time.sleep(eval(str(config["web_interval"])))
    for id in web_info_all:
        torrents[id] = (
            {**torrents[id], **web_info_all[id]} if id in torrents else web_info_all[id]
        )
    return {
        "[U2]" + id: torrent
        for id, torrent in torrents.items()
        if "downloaded" in torrent
    }
