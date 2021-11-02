import json
import socket
import ssl
import struct
import time
import zlib

import rencode
import requests

from utils import *


class deluge:
    def __init__(self, name, config):
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
        self.socket.settimeout(self.config["clients"][self.name]["timeout"])
        self.socket.connect(
            (
                self.config["clients"][self.name]["host"].split(":")[0],
                int(self.config["clients"][self.name]["host"].split(":")[1]),
            )
        )

    def get_response(self, version, data=b""):
        flags = None
        while True:
            recv = self.socket.recv(10)
            data += recv
            if version[0] == 2:
                if flags is None:
                    if len(data) < 5:
                        continue
                    header = data[:5]
                    data = data[5:]
                    if version[1] == 0:
                        if header[0] != b"D"[0]:
                            raise Exception
                    elif ord(header[:1]) != 1:
                        raise Exception
                    if version[1] == 1:
                        flags = struct.unpack("!I", header[1:])[0]
                    elif version[1] == 0:
                        flags = struct.unpack("!i", header[1:])[0]
                if flags <= len(data):
                    data = zlib.decompress(data)
                    break
            elif version[0] == 1:
                try:
                    data = zlib.decompress(data)
                except zlib.error:
                    if not recv:
                        raise Exception
                    continue
                break
        data = list(rencode.loads(data, decode_utf8=True))
        if data[0] == 1:
            return data[2]
        elif data[0] == 2:
            raise Exception

    def send_call(self, version, method, *args, **kwargs):
        self.request_id += 1
        request = zlib.compress(
            rencode.dumps(((self.request_id, method, args, kwargs),))
        )
        if version[0] == 2:
            if version[1] == 1:
                self.socket.send(struct.pack("!BI", 1, len(request)))
            elif version[1] == 0:
                self.socket.send(b"D" + struct.pack("!i", len(request)))
            else:
                raise Exception
        self.socket.send(request)

    def call(self, method, *args, **kwargs):
        self.send_call(self.version, method, *args, **kwargs)
        return self.get_response(self.version)

    def new_client(self):
        self.new_socket()
        self.request_id = 1
        if self.version is None:
            self.send_call([1, 0], "daemon.info")
            self.send_call([2, 0], "daemon.info")
            self.send_call([2, 1], "daemon.info")
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
                self.config["clients"][self.name]["user"],
                self.config["clients"][self.name]["pass"],
                client_version="deluge",
            )
        elif self.version[0] == 1:
            self.call(
                "daemon.login",
                self.config["clients"][self.name]["user"],
                self.config["clients"][self.name]["pass"],
            )

    def reconnect(self):
        try:
            self.socket.close()
            del self.socket
        except Exception:
            pass
        time.sleep(self.config["clients"][self.name]["reconnect_interval"])
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
        self.total_size = (
            sum([task["size"] for _, task in self.tasks.items()]) / 1073741824
        )
        self.task_count = len(self.tasks)

    def add_torrent(self, torrent, name, logger):
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
 总体积：{self.total_size + torrent["size"]:.2f}GB\
 任务数：{self.task_count + 1}"""
        self.call(
            "core.add_torrent_url",
            torrent["link"],
            {
                "name": name,
                "download_location": self.config["projects"][torrent["project"]][
                    "path"
                ],
                "add_paused": False,
                "auto_managed": False,
                **self.config["projects"][torrent["project"]]["extra_options"],
            },
        )
        print_t(text, logger=logger)

    def remove_torrent(self, torrent, name, info, logger):
        text = f'[{self.name}] 删除种子 {name}\
 原因：{info}\
 体积：{torrent["size"]:.2f}GB\
 总体积：{self.total_size - self.tasks[name]["size"] / 1073741824 + 0:.2f}GB\
 任务数：{self.task_count - 1}'
        self.call("core.remove_torrent", self.tasks[name]["hash"], True)
        print_t(text, logger=logger)


class qbittorrent:
    def __init__(self, name, config):
        self.name = name
        self.config = config
        self.new_client()
        self.ver = self.get_response("/api/v2/app/webapiVersion").text

    def __del__(self):
        self.get_response("/api/v2/auth/logout", nobreak=True)

    def get_response(self, api, data={}, nobreak=False):
        try:
            response = requests.post(
                url=self.config["clients"][self.name]["host"] + api,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
                    **self.config["clients"][self.name]["headers"],
                },
                data=data,
                cookies=self.cookies,
                timeout=self.config["clients"][self.name]["timeout"],
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
                "username": self.config["clients"][self.name]["user"],
                "password": self.config["clients"][self.name]["pass"],
            },
        )
        self.cookies = {
            "SID": part.replace("SID=", "")
            for part in response.headers["set-cookie"].split(";")
            if "SID=" in part
        }

    def reconnect(self):
        self.get_response("/api/v2/auth/logout", nobreak=True)
        time.sleep(self.config["clients"][self.name]["reconnect_interval"])
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
        if not compare_version(self.ver, "2.8.1"):
            for name, stats in self.tasks.items():
                if "seeding_time" not in stats:
                    self.tasks[name]["seeding_time"] = 0
                response = self.get_response(
                    "/api/v2/torrents/properties", {"hash": stats["hash"]}, True
                )
                info = json.loads(response.text) if response.text != "" else {}
                if "seeding_time" in info:
                    self.tasks[name]["seeding_time"] = info["seeding_time"]
        self.total_size = (
            sum([task["size"] for _, task in self.tasks.items()]) / 1073741824
        )
        self.task_count = len(self.tasks)

    def add_torrent(self, torrent, name, logger):
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
 总体积：{self.total_size + torrent["size"]:.2f}GB\
 任务数：{self.task_count + 1}"""
        self.get_response(
            "/api/v2/torrents/add",
            {
                "urls": torrent["link"],
                "savepath": self.config["projects"][torrent["project"]]["path"],
                "rename": name,
                "paused": "false",
                **self.config["projects"][torrent["project"]]["extra_options"],
            },
        )
        print_t(text, logger=logger)

    def remove_torrent(self, torrent, name, info, logger):
        text = f'[{self.name}] 删除种子 {name}\
 原因：{info}\
 体积：{torrent["size"]:.2f}GB\
 总体积：{self.total_size - self.tasks[name]["size"] / 1073741824 + 0:.2f}GB\
 任务数：{self.task_count - 1}'
        self.get_response(
            "/api/v2/torrents/delete",
            {"hashes": self.tasks[name]["hash"], "deleteFiles": "true"},
        )
        print_t(text, logger=logger)
