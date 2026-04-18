# GSB-WIFI Phishing Saldırısı Simülasyon Aracı

Bu proje, halka açık Captive Portal (GSBWIFI) ağ yapılarındaki güvenlik açıklarını analiz etmek ve kullanıcı farkındalığını test etmek amacıyla geliştirilmiş, uçtan uca otomatize edilmiş bir **Evil Twin saldırı simülasyon aracıdır**.

---

## Teknik Çalışma Prensibi ve Arkaplan Mimarisi

Sistem, sadece bir ağ yayını yapmanın ötesinde, arkaplanda entegre çalışan **dört farklı katmandan** oluşur:

### 1. Ağ Katmanı (The Double-Edge NAT)

`create_ap` servisi kullanılarak hedef ağ ile aynı SSID (**GSBWIFI**) üzerinden bir yayın açılır.

Bu aşamada sistem, kurbanın internete çıkışını sağlayan kaynak arayüz ile yayın yapan arayüz arasında bir **NAT (Network Address Translation)** köprüsü kurar.

**Evil Twin saldırısı** bu aşamada gerçekleşir.

---

### 2. Captive Portal Yönlendirmesi

`nodogsplash` motoru kullanılarak client cihazın türüne ve işletim sistemine uyumlu olarak sahte captive portal yönlendirmesi yapılır.

**Phishing saldırısı** katmanı burada kurulur.

---

### 3. Dinamik Portal ve Taklit Yeteneği

Hazırlanan `splash.html`, gerçek GSBWIFI giriş ekranının CSS ve JS davranışlarını birebir taklit eder.

Script, her açılışta Portal içindeki tüm yönlendirme linklerini ve API endpointlerini o anki **Gateway IP adresine göre dinamik olarak günceller**.

Bu sayede 404 hataları ve Timeout problemleri tamamen engellenir.

---

### 4. Veri Hasadı ve Logger Servisi (Backend)

Arkaplanda asenkron çalışan `logger.py` servisi, portal üzerinden gönderilen form verilerini dinler, **verilerin ele geçirilmesi** bu aşamada gerçekleşir.

* Kullanıcı giriş bilgileri → `/etc/nodogsplash/passwords.txt` dosyasına yazılır
* Ana kontrol scripti (`gsb.py`) → bu dosyayı `tail -f` benzeri mantıkla izler
* Terminale **anlık bildirim** düşer

---

## Kurulum ve Bağımlılıklar

Script, sistemde gerekli bağımlılıkların varlığını otomatik olarak kontrol eder.

### Gereksinimler

* `create_ap` → Wireless Access Point yönetimi
* `nodogsplash` → Captive Portal motoru
* `dnsmasq` → DHCP ve DNS konfigürasyonu
* `python3` → Ana kontrol ve watcher

### Kurulum

```bash
git clone https://github.com/EverettIsNotDead/gsbwifi-phishing-simulasyonu
cd gsbwifi-phishing-simulasyonu
sudo python3 gsb.py
```

---

## Kullanım ve CLI Parametreleri

Araç hem interaktif mod hem de CLI parametreleri destekler.

### Parametre Listesi

| Kısa | Uzun          | Açıklama                    | Varsayılan |
| ---- | ------------- | --------------------------- | ---------- |
| `-i` | `--interface` | Yayın yapılacak Wi-Fi kartı | İnteraktif |
| `-s` | `--ssid`      | Yayınlanacak ağ adı         | GSBWIFI    |
| `-h` | `--help`      | Yardım menüsü               | -          |

---

### CLI Mode Örnek Kullanım

```bash
# wlan1 üzerinden 'GSBWIFI' adıyla operasyon başlat
sudo python3 gsb.py -i wlan1 -s GSBWIFI
```

---

## Operasyonel Veri Yönetimi

Operasyon sırasında üretilen veriler:

* **Sistem logları:** `./gsb_activity.log`
* **Toplanan veriler:** `/etc/nodogsplash/passwords.txt`

adreslerine loglanır.

---

## ⚠️ Yasal Uyarı

Bu yazılım sadece etik hackerlık ve sızma testi simulasyonları oluşturmak, sosyal mühendislik çalışmalarının arkaplanını öğrenmek ve toplumda phishing saldırılarına karşı farkındalık uyandırılması amacıyla geliştirilmiştir.

Yazılımın gerçek kişisel bilgileri ve şifreleri ele geçirmek, ağın iletişimini bozmak veya ağa bağlanmayı zorlaştırmak gibi ve benzeri herhangi bir sebeple kullanımı **suçtur** ve **tüm sorumluluk son kullanıcıya aittir**.

---

**Geliştirici:** [EverettIsNotDead](https://github.com/EverettIsNotDead)
