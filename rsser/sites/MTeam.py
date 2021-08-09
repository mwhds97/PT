import re
import time

import feedparser
import requests
from bs4 import BeautifulSoup

from utils import *


def MTeam(config):
    def epoch(duration):
        durs = re.search("(?:(\d+)[日|D])*(?:(\d+)[時|H])*(?:(\d+)[分|M])*", duration)
        if durs != None:
            durs = durs.groups()
        day = int(durs[0]) if durs[0] != None else 0
        hour = int(durs[1]) if durs[1] != None else 0
        min = int(durs[2]) if durs[2] != None else 0
        return time.mktime(time.localtime()) + day * 86400 + hour * 3600 + min * 60

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
    torrents = dict(
        filter(
            lambda torrent: filter_regexp(torrent[1], config["MTeam"]["regexp"])
            and filter_size(torrent[1], config["MTeam"]["size"]),
            torrents.items(),
        )
    )
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
                        if re.search('class="pro_\S*free', str(cols[1])) != None:
                            free_duration = re.search(
                                "<span.+(?:限時：|will end in)(.+?)</span>", str(cols[1])
                            )
                            if free_duration == None:
                                web_info["free"] = True
                            elif not "<" in free_duration.group(1):
                                web_info["free"] = True
                                web_info["free_end"] = epoch(free_duration.group(1))
                        web_info["seeder"] = int(re.sub("\D", "", cols[5].text))
                        web_info["leecher"] = int(re.sub("\D", "", cols[6].text))
                        web_info["snatch"] = int(re.sub("\D", "", cols[7].text))
                        if re.search("\d", cols[8].text) != None:
                            web_info["downloaded"] = True
                        torrents[id] = dict(torrents[id], **web_info)
        else:
            raise Exception
        time.sleep(1)
    return {
        "[MTeam]" + id: torrent
        for id, torrent in torrents.items()
        if "downloaded" in torrent
    }
