# Testing Guide

***Hướng dẫn chạy, viết mới, và mở rộng test suite cho tele-leech-bot.***

> Last updated: [`1b76856`](https://github.com/tansautn/tele-leech-bot/commit/1b76856) — đối chiếu `tests/`, `pixi.toml`, `pyproject.toml`

> [!IMPORTANT]
> Test suite được thiết kế để **bắt lỗi syntax/merge trước khi deploy**.
> `test_syntax.py` compile-check mọi file `.py` trong project — chạy nó sau mỗi merge.

## Mục lục

- [1. Cài đặt](#1-cài-đặt)
- [2. Chạy tests](#2-chạy-tests)
- [3. Cấu trúc test suite](#3-cấu-trúc-test-suite)
- [4. Viết test mới](#4-viết-test-mới)
- [5. Conventions](#5-conventions)
- [6. Mở rộng (Roadmap)](#6-mở-rộng-roadmap)

## 1. Cài đặt

Test dependencies nằm trong feature `test` của pixi, tách biệt khỏi bot runtime:

```bash
pixi install -e test
```

Dependencies: `pytest >=8.0`, `pytest-asyncio >=0.25`.

Config pytest nằm trong [@pyproject.toml](../pyproject.toml):

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

## 2. Chạy tests

| Lệnh | Mục đích |
|---|---|
| `pixi run -e test test` | Chạy **toàn bộ** test suite |
| `pixi run -e test test-syntax` | Chỉ syntax check (nhanh, ~0.5s) |
| `pixi run -e test python -m pytest tests/test_links_utils.py -v` | Chạy một file cụ thể |
| `pixi run -e test python -m pytest -k "TestConvert" -v` | Chạy một class/pattern cụ thể |

> [!TIP]
> Sau mỗi lần merge upstream, chạy `pixi run -e test test-syntax` trước tiên.
> Nó bắt được syntax errors mà không cần import bất kỳ module nào (không cần DB, không cần bot token).

## 3. Cấu trúc test suite

```
tests/
├── __init__.py
├── conftest.py              # Project root vào sys.path
├── test_syntax.py           # Compile-check mọi .py file
├── test_links_utils.py      # Unit tests: URL/link detection regex
└── test_config_manager.py   # Unit tests: Config type conversion
```

### 3.1. `test_syntax.py` — Syntax compile check

**Loại:** Smoke test (không import, không side effects).

Duyệt mọi file `.py` trong project (trừ `.pixi/`, `.git/`, `__pycache__/`, `.claude/`) và gọi `py_compile.compile()`. Mỗi file là một test case riêng — khi fail sẽ chỉ rõ file + dòng lỗi.

**Bắt được:**
- Syntax errors do merge conflict (ví dụ: hai `else` cùng cấp indent)
- F-string syntax chỉ hợp lệ trên Python 3.12+ nhưng project dùng 3.11
- `from __future__` import sai vị trí
- Bất kỳ lỗi nào khiến Python không parse được file

**KHÔNG bắt được:** lỗi runtime (import thiếu module, attribute không tồn tại, logic sai).

### 3.2. `test_links_utils.py` — URL/link detection

**Loại:** Unit test (pure functions, không async, không side effects).

Test các regex functions trong [@bot/helper/ext_utils/links_utils.py](../bot/helper/ext_utils/links_utils.py):
`is_magnet`, `is_url`, `is_gdrive_link`, `is_telegram_link`, `is_share_link`, `is_rclone_path`, `is_gdrive_id`.

Mỗi function có test cho cả valid input và invalid input.

### 3.3. `test_config_manager.py` — Config singleton

**Loại:** Unit test (import `bot` package — triggers logging setup nhưng không kết nối external services).

Test 3 nhóm logic của [@bot/core/config_manager.py](../bot/core/config_manager.py):
- **`Config._convert()`** — chuyển đổi type: bool, int, str, list, dict, None, invalid key/value
- **`Config.set()` / `Config.get()`** — đọc/ghi + error handling
- **`Config._process_config_value()`** — business rules: DEFAULT_UPLOAD fallback, URL strip trailing slash

> [!NOTE]
> Tests cho `Config` dùng `setup_method`/`teardown_method` để restore state sau mỗi test,
> vì `Config` là class-level singleton (classmethod-based, không có instance).

## 4. Viết test mới

### 4.1. Chọn đúng loại test

| Loại | Khi nào dùng | Ví dụ |
|---|---|---|
| **Syntax check** | Tự động — mọi `.py` file mới đều được check | Không cần viết thêm |
| **Unit test (pure)** | Function không import heavy dependencies | `links_utils`, `get_size_bytes` |
| **Unit test (with bot import)** | Cần `Config` hoặc module trong `bot/` | `config_manager`, `help_messages` |
| **Async unit test** | Function async nhưng mock được I/O | (chưa có — xem [Roadmap](#6-mở-rộng-roadmap)) |

### 4.2. Tạo file test

1. Tạo file `tests/test_<module_name>.py`
2. Naming convention: `Test<ClassName>` cho class, `test_<behavior>` cho function
3. Parametrize khi test nhiều input cùng logic:

```python
import pytest

@pytest.mark.parametrize("input_val,expected", [
    ("100k", 102400),
    ("5m", 5242880),
    ("2g", 2147483648),
])
def test_get_size_bytes(input_val, expected):
    from bot.helper.ext_utils.bot_utils import get_size_bytes
    assert get_size_bytes(input_val) == expected
```

### 4.3. Test async functions

`pytest-asyncio` đã được cấu hình với `asyncio_mode = "auto"`. Viết test async bình thường:

```python
async def test_some_async_function():
    result = await my_async_func()
    assert result == expected
```

### 4.4. Modules nên test tiếp theo

| Module | File | Lý do ưu tiên |
|---|---|---|
| `bot_utils.get_size_bytes` | `bot/helper/ext_utils/bot_utils.py` | Pure function, parse size strings |
| `bot_utils.arg_parser` | `bot/helper/ext_utils/bot_utils.py` | Logic phức tạp, dễ regression |
| `files_utils.get_base_name` | `bot/helper/ext_utils/files_utils.py` | Path/filename processing |
| `bulk_links` | `bot/helper/ext_utils/bulk_links.py` | Text parsing, dễ test |

## 5. Conventions

- **Không import file có side effects nặng** (kết nối DB, tạo Telegram client) trong unit tests — mock hoặc skip.
- **`bot/__init__.py` import là OK** — nó chỉ setup logging và tạo event loop, không kết nối external services.
- **Restore state** khi test mutate global state (ví dụ `Config.set()`), dùng `setup_method`/`teardown_method`.
- **Test ID phải descriptive** — `test_valid_btih` rõ hơn `test_case_1`.
- **Thư mục skip cho syntax check:** thêm vào `SKIP_DIRS` trong `test_syntax.py` nếu cần.

## 6. Mở rộng (Roadmap)

<details><summary>Các hướng mở rộng test suite trong tương lai</summary>

### CI Integration

Thêm GitHub Actions workflow chạy `pixi run -e test test` trên mỗi PR:

```yaml
# .github/workflows/test.yml (draft)
name: Tests
on: [pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: prefix-dev/setup-pixi@v0.8.1
      - run: pixi run -e test test
```

### Async integration tests

Mock external services (Telegram API, MongoDB, aria2c RPC) để test task lifecycle:
- `TaskConfig` initialization
- Download listener callbacks
- Upload flow orchestration

### Coverage tracking

Thêm `pytest-cov` vào `feature.test`:

```bash
pixi run -e test python -m pytest --cov=bot --cov-report=term-missing tests/
```

</details>
