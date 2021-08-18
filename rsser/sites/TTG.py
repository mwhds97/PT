import re
import time

import feedparser
import requests
from bs4 import BeautifulSoup

from utils import *


def TTG(config):
    response = requests.get(
        config["TTG"]["rss"],
        proxies=config["TTG"]["proxies"],
        timeout=config["TTG"]["rss_timeout"],
    )
    if response.status_code == 200:
        feed = feedparser.parse(response.text)
    else:
        raise Exception
    torrents = {}
    for entry in feed["entries"]:
        title_size = re.match("(.+) (\d+(?:\.\d+)? \w+?)$", entry["title"]).groups()
        torrents[re.search("id=(\d+)", entry["link"]).group(1)] = {
            "site": "TTG",
            "title": title_size[0],
            "size": size_G(title_size[1]),
            "publish_time": time.mktime(entry["published_parsed"]) - time.timezone,
            "link": entry["links"][1]["href"],
        }
    for web in config["TTG"]["web"]:
        response = requests.get(
            web,
            headers={"user-agent": config["TTG"]["user_agent"]},
            cookies=config["TTG"]["cookies"],
            proxies=config["TTG"]["proxies"],
            timeout=config["TTG"]["web_timeout"],
        )
        if response.status_code == 200:
            soup = BeautifulSoup(response.content.decode("utf-8"), "lxml")
            rows = soup.find("table", id="torrent_table").find_all(
                "tr", recursive=False
            )
            if rows == []:
                raise Exception
            for row in rows[1:]:
                cols = row.find_all("td", recursive=False)
                if len(cols) >= 10:
                    id = re.search('tid="(\d+)"', str(cols[1])).group(1)
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
                        if cols[1].find("img", alt="free") != None:
                            web_info["free"] = True
                            free_end = re.search(
                                "javascript:alert.+(\d{4}年\d{2}月\d{2}日\d{2}点\d{2}分)",
                                str(cols[1]),
                            )
                            web_info["free_end"] = (
                                None
                                if free_end == None
                                else time.mktime(
                                    time.strptime(free_end.group(1), "%Y年%m月%d日%H点%M分")
                                )
                                - time.timezone
                                - config["TTG"]["timezone"] * 3600
                            )
                        if cols[1].find("img", title="Hit and Run") != None:
                            web_info["hr"] = (
                                86400
                                if re.search("第\d+[集话話周週]|EP?\d+(?!-)", str(cols[1]))
                                != None
                                else 216000
                            )
                        if cols[1].find("div", class_="process") != None:
                            web_info["downloaded"] = True
                        web_info["snatch"] = int(re.sub("\D", "", cols[7].text))
                        seeder_leecher = re.sub("[^\d/]", "", cols[8].text).split("/")
                        web_info["seeder"] = int(seeder_leecher[0])
                        web_info["leecher"] = int(seeder_leecher[1])
                        torrents[id] = dict(torrents[id], **web_info)
        else:
            raise Exception
        time.sleep(1)
    return {
        "[TTG]" + id: torrent
        for id, torrent in torrents.items()
        if "downloaded" in torrent
    }
