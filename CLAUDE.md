# CLAUDE.md

Telegram mirror/leech bot — downloads via aria2c, qBittorrent, JDownloader, SABnzbd, yt-dlp; uploads to Google Drive, Rclone remotes, or Telegram. Fork of [mirror-leech-telegram-bot](https://github.com/anasty17/mirror-leech-telegram-bot), upstream `tansautn/tele-leech-bot` (`UPSTREAM_BRANCH=deploy2025`).

## Tech Stack

- **Python 3.11** (pinned `>=3.11,<3.12` in `pixi.toml`)
- **Pyrogram** via `kurigram` fork — async Telegram client
- **uvloop** (linux-64 only) — high-perf event loop
- **MongoDB** via `pymongo.AsyncMongoClient` — config overrides, user data, RSS
- **pixi** — package/environment manager (replaces pip+venv)
- Platforms: `win-64`, `linux-64`

## Commands

```bash
# Run bot
pixi run bot                    # = python -m bot

# Tests — ALL
pixi run -e test test           # = python -m pytest tests/ -v

# Tests — syntax only (FAST, ~0.5s — run after every merge)
pixi run -e test test-syntax    # = python -m pytest tests/test_syntax.py -v

# Tests — single file
pixi run -e test python -m pytest tests/test_links_utils.py -v

# Tests — single test by name
pixi run -e test python -m pytest -k "TestConvert::test_bool_true_values" -v

# Install environments
pixi install                    # default (bot runtime)
pixi install -e test            # test suite (pytest, pytest-asyncio)
pixi install -e cli             # CLI tools (GDrive token gen, service accounts)

# CLI scripts
pixi run gen-session-str        # generate Pyrogram session string
```

Test config: `pyproject.toml`. Test guide: `docs/03-testing-guide.md`.

## Code Conventions

- **Logger, never print.** Use module `LOGGER` from `bot/__init__.py`.
- **English** for code, identifiers, comments. **Vietnamese** for explanations to the user. Technical terms stay English.
- **Python 3.11 syntax only.** No PEP 701 f-string nesting (e.g. `f"{d["key"]}"` — use `f"{d['key']}"` instead). This is the #1 merge-breakage pattern from upstream.
- **Config keys** — source of truth is `Config` class in `bot/core/config_manager.py`. No `config_sample.py`. `.env.example` is the working sample.
- **Never reference or import** files the user flags as samples/reference — especially paths containing `sample`.
- **Never `git add .`** — stage only files you created or changed. Untracked files are intentional.
- **Don't assume a library exists** — check `pixi.toml` first. Don't use pip/uv directly — declare in `pixi.toml` under `[pypi-dependencies]`.
- Config/secret files (`config.py`, `.env`, `*.pickle`, `*.conf`, `rclone/`, `sabnzbd/`, `accounts/`) are gitignored.

## Architecture

```
bot/
├── __init__.py            # Global state: dicts, locks, scheduler, DOWNLOAD_DIR
├── __main__.py            # Entry point — Config.load() → startup → run_forever
├── core/
│   ├── config_manager.py  # Config singleton (classmethod-based)
│   ├── mltb_client.py     # TgClient — Pyrogram bot + optional user client
│   ├── torrent_manager.py # TorrentManager — aria2 + qBittorrent connections
│   ├── handlers.py        # All Pyrogram handler registrations
│   └── startup.py         # DB load, daemon config (runs aria-nox-nzb.sh)
├── helper/
│   ├── common.py          # TaskConfig — base class for all download tasks
│   ├── listeners/         # Per-engine download listeners
│   │   └── task_listener.py  # TaskListener — post-download orchestrator
│   ├── ext_utils/         # Utilities: db_handler, media, files, links, status
│   ├── mirror_leech_utils/
│   │   ├── download_utils/   # Engine-specific downloaders
│   │   ├── gdrive_utils/     # GDrive upload/search/clone/count
│   │   ├── rclone_utils/     # Rclone transfer/list/serve
│   │   ├── status_utils/     # Per-engine status reporters
│   │   └── telegram_uploader.py
│   └── telegram_helper/   # Bot commands, button builder, message utils, filters
├── modules/               # Command handlers (one file per command group)
tests/                     # pytest suite — syntax check + unit tests
myjd/                      # JDownloader MyJD API client (vendored)
sabnzbdapi/                # SABnzbd REST client (vendored)
web/                       # FastAPI file selector (torrent file picker UI)
```

### Key Patterns

- **Global mutable state** — `bot/__init__.py` holds shared dicts (`task_dict`, `user_data`, `qb_torrents`, `rss_dict`, …) and `asyncio.Lock` instances. Modules import directly.
- **Task lifecycle**: command handler → `TaskConfig` → engine downloader → engine listener → `TaskListener.on_download_complete` → post-processing (extract, ffmpeg, rename) → upload (Telegram/GDrive/Rclone) → `on_upload_complete`.
- **Handler registration** — all in `core/handlers.py` via `bot/modules/__init__.py`. Commands support suffix via `Config.CMD_SUFFIX`.
- **Permission model** — three tiers: `owner` (`OWNER_ID`), `sudo` (`SUDO_USERS` + DB), `authorized` (`AUTHORIZED_CHATS` + `user_data`). Filters in `helper/telegram_helper/filters.py`.
- **Config loading** — `Config.load()` loads from ONE source (not merged): `config.py` module if importable, else env vars. Then MongoDB overrides via `load_settings()` when `DATABASE_URL` is set. Required: `BOT_TOKEN`, `OWNER_ID`, `TELEGRAM_API`, `TELEGRAM_HASH`.

### Download Engines

| Engine | Downloader | Listener | Status |
|---|---|---|---|
| aria2c | `download_utils/aria2_download.py` | `listeners/aria2_listener.py` | `status_utils/aria2_status.py` |
| qBittorrent | `download_utils/qbit_download.py` | `listeners/qbit_listener.py` | `status_utils/qbit_status.py` |
| JDownloader | `download_utils/jd_download.py` | `listeners/jdownloader_listener.py` | `status_utils/jd_status.py` |
| SABnzbd | `download_utils/nzb_download.py` | `listeners/nzb_listener.py` | `status_utils/nzb_status.py` |
| Direct/HTTP | `download_utils/direct_listener.py` | `listeners/direct_listener.py` | `status_utils/direct_status.py` |
| yt-dlp | `download_utils/yt_dlp_download.py` | (inline) | `status_utils/ytdlp_status.py` |

### Companion Daemons (Linux container)

Startup (`bot/core/startup.py`) runs `aria-nox-nzb.sh`:
- **aria2c** — RPC on `localhost:6800`
- **qbittorrent-nox** — Web API on `localhost:8090`
- **sabnzbdplus** — API on `localhost:8070`, key `mltb`

Optional web file selector (FastAPI/Gunicorn) starts only if `BASE_URL` is set on `BASE_URL_PORT`.

### Hardcoded Paths (Linux container assumed)

- `<CWD>/downloads/` — `DOWNLOAD_DIR` in `bot/__init__.py`
- `/JDownloader/cfg` — JDownloader config
- `/root/.netrc` — copied from repo `.netrc` at startup

## Workflow & Process

### Session Start

Project rules live in `.agents/` git submodule (repo `tansautn/zuko-ai-rules`, branch `python-qt`). If `.agents/rules/` is empty:

```bash
git submodule update --init --recursive
```

If that fails (private repo / headless agent), **skip and continue**.

**Read every `000-*` file in `.agents/rules/` before writing code.** Key rules:

| Rule file | What it governs |
|---|---|
| `000-general-rules.md` | Tone, doc-first, max 4 sub-agents, accuracy-first, git discipline |
| `002-use-logger.md` | Use `LOGGER`, never `print` |
| `003-claude-md-canonical.md` | This file is the single source of truth |
| `003-documentation-context.md` | Use Context7 MCP / web search for library docs |
| `005-build-automation.md` | Read before editing `.github/workflows/` |

### Doc-first

Non-trivial changes begin with a plan doc at `docs/agent-plans/<yyyymmdd>_<issue_title>.md` before code.

### Git

- **Never `git add .`** — stage only files you created or changed.
- CI workflows must skip subjects containing `skip ci` / `skip-ci` / `skip_ci` (case-insensitive).

### CLAUDE.md Is Canonical

This file is the single source of truth for every AI agent. Other runtime filenames (`AGENTS.md`, `.cursorrules`, `.github/copilot-instructions.md`, …) must be **symlinks** to `CLAUDE.md`, never divergent copies.

## @imports

- `docs/02-pixi-guide.md` — Pixi environments, tasks, dependency management
- `docs/03-testing-guide.md` — Test suite structure, how to write new tests, roadmap
- `.agents/rules/` — Shared AI agent rules (git submodule)
