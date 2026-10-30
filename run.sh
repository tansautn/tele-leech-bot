#!/bin/bash

# Đường dẫn đến thư mục .venv
VENV_DIR="$PWD/.venv"

# Nếu thư mục .venv không tồn tại thì cài đặt environment
if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found. Running uv pip sync requirements.txt..."
    uv pip sync requirements.txt
fi

# Kích hoạt virtual environment
source "$VENV_DIR/bin/activate"

# Đợi 2 giây
sleep 2

# Lấy ngày hôm nay để ghi log theo định dạng yyyy-mm-dd
TODAY=$(date +%Y-%m-%d)

# Chạy bot và lưu log
python -m bot >> "$PWD/log-$TODAY.log"
