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
        re.search(r"id=(\d+)", entry["link"]).group(1): {
            "site": "U2",
            "title": re.match(r"(.+)\[.+\]$", entry["title"]).group(1),
            "size": size_G(re.search(r"\[([\w\.\s]+)\]$", entry["title"]).group(1)),
            "link": entry["links"][1]["href"],
        }
        for entry in feed["entries"]
    }
    for web in config["U2"]["web"]:
        response = requests.get(
            web,
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
                cols = row.find_all("td", recursive=False)
                if len(cols) >= 8:
                    id = re.search(r"id=(\d+)", str(cols[1])).group(1)
                    if id in torrents:
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
                            free_end = re.search(r'<time title="(.+?)"', str(cols[1]))
                            web_info["free_end"] = (
                                None
                                if free_end is None
                                else time.mktime(
                                    time.strptime(
                                        free_end.group(1), "%Y-%m-%d %H:%M:%S"
                                    )
                                )
                                - time.timezone
                                - config["U2"]["timezone"] * 3600
                            )
                        web_info["publish_time"] = (
                            time.mktime(
                                time.strptime(
                                    re.search(
                                        r'<time title="(.+?)"', str(cols[3])
                                    ).group(1),
                                    "%Y-%m-%d %H:%M:%S",
                                )
                            )
                            - time.timezone
                            - config["U2"]["timezone"] * 3600
                        )
                        web_info["seeder"] = int(re.sub("\D", "", cols[5].text))
                        web_info["leecher"] = int(re.sub("\D", "", cols[6].text))
                        web_info["snatch"] = int(re.sub("\D", "", cols[7].text))
                        if re.search(r"snatchhlc", str(cols[7])) is not None:
                            web_info["downloaded"] = True
                        torrents[id] = {**torrents[id], **web_info}
        else:
            raise Exception
        time.sleep(1)
    return {
        "[U2]" + id: torrent
        for id, torrent in torrents.items()
        if "downloaded" in torrent
    }
