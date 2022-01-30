import re
import time

import feedparser
import requests
from bs4 import BeautifulSoup

from utils import *


def HDSky(config: dict) -> dict:
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
            "site": "HDSky",
            "title": re.match(r"(.+)\[.+\]$", entry["title"]).group(1),
            "size": size_G(re.search(r"\[([\w\.\s]+)\]$", entry["title"]).group(1)),
            "publish_time": time.mktime(entry["published_parsed"]) - time.timezone,
            "link": entry["links"][1]["href"],
        }
        for entry in feed["entries"]
    }
    if config["web"] == []:
        return {
            "[HDSky]"
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
    for web in config["web"]:
        response = requests.get(
            web,
            headers={"User-Agent": config["user_agent"]},
            cookies=config["cookies"],
            proxies=config["proxies"],
            timeout=config["web_timeout"],
        )
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "lxml")
            rows = soup.find("table", class_="torrents progresstable").find_all(
                "tr", recursive=False
            )
            if rows == []:
                raise Exception
            for row in rows[1:]:
                cols = row.find_all("td", recursive=False)
                if len(cols) >= 10:
                    id = re.search(r"id=(\d+)", str(cols[1])).group(1)
                    if id in torrents:
                        web_info = {
                            "free": False,
                            "free_end": None,
                            "hr": None,
                            "downloaded": False,
                            "seeder": -1,
                            "leecher": -1,
                            "snatch": -1,
                        }
                        if re.search(r'class="pro_\S*free', str(cols[1])) is not None:
                            if re.search(r"\[.+<b>.+\]", str(cols[1])) is None:
                                web_info["free"] = True
                            else:
                                free_end = re.search(
                                    r'<span title="(.+?)"', str(cols[1])
                                )
                                if free_end is not None:
                                    web_info["free"] = True
                                    web_info["free_end"] = (
                                        time.mktime(
                                            time.strptime(
                                                free_end.group(1), "%Y-%m-%d %H:%M:%S"
                                            )
                                        )
                                        - time.timezone
                                        - config["timezone"] * 3600
                                    )
                        if (
                            re.search(r'<div class="progress.*', str(cols[1]))
                            is not None
                        ):
                            web_info["downloaded"] = True
                        web_info["seeder"] = int(re.sub("\D", "", cols[5].text))
                        web_info["leecher"] = int(re.sub("\D", "", cols[6].text))
                        web_info["snatch"] = int(re.sub("\D", "", cols[7].text))
                        torrents[id] = {**torrents[id], **web_info}
        else:
            raise Exception
    return {
        "[HDSky]" + id: torrent
        for id, torrent in torrents.items()
        if "downloaded" in torrent
    }
