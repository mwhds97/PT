import re
import time

import feedparser
import requests
from bs4 import BeautifulSoup

from utils import *


def CHDBits(config):
    response = requests.get(
        config["CHDBits"]["rss"],
        proxies=config["CHDBits"]["proxies"],
        timeout=config["CHDBits"]["rss_timeout"],
    )
    if response.status_code == 200:
        feed = feedparser.parse(response.text)
    else:
        raise Exception
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
    for web in config["CHDBits"]["web"]:
        response = requests.get(
            web,
            headers={"user-agent": config["CHDBits"]["user_agent"]},
            cookies=config["CHDBits"]["cookies"],
            proxies=config["CHDBits"]["proxies"],
            timeout=config["CHDBits"]["web_timeout"],
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
                    if re.search('class="pro_\S*free', str(row)) != None:
                        web_info["free"] = True
                        free_end = re.search('\(.+<span title="(.+?)".+\)', str(row))
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
                        web_info["hr"] = int(hr.group(1)) * 86400
                    if re.search("%</td>", str(row)) != None:
                        web_info["downloaded"] = True
                    torrents[id] = dict(torrents[id], **web_info)
        else:
            raise Exception
        time.sleep(1)
    return {"[CHDBits]" + id: torrent for id, torrent in torrents.items()}
