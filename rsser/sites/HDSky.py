import re
import time

import feedparser
import requests
from bs4 import BeautifulSoup

from utils import *


def HDSky(config):
    response = requests.get(
        config["HDSky"]["rss"],
        proxies=config["HDSky"]["proxies"],
        timeout=config["HDSky"]["rss_timeout"],
    )
    if response.status_code == 200:
        feed = feedparser.parse(response.text)
    else:
        raise Exception
    torrents = {
        re.search("id=(\d+)", entry["link"]).group(1): {
            "site": "HDSky",
            "title": entry["title"],
            "size": size_G(re.search("\[([\w\.\s]+)\]$", entry["title"]).group(1)),
            "publish_at": time.mktime(entry["published_parsed"]) - time.timezone,
            "link": entry["links"][1]["href"],
        }
        for entry in feed["entries"]
    }
    torrents = dict(
        filter(
            lambda torrent: config["HDSky"]["size"][0]
            <= torrent[1]["size"]
            <= config["HDSky"]["size"][1]
            and re.search(config["HDSky"]["regexp"], torrent[1]["title"]) != None,
            torrents.items(),
        )
    )
    for web in config["HDSky"]["web"]:
        response = requests.get(
            web,
            headers={"user-agent": config["HDSky"]["user_agent"]},
            cookies=config["HDSky"]["cookies"],
            proxies=config["HDSky"]["proxies"],
            timeout=config["HDSky"]["web_timeout"],
        )
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "lxml")
            rows = soup.find("table", class_="torrents progresstable").find_all(
                "tr", recursive=False
            )
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
                    if re.search('class="pro_\S*free', str(row)) != None:
                        if re.search("\[.+<b>.+\]", str(row)) == None:
                            web_info["free"] = True
                        else:
                            free_end = re.search(
                                '\[.+<span title="(.+?)".+\]', str(row)
                            )
                            if free_end != None:
                                web_info["free"] = True
                                web_info["free_end"] = (
                                    time.mktime(
                                        time.strptime(
                                            free_end.group(1), "%Y-%m-%d %H:%M:%S"
                                        )
                                    )
                                    - time.timezone
                                    - 28800
                                )
                    if re.search('<div class="\w', str(row)) != None:
                        web_info["downloaded"] = True
                    torrents[id] = dict(torrents[id], **web_info)
        else:
            raise Exception
        time.sleep(1)
    return {"[HDSky]" + id: torrent for id, torrent in torrents.items()}
