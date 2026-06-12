#!/bin/bash
# ═══════════════════════════════════════════
# MACH-1 v3 — Setup Script
# Run once on a fresh machine:
#   chmod +x setup.sh && ./setup.sh
# ═══════════════════════════════════════════

set -e

MACH1_HOME="$(cd "$(dirname "$0")" && pwd)"
USER=$(whoami)

echo "══════════════════════════════════════"
echo "  MACH-1 v3 Setup"
echo "  Home: $MACH1_HOME"
echo "  User: $USER"
echo "══════════════════════════════════════"

# ── 1. System packages ──────────────────
echo "[1/6] Installing system packages..."
sudo apt-get update -qq
sudo apt-get install -y -qq python3 python3-pip python3-venv git curl

# ── 2. Python virtual environment ───────
echo "[2/6] Setting up Python venv..."
if [ ! -d "$MACH1_HOME/venv" ]; then
    python3 -m venv "$MACH1_HOME/venv"
fi
source "$MACH1_HOME/venv/bin/activate"
pip install --upgrade pip -q
pip install -r "$MACH1_HOME/requirements.txt" -q

# ── 3. Environment file ────────────────
echo "[3/6] Setting up .env..."
if [ ! -f "$MACH1_HOME/.env" ]; then
    cp "$MACH1_HOME/.env.example" "$MACH1_HOME/.env"
    # Fix paths for this machine
    sed -i "s|/home/cumpooter/mach-1|$MACH1_HOME|g" "$MACH1_HOME/.env"
    echo "  → Created .env from template"
    echo "  → EDIT .env AND ADD YOUR API KEYS!"
else
    echo "  → .env already exists, skipping"
fi

# ── 4. Create directories ──────────────
echo "[4/6] Creating directories..."
mkdir -p "$MACH1_HOME/data/projects"
mkdir -p "$MACH1_HOME/logs"
mkdir -p "$MACH1_HOME/backups"

# ── 5. Initialize database ─────────────
echo "[5/6] Initializing database..."
cd "$MACH1_HOME"
source venv/bin/activate
python3 -c "from utils.database import db; print(f'Database ready: {db.db_path}')"

# ── 6. Install systemd services ────────
echo "[6/6] Installing systemd services..."

# Main agent service
sudo tee /etc/systemd/system/mach1.service > /dev/null <<EOF
[Unit]
Description=MACH-1 Agent System
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$MACH1_HOME
Environment=PATH=$MACH1_HOME/venv/bin:/usr/bin:/bin
ExecStart=$MACH1_HOME/venv/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Dashboard service
sudo tee /etc/systemd/system/mach1-dashboard.service > /dev/null <<EOF
[Unit]
Description=MACH-1 Dashboard
After=network.target mach1.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$MACH1_HOME/dashboard
Environment=PATH=$MACH1_HOME/venv/bin:/usr/bin:/bin
Environment=PYTHONPATH=$MACH1_HOME
ExecStart=$MACH1_HOME/venv/bin/python3 app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable mach1.service
sudo systemctl enable mach1-dashboard.service

echo ""
echo "══════════════════════════════════════"
echo "  SETUP COMPLETE!"
echo "══════════════════════════════════════"
echo ""
echo "  Next steps:"
echo "  1. Edit .env and add your API keys:"
echo "     nano $MACH1_HOME/.env"
echo ""
echo "  2. Start the services:"
echo "     sudo systemctl start mach1"
echo "     sudo systemctl start mach1-dashboard"
echo ""
echo "  3. Open dashboard:"
echo "     http://localhost:5000"
echo ""
echo "  4. Check status:"
echo "     sudo systemctl status mach1"
echo "     sudo systemctl status mach1-dashboard"
echo ""
echo "  5. View logs:"
echo "     tail -f $MACH1_HOME/logs/mach1.log"
echo "     journalctl -u mach1 -f"
echo ""
