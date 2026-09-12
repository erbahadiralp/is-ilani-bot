> Güncel ayrıntılı rehber: [PROJE_DOKUMANTASYONU.md](PROJE_DOKUMANTASYONU.md). Aşağıdaki eski bilgiler tarihsel olabilir.

# Job Hunter Telegram Bot — Proje Dokümanı

## Amaç

İş arama sürecini otomatikleştirmek. LinkedIn, Kariyer.net ve Indeed TR'yi periyodik olarak tarayıp yeni junior/yeni mezun ilanlarını anında Telegram üzerinden bildiren bir bot.

---

## Hedef Pozisyonlar

- Junior Java Backend Developer
- Junior Spring Boot Developer
- Junior Data Scientist / Veri Bilimcisi
- Junior Data Engineer / Veri Mühendisi

**Lokasyon:** İstanbul (remote ilanlar da dahil)  
**Deneyim seviyesi:** Yeni mezun · 0-2 yıl · Entry Level

---

## Veri Kaynakları

| Kaynak | URL | Notlar |
|--------|-----|--------|
| LinkedIn Jobs | linkedin.com/jobs/search | JavaScript ağırlıklı, bot koruması var |
| Kariyer.net | kariyer.net/is-ilanlari | TR'nin en büyük iş ilanı sitesi |
| Indeed TR | tr.indeed.com/jobs | Cloudflare koruması mevcut |

---

## Nasıl Çalışır

1. Bot her 30 dakikada bir 3 kaynağı tarar
2. Her kaynakta birden fazla query çalıştırır (Türkçe + İngilizce kombinasyonları)
3. Bulunan ilanlar keyword filtreden geçer — senior / lead / deneyimli elenır
4. Daha önce görülmemiş ilanlar SQLite'a kaydedilir
5. Yeni ilan varsa Telegram'a bildirim gönderilir
6. Herhangi bir scraper çökerse Telegram'a hata alarmı gönderilir

---

## Teknoloji Stack

| Katman | Teknoloji | Gerekçe |
|--------|-----------|---------|
| Dil | Python 3 | |
| Browser otomasyonu | Playwright | LinkedIn ve Indeed JS ağırlıklı sayfalar render eder, düz requests ile boş HTML döner. Playwright gerçek bir tarayıcı ayağa kaldırır, bot tespitini zorlaştırır |
| Fallback scraping | requests + BeautifulSoup4 | Playwright'ın işe yaramadığı durumlarda ve Kariyer.net gibi daha basit sitelerde |
| Proxy rotasyonu | Rotating proxy servisi (örn. Webshare, BrightData) | Hetzner gibi veri merkezi IP'leri LinkedIn/Indeed tarafından hızla banlanır |
| Zamanlama | APScheduler | Scraping döngüsü + DB bakım görevi |
| Veritabanı | SQLite | Mükerrer ilan engeli |
| Telegram | pyTelegramBotAPI | Bildirim + hata alarmı |
| Ortam değişkenleri | python-dotenv (.env) | Hassas bilgilerin kod dışında tutulması |
| Çalışma ortamı | Hetzner VPS, systemd service | |

---

## Anti-Bot Stratejisi

LinkedIn ve Indeed IP bazlı ve davranışsal bot tespiti yapar. Bunu aşmak için:

- **Playwright** ile gerçek tarayıcı ayağa kaldırılır (headless Chromium)
- **Proxy rotasyonu** — her istek farklı bir IP'den gönderilir, veri merkezi IP'si kullanılmaz
- **Random sleep** — istekler arasına rastgele bekleme süresi eklenir, düzenli örüntü oluşmaz
- **Rotating user-agent** — her istekte farklı tarayıcı kimliği

---

## Ortam Değişkenleri (.env)

Hassas bilgiler `.env` dosyasında tutulur, Git'e commit edilmez.

```
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
CHECK_INTERVAL_MINUTES=30
PROXY_URL=
DB_PATH=jobs.db
```

---

## Hata Alarm Mekanizması

Scraper çöktüğünde sadece log dosyasına yazmakla kalmaz, Telegram'a doğrudan bildirim gönderir:

```
🚨 HATA: LinkedIn taraması çöktü!
Hata: TimeoutError - sayfa yüklenemedi
Zaman: 2026-06-28 04:15:33
```

Site HTML yapısını değiştirdiğinde (selector bozulması) de aynı alarm tetiklenir.

---

## Veritabanı Bakımı

SQLite tablosu zamanla şişmemesi için APScheduler üzerinden haftalık otomatik temizlik görevi çalışır — 30 günden eski ilan kayıtları silinir.

---

## Bildirim Formatı

```
🚀 YENİ İLAN BULDUM!

💼 Kaynak: LinkedIn
🏢 Firma: Acme Corp
👤 Pozisyon: Junior Java Developer
📍 Konum: İstanbul

[İlana Git / Başvur]
```

---

## Telegram Bot Komutları

| Komut | Açıklama |
|-------|----------|
| `/start` | Bot durumu ve takip edilen ilan sayısı |
| `/durum` | Aynısı |
| `/tara` | Manuel anında tarama başlat |

---

## Çalışma Ortamı

- Hetzner VPS üzerinde 7/24 çalışır
- systemd service olarak yönetilir, sunucu restart'ta otomatik ayağa kalkar
- Loglar `bot.log` dosyasına yazılır
- Scraper hataları hem loga hem Telegram'a düşer

---

## Teknik Notlar

**Telegram Rate Limit:** Tek taramada çok sayıda yeni ilan bulunabilir. Bunların aynı anda gönderilmesi Telegram'ın `429 Too Many Requests` hatasını tetikler ve botu geçici olarak susturur. Her mesaj arasına kısa bir bekleme süresi konulmalı.

**Playwright Sunucu Kurulumu:** Playwright, tarayıcıları ve Linux grafik bağımlılıklarını ayrıca indirmek ister. VPS'e kurulum sırasında `playwright install --with-deps` komutu çalıştırılmalı, aksi halde tarayıcı başlatılamaz.
