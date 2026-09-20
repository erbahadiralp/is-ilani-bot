# İş İlanı Bulucu 

Türkiye'deki şirketlerin **resmî kariyer sayfalarını ve ATS portallerini** düzenli olarak tarayan, yeni mezun / junior seviyesindeki teknoloji ilanlarını **Telegram'dan anlık bildiren** bir otomasyon botu.

Amaç, ilanı yayımlandığı gün görmek: aracı sitelerin gecikmesini beklemeden şirketin kendi panosundan okur.

---

## Ne yapar

- 162 kayıtlı kaynağı (şu an 96'sı etkin) belirli aralıklarla tarar.
- Yalnız **teknoloji alanındaki erken kariyer** ilanlarını bildirir; senior/lead ilanlarını ve "en az 3+ yıl deneyim" isteyen ilanları eler.
- Aynı ilanı ikinci kez bildirmez (URL bazlı kalıcı mükerrer kontrolü).
- Yeni mezun **program sayfalarındaki** (Yetenek Kuşağı, Road to Tech vb.) içerik değişikliklerini izler, başvuru dönemi açıldığında haber verir.
- Bir kaynak bozulursa sessizce sıfır ilan dönmez; hata verir ve Telegram'a alarm düşer.

## Nasıl çalışır

```
Kaynaklar  ->  Okuyucular      ->  Filtre        ->  SQLite      ->  Telegram
(96 kaynak)    (adaptörler)        (uygunluk)        (mükerrer)      (bildirim kuyruğu)
```

1. **Zamanlayıcı** (APScheduler) tarama döngüsünü tetikler.
2. **Okuyucu** her kaynağı kendi tipine uygun adaptörle okur (REST API, HTML, JSON-LD veya tarayıcı).
3. **Filtre** başlığı ve açıklamayı Türkçe-İngilizce eşleştirmeyle değerlendirir; uygun olmayanlar atılır.
4. **Veritabanı** ilanı URL hash'iyle kaydeder; kayıt zaten varsa bildirim üretilmez.
5. **Bildirici** kuyruktaki ilanları Telegram'a gönderir; gönderim başarısız olursa kayıt kuyrukta kalır ve 2 dakikada bir yeniden denenir.

## Tarama saatleri

| Saat (Europe/Istanbul) | Genel kaynaklar | Şirket + program sayfaları |
|---|---|---|
| 08:00 – 18:59 | 15 dakikada bir | 15 dakikada bir |
| 19:00 – 23:59 | 45 dakikada bir | 15 dakikada bir |
| 00:00 – 07:59 | taranmaz | 15 dakikada bir |

`/tara` komutu saat gözetmeksizin anlık tarama başlatır.

## Desteklenen kaynak tipleri

Her kaynak `companies.json` içinde bir `type` değeriyle tanımlıdır ve o tipin adaptörüyle okunur.

- **ATS platformları:** Workday, Lever, Greenhouse, SmartRecruiters, Ashby, SAP SuccessFactors (klasik ve Career Site Builder), Oracle Cloud Recruiting, Teamtailor, Eightfold, HRPeak, Hirebridge, Peoplise, FlowQ
- **Kurum içi portaller:** Akbank, QNB, Turkcell, Baykar, Amazon, AlbarakaTech ve savunma sanayii panoları için ayrı adaptörler
- **`generic`:** CSS seçici ile yapılandırılan, JSON-LD veya HTML kartlarından okuyan genel adaptör
- **Tarayıcı gerektirenler:** JavaScript ile render edilen 7 portal Playwright + Chromium ile okunur; diğerleri tarayıcısız çalışır

Ek kaynaklar: LinkedIn ve Indeed TR (`python-jobspy` üzerinden), Kariyer.net (varsayılan kapalı).

---

## Kurulum

Gereksinim: Python 3.10+

```bash
git clone https://github.com/erbahadiralp/isapp.git
cd isapp

python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

Tarayıcı gerektiren kaynakları da kullanacaksan Chromium'u kur:

```bash
python -m playwright install chromium
# Linux'ta sistem kütüphaneleri için ayrıca:
sudo python -m playwright install-deps chromium
```

Chromium kurulmazsa yalnız o 7 kaynak hata verir, diğerleri çalışmaya devam eder.

### Ayarlar

```bash
cp .env.example .env
```

`.env` içindeki zorunlu iki değer:

| Değişken | Nereden alınır |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Telegram'da [@BotFather](https://t.me/BotFather)'a `/newbot` yaz |
| `TELEGRAM_CHAT_ID` | Telegram'da [@userinfobot](https://t.me/userinfobot)'a `/start` yaz |

Kalan değişkenler (tarama aralığı, veritabanı yolu, sessiz saatler, proxy) isteğe bağlıdır; açıklamaları `.env.example` içindedir.

### Çalıştırma

```bash
python main.py
```

Bot açılışta veritabanını hazırlar, ilk taramayı hemen yapar ve Telegram'da komutları dinlemeye başlar.

## Telegram komutları

| Komut | Açıklama |
|---|---|
| `/start` | Bot durumu ve ilan istatistikleri |
| `/durum` | Aynı |
| `/tara` | Saat gözetmeksizin anlık tarama |

---

## Sunucuda sürekli çalıştırma

`jobhunter.service` dosyasındaki kullanıcı adını ve yolları kendine göre düzenleyip systemd'ye tanıt:

```bash
sudo cp jobhunter.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now jobhunter
sudo systemctl status jobhunter
journalctl -u jobhunter -f
```

Güncelleme adımlarının tamamı [SERVER_UPDATE.md](SERVER_UPDATE.md) içindedir.

## Proje yapısı

```
main.py                 Giriş noktası
config.py               Ayarlar (.env okur)
scheduler.py            Zamanlanmış görevler
database.py             SQLite, mükerrer kontrolü, bildirim kuyruğu
notifier.py             Telegram bildirimleri
bot.py                  Telegram komutları
watchlist.py            Uygunluk filtresi ve radar listesi
companies.json          Kaynak tanımları (162 kayıt)
programs.json           İzlenen program sayfaları (14 kayıt)
scrapers/               Kaynak adaptörleri
tools/                  Kaynak keşif ve doğrulama araçları (CLI)
tests/                  Birim testleri (66 test, ağ erişimi gerektirmez)
```

## Test ve doğrulama

```bash
python -m pytest tests -q                  # birim testleri, ağ erişimi gerekmez
python tools/audit_companies.py            # kaynakları canlı okur, rapor üretir (DB/Telegram kullanmaz)
python tools/verify_candidates.py          # aday kaynakları gerçek okuyucuyla dener
python tools/report_coverage.py            # kapsam raporunu yeniden üretir
```

`tools/` altındaki araçların tamamı salt okunur çalışır: veritabanına yazmaz, bildirim göndermez.

## Yeni kaynak ekleme

Kaynaklar **doğrulanmadan etkinleştirilmez**. HTTP 200 dönmesi tek başına kanıt sayılmaz; Cloudflare kontrol sayfaları, aday giriş ekranları ve kapanmış panolar da 200 döner.

1. Kaynağı `tools/add_sources.py` ile `enabled: false` olarak ekle.
2. `python tools/verify_candidates.py` ile gerçek okuyucudan geçir.
3. Okuma hatasızsa, sayfalama ve sonuç sayımı tutarlıysa ve pano gerçekten o şirkete aitse `enabled: true` yap.

## Kapsam ve ilkeler

- Yalnız **kamuya açık** sayfalar okunur. Oturum açılmaz, kimlik bilgisi istenmez, saklanmaz.
- Bot **başvuru göndermez**; sadece ilanı bulur ve bildirir.
- Kişisel hiçbir veri toplanmaz; veritabanında yalnız ilan başlığı, şirket, konum ve bağlantı tutulur.
- Bu depo kişisel kullanım için yazılmıştır. Kullanacaksan taradığın sitelerin kullanım şartlarına ve `robots.txt` kurallarına uymak senin sorumluluğundadır.

## Ayrıntılı dokümanlar

| Dosya | İçerik |
|---|---|
| [PROJE_DOKUMANTASYONU.md](PROJE_DOKUMANTASYONU.md) | Mimari, filtre mantığı, kaynak keşif hattı, açık sınırlamalar |
| [SOURCE_COVERAGE.md](SOURCE_COVERAGE.md) | Kaynak kapsamı ve doğrulama durumu |
| [BANK_COVERAGE.md](BANK_COVERAGE.md) | Banka kaynaklarının durumu |
| [TRACKING.md](TRACKING.md) | Şirket ve program takibi notları |
| [SERVER_UPDATE.md](SERVER_UPDATE.md) | Sunucu kurulumu ve güncelleme |

## Lisans

MIT — bkz. [LICENSE](LICENSE)
