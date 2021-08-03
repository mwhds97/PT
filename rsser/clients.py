import re
import time

import qbittorrentapi
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
        self.client.connect()
        self.flush()

    def reconnect(self):
        try:
            self.client.disconnect()
        except Exception:
            pass
        time.sleep(5)
        self.new_client()

    def flush(self):
        key_map = {
            "total_wanted": "size",
            "active_time": "active_time",
            "seeding_time": "seeding_time",
            "ratio": "ratio",
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
                "ratio",
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
        self.flush()
        text = f"""添加种子（{torrent["size"]:.2f}GB）（{torrent["site"]}）\
，免费：{"是" if torrent["free"] else "否"}\
，到期时间：{"N/A" if not torrent["free"] or torrent["free_end"] == None else time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(torrent["free_end"]))}\
，H&R：{"无" if torrent["hr"] == None else f'{torrent["hr"] / 3600:.2f}小时'}\
，总体积：{self.total_size + torrent["size"]:.2f}GB"""
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
            self.flush()
            print_t(text, logger=logger)
        except Exception as e:
            hash = re.match("Torrent already in session \((\w{40})\)", str(e))
            if hash != None:
                self.client.call(
                    "core.set_torrent_options", hash.group(1), {"name": name}
                )
                self.flush()
            elif re.match("Torrent already being added", str(e)) == None:
                print_t("试" + text, logger=logger)
                torrent["retry_count"] += 1
                raise e

    def remove_torrent(self, name, info, logger):
        self.flush()
        pattern = "\[(\w+)\]"
        text = f'删除种子（{self.tasks[name]["size"] / 1073741824:.2f}GB）（{re.search(pattern, name).group(1)}）\
，原因：{info}\
，总体积：{self.total_size - self.tasks[name]["size"] / 1073741824 + 0:.2f}GB'
        try:
            self.client.call("core.remove_torrent", self.tasks[name]["hash"], True)
            self.flush()
            print_t(text, logger=logger)
        except Exception as e:
            print_t("试" + text, logger=logger)
            raise e


class qbittorrent:
    def __init__(self, config):
        self.config = config
        self.new_client()

    def __del__(self):
        try:
            self.client.auth_log_out()
        except Exception:
            pass

    def new_client(self):
        self.client = qbittorrentapi.Client(
            host=self.config["host"],
            username=self.config["user"],
            password=self.config["pass"],
            VERIFY_WEBUI_CERTIFICATE=False,
            EXTRA_HEADERS=self.config["headers"],
            DISABLE_LOGGING_DEBUG_OUTPUT=True,
        )
        self.client.auth_log_in()
        self.flush()

    def reconnect(self):
        try:
            self.client.auth_log_out()
        except Exception:
            pass
        time.sleep(5)
        self.new_client()

    def flush(self):
        key_map = {
            "hash": "hash",
            "size": "size",
            "time_active": "active_time",
            "seeding_time": "seeding_time",
            "ratio": "ratio",
            "tracker": "tracker_status",
        }
        self.tasks = self.client.torrents_info()
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
                    "ratio",
                    "tracker",
                ]
            }
            for task in self.tasks
        }
        for name, stats in self.tasks.items():
            tracker_status = ""
            if stats["tracker_status"] == "":
                try:
                    trackers = self.client.torrents_trackers(stats["hash"])
                    for i in range(3, len(trackers)):
                        tracker_status += trackers[i]["msg"]
                except Exception:
                    pass
            self.tasks[name]["tracker_status"] = tracker_status
        self.total_size = (
            sum([task["size"] for _, task in self.tasks.items()]) / 1073741824
        )
        self.task_count = len(self.tasks)

    def add_torrent(self, torrent, name, logger):
        self.flush()
        text = f"""添加种子（{torrent["size"]:.2f}GB）（{torrent["site"]}）\
，免费：{"是" if torrent["free"] else "否"}\
，到期时间：{"N/A" if not torrent["free"] or torrent["free_end"] == None else time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(torrent["free_end"]))}\
，H&R：{"无" if torrent["hr"] == None else f'{torrent["hr"] / 3600:.2f}小时'}\
，总体积：{self.total_size + torrent["size"]:.2f}GB"""
        try:
            response = self.client.torrents_add(
                urls=torrent["link"],
                save_path=self.config[torrent["site"]]["path"],
                rename=name,
                is_paused=False,
                **self.config[torrent["site"]]["extra_options"],
            )
            if response != "Ok.":
                raise Exception
            self.flush()
            print_t(text, logger=logger)
        except Exception as e:
            print_t("试" + text, logger=logger)
            torrent["retry_count"] += 1
            raise e

    def remove_torrent(self, name, info, logger):
        self.flush()
        pattern = "\[(\w+)\]"
        text = f'删除种子（{self.tasks[name]["size"] / 1073741824:.2f}GB）（{re.search(pattern, name).group(1)}）\
，原因：{info}\
，总体积：{self.total_size - self.tasks[name]["size"] / 1073741824 + 0:.2f}GB'
        try:
            self.client.torrents_delete(True, self.tasks[name]["hash"])
            self.flush()
            print_t(text, logger=logger)
        except Exception as e:
            print_t("试" + text, logger=logger)
            raise e
