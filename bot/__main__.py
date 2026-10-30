from . import LOGGER, bot_loop, ENABLED_MODULES
from .core.mltb_client import TgClient
from .core.config_manager import Config

Config.load()


async def main():
    from asyncio import gather
    from .core.startup import (
        load_settings,
        load_configurations,
        save_settings,
        update_aria2_options,
        update_nzb_options,
        update_qb_options,
        update_variables,
    )

    await load_settings()

    await gather(TgClient.start_bot(), TgClient.start_user())
    await gather(load_configurations(), update_variables())

    from .core.torrent_manager import TorrentManager

    if "aria2c" in ENABLED_MODULES or "qBit" in ENABLED_MODULES:
        await TorrentManager.initiate()

    update_tasks = []
    if "qBit" in ENABLED_MODULES:
        update_tasks.append(update_qb_options())
    if "aria2c" in ENABLED_MODULES:
        update_tasks.append(update_aria2_options())
    if "nZB" in ENABLED_MODULES:
        update_tasks.append(update_nzb_options())
    if update_tasks:
        await gather(*update_tasks)

    from .helper.ext_utils.files_utils import clean_all
    from .helper.ext_utils.telegraph_helper import telegraph
    from .helper.mirror_leech_utils.rclone_utils.serve import rclone_serve_booter
    from .modules import (
        initiate_search_tools,
        get_packages_version,
        restart_notification,
    )

    post_tasks = [
        save_settings(),
        clean_all(),
        get_packages_version(),
        restart_notification(),
        telegraph.create_account(),
    ]
    if "jD" in ENABLED_MODULES:
        from .core.jdownloader_booter import jdownloader
        post_tasks.append(jdownloader.boot())
    if "qBit" in ENABLED_MODULES:
        post_tasks.append(initiate_search_tools())
    if "rclone" in ENABLED_MODULES:
        post_tasks.append(rclone_serve_booter())
    await gather(*post_tasks)


bot_loop.run_until_complete(main())

from .helper.ext_utils.bot_utils import create_help_buttons
from .core.handlers import add_handlers

if "aria2c" in ENABLED_MODULES:
    from .helper.listeners.aria2_listener import add_aria2_callbacks
    add_aria2_callbacks()
create_help_buttons()
add_handlers()

LOGGER.info("Bot Started!")
bot_loop.run_forever()
