#!/usr/bin/env python3

import os
import signal
import sys
import threading
import time
from collections import deque

from clients import *
from sites import *
from utils import *


def uncaught_exception_handler(type, value, traceback):
    print_t("发生未知错误，正在保存种子数据…", logger=logger)
    lock.acquire()
    yaml_dump(torrent_pool, os.path.join(script_dir, "torrent_pool.yaml"))
    yaml_dump(list(name_queue), os.path.join(script_dir, "name_queue.yaml"))
    lock.release()
    print_t("正在停止…", logger=logger)
    logger.close()
    sys.exit(0)


sys.excepthook = uncaught_exception_handler


def SIGINT_handler(signum, frame):
    print_t("正在保存种子数据…", logger=logger)
    lock.acquire()
    yaml_dump(torrent_pool, os.path.join(script_dir, "torrent_pool.yaml"))
    yaml_dump(list(name_queue), os.path.join(script_dir, "name_queue.yaml"))
    lock.release()
    print_t("正在停止…", logger=logger)
    logger.close()
    sys.exit(0)


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
            client.flush()
            print_t("客户端连接正常，正在等候任务…", True)
            time.sleep(1)
            lock.acquire()
            for name, stats in client.tasks.items():
                to_remove = False
                if name in torrent_pool:
                    torrent = torrent_pool[name]
                    site = torrent["site"]
                    if "registered" in stats["tracker_status"]:
                        to_remove = True
                        info = "种子被撤除"
                    elif (
                        config[site]["free_only"]
                        and stats["seeding_time"] == 0
                        and (
                            not torrent["free"]
                            or torrent["free_end"] != None
                            and torrent["free_end"] - time.mktime(time.localtime())
                            <= config["run_interval"]
                        )
                    ):
                        to_remove = True
                        info = "免费失效"
                    else:
                        if config[site]["ignore_hr"] or torrent["hr"] == None:
                            hr_time = 0
                        elif (
                            config[site]["seed_ratio_hr"] != None
                            and stats["ratio"] >= config[site]["seed_ratio_hr"]
                        ):
                            hr_time = config[site]["seed_delay_hr"]
                        else:
                            hr_time = torrent["hr"] + config[site]["seed_delay_hr"]
                        if (
                            hr_time == 0
                            and stats["active_time"] >= config[site]["life"]
                        ):
                            to_remove = True
                            info = "活动时长超过限制"
                        if config[site]["seed_by_size"]:
                            if stats["seeding_time"] >= max(
                                config[site]["seed_time_size_ratio"]
                                * torrent["size"]
                                * 60,
                                hr_time,
                            ):
                                to_remove = True
                                info = "做种时长（弹性）达到要求"
                        elif stats["seeding_time"] >= max(
                            config[site]["seed_time_fixed"], hr_time
                        ):
                            to_remove = True
                            info = "做种时长（固定）达到要求"
                if to_remove:
                    client.remove_torrent(name, info, logger)
                    time.sleep(1)
            torrent_pool = {
                name: torrent
                for name, torrent in torrent_pool.items()
                if name in name_queue
            }
            torrent_pool = dict(
                sorted(
                    torrent_pool.items(),
                    key=lambda torrent: torrent[1]["size"],
                    reverse=True,
                )
            )
            if config["order_by_site"]:
                site_order = {}
                for i in range(len(config["sites"])):
                    site_order[config["sites"][i]] = i
                torrent_pool = dict(
                    sorted(
                        torrent_pool.items(),
                        key=lambda torrent: site_order[torrent[1]["site"]],
                    )
                )
            client.flush()
            time.sleep(1)
            for name, torrent in torrent_pool.items():
                site = torrent["site"]
                if (
                    client.task_count < config["task_count_max"]
                    and not name in client.tasks
                    and torrent["retry_count"] <= config[site]["retry_count_max"]
                    and "downloaded" in torrent
                    and not torrent["downloaded"]
                    and (
                        time.mktime(time.localtime()) - torrent["publish_at"]
                        <= config[site]["publish_within"]
                    )
                    and client.total_size + torrent["size"] <= config["space"]
                    and (
                        not config[site]["free_only"]
                        or torrent["free"]
                        and (
                            torrent["free_end"] == None
                            or torrent["free_end"] - time.mktime(time.localtime())
                            >= config[site]["free_time_min"]
                        )
                    )
                    and (not (config[site]["exclude_hr"] and torrent["hr"] != None))
                ):
                    client.add_torrent(torrent, name, logger)
                    time.sleep(1)
            lock.release()
            time.sleep(config["run_interval"])
        except Exception:
            if lock.locked():
                lock.release()
            try:
                print_t("出现异常，正在重新连接客户端…", True, logger)
                client.reconnect()
            except Exception:
                pass


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
                lock.release()
                time.sleep(config[site]["fetch_interval"])
            except Exception:
                if lock.locked():
                    lock.release()
                print_t(f"[{site}]获取种子信息失败，正在重试…", True, logger)
                time.sleep(config[site]["retry_interval"])

    return template


threads = [threading.Thread(target=task_processor)]
for site in config["sites"]:
    threads.append(threading.Thread(target=torrent_fetcher(site)))
for thread in threads:
    thread.setDaemon(True)
    thread.start()
while True:
    time.sleep(86400)
