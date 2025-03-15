#!/bin/bash
echo "Menginstal dependencies..."
pkg update && pkg upgrade -y
pkg install python -y
pip install requests scapy
echo "Instalasi selesai. Jalankan dengan: python3 attack.py"
