import re
import time

import feedparser
import requests
from bs4 import BeautifulSoup

from utils import *


def OpenCD(config):
    response = requests.get(
        config["OpenCD"]["rss"],
        proxies=config["OpenCD"]["proxies"],
        timeout=config["OpenCD"]["rss_timeout"],
    )
    if response.status_code == 200:
        feed = feedparser.parse(response.text)
    else:
        raise Exception
    torrents = {
        re.search("id=(\d+)", entry["link"]).group(1): {
            "site": "OpenCD",
            "title": re.match("(.+)\[.+\]$", entry["title"]).group(1),
            "size": size_G(re.search("\[([\w\.\s]+)\]$", entry["title"]).group(1)),
            "publish_time": time.mktime(entry["published_parsed"]) - time.timezone,
            "link": entry["links"][1]["href"],
        }
        for entry in feed["entries"]
    }
    for web in config["OpenCD"]["web"]:
        response = requests.get(
            web,
            headers={"user-agent": config["OpenCD"]["user_agent"]},
            cookies=config["OpenCD"]["cookies"],
            proxies=config["OpenCD"]["proxies"],
            timeout=config["OpenCD"]["web_timeout"],
        )
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "lxml")
            rows = soup.find("table", class_="torrents").find_all("tr", recursive=False)
            if rows == []:
                raise Exception
            for row in rows[1:]:
                cols = row.find_all("td", recursive=False)
                if len(cols) >= 11:
                    id = re.search("id=(\d+)", str(cols[2])).group(1)
                    if id in torrents:
                        web_info = {
                            "free": False,
                            "free_end": None,
                            "hr": 259200,
                            "downloaded": False,
                            "seeder": -1,
                            "leecher": -1,
                            "snatch": -1,
                        }
                        if re.search('class="pro_\S*free', str(cols[2])) is not None:
                            web_info["free"] = True
                            free_end = re.search('<span title="(.+?)"', str(cols[2]))
                            web_info["free_end"] = (
                                None
                                if free_end is None
                                else time.mktime(
                                    time.strptime(
                                        free_end.group(1), "%Y-%m-%d %H:%M:%S"
                                    )
                                )
                                - time.timezone
                                - config["OpenCD"]["timezone"] * 3600
                            )
                        if cols[2].find("div", class_="progress") is not None:
                            web_info["downloaded"] == True
                        web_info["seeder"] = int(re.sub("\D", "", cols[7].text))
                        web_info["leecher"] = int(re.sub("\D", "", cols[8].text))
                        web_info["snatch"] = int(re.sub("\D", "", cols[9].text))
                        torrents[id] = {**torrents[id], **web_info}
        else:
            raise Exception
        time.sleep(1)
    return {
        "[OpenCD]" + id: torrent
        for id, torrent in torrents.items()
        if "downloaded" in torrent
    }
