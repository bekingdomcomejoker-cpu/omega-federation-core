#!/bin/bash
# Omega Federation v2.0 - Termux Deployment Script
# This script sets up and runs the Omega Federation locally on Termux

set -e

echo "🌟 Omega Federation v2.0 - Termux Setup"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on Termux
if [ ! -d "$PREFIX" ]; then
    echo -e "${RED}❌ This script is designed for Termux. Please run it in a Termux environment.${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 1: Installing system dependencies...${NC}"
pkg update -y
pkg install -y python3 python3-dev pip git sqlite3

echo -e "${YELLOW}Step 2: Creating project directory...${NC}"
PROJECT_DIR="$HOME/omega-federation"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

echo -e "${YELLOW}Step 3: Cloning repository...${NC}"
if [ -d ".git" ]; then
    echo "Repository already exists. Pulling latest changes..."
    git pull origin main
else
    git clone https://github.com/bekingdomcomejoker-cpu/omega-federation-core.git .
fi

echo -e "${YELLOW}Step 4: Setting up Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

echo -e "${YELLOW}Step 5: Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install pydantic fastapi uvicorn

echo -e "${YELLOW}Step 6: Initializing Spine database...${NC}"
python3 omega_spine.py

echo -e "${YELLOW}Step 7: Setting up storage directory...${NC}"
mkdir -p storage/spine
mkdir -p storage/archive
mkdir -p logs

echo -e "${YELLOW}Step 8: Creating systemd service (optional)...${NC}"
SERVICE_FILE="$HOME/.config/systemd/user/omega-federation.service"
mkdir -p "$HOME/.config/systemd/user"

cat > "$SERVICE_FILE" << 'EOF'
[Unit]
Description=Omega Federation v2.0
After=network.target

[Service]
Type=simple
User=%u
WorkingDirectory=%h/omega-federation
Environment="PATH=%h/omega-federation/venv/bin"
ExecStart=%h/omega-federation/venv/bin/python3 -m uvicorn omega_api_server:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
EOF

echo -e "${GREEN}✓ Service file created at $SERVICE_FILE${NC}"

echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Start the API server: python3 -m uvicorn omega_api_server:app --host 0.0.0.0 --port 8000"
echo "2. The Spine database is at: $PROJECT_DIR/omega_spine.db"
echo "3. Storage directories are at: $PROJECT_DIR/storage/"
echo "4. Logs will be saved to: $PROJECT_DIR/logs/"
echo ""
echo "For persistent background execution, use:"
echo "  systemctl --user enable omega-federation.service"
echo "  systemctl --user start omega-federation.service"
echo ""
echo "To check logs:"
echo "  journalctl --user -u omega-federation.service -f"
echo ""
