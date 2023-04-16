#!/bin/bash
set -e 
echo "Installing to /opt/niberator.."
mkdir -p /opt/niberator && touch /opt/niberator/write-test.txt
if [ $? -ne 0 ]; then
    echo "Cannot write to /opt/niberator. Please run as root or sudo."
    exit 1
fi
rm /opt/niberator/write-test.txt
systemd --version
if [ $? -ne 0 ]; then
    echo "Systemd not found. Please install systemd."
    exit 1
fi
cp switch-speed-by-hat-input.py /opt/niberator
cp switch-speed-by-hat-input.service /etc/systemd/system
systemctl daemon-reload
echo "Installed."
