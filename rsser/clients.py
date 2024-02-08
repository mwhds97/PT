import json
import math
import random
import re
import socket
import ssl
import struct
import time
import zlib
from io import TextIOWrapper
from typing import Optional

import rencode
import requests

from utils import *


class deluge:
    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config
        self.context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.context.check_hostname = False
        self.context.verify_mode = ssl.CERT_NONE
        self.version = None
        self.new_client()

    def __del__(self):
        try:
            self.socket.close()
            del self.socket
        except Exception:
            pass

    def new_socket(self):
        self.socket = self.context.wrap_socket(
            socket.socket(socket.AF_INET, socket.SOCK_STREAM),
        )
        self.socket.settimeout(self.config["timeout"])
        self.socket.connect(
            (
                self.config["host"].split(":")[0],
                int(self.config["host"].split(":")[1]),
            )
        )

    def get_response(self, version: list, data: bytes = b""):
        flags = None
        null_count = 0
        while True:
            if null_count > 10:
                raise Exception
            recv = self.socket.recv(10)
            if len(recv) > 0:
                data += recv
                null_count = 0
            else:
                null_count += 1
            if version[0] == 2:
                if flags is None:
                    if len(data) < 5:
                        continue
                    header = data[:5]
                    data = data[5:]
                    if version[1] == 1:
                        if ord(header[:1]) != 1:
                            raise Exception
                        flags = struct.unpack("!I", header[1:])[0]
                    elif version[1] == 0:
                        if header[0] != b"D"[0]:
                            raise Exception
                        flags = struct.unpack("!i", header[1:])[0]
                if flags <= len(data):
                    data = zlib.decompress(data)
                    break
            elif version[0] == 1:
                try:
                    data = zlib.decompress(data)
                except zlib.error:
                    if len(recv) == 0:
                        raise Exception
                    continue
                break
        data = list(rencode.loads(data, decode_utf8=True))
        if data[0] == 1:
            return data[2]
        elif data[0] == 2:
            raise Exception

    def send_request(self, version: list, method: str, *args, **kwargs):
        self.request_id += 1
        request = zlib.compress(
            rencode.dumps(((self.request_id, method, args, kwargs),))
        )
        if version[0] == 2:
            if version[1] == 1:
                self.socket.send(struct.pack("!BI", 1, len(request)))
            elif version[1] == 0:
                self.socket.send(b"D" + struct.pack("!i", len(request)))
        self.socket.send(request)

    def call(self, method: str, *args, **kwargs):
        self.send_request(self.version, method, *args, **kwargs)
        return self.get_response(self.version)

    def new_client(self):
        self.new_socket()
        self.request_id = 0
        if self.version is None:
            self.send_request([1, 0], "daemon.info")
            self.send_request([2, 0], "daemon.info")
            self.send_request([2, 1], "daemon.info")
            recv = self.socket.recv(1)
            if recv[:1] == b"D":
                self.version = [2, 0]
                self.get_response(self.version, recv)
            elif ord(recv[:1]) == 1:
                self.version = [2, 1]
                self.get_response(self.version, recv)
            else:
                self.version = [1, 0]
                self.socket.close()
                del self.socket
                self.new_socket()
        if self.version[0] == 2:
            self.call(
                "daemon.login",
                self.config["user"],
                self.config["pass"],
                client_version="deluge",
            )
        elif self.version[0] == 1:
            self.call(
                "daemon.login",
                self.config["user"],
                self.config["pass"],
            )

    def reconnect(self):
        try:
            self.socket.close()
            del self.socket
        except Exception:
            pass
        time.sleep(eval(str(self.config["reconnect_interval"])))
        try:
            self.new_client()
        except Exception:
            pass

    def flush(self):
        key_map = {
            "total_wanted": "size",
            "active_time": "active_time",
            "seeding_time": "seeding_time",
            "total_seeds": "total_seeds",
            "total_peers": "total_peers",
            "num_seeds": "num_seeds",
            "num_peers": "num_peers",
            "progress": "progress",
            "ratio": "ratio",
            "total_uploaded": "uploaded",
            "total_done": "downloaded",
            "upload_payload_rate": "upload_speed",
            "download_payload_rate": "download_speed",
            "eta": "eta",
            "tracker_status": "tracker_status",
        }
        self.tasks = self.call(
            "core.get_torrents_status",
            {},
            [
                "name",
                "total_wanted",
                "active_time",
                "seeding_time",
                "total_seeds",
                "total_peers",
                "num_seeds",
                "num_peers",
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
            stats["name"]: {
                "hash": hash,
                **{
                    key_map[key]: value for key, value in stats.items() if key != "name"
                },
            }
            for hash, stats in self.tasks.items()
        }
        self.task_count = 0
        self.total_size = 0
        self.upload_speed = 0
        self.download_speed = 0
        for _, stats in self.tasks.items():
            stats["up_div_down"] = (
                stats["uploaded"] / (stats["size"] * stats["progress"] / 100)
                if stats["progress"] > 0
                else -1
            )
            self.task_count += 1
            self.total_size += stats["size"] / 1073741824
            self.upload_speed += stats["upload_speed"] / 1048576
            self.download_speed += stats["download_speed"] / 1048576
            stats["seeder"] = max(stats["total_seeds"], stats["num_seeds"])
            stats["leecher"] = max(stats["total_peers"], stats["num_peers"])

    def add_torrent(
        self,
        torrent: dict,
        name: str,
        path: str,
        extra_options: dict,
        logger: Optional[TextIOWrapper] = None,
    ):
        free_end = (
            "N/A"
            if torrent["free_end"] is None
            else time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(torrent["free_end"]))
        )
        text = f"""[{self.name}] 添加种子 {name}\
 免费：{"是" if torrent["free"] else "否"}\
 到期时间：{free_end}\
 H&R：{"无" if torrent["hr"] is None else f'{torrent["hr"] / 3600:.2f}小时'}\
 体积：{torrent["size"]:.2f}GB\
 任务数：{self.task_count + 1}\
 总体积：{self.total_size + torrent["size"]:.2f}GB"""
        self.call(
            "core.add_torrent_url",
            torrent["link"],
            {
                "name": name,
                "download_location": path,
                "add_paused": False,
                "auto_managed": False,
                **extra_options,
            },
        )
        print_t(text, logger=logger)

    def remove_torrent(
        self,
        torrent: dict,
        name: str,
        info: str,
        force_reannounce: bool = False,
        new_trackers: Optional[list] = None,
        logger: Optional[TextIOWrapper] = None,
    ):
        text = f'[{self.name}] 删除种子 {name}\
 原因：{info}\
 体积：{torrent["size"]:.2f}GB\
 上传量：{self.tasks[name]["uploaded"] / 1073741824:.2f}GB\
 分享率：{self.tasks[name]["up_div_down"]:.2f}\
 任务数：{self.task_count - 1}\
 总体积：{self.total_size - self.tasks[name]["size"] / 1073741824 + 0:.2f}GB'
        if new_trackers is not None:
            self.call(
                "core.set_torrent_trackers",
                self.tasks[name]["hash"],
                [
                    {"url": tracker, "tier": tier}
                    for tier, tracker in enumerate(new_trackers)
                ],
            )
            time.sleep(5)
        if force_reannounce:
            self.call("core.force_reannounce", [self.tasks[name]["hash"]])
            time.sleep(5)
        self.call("core.remove_torrent", self.tasks[name]["hash"], True)
        print_t(text, logger=logger)


class qbittorrent:
    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config
        self.new_client()
        self.ver = self.get_response("/api/v2/app/webapiVersion").text

    def __del__(self):
        self.get_response("/api/v2/auth/logout", nobreak=True)

    def get_response(self, api: str, data: dict = {}, nobreak: bool = False):
        try:
            response = requests.post(
                url=self.config["host"] + api,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
                    **self.config["headers"],
                },
                data=data,
                cookies=self.cookies,
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
            {
                "username": self.config["user"],
                "password": self.config["pass"],
            },
        )
        self.cookies = {
            "SID": part.replace("SID=", "")
            for part in response.headers["set-cookie"].split(";")
            if "SID=" in part
        }

    def reconnect(self):
        self.get_response("/api/v2/auth/logout", nobreak=True)
        time.sleep(eval(str(self.config["reconnect_interval"])))
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
            "num_complete": "num_complete",
            "num_incomplete": "num_incomplete",
            "num_seeds": "num_seeds",
            "num_leechs": "num_leechs",
            "progress": "progress",
            "ratio": "ratio",
            "uploaded": "uploaded",
            "downloaded": "downloaded",
            "upspeed": "upload_speed",
            "dlspeed": "download_speed",
            "eta": "eta",
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
                    "num_seeds",
                    "num_leechs",
                    "progress",
                    "ratio",
                    "uploaded",
                    "downloaded",
                    "upspeed",
                    "dlspeed",
                    "eta",
                ]
            }
            for task in self.tasks
        }
        self.task_count = 0
        self.total_size = 0
        self.upload_speed = 0
        self.download_speed = 0
        for _, stats in self.tasks.items():
            stats["progress"] *= 100
            stats["up_div_down"] = (
                stats["uploaded"] / (stats["size"] * stats["progress"] / 100)
                if stats["progress"] > 0
                else -1
            )
            self.task_count += 1
            self.total_size += stats["size"] / 1073741824
            self.upload_speed += stats["upload_speed"] / 1048576
            self.download_speed += stats["download_speed"] / 1048576
            stats["seeder"] = max(stats["num_complete"], stats["num_seeds"])
            stats["leecher"] = max(stats["num_incomplete"], stats["num_leechs"])
            stats["trackers"] = []
            tracker_status = ""
            response = self.get_response(
                "/api/v2/torrents/trackers", {"hash": stats["hash"]}, True
            )
            trackers = json.loads(response.text) if response.text != "" else []
            for tracker in trackers[3:]:
                stats["trackers"].append(tracker["url"])
                tracker_status += tracker["msg"]
            stats["tracker_status"] = tracker_status
        if not compare_version(self.ver, "2.8.1"):
            for _, stats in self.tasks.items():
                response = self.get_response(
                    "/api/v2/torrents/properties", {"hash": stats["hash"]}
                )
                stats["seeding_time"] = json.loads(response.text)["seeding_time"]

    def add_torrent(
        self,
        torrent: dict,
        name: str,
        path: str,
        extra_options: dict,
        logger: Optional[TextIOWrapper] = None,
    ):
        free_end = (
            "N/A"
            if torrent["free_end"] is None
            else time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(torrent["free_end"]))
        )
        text = f"""[{self.name}] 添加种子 {name}\
 免费：{"是" if torrent["free"] else "否"}\
 到期时间：{free_end}\
 H&R：{"无" if torrent["hr"] is None else f'{torrent["hr"] / 3600:.2f}小时'}\
 体积：{torrent["size"]:.2f}GB\
 任务数：{self.task_count + 1}\
 总体积：{self.total_size + torrent["size"]:.2f}GB"""
        self.get_response(
            "/api/v2/torrents/add",
            {
                "urls": torrent["link"],
                "savepath": path,
                "rename": name,
                "paused": "false",
                **extra_options,
            },
        )
        print_t(text, logger=logger)

    def remove_torrent(
        self,
        torrent: dict,
        name: str,
        info: str,
        force_reannounce: bool = False,
        new_trackers: Optional[list] = None,
        logger: Optional[TextIOWrapper] = None,
    ):
        text = f'[{self.name}] 删除种子 {name}\
 原因：{info}\
 体积：{torrent["size"]:.2f}GB\
 上传量：{self.tasks[name]["uploaded"] / 1073741824:.2f}GB\
 分享率：{self.tasks[name]["up_div_down"]:.2f}\
 任务数：{self.task_count - 1}\
 总体积：{self.total_size - self.tasks[name]["size"] / 1073741824 + 0:.2f}GB'
        if new_trackers is not None:
            self.get_response(
                "/api/v2/torrents/removeTrackers",
                {
                    "hash": self.tasks[name]["hash"],
                    "urls": "|".join(self.tasks[name]["trackers"]),
                },
            )
            self.get_response(
                "/api/v2/torrents/addTrackers",
                {"hash": self.tasks[name]["hash"], "urls": "%0A".join(new_trackers)},
            )
            time.sleep(5)
        if force_reannounce:
            self.get_response(
                "/api/v2/torrents/reannounce", {"hashes": self.tasks[name]["hash"]}
            )
            time.sleep(5)
        self.get_response(
            "/api/v2/torrents/delete",
            {"hashes": self.tasks[name]["hash"], "deleteFiles": "true"},
        )
        print_t(text, logger=logger)
