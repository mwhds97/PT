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
            "title": re.match("(.+)\[.+\]$", entry["title"]).group(1),
            "size": size_G(re.search("\[([\w\.\s]+)\]$", entry["title"]).group(1)),
            "publish_time": time.mktime(entry["published_parsed"]) - time.timezone,
            "link": entry["links"][1]["href"],
        }
        for entry in feed["entries"]
    }
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
                cols = row.find_all("td", recursive=False)
                if len(cols) >= 10:
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
                        if re.search('class="pro_\S*free', str(cols[1])) is not None:
                            if re.search("\[.+<b>.+\]", str(cols[1])) is None:
                                web_info["free"] = True
                            else:
                                free_end = re.search(
                                    '<span title="(.+?)"', str(cols[1])
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
                                        - config["HDSky"]["timezone"] * 3600
                                    )
                        if (
                            re.search('<div class="progress.*', str(cols[1]))
                            is not None
                        ):
                            web_info["downloaded"] = True
                        web_info["seeder"] = int(re.sub("\D", "", cols[5].text))
                        web_info["leecher"] = int(re.sub("\D", "", cols[6].text))
                        web_info["snatch"] = int(re.sub("\D", "", cols[7].text))
                        torrents[id] = {**torrents[id], **web_info}
        else:
            raise Exception
        time.sleep(1)
    return {
        "[HDSky]" + id: torrent
        for id, torrent in torrents.items()
        if "downloaded" in torrent
    }
