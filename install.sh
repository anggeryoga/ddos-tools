#!/bin/bash

# Update daftar paket
pkg update

# Instal Python dan pip (jika belum terinstal)
pkg install -y python

# Instal dependensi Python menggunakan pip
pip install requests colorama

# Konfirmasi Instalasi
echo "Semua dependensi telah diinstal."
echo "Anda sekarang dapat menjalankan attack.py."