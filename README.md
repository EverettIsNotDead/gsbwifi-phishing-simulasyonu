# GSB-WIFI Phishing Simulation & Security Auditing Panel

![Operasyon Paneli](https://github.com/EverettIsNotDead/gsbwifi-phishing-simulasyonu/portal_files/resources/images/screenshot.png)

Bu proje, halka açık Captive Portal (GSBWIFI) ağ yapılarındaki güvenlik açıklarını analiz etmek ve kullanıcı farkındalığını test etmek amacıyla geliştirilmiş, uçtan uca otomatize edilmiş bir **Evil Twin** ve **Phishing** saldırı simülasyon aracıdır.

## 🧠 Teknik Çalışma Prensibi

Sistem, modern ağ cihazlarının varsayılan davranışlarını ve kullanıcı alışkanlıklarını suistimal eden dört temel aşama üzerine kuruludur:

1. **Evil Twin & Auto-Association:** Mobil cihazlar, daha önce bağlandıkları ağları SSID isimlerine göre hafızada tutar. Bu araç, hedef ağ ile aynı isimde yayın yaparak kapsama alanındaki cihazların "bilinen güvenli ağ" varsayımıyla otomatik olarak ağa katılmasını sağlar.
2. **Traffic Interception (Layer 3):** NoDogSplash motoru kullanılarak ağa dahil olan istemcilerin tüm HTTP trafiği geçici bir duvara çarptırılır. Kullanıcı hangi URL'ye gitmeye çalışırsa çalışsın sahte portala hapsedilir.
3. **Dynamic Gateway Injection:** Script, çalışma anında ağ kartının aldığı IP adresini tespit eder ve portal dosyalarındaki tüm yönlendirme linklerini bu IP ile gerçek zamanlı olarak günceller.
4. **Asenkron Veri Hasadı:** Kullanıcı bilgileri, asenkron bir logger servisi üzerinden yerel sistemde depolanır ve anlık olarak operatör terminaline yansıtılır.

## 🛠️ Kurulum ve Bağımlılıklar

Script, sistemde aşağıdaki kritik bağımlılıkların varlığını denetler. Eğer araçlar manuel (GitHub) veya paket yöneticisi (APT) ile kurulmuşsa, yollarını otomatik olarak doğrular.

### Gereksinimler:
- create_ap (NAT ve AP yönetimi)
- nodogsplash (Captive Portal motoru)
- dnsmasq (DHCP/DNS konfigürasyonu)
- python3 (Ana kontrol ünitesi)

git clone https://github.com/EverettIsNotDead/gsbwifi-phishing-simulasyonu
cd gsbwifi-phishing-simulasyonu
sudo python3 gsb.py

## 💻 Kullanım ve CLI Parametreleri

Araç, hem interaktif seçim modunu hem de otomasyon süreçleri için komut satırı argümanlarını destekler.

sudo python3 gsb.py [seçenekler]

### Parametre Listesi

| Parametre | Uzun Versiyon | Açıklama | Varsayılan |
| :--- | :--- | :--- | :--- |
| -i | --interface | Yayın yapılacak fiziksel Wi-Fi arayüzü | (İnteraktif) |
| -s | --ssid | Yayınlanacak ağın görünen adı | GSBWIFI |
| -h | --help | Yardım menüsünü ve parametreleri gösterir | - |

**Örnek Senaryo:**
sudo python3 gsb.py -i wlan1 -s GSBWIFI

## 📊 Operasyonel Veri Yönetimi

Operasyon sırasında üretilen veriler, şu dosyalarda standardize edilmiştir:

- **Sistem Olay Kayıtları:** ./gsb_activity.log
- **Kimlik Bilgisi Havuzu:** /etc/nodogsplash/passwords.txt

## ⚠️ Yasal Uyarı

Bu yazılım sadece etik hackerlık ve sızma testi eğitimleri için geliştirilmiştir. Yetkisiz ağlar üzerinde kullanımı yerel ve uluslararası yasalarca suç teşkil edebilir. Tüm hukuki sorumluluk son kullanıcıya aittir.

---
**Geliştirici:** [EverettIsNotDead](https://github.com/EverettIsNotDead)
