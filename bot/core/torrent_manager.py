from aioaria2 import Aria2WebsocketClient
from aioqbt.client import create_client
from asyncio import gather, TimeoutError
from aiohttp import ClientError
from pathlib import Path
from inspect import iscoroutinefunction
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from .. import LOGGER, aria2_options


def wrap_with_retry(obj, max_retries=3):
    for attr_name in dir(obj):
        if attr_name.startswith("_"):
            continue

        attr = getattr(obj, attr_name)
        if iscoroutinefunction(attr):
            retry_policy = retry(
                stop=stop_after_attempt(max_retries),
                wait=wait_exponential(multiplier=1, min=1, max=5),
                retry=retry_if_exception_type(
                    (ClientError, TimeoutError, RuntimeError)
                ),
            )
            wrapped = retry_policy(attr)
            setattr(obj, attr_name, wrapped)
    return obj


class TorrentManager:
    aria2 = None
    qbittorrent = None

    @classmethod
    async def initiate(cls):
        from .. import ENABLED_MODULES
        tasks = {}
        if "aria2c" in ENABLED_MODULES:
            tasks["aria2"] = Aria2WebsocketClient.new("http://localhost:6800/jsonrpc")
        if "qBit" in ENABLED_MODULES:
            tasks["qbit"] = create_client("http://localhost:8090/api/v2/")
        if tasks:
            results = await gather(*tasks.values())
            keys = list(tasks.keys())
            for i, key in enumerate(keys):
                if key == "aria2":
                    cls.aria2 = results[i]
                elif key == "qbit":
                    cls.qbittorrent = wrap_with_retry(results[i])

    @classmethod
    async def close_all(cls):
        tasks = []
        if cls.aria2:
            tasks.append(cls.aria2.close())
        if cls.qbittorrent:
            tasks.append(cls.qbittorrent.close())
        if tasks:
            await gather(*tasks)

    @classmethod
    async def aria2_remove(cls, download):
        if download.get("status", "") in ["active", "paused", "waiting"]:
            await cls.aria2.forceRemove(download.get("gid", ""))
        else:
            try:
                await cls.aria2.removeDownloadResult(download.get("gid", ""))
            except:
                pass

    @classmethod
    async def remove_all(cls):
        await cls.pause_all()
        tasks = []
        if cls.qbittorrent:
            tasks.append(cls.qbittorrent.torrents.delete("all", False))
        if cls.aria2:
            tasks.append(cls.aria2.purgeDownloadResult())
        if tasks:
            await gather(*tasks)
        if cls.aria2:
            downloads = []
            results = await gather(cls.aria2.tellActive(), cls.aria2.tellWaiting(0, 1000))
            for res in results:
                downloads.extend(res)
            force_tasks = [
                cls.aria2.forceRemove(download.get("gid")) for download in downloads
            ]
            try:
                await gather(*force_tasks)
            except:
                pass

    @classmethod
    async def overall_speed(cls):
        download_speed = 0
        upload_speed = 0
        tasks = {}
        if cls.qbittorrent:
            tasks["qbit"] = cls.qbittorrent.transfer.info()
        if cls.aria2:
            tasks["aria2"] = cls.aria2.getGlobalStat()
        if tasks:
            results = await gather(*tasks.values())
            keys = list(tasks.keys())
            for i, key in enumerate(keys):
                if key == "qbit":
                    download_speed += results[i].dl_info_speed
                    upload_speed += results[i].up_info_speed
                elif key == "aria2":
                    download_speed += int(results[i].get("downloadSpeed", "0"))
                    upload_speed += int(results[i].get("uploadSpeed", "0"))
        return download_speed, upload_speed

    @classmethod
    async def pause_all(cls):
        tasks = []
        if cls.aria2:
            tasks.append(cls.aria2.forcePauseAll())
        if cls.qbittorrent:
            tasks.append(cls.qbittorrent.torrents.stop("all"))
        if tasks:
            await gather(*tasks)

    @classmethod
    async def change_aria2_option(cls, key, value):
        downloads = []
        results = await gather(cls.aria2.tellActive(), cls.aria2.tellWaiting(0, 1000))
        for res in results:
            downloads.extend(res)
            tasks = []
        for download in downloads:
            if download.get("status", "") != "complete":
                tasks.append(cls.aria2.changeOption(download.get("gid"), {key: value}))
        if tasks:
            try:
                await gather(*tasks)
            except Exception as e:
                LOGGER.error(e)
        if key not in ["checksum", "index-out", "out", "pause", "select-file"]:
            await cls.aria2.changeGlobalOption({key: value})
            aria2_options[key] = value


def aria2_name(download_info):
    if "bittorrent" in download_info and download_info["bittorrent"].get("info"):
        return download_info["bittorrent"]["info"]["name"]
    elif download_info.get("files"):
        if download_info["files"][0]["path"].startswith("[METADATA]"):
            return download_info["files"][0]["path"]
        file_path = download_info["files"][0]["path"]
        dir_path = download_info["dir"]
        if file_path.startswith(dir_path):
            return Path(file_path[len(dir_path) + 1 :]).parts[0]
        else:
            return ""
    else:
        return ""


def is_metadata(download_info):
    return any(
        f["path"].startswith("[METADATA]") for f in download_info.get("files", [])
    )
