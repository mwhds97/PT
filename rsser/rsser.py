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
    pool_lock.acquire(timeout=10)
    yaml_dump(torrent_pool, os.path.join(script_dir, "torrent_pool.yaml"))
    yaml_dump(list(name_queue), os.path.join(script_dir, "name_queue.yaml"))
    if pool_lock.locked():
        pool_lock.release()
    print_t("正在停止…", logger=logger)
    logger.close()
    sys.exit(0)


def uncaught_exception_handler(type, value, traceback):
    print_t("发生未知错误，正在保存种子数据…", logger=logger)
    terminate()


def SIGINT_handler(signum, frame):
    print_t("正在保存种子数据…", logger=logger)
    terminate()


script_dir = os.path.dirname(
    sys.executable if getattr(sys, "frozen", False) else __file__
)
sys.excepthook = uncaught_exception_handler
signal.signal(signal.SIGINT, SIGINT_handler)
try:
    os.makedirs(os.path.join(script_dir, "logs"), exist_ok=True)
except Exception:
    print_t("创建日志目录失败")
    sys.exit(0)
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
    err_info = "配置文件无法读取或为空"
    config = yaml_read(os.path.join(script_dir, "config.yaml"))
    if config == {}:
        raise Exception
    err_info = "顶层键错误"
    if set(config.keys()) != {
        "torrent_pool_size",
        "sort_by",
        "snippets",
        "clients",
        "volumes",
        "sites",
        "projects",
    }:
        raise Exception
    err_info = "排序选项有误"
    if not set(config["sort_by"].keys()) <= {
        "size",
        "publish_time",
        "seeder",
        "leecher",
        "snatch",
        "site",
    }:
        raise Exception
    err_info = "客户端配置有误"
    for name, client in config["clients"].items():
        for snippet in client["snippets"]:
            config["clients"][name] = {
                **config["snippets"][snippet],
                **config["clients"][name],
            }
        del config["clients"][name]["snippets"]
        if not (
            (
                config["clients"][name]["type"] == "deluge"
                and set(config["clients"][name].keys())
                == {
                    "type",
                    "host",
                    "user",
                    "pass",
                    "timeout",
                    "reconnect_interval",
                    "run_interval",
                    "task_count_max",
                }
            )
            or (
                config["clients"][name]["type"] == "qbittorrent"
                and set(config["clients"][name].keys())
                == {
                    "type",
                    "host",
                    "user",
                    "pass",
                    "headers",
                    "timeout",
                    "reconnect_interval",
                    "run_interval",
                    "task_count_max",
                }
            )
        ):
            raise Exception
    err_info = "站点配置有误"
    for name, site in config["sites"].items():
        for snippet in site["snippets"]:
            config["sites"][name] = {
                **config["snippets"][snippet],
                **config["sites"][name],
            }
        del config["sites"][name]["snippets"]
        if set(config["sites"][name].keys()) != {
            "rss",
            "rss_timeout",
            "web",
            "web_timeout",
            "cookies",
            "user_agent",
            "proxies",
            "fetch_interval",
            "retry_interval",
            "priority",
            "timezone",
        }:
            raise Exception
    err_info = "任务计划配置有误"
    for name, project in config["projects"].items():
        for snippet in project["snippets"]:
            config["projects"][name] = {
                **config["snippets"][snippet],
                **config["projects"][name],
            }
        del config["projects"][name]["snippets"]
        if set(config["projects"][name].keys()) != {
            "client",
            "sites",
            "path",
            "volume",
            "regexp",
            "publish_within",
            "size",
            "seeder",
            "leecher",
            "snatch",
            "free_only",
            "free_time_min",
            "free_end_escape",
            "escape_trigger_time",
            "hr_time_max",
            "hr_seed_delay",
            "hr_seed_ratio",
            "ignore_hr_seeding",
            "ignore_hr_leeching",
            "task_count_max",
            "retry_count_max",
            "extra_options",
            "remove_conditions",
        }:
            raise Exception
    del config["snippets"]
    err_info = "任务计划缺失对应站点配置"
    active_sites = set()
    for _, project in config["projects"].items():
        for site in project["sites"]:
            active_sites.add(site)
    if not active_sites <= set(config["sites"].keys()):
        raise Exception
    err_info = "任务计划缺失对应客户端配置"
    active_clients = set(
        [project["client"] for _, project in config["projects"].items()]
    )
    if not active_clients <= set(config["clients"].keys()):
        raise Exception
except Exception:
    print_t(f"配置文件加载失败，原因：{err_info}", logger=logger)
    logger.close()
    sys.exit(0)
torrent_pool = yaml_read(os.path.join(script_dir, "torrent_pool.yaml"))
invalid_torrents = [
    name
    for name, torrent in torrent_pool.items()
    if "project" not in torrent
    or torrent["project"] not in config["projects"]
    or torrent["site"] not in config["projects"][torrent["project"]]["sites"]
]
name_list = yaml_read(os.path.join(script_dir, "name_queue.yaml"))
name_list = [name for name in name_list if name not in invalid_torrents]
name_queue = deque(maxlen=config["torrent_pool_size"])
name_queue.extend(name_list)
torrent_pool = {
    name: torrent for name, torrent in torrent_pool.items() if name in name_queue
}
clients = []
for client in active_clients:
    try:
        clients.append(eval(config["clients"][client]["type"] + "(client, config)"))
    except Exception:
        print_t(f"[{client}] 无法连接客户端，请重试", logger=logger)
        logger.close()
        sys.exit(0)
tasks_overall = {}
pool_lock = threading.Lock()
op_lock = threading.Lock()


def task_processor(client):
    def template():
        while True:
            try:
                client.flush()
                print_t(f"[{client.name}] 客户端连接正常，正在等候任务…", True)
                tasks_overall[client.name] = client.tasks
                if op_lock.locked():
                    op_lock.release()
                tasks = deepcopy(client.tasks)
                pool_lock.acquire(timeout=10)
                pool = deepcopy(torrent_pool)
                if pool_lock.locked():
                    pool_lock.release()
                for name, stats in tasks.items():
                    try:
                        pool_lock.acquire(timeout=10)
                        if name in torrent_pool:
                            torrent_pool[name]["downloaded"] = True
                        if pool_lock.locked():
                            pool_lock.release()
                        op_lock.acquire(timeout=120)
                        to_remove = False
                        if name in pool:
                            torrent = pool[name]
                            if (
                                config["projects"][torrent["project"]]["client"]
                                != client.name
                            ):
                                if op_lock.locked():
                                    op_lock.release()
                                continue
                            project = config["projects"][torrent["project"]]
                            if (
                                re.search(r"registered|回收", stats["tracker_status"])
                                is not None
                            ):
                                to_remove = True
                                info = "种子被撤除"
                            elif stats["seeding_time"] == 0:
                                if (
                                    project["ignore_hr_leeching"]
                                    or torrent["hr"] is None
                                ):
                                    if project["free_end_escape"] and (
                                        not torrent["free"]
                                        or (
                                            torrent["free_end"] is not None
                                            and torrent["free_end"]
                                            - time.mktime(time.localtime())
                                            < project["escape_trigger_time"]
                                        )
                                    ):
                                        to_remove = True
                                        info = "免费失效"
                                    for condition in project["remove_conditions"]:
                                        if condition["period"] in ["L", "B"] and eval(
                                            generate_exp(condition["exp"])
                                        ):
                                            to_remove = True
                                            info = condition["info"]
                                            break
                            else:
                                if (
                                    project["ignore_hr_seeding"]
                                    or torrent["hr"] is None
                                ):
                                    hr_time = 0
                                elif (
                                    project["hr_seed_ratio"] is not None
                                    and stats["ratio"] >= project["hr_seed_ratio"]
                                ):
                                    hr_time = project["hr_seed_delay"]
                                else:
                                    hr_time = torrent["hr"] + project["hr_seed_delay"]
                                if stats["seeding_time"] >= hr_time:
                                    for condition in project["remove_conditions"]:
                                        if condition["period"] in ["S", "B"] and eval(
                                            generate_exp(condition["exp"])
                                        ):
                                            to_remove = True
                                            info = condition["info"]
                                            break
                        if to_remove:
                            client.remove_torrent(torrent, name, info, logger)
                            time.sleep(5)
                            client.flush()
                            tasks_overall[client.name] = client.tasks
                        if op_lock.locked():
                            op_lock.release()
                    except Exception:
                        print_t(
                            f'[{client.name}] 删除种子 {name}（{torrent["size"]:.2f}GB）可能已失败，尝试删除其他种子…',
                            logger=logger,
                        )
                        time.sleep(5)
                        client.flush()
                        tasks_overall[client.name] = client.tasks
                        if op_lock.locked():
                            op_lock.release()
                pool_lock.acquire(timeout=10)
                pool = deepcopy(torrent_pool)
                if pool_lock.locked():
                    pool_lock.release()
                for name, torrent in pool.items():
                    try:
                        if (
                            config["projects"][torrent["project"]]["client"]
                            != client.name
                        ):
                            continue
                        project = config["projects"][torrent["project"]]
                        op_lock.acquire(timeout=120)
                        if (
                            name not in client.tasks
                            and not torrent["downloaded"]
                            and client.task_count
                            < config["clients"][client.name]["task_count_max"]
                            and len(
                                [
                                    title
                                    for title in client.tasks
                                    if title in pool
                                    and pool[title]["project"] == torrent["project"]
                                ]
                            )
                            < project["task_count_max"]
                            and (
                                set(tasks_overall.keys()) == active_clients
                                and torrent["size"]
                                + sum(
                                    [
                                        sum(
                                            [
                                                task["size"]
                                                for title, task in task_dict.items()
                                                if title in pool
                                                and project["volume"]
                                                == config["projects"][
                                                    pool[title]["project"]
                                                ]["volume"]
                                            ]
                                        )
                                        for task_dict in tasks_overall.values()
                                    ]
                                )
                                / 1073741824
                                <= config["volumes"][project["volume"]]
                            )
                            and torrent["retry_count"] < project["retry_count_max"]
                            and project["seeder"][0]
                            <= torrent["seeder"]
                            <= project["seeder"][1]
                            and project["leecher"][0]
                            <= torrent["leecher"]
                            <= project["leecher"][1]
                            and project["snatch"][0]
                            <= torrent["snatch"]
                            <= project["snatch"][1]
                            and (
                                time.mktime(time.localtime()) - torrent["publish_time"]
                                <= project["publish_within"]
                            )
                            and (
                                not project["free_only"]
                                or (
                                    torrent["free"]
                                    and (
                                        torrent["free_end"] is None
                                        or torrent["free_end"]
                                        - time.mktime(time.localtime())
                                        >= project["free_time_min"]
                                    )
                                )
                            )
                            and (
                                torrent["hr"] is None
                                or torrent["hr"] <= project["hr_time_max"]
                            )
                        ):
                            pool_lock.acquire(timeout=10)
                            if name in torrent_pool:
                                torrent_pool[name]["retry_count"] += 1
                            if pool_lock.locked():
                                pool_lock.release()
                            client.add_torrent(torrent, name, logger)
                            time.sleep(10)
                            client.flush()
                            tasks_overall[client.name] = client.tasks
                        if op_lock.locked():
                            op_lock.release()
                    except Exception:
                        print_t(
                            f'[{client.name}] 添加种子 {name}（{torrent["size"]:.2f}GB）可能已失败，尝试添加其他种子…',
                            logger=logger,
                        )
                        time.sleep(10)
                        client.flush()
                        tasks_overall[client.name] = client.tasks
                        if op_lock.locked():
                            op_lock.release()
                time.sleep(config["clients"][client.name]["run_interval"])
            except Exception:
                print_t(f"[{client.name}] 出现异常，正在重新连接客户端…", logger=logger)
                client.reconnect()

    return template


def torrent_fetcher(site):
    def template():
        global torrent_pool
        while True:
            try:
                torrents = eval(site + '(config["sites"])')
            except Exception:
                print_t(f"[{site}] 获取种子信息失败，正在重试…", logger=logger)
                time.sleep(config["sites"][site]["retry_interval"])
                continue
            if torrents != {}:
                pool_lock.acquire(timeout=10)
                for name, torrent in torrents.items():
                    project = match_project(torrent, config["projects"])
                    if name in torrent_pool:
                        torrent_pool[name] = {
                            **torrent_pool[name],
                            **{
                                key: value
                                for key, value in torrent.items()
                                if key != "downloaded"
                            },
                            **{
                                "downloaded": torrent_pool[name]["downloaded"]
                                or torrent["downloaded"]
                            },
                        }
                    elif project is not None:
                        torrent_pool[name] = {
                            **torrent,
                            "retry_count": -1,
                            "project": project,
                        }
                        name_queue.append(name)
                torrent_pool = {
                    name: torrent
                    for name, torrent in torrent_pool.items()
                    if name in name_queue
                }
                sort_keys = reversed(list(config["sort_by"].keys()))
                for sort_key in sort_keys:
                    torrent_pool = dict(
                        sorted(
                            torrent_pool.items(),
                            key=lambda torrent: torrent[1][sort_key]
                            if sort_key != "site"
                            else config["sites"][torrent[1]["site"]]["priority"],
                            reverse=config["sort_by"][sort_key],
                        )
                    )
                if pool_lock.locked():
                    pool_lock.release()
            time.sleep(config["sites"][site]["fetch_interval"])

    return template


threads = []
for client in clients:
    threads.append(threading.Thread(target=task_processor(client)))
for site in active_sites:
    threads.append(threading.Thread(target=torrent_fetcher(site)))
for thread in threads:
    thread.setDaemon(True)
    thread.start()
while True:
    time.sleep(86400)
