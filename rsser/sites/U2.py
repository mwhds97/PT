import re
import time

import feedparser
import requests
from bs4 import BeautifulSoup

from utils import *


def U2(config):
    response = requests.get(
        config["U2"]["rss"],
        proxies=config["U2"]["proxies"],
        timeout=config["U2"]["rss_timeout"],
    )
    if response.status_code == 200:
        feed = feedparser.parse(response.text)
    else:
        raise Exception
    torrents = {
        re.search("id=(\d+)", entry["link"]).group(1): {
            "site": "U2",
            "title": entry["title"],
            "size": size_G(re.search("\[([\w\.\s]+)\]$", entry["title"]).group(1)),
            "publish_at": time.mktime(entry["published_parsed"]) - time.timezone,
            "link": entry["links"][1]["href"],
        }
        for entry in feed["entries"]
    }
    torrents = dict(
        filter(
            lambda torrent: config["U2"]["size"][0]
            <= torrent[1]["size"]
            <= config["U2"]["size"][1]
            and re.search(config["U2"]["regexp"], torrent[1]["title"]) != None,
            torrents.items(),
        )
    )
    response = requests.get(
        config["U2"]["web"],
        headers={"user-agent": config["U2"]["user_agent"]},
        cookies=config["U2"]["cookies"],
        proxies=config["U2"]["proxies"],
        timeout=config["U2"]["web_timeout"],
    )
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "lxml")
        rows = soup.find("table", class_="torrents").find_all("tr", recursive=False)
        if rows == []:
            raise Exception
        for row in rows[1:]:
            id = re.search("id=(\d+)", str(row)).group(1)
            if id in torrents:
                web_info = {
                    "free": False,
                    "free_end": None,
                    "hr": None,
                    "downloaded": False,
                }
                if (
                    re.search('class="pro_\S*free', str(row)) != None
                    or re.search('class="pro_custom.+arrowdown.+0\.00X', str(row))
                    != None
                ):
                    web_info["free"] = True
                    free_end = re.search('\[.+<time title="(.+?)".+\]', str(row))
                    web_info["free_end"] = (
                        None
                        if free_end == None
                        else time.mktime(
                            time.strptime(free_end.group(1), "%Y-%m-%d %H:%M:%S")
                        )
                        - time.timezone
                        - 28800
                    )
                if re.search('class="rowfollow snatchhlc', str(row)) != None:
                    web_info["downloaded"] = True
                torrents[id] = dict(torrents[id], **web_info)
        return {"[U2]" + id: torrent for id, torrent in torrents.items()}
    else:
        raise Exception
