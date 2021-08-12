#!/usr/bin/env python3

import os
import signal
import sys
import threading
import time
from collections import deque
from copy import deepcopy

from clients import *
from sites import *
from utils import *


def terminate():
    lock.acquire()
    yaml_dump(torrent_pool, os.path.join(script_dir, "torrent_pool.yaml"))
    yaml_dump(list(name_queue), os.path.join(script_dir, "name_queue.yaml"))
    if lock.locked():
        lock.release()
    print_t("正在停止…", logger=logger)
    logger.close()
    sys.exit(0)


def uncaught_exception_handler(type, value, traceback):
    print_t("发生未知错误，正在保存种子数据…", logger=logger)
    terminate()


def SIGINT_handler(signum, frame):
    print_t("正在保存种子数据…", logger=logger)
    terminate()


sys.excepthook = uncaught_exception_handler
signal.signal(signal.SIGINT, SIGINT_handler)
script_dir = os.path.dirname(__file__)
config = yaml_read(os.path.join(script_dir, "config.yaml"))
torrent_pool = yaml_read(os.path.join(script_dir, "torrent_pool.yaml"))
name_queue = deque(maxlen=config["torrent_pool_size"])
name_queue.extend(yaml_read(os.path.join(script_dir, "name_queue.yaml")))
os.makedirs(os.path.join(script_dir, "logs"), exist_ok=True)
logger = open(
    os.path.join(
        script_dir,
        "logs",
        time.strftime("%Y-%m-%d %H-%M-%S", time.localtime()) + ".log",
    ),
    "a",
    encoding="utf-8",
    newline="\n",
)
try:
    client = eval(config["client"] + "(config)")
except Exception:
    print_t("无法连接客户端，请重试", logger=logger)
    logger.close()
    sys.exit(0)
lock = threading.Lock()


def task_processor():
    global torrent_pool
    while True:
        try:
            lock.acquire()
            pool = deepcopy(torrent_pool)
            if lock.locked():
                lock.release()
            client.flush()
            print_t("客户端连接正常，正在等候任务…", True)
            time.sleep(1)
            tasks = deepcopy(client.tasks)
            for name, stats in tasks.items():
                try:
                    to_remove = False
                    if name in pool:
                        torrent = pool[name]
                        site = torrent["site"]
                        if "registered" in stats["tracker_status"]:
                            to_remove = True
                            info = "种子被撤除"
                        elif stats["seeding_time"] == 0:
                            if (
                                config[site]["ignore_hr_leeching"]
                                or torrent["hr"] == None
                            ):
                                if config[site]["free_only"] and (
                                    not torrent["free"]
                                    or (
                                        torrent["free_end"] != None
                                        and torrent["free_end"]
                                        - time.mktime(time.localtime())
                                        <= config["run_interval"]
                                    )
                                ):
                                    to_remove = True
                                    info = "免费失效"
                                for condition in config[site]["remove_conditions"]:
                                    if "L" in condition["period"] and eval(
                                        generate_exp(condition["exp"])
                                    ):
                                        to_remove = True
                                        info = condition["info"]
                                        break
                        else:
                            if (
                                config[site]["ignore_hr_seeding"]
                                or torrent["hr"] == None
                            ):
                                hr_time = 0
                            elif (
                                config[site]["hr_seed_ratio"] != None
                                and stats["ratio"] >= config[site]["hr_seed_ratio"]
                            ):
                                hr_time = config[site]["hr_seed_delay"]
                            else:
                                hr_time = torrent["hr"] + config[site]["hr_seed_delay"]
                            if stats["seeding_time"] >= hr_time:
                                for condition in config[site]["remove_conditions"]:
                                    if "S" in condition["period"] and eval(
                                        generate_exp(condition["exp"])
                                    ):
                                        to_remove = True
                                        info = condition["info"]
                                        break
                    if to_remove:
                        client.remove_torrent(torrent, name, info, logger)
                        time.sleep(5 if config["client"] == "qbittorrent" else 1)
                        client.flush()
                        time.sleep(1)
                except Exception:
                    print_t(
                        f'删除种子{name}（{torrent["size"]:.2f}GB）可能已失败，尝试删除其他种子…',
                        logger=logger,
                    )
                    time.sleep(5 if config["client"] == "qbittorrent" else 1)
                    client.flush()
                    time.sleep(1)
            lock.acquire()
            torrent_pool = {
                name: torrent
                for name, torrent in torrent_pool.items()
                if name in name_queue
            }
            sort_keys = reversed(list(config["sort_by"].keys()))
            for key in sort_keys:
                torrent_pool = dict(
                    sorted(
                        torrent_pool.items(),
                        key=lambda torrent: torrent[1][key]
                        if key != "site"
                        else config[torrent[1]["site"]]["priority"],
                        reverse=config["sort_by"][key],
                    )
                )
            pool = deepcopy(torrent_pool)
            if lock.locked():
                lock.release()
            for name, torrent in pool.items():
                try:
                    site = torrent["site"]
                    if (
                        client.task_count < config["task_count_max"]
                        and not name in client.tasks
                        and torrent["retry_count"] <= config[site]["retry_count_max"]
                        and not torrent["downloaded"]
                        and config[site]["seeder"][0]
                        <= torrent["seeder"]
                        <= config[site]["seeder"][1]
                        and config[site]["leecher"][0]
                        <= torrent["leecher"]
                        <= config[site]["leecher"][1]
                        and config[site]["snatch"][0]
                        <= torrent["snatch"]
                        <= config[site]["snatch"][1]
                        and (
                            time.mktime(time.localtime()) - torrent["publish_time"]
                            <= config[site]["publish_within"]
                        )
                        and client.total_size + torrent["size"] <= config["space"]
                        and (
                            not config[site]["free_only"]
                            or (
                                torrent["free"]
                                and (
                                    torrent["free_end"] == None
                                    or torrent["free_end"]
                                    - time.mktime(time.localtime())
                                    >= config[site]["free_time_min"]
                                )
                            )
                        )
                        and (
                            torrent["hr"] == None
                            or torrent["hr"] <= config[site]["hr_time_max"]
                        )
                    ):
                        client.add_torrent(torrent, name, logger)
                        time.sleep(10 if config["client"] == "qbittorrent" else 2)
                        client.flush()
                        time.sleep(1)
                except Exception:
                    print_t(
                        f'添加种子{name}（{torrent["size"]:.2f}GB）可能已失败，尝试添加其他种子…',
                        logger=logger,
                    )
                    lock.acquire()
                    if name in torrent_pool:
                        torrent_pool[name]["retry_count"] = torrent["retry_count"]
                    if lock.locked():
                        lock.release()
                    time.sleep(10 if config["client"] == "qbittorrent" else 2)
                    client.flush()
                    time.sleep(1)
            time.sleep(config["run_interval"])
        except Exception:
            if lock.locked():
                lock.release()
            print_t("出现异常，正在重新连接客户端…", True, logger)
            client.reconnect()


def torrent_fetcher(site):
    def template():
        while True:
            try:
                torrents = eval(site + "(config)")
                lock.acquire()
                for name, torrent in torrents.items():
                    if name in torrent_pool:
                        torrent_pool[name] = dict(torrent_pool[name], **torrent)
                    else:
                        torrent_pool[name] = dict(torrent, **{"retry_count": 0})
                        name_queue.append(name)
                if lock.locked():
                    lock.release()
                time.sleep(config[site]["fetch_interval"])
            except Exception:
                if lock.locked():
                    lock.release()
                print_t(f"[{site}]获取种子信息失败，正在重试…", logger=logger)
                time.sleep(config[site]["retry_interval"])

    return template


threads = [threading.Thread(target=task_processor)]
for site in list(config.keys())[12:]:
    threads.append(threading.Thread(target=torrent_fetcher(site)))
for thread in threads:
    thread.setDaemon(True)
    thread.start()
while True:
    time.sleep(86400)
