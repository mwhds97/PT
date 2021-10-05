import json
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
    session = requests.session()
    for web in config["HDChina"]["web"]:
        response = session.get(
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
            csrf = soup.find("meta", {"name": "x-csrf"})["content"]
            if rows == [] or len(csrf) != 40:
                raise Exception
            ids = []
            for row in rows[1:]:
                cols = row.find_all("td", recursive=False)
                if len(cols) >= 9:
                    id = re.search("id=(\d+)", str(cols[1])).group(1)
                    ids.append(("ids[]", id))
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
                        if cols[1].find("div", class_="progress") is not None:
                            web_info["downloaded"] == True
                        web_info["seeder"] = int(re.sub("\D", "", cols[5].text))
                        web_info["leecher"] = int(re.sub("\D", "", cols[6].text))
                        web_info["snatch"] = int(re.sub("\D", "", cols[7].text))
                        torrents[id] = {**torrents[id], **web_info}
        else:
            raise Exception
        time.sleep(1)
        response = session.post(
            url="https://hdchina.org/ajax_promotion.php",
            headers={
                "User-Agent": config["HDChina"]["user_agent"],
                "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
            },
            data=ids + [("csrf", csrf)],
            cookies=config["HDChina"]["cookies"],
            proxies=config["HDChina"]["proxies"],
            timeout=config["HDChina"]["web_timeout"],
        )
        if response.status_code == 200:
            pro_info = json.loads(response.text)
            if pro_info["status"] != 200 or pro_info["message"] == {}:
                raise Exception
            for id, state in pro_info["message"].items():
                if (
                    id in torrents
                    and re.search('class="pro_\S*free', state["sp_state"]) is not None
                ):
                    torrents[id]["free"] = True
                    free_end = re.search('<span title="(.+?)"', state["timeout"])
                    torrents[id]["free_end"] = (
                        None
                        if free_end is None
                        else time.mktime(
                            time.strptime(free_end.group(1), "%Y-%m-%d %H:%M:%S")
                        )
                        - time.timezone
                        - config["HDChina"]["timezone"] * 3600
                    )
        else:
            raise Exception
        time.sleep(1)
    session.close()
    return {
        "[HDChina]" + id: torrent
        for id, torrent in torrents.items()
        if "downloaded" in torrent
    }
