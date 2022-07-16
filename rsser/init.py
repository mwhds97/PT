from utils import *


def init(config: dict) -> tuple:
    default_settings = {
        "pool": {
            "size": 5000,
            "sort_by": {},
            "scan_interval": 30,
            "save_interval": 3600,
        },
        "snippets": {},
        "clients": {
            "snippets": [],
            "headers": {},
            "timeout": 15,
            "reconnect_interval": 10,
            "run_interval": 30,
            "bandwidth": None,
            "task_count_max": float("inf"),
            "total_size_max": float("inf"),
            "download_speed_max": float("inf"),
        },
        "volumes": {},
        "sites": {
            "snippets": [],
            "rss_timeout": 15,
            "web": [],
            "web_timeout": 15,
            "cookies": {},
            "user_agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36",
            "proxies": {},
            "fetch_interval": 300,
            "retry_interval": 30,
            "retry_pause_count": float("inf"),
            "retry_pause_time": 600,
            "timezone": +8,
            "hr_seed_ratio": None,
            "hr_min_progress": 100,
            "task_count_max": float("inf"),
            "total_size_max": float("inf"),
        },
        "projects": {
            "snippets": [],
            "regexp": [r".*"],
            "size": [[float("-inf"), float("inf")]],
            "publish_within": float("inf"),
            "seeder": [float("-inf"), float("inf")],
            "leecher": [float("-inf"), float("inf")],
            "snatch": [float("-inf"), float("inf")],
            "free_only": False,
            "free_time_min": 0,
            "free_end_escape": False,
            "escape_trigger_time": 60,
            "hr_time_max": float("inf"),
            "hr_seed_delay": 0,
            "ignore_hr_seeding": False,
            "ignore_hr_leeching": False,
            "task_count_max": float("inf"),
            "total_size_max": float("inf"),
            "retry_count_max": 2,
            "remove_conditions": [],
            "tracker_message_remove": None,
            "load_balance_key": "0",
        },
    }
    for setting in {"pool", "snippets", "volumes"} - set(config.keys()):
        config[setting] = default_settings[setting]
    if set(config.keys()) != {
        "pool",
        "snippets",
        "clients",
        "volumes",
        "sites",
        "projects",
    }:
        raise Exception("顶层键错误")
    for setting in set(default_settings["pool"].keys()) - set(config["pool"].keys()):
        config["pool"][setting] = default_settings["pool"][setting]
    if set(config["pool"].keys()) != {
        "size",
        "sort_by",
        "scan_interval",
        "save_interval",
    }:
        raise Exception("种子池选项有误")
    if not set(config["pool"]["sort_by"].keys()) <= {
        "size",
        "publish_time",
        "seeder",
        "leecher",
        "snatch",
        "site",
    }:
        raise Exception("种子池排序选项有误")
    for name in config["clients"]:
        if "snippets" in config["clients"][name]:
            if not isinstance(config["clients"][name]["snippets"], list):
                config["clients"][name]["snippets"] = [
                    config["clients"][name]["snippets"]
                ]
            for snippet in config["clients"][name]["snippets"]:
                config["clients"][name] = {
                    **config["snippets"][snippet],
                    **config["clients"][name],
                }
        for setting in set(default_settings["clients"].keys()) - set(
            config["clients"][name].keys()
        ):
            config["clients"][name][setting] = default_settings["clients"][setting]
        if set(config["clients"][name].keys()) != {
            "snippets",
            "type",
            "host",
            "user",
            "pass",
            "headers",
            "timeout",
            "reconnect_interval",
            "run_interval",
            "bandwidth",
            "task_count_max",
            "total_size_max",
            "download_speed_max",
        } or config["clients"][name]["type"] not in ["deluge", "qbittorrent"]:
            raise Exception("客户端配置有误")
        config["clients"][name]["user"] = str(config["clients"][name]["user"])
        config["clients"][name]["pass"] = str(config["clients"][name]["pass"])
    for name in config["sites"]:
        if "snippets" in config["sites"][name]:
            if not isinstance(config["sites"][name]["snippets"], list):
                config["sites"][name]["snippets"] = [config["sites"][name]["snippets"]]
            for snippet in config["sites"][name]["snippets"]:
                config["sites"][name] = {
                    **config["snippets"][snippet],
                    **config["sites"][name],
                }
        for setting in set(default_settings["sites"].keys()) - set(
            config["sites"][name].keys()
        ):
            config["sites"][name][setting] = default_settings["sites"][setting]
        if not isinstance(config["sites"][name]["web"], list):
            config["sites"][name]["web"] = [config["sites"][name]["web"]]
        if set(config["sites"][name].keys()) != {
            "snippets",
            "rss",
            "rss_timeout",
            "web",
            "web_timeout",
            "cookies",
            "user_agent",
            "proxies",
            "fetch_interval",
            "retry_interval",
            "retry_pause_count",
            "retry_pause_time",
            "hr_seed_ratio",
            "hr_min_progress",
            "timezone",
            "task_count_max",
            "total_size_max",
        }:
            raise Exception("站点配置有误")
    for name in config["projects"]:
        if "snippets" in config["projects"][name]:
            if not isinstance(config["projects"][name]["snippets"], list):
                config["projects"][name]["snippets"] = [
                    config["projects"][name]["snippets"]
                ]
            for snippet in config["projects"][name]["snippets"]:
                config["projects"][name] = {
                    **config["snippets"][snippet],
                    **config["projects"][name],
                }
        for setting in set(default_settings["projects"].keys()) - set(
            config["projects"][name].keys()
        ):
            config["projects"][name][setting] = default_settings["projects"][setting]
        if not isinstance(config["projects"][name]["sites"], list):
            config["projects"][name]["sites"] = [config["projects"][name]["sites"]]
        if not isinstance(config["projects"][name]["regexp"], list):
            config["projects"][name]["regexp"] = [config["projects"][name]["regexp"]]
        if not isinstance(config["projects"][name]["size"][0], list):
            config["projects"][name]["size"] = [config["projects"][name]["size"]]
        if not isinstance(config["projects"][name]["remove_conditions"], list):
            config["projects"][name]["remove_conditions"] = [
                config["projects"][name]["remove_conditions"]
            ]
        if set(config["projects"][name].keys()) != {
            "snippets",
            "clients",
            "sites",
            "regexp",
            "size",
            "publish_within",
            "seeder",
            "leecher",
            "snatch",
            "free_only",
            "free_time_min",
            "free_end_escape",
            "escape_trigger_time",
            "hr_time_max",
            "hr_seed_delay",
            "ignore_hr_seeding",
            "ignore_hr_leeching",
            "task_count_max",
            "total_size_max",
            "retry_count_max",
            "remove_conditions",
            "tracker_message_remove",
            "load_balance_key",
        }:
            raise Exception("任务计划配置有误")
    active_sites = set()
    active_clients = set()
    active_volumes = set()
    for _, project in config["projects"].items():
        for site in project["sites"]:
            active_sites.add(site)
        for client, options in project["clients"].items():
            active_clients.add(client)
            if "volume" in options:
                if options["volume"] is not None:
                    active_volumes.add(options["volume"])
            else:
                options["volume"] = None
            if "extra_options" not in options:
                options["extra_options"] = {}
            if set(options.keys()) != {"volume", "path", "extra_options"}:
                raise Exception("任务计划配置有误")
        for condition in project["remove_conditions"]:
            if set(condition.keys()) != {"info", "exp", "period"}:
                raise Exception("移除规则配置有误")
    if not active_sites <= set(config["sites"].keys()):
        raise Exception("任务计划缺失对应站点配置")
    if not active_clients <= set(config["clients"].keys()):
        raise Exception("任务计划缺失对应客户端配置")
    if not active_volumes <= set(config["volumes"].keys()):
        raise Exception("任务计划缺失对应存储配置")
    return (active_sites, active_clients)
