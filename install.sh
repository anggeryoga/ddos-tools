#!/bin/bash

# Update daftar paket Termux
pkg update

# Instal Python dan pip (jika belum terinstal)
pkg install -y python

# Instal dependensi Python menggunakan pip
pip install scapy requests colorama

# Instal nmap (optional)
pkg install -y nmap

# Konfirmasi Instalasi
echo "Semua dependensi telah diinstal."
echo "Anda sekarang dapat menjalankan attack.py."