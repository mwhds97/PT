import re
import time

from deluge_client import DelugeRPCClient

from utils import *


class deluge:
    def __init__(self, config):
        self.config = config
        self.new_client()

    def __del__(self):
        self.client.disconnect()

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
        self.client.disconnect()
        time.sleep(5)
        self.new_client()

    def flush(self):
        self.tasks = self.client.call(
            "core.get_torrents_status",
            {},
            [
                "name",
                "total_size",
                "active_time",
                "seeding_time",
                "ratio",
                "tracker_status",
            ],
        )
        self.tasks = {
            stats["name"]: dict(
                {"hash": hash},
                **{key: value for key, value in stats.items() if key != "name"}
            )
            for hash, stats in self.tasks.items()
        }
        self.total_size = (
            sum([task["total_size"] for _, task in self.tasks.items()]) / 1073741824
        )
        self.task_count = len(self.tasks)

    def add_torrent(self, torrent, name):
        text = "添加种子（{:.2f}GB）（{}），免费：{}，到期时间：{}，H&R：{}，总体积：{:.2f}GB".format(
            torrent["size"],
            torrent["site"],
            "是" if torrent["free"] else "否",
            "N/A"
            if not torrent["free"] or torrent["free_end"] == None
            else time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(torrent["free_end"])
            ),
            "无" if torrent["hr"] == None else "{:.2f}小时".format(torrent["hr"] / 3600),
            self.total_size + torrent["size"],
        )
        try:
            self.client.call(
                "core.add_torrent_url",
                torrent["link"],
                dict(
                    {
                        "name": name,
                        "download_location": self.config[torrent["site"]]["path"],
                    },
                    **self.config[torrent["site"]]["extra_options"]
                ),
            )
            self.flush()
            print_t(text)
        except Exception as e:
            print_t("试" + text)
            raise e

    def remove_torrent(self, name, info):
        text = "删除种子（{:.2f}GB）（{}），原因：{}，总体积：{:.2f}GB".format(
            self.tasks[name]["total_size"] / 1073741824,
            re.search("\[(\w+)\]", name).group(1),
            info,
            self.total_size - self.tasks[name]["total_size"] / 1073741824 + 0,
        )
        try:
            self.client.call("core.remove_torrent", self.tasks[name]["hash"], True)
            self.flush()
            print_t(text)
        except Exception as e:
            print_t("试" + text)
            raise e
