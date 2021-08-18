import re
import time

import feedparser
import requests
from bs4 import BeautifulSoup

from utils import *


def HDChina(config):
    response = requests.get(
        config["HDChina"]["rss"],
        proxies=config["HDChina"]["proxies"],
        timeout=config["HDChina"]["rss_timeout"],
    )
    if response.status_code == 200:
        feed = feedparser.parse(response.text)
    else:
        raise Exception
    torrents = {
        re.search("id=(\d+)", entry["link"]).group(1): {
            "site": "HDChina",
            "title": re.match("(.+)\[.+\]$", entry["title"]).group(1),
            "size": size_G(re.search("\[([\w\.\s]+)\]$", entry["title"]).group(1)),
            "publish_time": time.mktime(entry["published_parsed"]) - time.timezone,
            "link": entry["links"][1]["href"],
        }
        for entry in feed["entries"]
    }
    for web in config["HDChina"]["web"]:
        response = requests.get(
            web,
            headers={"user-agent": config["HDChina"]["user_agent"]},
            cookies=config["HDChina"]["cookies"],
            proxies=config["HDChina"]["proxies"],
            timeout=config["HDChina"]["web_timeout"],
        )
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "lxml")
            rows = soup.find("table", class_="torrent_list").find_all(
                "tr", recursive=False
            )
            if rows == []:
                raise Exception
            for row in rows[1:]:
                cols = row.find_all("td", recursive=False)
                if len(cols) >= 9:
                    id = re.search("id=(\d+)", str(cols[1])).group(1)
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
                        # TODO: Promotion
                        if cols[1].find("div", class_="progress") != None:
                            web_info["downloaded"] == True
                        web_info["seeder"] = int(re.sub("\D", "", cols[5].text))
                        web_info["leecher"] = int(re.sub("\D", "", cols[6].text))
                        web_info["snatch"] = int(re.sub("\D", "", cols[7].text))
                        torrents[id] = dict(torrents[id], **web_info)
        else:
            raise Exception
        time.sleep(1)
    return {
        "[HDChina]" + id: torrent
        for id, torrent in torrents.items()
        if "downloaded" in torrent
    }
