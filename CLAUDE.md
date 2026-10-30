# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Telegram mirror/leech bot (fork of [mirror-leech-telegram-bot](https://github.com/anasty17/mirror-leech-telegram-bot)) that downloads via aria2c, qBittorrent, JDownloader, SABnzbd, and yt-dlp, then uploads to Google Drive, Rclone remotes, or back to Telegram. Built on **Pyrogram** (via the `kurigram` fork) as an async Python 3.11 codebase using `uvloop` (Linux only). Self-upstream is `tansautn/tele-leech-bot` (`UPSTREAM_BRANCH=deploy2025`); the working branch is `master`.

## Before You Write Anything — Rules & Conventions

Project rules live in the **`.agents/` git submodule** (repo `tansautn/zuko-ai-rules`, branch `python-qt`). It is **not** auto-initialized — if `.agents/rules/` is empty, run:

```bash
git submodule update --init --recursive
```

If that fails (private repo / no credentials in a headless agent), **skip it and continue** — do not block.

**RULE GO FIRST** — before writing code or emitting a plan, **read every `000-*` file in `.agents/rules/`** and follow them without exception. Rule files are *inputs referenced by this CLAUDE.md*, not competitors to it (see `003-claude-md-canonical.md`).

| Rule file | What it governs |
|---|---|
| `000-general-rules.md` | **Must read.** Tone (no preamble; Vietnamese explanations, English code), doc-first, max 4 sub-agents (hard cap 5, else queue), accuracy-first ("don't guess — read or ask"), git discipline, `skip ci` matching. |
| `000-python-qt-rules.md` | PySide6/Qt rules — inherited from the `python-qt` rules branch; **largely N/A** to this async Pyrogram bot. |
| `001-tasks-workflow.md` | Multi-file task workflow under `docs/tasks/`. |
| `002-service-locator-and-network.md` | Service Locator / Network Manager patterns (Qt-branch; mostly N/A here). |
| `002-use-logger.md` | Logger usage — use the module `LOGGER`, never `print`. |
| `003-claude-md-canonical.md` | **CLAUDE.md is the single source of truth** (see below). |
| `003-documentation-context.md` | Use **Context7** MCP / web search for library docs before integrating a package. |
| `003-i-have-adhd.md` | Opt-in output shaping (`/i-have-adhd`). |
| `003-mermaid-styling.md` | Mermaid diagram styling. |
| `005-build-automation.md` | Read before editing `.github/workflows/` (changelog, version bump, autofix). |
| `020-*` | Mirror-source sync, submodule setup, plus `020-CLAUDE.md-best-practices.pdf`. |
| `200-cursor-rules.md` | Meta: how to author rule files. |

### Workflow conventions (from `000-general-rules.md`)

- **Doc-first.** Non-trivial changes begin with a plan doc at `docs/agent-plans/<yyyymmdd>_<issue_title>.md` (goal → step-by-step → Mermaid for multi-module logic) before code. The `docs/` directory does not exist yet — create it when needed.
- **Communication.** Code, identifiers, and comments in **English**; technical explanations to the user in **Vietnamese**, keeping technical terms in English. No preamble/postamble.
- **Accuracy over everything.** Re-read a file before editing it. Don't assume a library exists — check `pixi.toml` first. Prefer the `codebase-memory-mcp` graph index over grep/fuzzy search when available.
- **Never reference or import files the user flags as samples/reference** — especially paths containing `sample` (e.g. do not `import` a sample config).

## CLAUDE.md Is Canonical

Per `003-claude-md-canonical.md`: **this file is the one source of truth** for every AI agent. Other runtime filenames (`AGENTS.md`, `GEMINI.md`, `.cursorrules`, `.github/copilot-instructions.md`, …) must be **symlinks** to the sibling `CLAUDE.md`, never divergent copies. None exist in the repo root today — if you add one, use `ln -s CLAUDE.md AGENTS.md`, not a copy. Do not create per-runtime rule dirs (`.cursor/rules/`, `.github/instructions/`).

## Running the Bot

```bash
pixi run bot          # local dev (= `python -m bot`)
./run.sh              # same, appends to log-YYYY-MM-DD.log (production uses supervisor.conf)
```

Startup (`bot/core/startup.py::load_configurations`) copies `.netrc` → `/root/.netrc` and runs `aria-nox-nzb.sh`, which launches three companion daemons:

- **aria2c** — RPC on `localhost:6800`
- **qbittorrent-nox** — Web API on `localhost:8090`
- **sabnzbdplus** — API on `localhost:8070`, key `mltb`

The optional web file selector (FastAPI/Gunicorn) starts only if `BASE_URL` is set, on `BASE_URL_PORT`.

> No automated test suite exists. There is no lint/format config; follow existing style.

## Configuration

`Config.load()` (`bot/core/config_manager.py`) loads config from **one** source, then DB overrides — the sources are **not merged**:

1. **If `config.py` is importable → load only its module attributes** (env loading is skipped). The real `config.py` runs `load_dotenv(".env")` and defines only the four required keys, so practically that is all the module path sets.
2. **Else → load from environment variables** (same key names).
3. **MongoDB overrides** applied afterward via `load_settings()` / `Config.load_dict()` when `DATABASE_URL` is set.

**Source of truth for every key and its default is the `Config` class in `bot/core/config_manager.py`** — there is no `config_sample.py`. `.env.example` is the working sample. Required keys: `BOT_TOKEN`, `OWNER_ID`, `TELEGRAM_API`, `TELEGRAM_HASH` (validated at load; missing → `ValueError`).

`Config` is a classmethod-only singleton: `Config.get(key)` / `Config.set(key, value)`. It auto-converts values to the type of the class-attribute default (bool / int / str / list / dict; list & dict via `ast.literal_eval`).

## Architecture

```
bot/
├── __init__.py          # Global state: dicts, locks, scheduler, sabnzbd_client, DOWNLOAD_DIR
├── __main__.py          # Entry point — Config.load() → startup sequence → run_forever
├── core/
│   ├── config_manager.py  # Config singleton (classmethod-based)
│   ├── mltb_client.py     # TgClient — Pyrogram bot + optional user client
│   ├── torrent_manager.py # TorrentManager — aria2 + qBittorrent connections
│   ├── handlers.py        # All Pyrogram handler registrations
│   └── startup.py         # DB load, variable init, daemon config (runs aria-nox-nzb.sh)
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
myjd/                      # JDownloader MyJD API client (vendored, not on PyPI)
sabnzbdapi/                # SABnzbd REST client (vendored, not on PyPI)
web/                       # FastAPI file selector (torrent file picker UI)
```

### Key Patterns

**Global mutable state** — `bot/__init__.py` holds shared dicts (`task_dict`, `user_data`, `qb_torrents`, `rss_dict`, …) and `asyncio.Lock` instances. Modules import these directly.

**Task lifecycle**: command handler → `TaskConfig` (`helper/common.py`, sets up options) → engine-specific downloader → engine listener polls/callbacks → `TaskListener.on_download_complete` → post-processing (extract, ffmpeg, rename) → upload (Telegram/GDrive/Rclone) → `on_upload_complete`.

**Handler registration** — all Pyrogram handlers are registered in `core/handlers.py` by calling functions from `bot/modules/__init__.py`. Commands support a configurable suffix via `Config.CMD_SUFFIX`.

**Permission model** — three tiers: `owner` (`OWNER_ID`), `sudo` (`SUDO_USERS` + DB), `authorized` (`AUTHORIZED_CHATS` + `user_data`). Defined as Pyrogram filter classes in `helper/telegram_helper/filters.py`.

**Database** — MongoDB via `pymongo.AsyncMongoClient`. Collections under the `mltb` DB: `settings.config`, `settings.files`, `settings.aria2c`, `settings.qbittorrent`, `settings.nzb`, `settings.deployConfig`, `users`, `rss[BOT_ID]`. Handler: `helper/ext_utils/db_handler.py`.

**Download engines → listener → status reporter**:

| Engine | Downloader | Listener | Status |
|--------|-----------|----------|--------|
| aria2c | `download_utils/aria2_download.py` | `listeners/aria2_listener.py` | `status_utils/aria2_status.py` |
| qBittorrent | `download_utils/qbit_download.py` | `listeners/qbit_listener.py` | `status_utils/qbit_status.py` |
| JDownloader | `download_utils/jd_download.py` | `listeners/jdownloader_listener.py` | `status_utils/jd_status.py` |
| SABnzbd | `download_utils/nzb_download.py` | `listeners/nzb_listener.py` | `status_utils/nzb_status.py` |
| Direct/HTTP | `download_utils/direct_listener.py` | `listeners/direct_listener.py` | `status_utils/direct_status.py` |
| yt-dlp | `download_utils/yt_dlp_download.py` | (inline) | `status_utils/ytdlp_status.py` |

## Dependencies

Managed via **pixi** (`pixi.toml`, `pixi.lock`) — Python 3.11, conda-forge, platforms `win-64` + `linux-64`. `uvloop` and `xattr` are **linux-64 only**.

```bash
pixi install          # default environment (bot runtime)
pixi install -e cli   # CLI tools env: GDrive token gen, service accounts, etc.
```

`scripts/` (GDrive/service-account/session helpers: `generate_drive_token.py`, `gen_sa_accounts.py`, `add_to_team_drive.py`, `driveid.py`, `generate_string_session.py`, `update.py`) run under the `cli` env. **Do not use pip/uv directly** — declare packages in `pixi.toml` under `[pypi-dependencies]` (`requirements*.txt` are legacy mirrors).

## Git Conventions

- **Never `git add .`** — stage only files you created or changed. Untracked files are intentional.
- Config/secret files (`config.py`, `.env`, `*.pickle`, `*.conf`, `rclone/`, `sabnzbd/`, `accounts/`) are gitignored.
- CI workflows must skip subjects containing `skip ci` / `skip-ci` / `skip_ci` (case-insensitive).

## Hardcoded Paths (Linux container assumed)

- `/usr/src/app/downloads/` — `DOWNLOAD_DIR`, hardcoded in `bot/__init__.py` (the `.env` value is not read).
- `/usr/src/app` — Pyrogram workdir
- `/JDownloader/cfg` — JDownloader config
- `/root/.netrc` — netrc for aria2c auth (copied from repo `.netrc` at startup)
