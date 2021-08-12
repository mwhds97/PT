import json
import re
import time

import requests
from deluge_client import DelugeRPCClient

from utils import *


class deluge:
    def __init__(self, config):
        self.config = config
        self.new_client()

    def __del__(self):
        try:
            self.client.disconnect()
        except Exception:
            pass

    def new_client(self):
        self.client = DelugeRPCClient(
            self.config["host"].split(":")[0],
            int(self.config["host"].split(":")[1]),
            self.config["user"],
            self.config["pass"],
            True,
            False,
        )
        self.client.timeout = self.config["timeout"]
        self.client.connect()

    def reconnect(self):
        try:
            self.client.disconnect()
        except Exception:
            pass
        time.sleep(self.config["reconnect_interval"])
        try:
            self.new_client()
        except Exception:
            pass

    def flush(self):
        key_map = {
            "total_wanted": "size",
            "active_time": "active_time",
            "seeding_time": "seeding_time",
            "total_seeds": "seeder",
            "total_peers": "leecher",
            "progress": "progress",
            "ratio": "ratio",
            "total_uploaded": "uploaded",
            "total_done": "downloaded",
            "upload_payload_rate": "upload_speed",
            "download_payload_rate": "download_speed",
            "eta": "eta",
            "tracker_status": "tracker_status",
        }
        self.tasks = self.client.call(
            "core.get_torrents_status",
            {},
            [
                "name",
                "total_wanted",
                "active_time",
                "seeding_time",
                "total_seeds",
                "total_peers",
                "progress",
                "ratio",
                "total_uploaded",
                "total_done",
                "upload_payload_rate",
                "download_payload_rate",
                "eta",
                "tracker_status",
            ],
        )
        self.tasks = {
            stats["name"]: dict(
                {"hash": hash},
                **{
                    key_map[key]: value for key, value in stats.items() if key != "name"
                },
            )
            for hash, stats in self.tasks.items()
        }
        self.total_size = (
            sum([task["size"] for _, task in self.tasks.items()]) / 1073741824
        )
        self.task_count = len(self.tasks)

    def add_torrent(self, torrent, name, logger):
        free_end = (
            "N/A"
            if torrent["free_end"] == None
            else time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(torrent["free_end"]))
        )
        text = f"""添加种子{name}\
，免费：{"是" if torrent["free"] else "否"}\
，到期时间：{free_end}\
，H&R：{"无" if torrent["hr"] == None else f'{torrent["hr"] / 3600:.2f}小时'}\
，体积：{torrent["size"]:.2f}GB\
，总体积：{self.total_size + torrent["size"]:.2f}GB\
，任务数：{self.task_count + 1}"""
        try:
            self.client.call(
                "core.add_torrent_url",
                torrent["link"],
                dict(
                    {
                        "name": name,
                        "download_location": self.config[torrent["site"]]["path"],
                        "add_paused": False,
                    },
                    **self.config[torrent["site"]]["extra_options"],
                ),
            )
            print_t(text, logger=logger)
        except Exception as e:
            hash = re.match("Torrent already in session \((\w{40})\)", str(e))
            if hash != None:
                self.client.call(
                    "core.set_torrent_options", hash.group(1), {"name": name}
                )
            elif re.match("Torrent already being added", str(e)) == None:
                torrent["retry_count"] += 1
                raise e

    def remove_torrent(self, torrent, name, info, logger):
        text = f'删除种子{name}\
，原因：{info}\
，体积：{torrent["size"]:.2f}GB\
，总体积：{self.total_size - self.tasks[name]["size"] / 1073741824 + 0:.2f}GB\
，任务数：{self.task_count - 1}'
        self.client.call("core.remove_torrent", self.tasks[name]["hash"], True)
        print_t(text, logger=logger)


class qbittorrent:
    def __init__(self, config):
        self.config = config
        self.new_client()

    def __del__(self):
        self.get_response("/api/v2/auth/logout", nobreak=True)

    def get_response(self, api, data={}, nobreak=False):
        try:
            response = requests.post(
                url=self.config["host"] + api,
                headers=dict(
                    {
                        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
                        "Cookie": self.cookies,
                    },
                    **self.config["headers"],
                ),
                data=data,
                timeout=self.config["timeout"],
            )
            if response.status_code != 200:
                raise Exception
        except Exception as e:
            if nobreak:
                return requests.Response()
            raise e
        return response

    def new_client(self):
        self.cookies = ""
        response = self.get_response(
            "/api/v2/auth/login",
            {"username": self.config["user"], "password": self.config["pass"]},
        )
        self.cookies = response.headers["set-cookie"]

    def reconnect(self):
        self.get_response("/api/v2/auth/logout", nobreak=True)
        time.sleep(self.config["reconnect_interval"])
        try:
            self.new_client()
        except Exception:
            pass

    def flush(self):
        key_map = {
            "hash": "hash",
            "size": "size",
            "time_active": "active_time",
            "seeding_time": "seeding_time",
            "num_complete": "seeder",
            "num_incomplete": "leecher",
            "progress": "progress",
            "ratio": "ratio",
            "uploaded": "uploaded",
            "downloaded": "downloaded",
            "upspeed": "upload_speed",
            "dlspeed": "download_speed",
            "eta": "eta",
            "tracker": "tracker_status",
        }
        response = self.get_response("/api/v2/torrents/info")
        self.tasks = json.loads(response.text)
        self.tasks = {
            task["name"]: {
                key_map[key]: value
                for key, value in task.items()
                if key
                in [
                    "hash",
                    "size",
                    "time_active",
                    "seeding_time",
                    "num_complete",
                    "num_incomplete",
                    "progress",
                    "ratio",
                    "uploaded",
                    "downloaded",
                    "upspeed",
                    "dlspeed",
                    "eta",
                    "tracker",
                ]
            }
            for task in self.tasks
        }
        for name, stats in self.tasks.items():
            tracker_status = ""
            if stats["tracker_status"] == "":
                response = self.get_response(
                    "/api/v2/torrents/trackers", {"hash": stats["hash"]}, True
                )
                trackers = json.loads(response.text) if response.text != "" else []
                for tracker in trackers[3:]:
                    tracker_status += tracker["msg"]
            self.tasks[name]["tracker_status"] = tracker_status
        self.total_size = (
            sum([task["size"] for _, task in self.tasks.items()]) / 1073741824
        )
        self.task_count = len(self.tasks)

    def add_torrent(self, torrent, name, logger):
        free_end = (
            "N/A"
            if torrent["free_end"] == None
            else time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(torrent["free_end"]))
        )
        text = f"""添加种子{name}\
，免费：{"是" if torrent["free"] else "否"}\
，到期时间：{free_end}\
，H&R：{"无" if torrent["hr"] == None else f'{torrent["hr"] / 3600:.2f}小时'}\
，体积：{torrent["size"]:.2f}GB\
，总体积：{self.total_size + torrent["size"]:.2f}GB\
，任务数：{self.task_count + 1}"""
        try:
            self.get_response(
                "/api/v2/torrents/add",
                dict(
                    {
                        "urls": torrent["link"],
                        "savepath": self.config[torrent["site"]]["path"],
                        "rename": name,
                        "paused": "false",
                    },
                    **self.config[torrent["site"]]["extra_options"],
                ),
            )
            print_t(text, logger=logger)
        except Exception as e:
            torrent["retry_count"] += 1
            raise e

    def remove_torrent(self, torrent, name, info, logger):
        text = f'删除种子{name}\
，原因：{info}\
，体积：{torrent["size"]:.2f}GB\
，总体积：{self.total_size - self.tasks[name]["size"] / 1073741824 + 0:.2f}GB\
，任务数：{self.task_count - 1}'
        self.get_response(
            "/api/v2/torrents/delete",
            {"hashes": self.tasks[name]["hash"], "deleteFiles": "true"},
        )
        print_t(text, logger=logger)
