#!/usr/bin/env python3

import os
import random
import signal
import sys
import threading
import time
from collections import deque
from copy import deepcopy
from typing import Union

import sites
from clients import deluge, qbittorrent
from init import init
from utils import *


script_dir = os.path.dirname(
    sys.executable if getattr(sys, "frozen", False) else __file__
)
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
    config = yaml_read(os.path.join(script_dir, "config.yaml"))
    if config == {}:
        raise Exception("文件读取错误或为空")
    active_sites, active_clients = init(config)
except Exception as e:
    print_t(f"配置文件加载失败，原因：{str(e)}", logger=logger)
    logger.close()
    sys.exit(0)


def match_project(torrent: dict, allow_site_only: bool = False) -> Union[str, None]:
    first_match_site_project = None
    for name, project in config["projects"].items():
        if torrent["site"] in project["sites"]:
            if first_match_site_project is None:
                first_match_site_project = name
            match_regexp = False
            for pattern in project["regexp"]:
                if re.search(pattern, torrent["title"]) is not None:
                    match_regexp = True
                    break
            match_size = False
            for range in project["size"]:
                if range[0] <= torrent["size"] <= range[1]:
                    match_size = True
                    break
            if match_regexp and match_size:
                return name
    if allow_site_only:
        return first_match_site_project
    return None


torrent_pool = yaml_read(os.path.join(script_dir, "torrent_pool.yaml"))
invalid_torrents = []
for name, torrent in torrent_pool.items():
    if re.match(r"\[.+\]\d+$", name) is None:
        invalid_torrents.append(name)
    elif set(torrent.keys()) != {
        "site",
        "title",
        "size",
        "link",
        "publish_time",
        "free",
        "free_end",
        "hr",
        "downloaded",
        "seeder",
        "leecher",
        "snatch",
        "retry_count",
        "project",
    }:
        invalid_torrents.append(name)
    elif torrent["project"] not in config["projects"]:
        project = match_project(torrent, True)
        if project is not None:
            torrent["project"] = project
        else:
            invalid_torrents.append(name)
name_list = yaml_read(os.path.join(script_dir, "name_queue.yaml"))
name_list = [name for name in name_list if name not in invalid_torrents]
name_queue = deque(maxlen=config["pool"]["size"])
name_queue.extend(name_list)


def renew_torrent_pool():
    global torrent_pool
    torrent_pool = {
        name: torrent for name, torrent in torrent_pool.items() if name in name_queue
    }
    sort_keys = reversed(list(config["pool"]["sort_by"].keys()))
    for sort_key in sort_keys:
        torrent_pool = dict(
            sorted(
                torrent_pool.items(),
                key=lambda torrent: torrent[1][sort_key]
                if sort_key != "site"
                else list(config["sites"].keys()).index(torrent[1]["site"]),
                reverse=config["pool"]["sort_by"][sort_key],
            )
        )


renew_torrent_pool()
clients = []
for client in active_clients:
    try:
        clients.append(
            eval(
                f'{config["clients"][client]["type"]}(client, config["clients"][client])'
            )
        )
    except Exception:
        print_t(f"[{client}] 无法连接客户端，请重试", logger=logger)
        logger.close()
        sys.exit(0)


tasks_overall = {}
torrents_candidate = {client: {} for client in active_clients}
pool_lock = threading.Lock()
task_lock = threading.Lock()


def match_remove_conditions(torrent: dict, stats: dict) -> Union[tuple, None]:
    def generate_exp(exp: str) -> str:
        fields = [
            "size",
            "active_time",
            "seeding_time",
            "seeder",
            "leecher",
            "progress",
            "ratio",
            "up_div_down",
            "uploaded",
            "downloaded",
            "upload_speed",
            "download_speed",
            "eta",
        ]
        for field in fields:
            exp = re.sub(field, f'stats["{field}"]', exp)
        return f"({exp})"

    project = config["projects"][torrent["project"]]
    site = config["sites"][torrent["site"]]
    if (
        re.search(
            r"(?i)not.*reg|not.*auth|delete|remove|dupe|trump|rev|nuke|same|diff|loc|收|除|撤|同|重",
            stats["tracker_status"],
        )
        is not None
    ):
        return ("服务器信息异常", False)
    if stats["seeding_time"] == 0:
        if (
            project["ignore_hr_leeching"]
            or torrent["hr"] is None
            or stats["progress"] < site["hr_min_progress"]
        ):
            if project["free_end_escape"]:
                if not torrent["free"]:
                    return ("免费已失效", False)
                elif torrent["free_end"] is not None:
                    if (
                        torrent["free_end"] - time.mktime(time.localtime())
                        < project["escape_trigger_time"]
                    ):
                        return ("免费即将失效", True)
            for condition in project["remove_conditions"]:
                if condition["period"] in ["L", "B"] and eval(
                    generate_exp(condition["exp"])
                ):
                    return (condition["info"], True)
    elif stats["seeding_time"] > 0:
        if project["ignore_hr_seeding"] or torrent["hr"] is None:
            hr_time = 0
        elif (
            site["hr_seed_ratio"] is not None
            and stats["up_div_down"] >= site["hr_seed_ratio"]
        ):
            hr_time = project["hr_seed_delay"]
        else:
            hr_time = torrent["hr"] + project["hr_seed_delay"]
        if stats["seeding_time"] >= hr_time:
            for condition in project["remove_conditions"]:
                if condition["period"] in ["S", "B"] and eval(
                    generate_exp(condition["exp"])
                ):
                    return (condition["info"], True)
    return None


def unlock(lock: threading.Lock, locked: bool = True):
    if lock.locked() and locked:
        lock.release()


def task_generator():
    global torrents_candidate

    def match_add_conditions(
        torrent: dict, client: Union[deluge, qbittorrent], pool: dict, tasks: dict
    ) -> bool:
        project = config["projects"][torrent["project"]]
        volume = project["clients"][client.name]["volume"]
        client_task_count = 0
        client_total_size = 0
        project_task_count = 0
        project_total_size = 0
        site_task_count = 0
        site_total_size = 0
        volume_total_size = 0
        for group_client, task_group in tasks.items():
            group_total_size = 0
            for name in task_group:
                if name in pool:
                    if group_client == client.name:
                        client_task_count += 1
                        client_total_size += pool[name]["size"]
                    if pool[name]["project"] == torrent["project"]:
                        project_task_count += 1
                        project_total_size += pool[name]["size"]
                    if pool[name]["site"] == torrent["site"]:
                        site_task_count += 1
                        site_total_size += pool[name]["size"]
                    task_project = config["projects"][pool[name]["project"]]
                    if group_client in task_project["clients"]:
                        if task_project["clients"][group_client]["volume"] == volume:
                            group_total_size += pool[name]["size"]
            volume_total_size += group_total_size
        matchers = [
            lambda: not torrent["downloaded"],
            lambda: torrent["retry_count"] < project["retry_count_max"],
            lambda: project["seeder"][0] <= torrent["seeder"] <= project["seeder"][1],
            lambda: project["leecher"][0]
            <= torrent["leecher"]
            <= project["leecher"][1],
            lambda: project["snatch"][0] <= torrent["snatch"] <= project["snatch"][1],
            lambda: time.mktime(time.localtime()) - torrent["publish_time"]
            <= project["publish_within"],
            lambda: not project["free_only"]
            or (
                torrent["free"]
                and (
                    torrent["free_end"] is None
                    or torrent["free_end"] - time.mktime(time.localtime())
                    >= project["free_time_min"]
                )
            ),
            lambda: torrent["hr"] is None or torrent["hr"] <= project["hr_time_max"],
            lambda: client.name in project["clients"],
            lambda: client_task_count < client.config["task_count_max"],
            lambda: client_total_size + torrent["size"]
            <= client.config["total_size_max"],
            lambda: client.download_speed < client.config["download_speed_max"],
            lambda: project_task_count < project["task_count_max"],
            lambda: project_total_size + torrent["size"] <= project["total_size_max"],
            lambda: site_task_count
            < config["sites"][torrent["site"]]["task_count_max"],
            lambda: site_total_size + torrent["size"]
            <= config["sites"][torrent["site"]]["total_size_max"],
            lambda: volume is None
            or volume_total_size + torrent["size"] <= config["volumes"][volume],
        ]
        for matcher in matchers:
            if not matcher():
                return False
        return True

    while True:
        task_locked = task_lock.acquire(timeout=300)
        start = set(tasks_overall.keys()) == active_clients
        unlock(task_lock, task_locked)
        if start:
            break
        time.sleep(5)

    def generate_exp(exp: str) -> str:
        client_fields = [
            "task_count",
            "total_size",
            "upload_speed",
            "download_speed",
        ]
        torrent_fields = ["seeder", "leecher", "snatch"]
        for field in client_fields:
            exp = re.sub(field, f"client.{field}", exp)
        for field in torrent_fields:
            exp = re.sub(field, f'torrent["{field}"]', exp)
        exp = re.sub(r"bandwidth", 'client.config["bandwidth"]', exp)
        exp = re.sub(
            r"volume_size",
            'config["volumes"][project["clients"][client.name]["volume"]]',
            exp,
        )
        exp = re.sub(r"torrent_size", 'torrent["size"]', exp)
        exp = re.sub(r"hr_time", 'torrent["hr"]', exp)
        return f"({exp})"

    while True:
        task_locked = task_lock.acquire(timeout=300)
        tasks = deepcopy(tasks_overall)
        pool_locked = pool_lock.acquire(timeout=30)
        renew_torrent_pool()
        pool = deepcopy(torrent_pool)
        unlock(pool_lock, pool_locked)
        pool = dict(
            sorted(
                pool.items(),
                key=lambda torrent: list(config["projects"].keys()).index(
                    torrent[1]["project"]
                ),
            )
        )
        torrents_candidate = {client: {} for client in active_clients}
        for name, torrent in pool.items():
            project = config["projects"][torrent["project"]]
            clients_candidate = [
                client for client in clients if client.name in project["clients"]
            ]
            random.shuffle(clients_candidate)
            clients_candidate = sorted(
                clients_candidate,
                key=lambda client: eval(generate_exp(project["load_balance_key"])),
            )
            for client in clients_candidate:
                if name not in [
                    task for _, task_group in tasks.items() for task in task_group
                ] and match_add_conditions(torrent, client, pool, tasks):
                    torrents_candidate[client.name][name] = torrent
                    tasks[client.name][name] = {}
                    break
        unlock(task_lock, task_locked)
        del pool
        time.sleep(config["pool"]["scan_interval"])


def task_processor(client: Union[deluge, qbittorrent]):
    def template():
        halted = False
        reconnect_count = 0
        while True:
            try:
                if reconnect_count > 10:
                    unlock(task_lock, halted)
                    halted = False
                client.flush()
                print_t(f"[{client.name}] 客户端连接正常，正在等候任务…", True)
                reconnect_count = 0
                if not halted:
                    task_locked = task_lock.acquire(timeout=300)
                    tasks_overall[client.name] = deepcopy(client.tasks)
                    unlock(task_lock, task_locked)
                else:
                    tasks_overall[client.name] = deepcopy(client.tasks)
                    unlock(task_lock)
                    halted = False
                tasks = deepcopy(client.tasks)
                pool_locked = pool_lock.acquire(timeout=30)
                pool = deepcopy(torrent_pool)
                unlock(pool_lock, pool_locked)
                for name, stats in tasks.items():
                    pool_locked = pool_lock.acquire(timeout=30)
                    if name in torrent_pool:
                        torrent_pool[name]["downloaded"] = True
                    unlock(pool_lock, pool_locked)
                    if name in pool:
                        torrent = pool[name]
                        info = match_remove_conditions(torrent, stats)
                        if info is not None:
                            halted = task_lock.acquire(timeout=300)
                            try:
                                client.remove_torrent(
                                    torrent, name, info[0], info[1], logger
                                )
                            except Exception:
                                print_t(
                                    f'[{client.name}] 删除种子 {name}（{torrent["size"]:.2f}GB）可能已失败，尝试删除其他种子…',
                                    logger=logger,
                                )
                            time.sleep(5)
                            client.flush()
                            tasks_overall[client.name] = deepcopy(client.tasks)
                            unlock(task_lock, halted)
                            halted = False
                del pool

                if client.download_speed < client.config["download_speed_max"]:
                    pool_locked = pool_lock.acquire(timeout=30)
                    pool = deepcopy(torrent_pool)
                    unlock(pool_lock, pool_locked)
                    task_locked = task_lock.acquire(timeout=300)
                    torrents = deepcopy(torrents_candidate[client.name])
                    unlock(task_lock, task_locked)
                    for name, torrent in torrents.items():
                        halted = task_lock.acquire(timeout=300)
                        for _, task_group in tasks_overall.items():
                            if name in task_group:
                                break
                        else:
                            project = config["projects"][torrent["project"]]
                            pool_locked = pool_lock.acquire(timeout=30)
                            if name in torrent_pool:
                                if (
                                    torrent_pool[name]["retry_count"]
                                    >= project["retry_count_max"]
                                ):
                                    unlock(task_lock, halted)
                                    halted = False
                                    unlock(pool_lock, pool_locked)
                                    continue
                                else:
                                    torrent_pool[name]["retry_count"] += 1
                                    unlock(pool_lock, pool_locked)
                            try:
                                client.add_torrent(
                                    torrent,
                                    name,
                                    project["clients"][client.name]["path"],
                                    project["clients"][client.name]["extra_options"],
                                    logger,
                                )
                            except Exception:
                                print_t(
                                    f'[{client.name}] 添加种子 {name}（{torrent["size"]:.2f}GB）可能已失败，尝试添加其他种子…',
                                    logger=logger,
                                )
                            time.sleep(10)
                            client.flush()
                            if name in client.tasks:
                                pool_locked = pool_lock.acquire(timeout=30)
                                if name in torrent_pool:
                                    torrent_pool[name]["downloaded"] = True
                                unlock(pool_lock, pool_locked)
                            tasks_overall[client.name] = deepcopy(client.tasks)
                        unlock(task_lock, halted)
                        halted = False
                    del pool
                time.sleep(client.config["run_interval"])
            except Exception:
                print_t(f"[{client.name}] 出现异常，正在重新连接客户端…", logger=logger)
                reconnect_count += 1
                client.reconnect()

    return template


def torrent_fetcher(site: str, config: dict):
    def template():
        retry_count = 0
        while True:
            try:
                torrents = eval(f"sites.{site}(config)")
                retry_count = 0
            except Exception:
                print_t(f"[{site}] 获取种子信息失败，正在重试…", logger=logger)
                retry_count += 1
                if retry_count <= 5 or config["retry_pause_time"] is None:
                    time.sleep(config["retry_interval"])
                else:
                    time.sleep(config["retry_pause_time"])
                    retry_count = 0
                continue
            if torrents != {}:
                pool_locked = pool_lock.acquire(timeout=30)
                for name, torrent in torrents.items():
                    project = match_project(torrent) if "link" in torrent else None
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
                unlock(pool_lock, pool_locked)
            time.sleep(config["fetch_interval"])

    return template


def pool_saver(loop: bool, interval: Union[int, float], block: bool = False):
    def template():
        while True:
            time.sleep(interval)
            print_t("正在保存种子数据…", logger=logger)
            pool_locked = pool_lock.acquire(timeout=300)
            renew_torrent_pool()
            try:
                yaml_dump(torrent_pool, os.path.join(script_dir, "torrent_pool.yaml"))
                yaml_dump(list(name_queue), os.path.join(script_dir, "name_queue.yaml"))
            except Exception:
                print_t("种子数据保存失败", logger=logger)
            if not block:
                unlock(pool_lock, pool_locked)
            if not loop:
                break

    return template


def terminate():
    pool_saver(False, 0, True)()
    print_t("正在停止…", logger=logger)
    logger.close()
    sys.exit(0)


def uncaught_exception_handler(type, value, traceback):
    print_t("发生未知错误", logger=logger)
    terminate()


def SIGINT_handler(signum, frame):
    terminate()


sys.excepthook = uncaught_exception_handler
signal.signal(signal.SIGINT, SIGINT_handler)
threads = []
for client in clients:
    threads.append(threading.Thread(target=task_processor(client)))
for site in active_sites:
    threads.append(
        threading.Thread(target=torrent_fetcher(site, config["sites"][site]))
    )
threads.append(
    threading.Thread(target=pool_saver(True, config["pool"]["save_interval"]))
)
threads.append(threading.Thread(target=task_generator))
for thread in threads:
    thread.setDaemon(True)
    thread.start()
while True:
    time.sleep(86400)
    logger.flush()
