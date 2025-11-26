#!/bin/bash
# deploy_to_pi.sh - One-shot deployment script for DedSec OS

PI_USER="berry"
PI_HOST="berry"
PI_PATH="/home/berry/dedsec"

echo "════════════════════════════════════════════════════════════════"
echo "  DedSec OS - Deployment to Raspberry Pi"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check if Pi is reachable
echo "[*] Checking connection to $PI_HOST..."
if ! ping -c 1 -W 2 $PI_HOST &> /dev/null; then
    echo "[✗] Error: Cannot reach $PI_HOST"
    exit 1
fi
echo "[✓] Connection OK"
echo ""

# Create directory structure on Pi
echo "[*] Creating directory structure..."
ssh $PI_USER@$PI_HOST "mkdir -p $PI_PATH/{ui,core,logs,docs,archive}"
echo "[✓] Directories created"
echo ""

# Deploy main application files
echo "[*] Deploying core application files..."
scp -q app.py           $PI_USER@$PI_HOST:$PI_PATH/
echo "[✓] Core files deployed"

# Deploy configuration
echo "[*] Deploying configuration..."
scp -q config/settings.py  $PI_USER@$PI_HOST:$PI_PATH/config/ 2>/dev/null || {
    ssh $PI_USER@$PI_HOST "mkdir -p $PI_PATH/config"
    scp -q config/settings.py  $PI_USER@$PI_HOST:$PI_PATH/config/
}
echo "[✓] Configuration deployed"
echo ""

# Deploy UI framework
echo "[*] Deploying UI framework..."
scp -q ui/__init__.py       $PI_USER@$PI_HOST:$PI_PATH/ui/
scp -q ui/architecture.py   $PI_USER@$PI_HOST:$PI_PATH/ui/
scp -q ui/components.py     $PI_USER@$PI_HOST:$PI_PATH/ui/
scp -q ui/state.py          $PI_USER@$PI_HOST:$PI_PATH/ui/
scp -q ui/themes.py         $PI_USER@$PI_HOST:$PI_PATH/ui/
scp -q ui/rendering.py      $PI_USER@$PI_HOST:$PI_PATH/ui/
scp -q ui/tool_manager.py   $PI_USER@$PI_HOST:$PI_PATH/ui/
echo "[✓] UI framework deployed (7 modules)"

# Deploy core framework
echo "[*] Deploying core framework..."
scp -q core/__init__.py $PI_USER@$PI_HOST:$PI_PATH/core/
scp -q core/logging.py  $PI_USER@$PI_HOST:$PI_PATH/core/
echo "[✓] Core framework deployed (2 modules)"
echo ""

# Deploy systemd service file
echo "[*] Deploying systemd service..."
if [ -f "config/dedsec.service" ]; then
    scp -q config/dedsec.service $PI_USER@$PI_HOST:$PI_PATH/
    ssh $PI_USER@$PI_HOST "mkdir -p ~/.config/systemd/user && cp $PI_PATH/dedsec.service ~/.config/systemd/user/"
    echo "[✓] Service file deployed"
else
    echo "[!] Warning: config/dedsec.service not found"
fi
echo ""

# Set permissions
echo "[*] Setting permissions..."
ssh $PI_USER@$PI_HOST "chmod +x $PI_PATH/app.py && chmod -R 755 $PI_PATH"
echo "[✓] Permissions set"
echo ""

# Reload and restart service
echo "[*] Restarting DedSec service..."
ssh $PI_USER@$PI_HOST "systemctl --user daemon-reload && systemctl --user restart dedsec"

# Wait for service to start
sleep 2

# Check service status
echo "[*] Checking service status..."
if ssh $PI_USER@$PI_HOST "systemctl --user is-active dedsec" &> /dev/null; then
    echo "[✓] Service is running"
else
    echo "[!] Warning: Service may not be running. Check with:"
    echo "    ssh $PI_USER@$PI_HOST 'systemctl --user status dedsec'"
fi
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "  Deployment Summary"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "  Deployed to: $PI_USER@$PI_HOST:$PI_PATH"
echo "  Files deployed:"
echo "    • app.py (main application)"
echo "    • config/settings.py (configuration)"
echo "    • 7 UI framework modules"
echo "    • 2 core framework modules"
echo "    • 1 systemd service file"
echo ""
echo "  Service: dedsec.service"
echo "  Status: systemctl --user status dedsec"
echo "  Logs: journalctl --user -u dedsec -f"
echo ""
echo "[✓] Deployment complete!"
echo "════════════════════════════════════════════════════════════════"