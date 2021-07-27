#!/usr/bin/env python3
# coding=utf-8

import signal
import sys
import threading
import time
from collections import deque

from deluge import *
from sites import *
from utils import *


def uncaught_exception_handler(type, value, traceback):
    print_t("发生未知错误，正在保存种子数据…")
    lock.acquire()
    yaml_dump(torrent_pool, "torrent_pool.yaml")
    yaml_dump(list(name_queue), "name_queue.yaml")
    lock.release()
    print_t("正在停止…")
    sys.exit(0)


sys.excepthook = uncaught_exception_handler


def SIGINT_handler(signum, frame):
    print_t("正在保存种子数据…")
    lock.acquire()
    yaml_dump(torrent_pool, "torrent_pool.yaml")
    yaml_dump(list(name_queue), "name_queue.yaml")
    lock.release()
    print_t("正在停止…")
    sys.exit(0)


signal.signal(signal.SIGINT, SIGINT_handler)


config = yaml_read("config.yaml")
torrent_pool = yaml_read("torrent_pool.yaml")
name_queue = deque(maxlen=config["torrent_pool_size"])
name_queue.extend(yaml_read("name_queue.yaml"))
try:
    daemon = deluge(config)
except Exception:
    print_t("无法连接客户端，请重试", sol="")
    sys.exit(0)
lock = threading.Lock()


def task_processor():
    global torrent_pool
    while True:
        try:
            daemon.flush()
            print_t("客户端连接正常，正在等候任务…", "\r")
            lock.acquire()
            for name, stats in daemon.tasks.items():
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
                            config[site]["ignore_hr"] or torrent["hr"] == None
                        ) and stats["active_time"] >= config[site]["life"]:
                            to_remove = True
                            info = "活动时长超过限制"
                        else:
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
                    daemon.remove_torrent(name, info)
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
            for name, torrent in torrent_pool.items():
                site = torrent["site"]
                if (
                    daemon.task_count < config["task_count_max"]
                    and not name in daemon.tasks
                    and "downloaded" in torrent
                    and not torrent["downloaded"]
                    and (
                        time.mktime(time.localtime()) - torrent["publish_at"]
                        <= config[site]["publish_within"]
                    )
                    and daemon.total_size + torrent["size"] <= config["space"]
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
                    daemon.add_torrent(torrent, name)
            lock.release()
            time.sleep(config["run_interval"])
        except Exception:
            if lock.locked():
                lock.release()
            try:
                print_t("出现异常，正在重新连接客户端…", "\r")
                daemon.reconnect()
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
                        torrent_pool[name] = torrent
                        name_queue.append(name)
                lock.release()
                time.sleep(config[site]["fetch_interval"])
            except Exception:
                if lock.locked():
                    lock.release()
                print_t("[{}]获取种子信息失败，正在重试…".format(site), "\r")
                time.sleep(5)

    return template


threads = [threading.Thread(target=task_processor)]
for site in config["sites"]:
    threads.append(threading.Thread(target=torrent_fetcher(site)))
for thread in threads:
    thread.setDaemon(True)
    thread.start()
while True:
    time.sleep(1)
