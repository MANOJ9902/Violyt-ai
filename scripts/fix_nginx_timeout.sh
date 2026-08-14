#!/bin/bash
set -e
# Phase 1 lands just over 600s on research-heavy prompts, so nginx was severing
# runs the API had actually completed. Match the 20 minute client ceiling.
CONF=/etc/nginx/sites-enabled/default
BACKUP_DIR=/var/backups/nginx

# Backups must live outside sites-enabled — nginx globs that directory and a copy
# there registers a second default server.
sudo rm -f /etc/nginx/sites-enabled/default.bak.*
sudo mkdir -p "$BACKUP_DIR"
sudo cp "$CONF" "$BACKUP_DIR/default.$(date +%s)"

sudo sed -i 's/proxy_connect_timeout 600s;/proxy_connect_timeout 75s;/' "$CONF"
sudo sed -i 's/proxy_send_timeout 600s;/proxy_send_timeout 1200s;/' "$CONF"
sudo sed -i 's/proxy_read_timeout 600s;/proxy_read_timeout 1200s;/' "$CONF"
sudo sed -i 's/send_timeout 600s;/send_timeout 1200s;/' "$CONF"

echo "=== /api/ block after edit ==="
sudo sed -n '40,52p' "$CONF"

echo "=== stray backups in sites-enabled (must be empty) ==="
ls -1 /etc/nginx/sites-enabled/

sudo nginx -t
sudo systemctl reload nginx
echo "nginx_reloaded"

echo "=== effective timeouts ==="
sudo grep -hE 'proxy_(read|send|connect)_timeout|send_timeout' "$CONF" | sort -u
