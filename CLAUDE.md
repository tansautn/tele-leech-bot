# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Telegram mirror/leech bot (fork of [mirror-leech-telegram-bot](https://github.com/anasty17/mirror-leech-telegram-bot)) that downloads via aria2c, qBittorrent, JDownloader, SABnzbd, and yt-dlp, then uploads to Google Drive, Rclone remotes, or back to Telegram. Built on **Pyrogram** (via `kurigram` fork) with an async Python 3.11 codebase using `uvloop`.

## Running the Bot

```bash
# Local dev
pixi run bot

# Production (supervisor + run.sh)
./run.sh  # runs `pixi run bot`, logs to log-YYYY-MM-DD.log
```

The bot requires three companion daemons launched by `aria-nox-nzb.sh` (runs automatically at startup via `load_configurations`):
- **aria2c** — RPC on `localhost:6800`
- **qbittorrent-nox** — Web API on `localhost:8090`
- **sabnzbdplus** — API on `localhost:8070`, key `mltb`

The optional web file selector (FastAPI/Gunicorn) starts if `BASE_URL` is set, on `BASE_URL_PORT`.

## Configuration

Config loads in order (**later wins**):
1. `config.py` module (see `config_sample.py` for all keys — **never import config_sample.py**)
2. Environment variables (same key names)
3. MongoDB database overrides (if `DATABASE_URL` is set)

Required keys: `BOT_TOKEN`, `OWNER_ID`, `TELEGRAM_API`, `TELEGRAM_HASH`.

The `Config` class (`bot/core/config_manager.py`) is a classmethod-only singleton — access via `Config.get(key)` / `Config.set(key, value)`. It auto-converts types based on the class attribute defaults (bool, int, str, list, dict).

## Architecture

```
bot/
├── __init__.py          # Global state: dicts, locks, scheduler, sabnzbd_client
├── __main__.py          # Entry point — startup sequence then run_forever
├── core/
│   ├── config_manager.py  # Config singleton (classmethod-based)
│   ├── mltb_client.py     # TgClient — Pyrogram bot + optional user client
│   ├── torrent_manager.py # TorrentManager — aria2 + qBittorrent connections
│   ├── handlers.py        # All Pyrogram handler registrations
│   └── startup.py         # DB load, variable init, daemon config
├── helper/
│   ├── common.py          # TaskConfig — base class for all download tasks
│   ├── listeners/         # Per-engine download listeners (aria2, qbit, jd, nzb, direct)
│   │   └── task_listener.py  # TaskListener(TaskConfig) — post-download orchestrator
│   ├── ext_utils/         # Utilities: db_handler, media (ffmpeg), files, links, status
│   ├── mirror_leech_utils/
│   │   ├── download_utils/   # Engine-specific downloaders
│   │   ├── gdrive_utils/     # GDrive upload/search/clone/count
│   │   ├── rclone_utils/     # Rclone transfer/list/serve
│   │   ├── status_utils/     # Per-engine status reporters
│   │   └── telegram_uploader.py
│   └── telegram_helper/   # Bot commands, button builder, message utils, filters
├── modules/               # Command handlers (one file per command group)
myjd/                      # JDownloader MyJD API client (vendored)
sabnzbdapi/                # SABnzbd REST client (vendored)
web/                       # FastAPI file selector (torrent file picker UI)
```

### Key Patterns

**Global mutable state** — `bot/__init__.py` holds shared dicts (`task_dict`, `user_data`, `qb_torrents`, `rss_dict`, etc.) and `asyncio.Lock` instances. Modules import these directly.

**Task lifecycle**: Command handler → `TaskConfig` (in `helper/common.py`, sets up options) → engine-specific downloader → engine listener polls/callbacks → `TaskListener.on_download_complete` → post-processing (extract, ffmpeg, rename) → upload (Telegram/GDrive/Rclone) → `on_upload_complete`.

**Handler registration** — All Pyrogram handlers are registered in `core/handlers.py` by calling functions from `bot/modules/__init__.py`. Commands support a configurable suffix via `Config.CMD_SUFFIX`.

**Permission model** — Three tiers: `owner` (OWNER_ID), `sudo` (SUDO_USERS + DB), `authorized` (auth_chats + user_data). Defined as Pyrogram filter classes in `helper/telegram_helper/filters.py`.

**Database** — MongoDB via `pymongo.AsyncMongoClient`. Collections under `mltb` DB: `settings.config`, `settings.files`, `settings.aria2c`, `settings.qbittorrent`, `settings.nzb`, `settings.deployConfig`, `users`, `rss[BOT_ID]`. Handler: `helper/ext_utils/db_handler.py`.

**Download engines and their listeners**:
| Engine | Downloader | Listener | Status |
|--------|-----------|----------|--------|
| aria2c | `download_utils/aria2_download.py` | `listeners/aria2_listener.py` | `status_utils/aria2_status.py` |
| qBittorrent | `download_utils/qbit_download.py` | `listeners/qbit_listener.py` | `status_utils/qbit_status.py` |
| JDownloader | `download_utils/jd_download.py` | `listeners/jdownloader_listener.py` | `status_utils/jd_status.py` |
| SABnzbd | `download_utils/nzb_download.py` | `listeners/nzb_listener.py` | `status_utils/nzb_status.py` |
| Direct/HTTP | `download_utils/direct_listener.py` | `listeners/direct_listener.py` | `status_utils/direct_status.py` |
| yt-dlp | `download_utils/yt_dlp_download.py` | (inline) | `status_utils/ytdlp_status.py` |

### Vendored Libraries

- `myjd/` — MyJDownloader API client (custom, not from PyPI)
- `sabnzbdapi/` — SABnzbd REST client (custom, not from PyPI)

## Dependencies

All dependencies are managed via **pixi** (`pixi.toml`). Python 3.11, conda-forge channel.

```bash
pixi install          # install default environment
pixi install -e cli   # install CLI tools environment (GDrive token gen, service accounts, etc.)
```

Helper scripts in `scripts/` use the `cli` feature environment. **Do not use pip/uv directly** — all packages are declared in `pixi.toml` under `[pypi-dependencies]`.

## Git Conventions

- **Never `git add .`** — only stage files you created or changed. Untracked files are intentional.
- Branch: `master`
- Config files (`config.py`, `*.pickle`, `*.conf`, `rclone/`, `sabnzbd/`, `accounts/`) are gitignored.

## Hardcoded Paths (Linux container assumed)

- `/usr/src/app/downloads/` — download directory (`DOWNLOAD_DIR`)
- `/usr/src/app` — Pyrogram workdir
- `/JDownloader/cfg` — JDownloader config
- `/root/.netrc` — netrc for aria2c auth
