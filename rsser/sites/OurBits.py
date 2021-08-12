import re
import time

import feedparser
import requests
from bs4 import BeautifulSoup

from utils import *


def OurBits(config):
    response = requests.get(
        config["OurBits"]["rss"],
        proxies=config["OurBits"]["proxies"],
        timeout=config["OurBits"]["rss_timeout"],
    )
    if response.status_code == 200:
        feed = feedparser.parse(response.text)
    else:
        raise Exception
    torrents = {
        re.search("id=(\d+)", entry["link"]).group(1): {
            "site": "OurBits",
            "title": re.match("(.+)\[.+\]$", entry["title"]).group(1),
            "size": size_G(re.search("\[([\w\.\s]+)\]$", entry["title"]).group(1)),
            "publish_time": time.mktime(entry["published_parsed"]) - time.timezone,
            "link": entry["links"][1]["href"],
        }
        for entry in feed["entries"]
    }
    torrents = dict(
        filter(
            lambda torrent: filter_regexp(torrent[1], config["OurBits"]["regexp"])
            and filter_size(torrent[1], config["OurBits"]["size"]),
            torrents.items(),
        )
    )
    for web in config["OurBits"]["web"]:
        response = requests.get(
            web,
            headers={"user-agent": config["OurBits"]["user_agent"]},
            cookies=config["OurBits"]["cookies"],
            proxies=config["OurBits"]["proxies"],
            timeout=config["OurBits"]["web_timeout"],
        )
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "lxml")
            rows = soup.find("table", class_="torrents").find_all("tr", recursive=False)
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
                        if re.search('class="pro_\S*free', str(cols[1])) != None:
                            web_info["free"] = True
                            free_end = re.search('<span title="(.+?)"', str(cols[1]))
                            web_info["free_end"] = (
                                None
                                if free_end == None
                                else time.mktime(
                                    time.strptime(
                                        free_end.group(1), "%Y-%m-%d %H:%M:%S"
                                    )
                                )
                                - time.timezone
                                - config["OurBits"]["timezone"] * 3600
                            )
                        if (
                            cols[1].find("img", class_="hitandrun") != None
                            and time.mktime(time.localtime())
                            - torrents[id]["publish_time"]
                            <= 2592000
                        ):
                            web_info["hr"] = 172800
                        if cols[1].find("div", class_="progressBar") != None:
                            web_info["downloaded"] = True
                        web_info["seeder"] = int(re.sub("\D", "", cols[5].text))
                        web_info["leecher"] = int(re.sub("\D", "", cols[6].text))
                        web_info["snatch"] = int(re.sub("\D", "", cols[7].text))
                        torrents[id] = dict(torrents[id], **web_info)
        else:
            raise Exception
        time.sleep(1)
    return {
        "[OurBits]" + id: torrent
        for id, torrent in torrents.items()
        if "downloaded" in torrent
    }
