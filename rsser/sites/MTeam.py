import re
import time

import feedparser
import requests
from bs4 import BeautifulSoup

from utils import *


def MTeam(config):
    def epoch(duration):
        dur = re.sub("日|D", "*86400+", re.sub("\W", "", duration))
        dur = re.sub("時|H", "*3600+", dur)
        dur = re.sub("分|M", "*60+", dur)
        return time.mktime(time.localtime()) + eval(dur[:-1])

    response = requests.get(
        config["MTeam"]["rss"],
        proxies=config["MTeam"]["proxies"],
        timeout=config["MTeam"]["rss_timeout"],
    )
    if response.status_code == 200:
        feed = feedparser.parse(response.text)
    else:
        raise Exception
    torrents = {
        re.search("id=(\d+)", entry["link"]).group(1): {
            "site": "MTeam",
            "title": re.match("(.+)\[.+\]$", entry["title"]).group(1),
            "size": size_G(re.search("\[([\w\.\s]+)\]$", entry["title"]).group(1)),
            "publish_time": time.mktime(entry["published_parsed"]) - time.timezone,
            "link": entry["links"][1]["href"],
        }
        for entry in feed["entries"]
    }
    for web in config["MTeam"]["web"]:
        response = requests.get(
            web,
            headers={"user-agent": config["MTeam"]["user_agent"]},
            cookies=config["MTeam"]["cookies"],
            proxies=config["MTeam"]["proxies"],
            timeout=config["MTeam"]["web_timeout"],
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
                        if re.search('class="pro_\S*free', str(cols[1])) is not None:
                            free_duration = re.search(
                                "<span.+(?:限時：|will end in)(.+?)</span>", str(cols[1])
                            )
                            if free_duration is None:
                                web_info["free"] = True
                            elif "<" not in free_duration.group(1):
                                web_info["free"] = True
                                web_info["free_end"] = epoch(free_duration.group(1))
                        web_info["seeder"] = int(re.sub("\D", "", cols[5].text))
                        web_info["leecher"] = int(re.sub("\D", "", cols[6].text))
                        web_info["snatch"] = int(re.sub("\D", "", cols[7].text))
                        if re.search("\d", cols[8].text) is not None:
                            web_info["downloaded"] = True
                        torrents[id] = {**torrents[id], **web_info}
        else:
            raise Exception
        time.sleep(1)
    return {
        "[MTeam]" + id: torrent
        for id, torrent in torrents.items()
        if "downloaded" in torrent
    }
