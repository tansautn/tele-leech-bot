# Pixi Guide

***Hướng dẫn sử dụng Pixi để quản lý environments và dependencies cho tele-leech-bot.***

> Last updated: [`1b76856`](https://github.com/tansautn/tele-leech-bot/commit/1b76856) — đối chiếu `pixi.toml`

> [!IMPORTANT]
> Project dùng Pixi thay cho `pip` + `venv`. Mọi lệnh PHẢI chạy qua `pixi run` hoặc `pixi shell`.
> KHÔNG dùng `pip install` trực tiếp — khai báo trong `pixi.toml` dưới `[pypi-dependencies]`.

## Mục lục

- [1. Pixi là gì?](#1-pixi-là-gì)
- [2. Pixi vs Pip/Venv](#2-pixi-vs-pipvenv)
- [3. Cài đặt](#3-cài-đặt)
- [4. Environments](#4-environments)
- [5. Tasks (lệnh tắt)](#5-tasks-lệnh-tắt)
- [6. Quản lý dependencies](#6-quản-lý-dependencies)
- [7. Platform-specific dependencies](#7-platform-specific-dependencies)
- [8. Troubleshooting](#8-troubleshooting)

## 1. Pixi là gì?

Pixi là công cụ quản lý package và environment hiệu năng cao, dùng [uv](https://github.com/astral-sh/uv) (Rust) bên dưới. Trong project này, Pixi:
- **Đồng bộ environment**: đảm bảo mọi developer chạy cùng Python 3.11 và đúng phiên bản thư viện.
- **Quản lý nhiều environments**: runtime bot, CLI tools, test suite — tách biệt nhau.
- **Cross-platform**: `win-64` + `linux-64` (định nghĩa trong `pixi.toml`).

Cài Pixi trước khi bắt đầu: [Hướng dẫn cài đặt](https://pixi.sh/latest/#installation) | [Documentation](https://pixi.sh/latest/)

## 2. Pixi vs Pip/Venv

| Feature | Pip + Venv | Pixi |
|---|---|---|
| **Tạo environment** | `python -m venv venv` | Tự động khi `pixi install` hoặc `pixi run` |
| **Activate env** | `venv\Scripts\activate` | `pixi shell` (hoặc `pixi run <cmd>`) |
| **Cài thư viện** | `pip install <package>` | `pixi add --pypi <package>` |
| **Gỡ thư viện** | `pip uninstall <package>` | `pixi remove <package>` |
| **Config file** | `requirements.txt` | [@pixi.toml](../pixi.toml) + `pixi.lock` |
| **Tốc độ** | Bình thường | **Rất nhanh** (nhờ `uv` bên dưới) |

## 3. Cài đặt

```bash
# Cài environment mặc định (bot runtime)
pixi install
```

```bash
# Cài environment test
pixi install -e test
```

```bash
# Cài environment CLI tools
pixi install -e cli
```

## 4. Environments

Project có 3 environments, mỗi cái phục vụ mục đích riêng:

| Environment | Lệnh cài | Mục đích | Dependencies riêng |
|---|---|---|---|
| **default** | `pixi install` | Chạy bot | Tất cả `[pypi-dependencies]` |
| **test** | `pixi install -e test` | Chạy test suite | `pytest`, `pytest-asyncio` |
| **cli** | `pixi install -e cli` | CLI tools (token gen, SA) | `oauth2client`, `progress`, ... |

> [!NOTE]
> Environment `test` và `cli` kế thừa `[dependencies]` (Python 3.11) nhưng KHÔNG kế thừa `[pypi-dependencies]` của default.
> Environment `test` chỉ cần `pytest` — không cần toàn bộ bot dependencies để chạy syntax check.

## 5. Tasks (lệnh tắt)

Định nghĩa trong `[tasks]` của [@pixi.toml](../pixi.toml):

| Task | Lệnh đầy đủ | Environment |
|---|---|---|
| `pixi run bot` | `python -m bot` | default |
| `pixi run gen-session-str` | `python scripts/generate_string_session.py` | default |
| `pixi run -e test test` | `python -m pytest tests/ -v` | test |
| `pixi run -e test test-syntax` | `python -m pytest tests/test_syntax.py -v` | test |

> [!TIP]
> Sau mỗi merge, chạy `pixi run -e test test-syntax` để bắt lỗi syntax trước khi deploy.
> Chi tiết về test suite: xem [@03-testing-guide.md](03-testing-guide.md).

## 6. Quản lý dependencies

```bash
# Thêm package PyPI vào bot runtime
pixi add --pypi <package-name>
```

```bash
# Thêm package vào feature test
pixi add --feature test --pypi <package-name>
```

```bash
# Thêm package vào feature cli
pixi add --feature cli --pypi <package-name>
```

> [!WARNING]
> KHÔNG dùng `pip install` trực tiếp. Package cài bằng pip không được ghi vào `pixi.toml`,
> nghĩa là người khác sẽ không có thư viện đó.
> File `requirements*.txt` là mirror cũ (legacy) — source of truth là `pixi.toml`.

## 7. Platform-specific dependencies

Một số dependencies chỉ cài trên Linux (môi trường deploy):

```toml
[target.linux-64.pypi-dependencies]
uvloop = ">=0.23.0, <0.24"   # Async event loop tối ưu
xattr = ">=1.3.0, <2"         # Extended file attributes
```

Trên Windows, `bot/__init__.py` tự handle bằng `try/except ImportError` cho `uvloop`.

## 8. Troubleshooting

- **Q: Chạy `python -m bot` báo thiếu thư viện?**
    - A: Chưa activate environment. Dùng `pixi run bot` hoặc `pixi shell` trước.

- **Q: `pixi run test` báo `pytest` not found?**
    - A: Test suite nằm trong test environment. Thêm `-e test` và sau `pixi run`.
    - `-e` là chỉ định enviroment sẽ chạy `pixi-task`

- **Q: Thêm dependency mới nhưng `pixi install` báo conflict?**
    - A: Kiểm tra version range trong `pixi.toml`. Project pin Python `>=3.11, <3.12` — một số package mới có thể yêu cầu 3.12+.
