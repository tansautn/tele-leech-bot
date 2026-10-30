#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="teleleech"
SERVICE_USER="telebot"
SERVICE_GROUP="www-data"
UMASK="0066"
WORK_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="/home/${SERVICE_USER}/logs"
PIXI_HOME="/home/${SERVICE_USER}/.pixi"

# --- helpers ---
info()  { printf '\033[1;32m[+]\033[0m %s\n' "$*"; }
warn()  { printf '\033[1;33m[!]\033[0m %s\n' "$*"; }
die()   { printf '\033[1;31m[x]\033[0m %s\n' "$*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || die "Run as root (sudo $0)"

# --- user setup ---
if id "$SERVICE_USER" &>/dev/null; then
    info "User '$SERVICE_USER' already exists"
else
    info "Creating user '$SERVICE_USER' (group=$SERVICE_GROUP)"
    groupadd -f "$SERVICE_GROUP"
    useradd -r -m -g "$SERVICE_GROUP" -s /usr/sbin/nologin "$SERVICE_USER"
    info "User created"
fi

# --- log directory ---
mkdir -p "$LOG_DIR"
chown "${SERVICE_USER}:${SERVICE_GROUP}" "$LOG_DIR"

# --- install pixi if missing ---
if sudo -u "$SERVICE_USER" bash -c 'command -v pixi' &>/dev/null; then
    info "pixi already installed for $SERVICE_USER"
else
    info "Installing pixi for $SERVICE_USER ..."
    sudo -u "$SERVICE_USER" bash -c \
        'curl -fsSL https://pixi.sh/install.sh | PIXI_NO_PATH_UPDATE=1 bash'
    info "pixi installed at $PIXI_HOME/bin/pixi"
fi

PIXI_BIN="${PIXI_HOME}/bin"

# --- install project deps ---
info "Running pixi install in $WORK_DIR ..."
sudo -u "$SERVICE_USER" bash -c "export PATH=\"${PIXI_BIN}:\$PATH\" && cd \"$WORK_DIR\" && pixi install"

# --- ownership ---
chown -R "${SERVICE_USER}:${SERVICE_GROUP}" "$WORK_DIR"

# --- systemd unit ---
UNIT_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
info "Writing $UNIT_FILE"

cat > "$UNIT_FILE" <<EOF
[Unit]
Description=Tele Leech Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${SERVICE_USER}
Group=${SERVICE_GROUP}
UMask=${UMASK}
WorkingDirectory=${WORK_DIR}
Environment=PATH=${PIXI_BIN}:/usr/local/bin:/usr/bin:/bin
ExecStart=${PIXI_BIN}/pixi run bot
Restart=always
RestartSec=5
KillMode=mixed
KillSignal=SIGINT
TimeoutStopSec=60

StandardOutput=append:${LOG_DIR}/${SERVICE_NAME}.log
StandardError=append:${LOG_DIR}/${SERVICE_NAME}.log

[Install]
WantedBy=multi-user.target
EOF

# --- enable & start ---
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
info "Service '${SERVICE_NAME}' enabled"

if systemctl is-active --quiet "$SERVICE_NAME"; then
    systemctl restart "$SERVICE_NAME"
    info "Service restarted"
else
    systemctl start "$SERVICE_NAME"
    info "Service started"
fi

info "Done! Useful commands:"
echo "  systemctl status  $SERVICE_NAME"
echo "  journalctl -u $SERVICE_NAME -f"
echo "  tail -f $LOG_DIR/${SERVICE_NAME}.log"
