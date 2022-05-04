import json
import re
import time

import feedparser
import requests
from bs4 import BeautifulSoup

from utils import *


def HDChina(config: dict) -> dict:
    response = requests.get(
        config["rss"],
        proxies=config["proxies"],
        timeout=config["rss_timeout"],
    )
    if response.status_code == 200:
        feed = feedparser.parse(response.text)
    else:
        raise Exception
    torrents = {
        re.search(r"id=(\d+)", entry["link"]).group(1): {
            "site": "HDChina",
            "title": re.match(r"(.+)\[.+\]$", entry["title"]).group(1),
            "size": size_G(re.search(r"\[([\w\.\s]+)\]$", entry["title"]).group(1)),
            "publish_time": time.mktime(entry["published_parsed"]) - time.timezone,
            "link": entry["links"][1]["href"],
        }
        for entry in feed["entries"]
    }
    if config["web"] == []:
        return {
            "[HDChina]"
            + id: {
                **torrent,
                **{
                    "free": False,
                    "free_end": None,
                    "hr": None,
                    "downloaded": False,
                    "seeder": -1,
                    "leecher": -1,
                    "snatch": -1,
                },
            }
            for id, torrent in torrents.items()
        }
    """ web_info_all = {}
    session = requests.session()
    for web in config["web"]:
        response = session.get(
            web,
            headers={"User-Agent": config["user_agent"]},
            cookies=config["cookies"],
            proxies=config["proxies"],
            timeout=config["web_timeout"],
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
                    id = re.search(r"id=(\d+)", str(cols[1])).group(1)
                    ids.append(("ids[]", id))
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
                    web_info_all[id] = web_info
        else:
            raise Exception
        time.sleep(1)
        response = session.post(
            url="https://hdchina.org/ajax_promotion.php",
            headers={
                "User-Agent": config["user_agent"],
                "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
            },
            data=ids + [("csrf", csrf)],
            cookies=config["cookies"],
            proxies=config["proxies"],
            timeout=config["web_timeout"],
        )
        if response.status_code == 200:
            pro_info = json.loads(response.text)
            if pro_info["status"] != 200 or pro_info["message"] == {}:
                raise Exception
            sp_states = set(
                state["sp_state"] for _, state in pro_info["message"].items()
            )
            if len(sp_states) == 1 and "" not in sp_states:
                if (
                    re.match(
                        r' <img class="pro_free" src="pic/trans.gif" alt="Free"',
                        min(sp_states),
                    )
                    is None
                ):
                    raise Exception
            for id, state in pro_info["message"].items():
                if (
                    id in web_info_all
                    and re.search(r'class="pro_\S*free', state["sp_state"]) is not None
                ):
                    web_info_all[id]["free"] = True
                    free_end = re.search(r'<span title="(.+?)"', state["timeout"])
                    web_info_all[id]["free_end"] = (
                        None
                        if free_end is None
                        else time.mktime(
                            time.strptime(free_end.group(1), "%Y-%m-%d %H:%M:%S")
                        )
                        - time.timezone
                        - config["timezone"] * 3600
                    )
        else:
            raise Exception
    session.close()
    for id in web_info_all:
        torrents[id] = (
            {**torrents[id], **web_info_all[id]} if id in torrents else web_info_all[id]
        ) """
    return {
        "[HDChina]" + id: torrent
        for id, torrent in torrents.items()
        if "downloaded" in torrent
    }
