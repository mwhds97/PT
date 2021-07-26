import re
import time
import urllib.request

import feedparser
import requests
from bs4 import BeautifulSoup

from utils import *


def CHDBits(config):
    try:
        if (
            config["CHDBits"]["http_proxy"] == None
            and config["CHDBits"]["https_proxy"] == None
        ):
            feed = feedparser.parse(config["CHDBits"]["rss"])
        else:
            feed = feedparser.parse(
                config["CHDBits"]["rss"],
                handlers=urllib.request.ProxyHandler(
                    {
                        key[:-6]: value
                        for key, value in config["CHDBits"].items()
                        if key in ["http_proxy", "https_proxy"] and value != None
                    }
                ),
            )
        torrents = {
            re.search("id=(\d+)", entry["link"]).group(1): {
                "site": "CHDBits",
                "title": entry["title"],
                "size": size_G(re.search("\[([\w\.\s]+)\]$", entry["title"]).group(1)),
                "publish_at": time.mktime(entry["published_parsed"]) - time.timezone,
                "link": entry["links"][1]["href"],
            }
            for entry in feed["entries"]
        }
        torrents = dict(
            filter(
                lambda torrent: config["CHDBits"]["size"][0]
                <= torrent[1]["size"]
                <= config["CHDBits"]["size"][1]
                and re.search(config["CHDBits"]["regexp"], torrent[1]["title"]) != None,
                torrents.items(),
            )
        )
        response = requests.get(
            "https://chdbits.co/torrents.php?sort=4&type=desc",
            headers={"user-agent": config["CHDBits"]["user_agent"]},
            cookies=config["CHDBits"]["cookies"],
            proxies={
                "http": config["CHDBits"]["http_proxy"],
                "https": config["CHDBits"]["https_proxy"],
            },
            timeout=15,
        )
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "lxml")
            rows = soup.find("table", class_="torrents").find_all(
                "tr", class_=re.compile(".+"), recursive=False
            )
            for row in rows:
                id = re.search("id=(\d+)", str(row)).group(1)
                if id in torrents:
                    web_info = {
                        "free": False,
                        "free_end": None,
                        "hr": None,
                        "downloaded": False,
                    }
                    if re.search('class="pro_\S*free', str(row)) != None:
                        web_info["free"] = True
                        free_end = re.search('限时：<span title="(.+?)"', str(row))
                        web_info["free_end"] = (
                            None
                            if free_end == None
                            else time.mktime(
                                time.strptime(free_end.group(1), "%Y-%m-%d %H:%M:%S")
                            )
                            - time.timezone
                            - 28800
                        )
                    hr = re.search("circle-text.+?(\d+)</div>", str(row))
                    if hr != None:
                        web_info["hr"] = int(hr.group(1)) * 3600
                    if re.search("%</td>", str(row)) != None:
                        web_info["downloaded"] = True
                    torrents[id] = dict(torrents[id], **web_info)
            return {"[CHDBits]" + id: torrent for id, torrent in torrents.items()}
        else:
            return {}
    except Exception:
        return {}
