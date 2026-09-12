> Güncel ayrıntılı rehber: [PROJE_DOKUMANTASYONU.md](PROJE_DOKUMANTASYONU.md). Aşağıdaki eski bilgiler tarihsel olabilir.

> Şirket/program takibi güncellemesi ve kurulum sınırları: [TRACKING.md](TRACKING.md). Şirket kapsamı: [SOURCE_COVERAGE.md](SOURCE_COVERAGE.md).

# Job Hunter Telegram Bot 🤖

LinkedIn, Indeed TR ve Kariyer.net'i otomatik tarayan, yeni junior/yeni mezun ilanlarını Telegram'a bildiren bot.

---

## Özellikler

- 🔄 Her 30 dakikada otomatik tarama (ayarlanabilir)
- 🎯 Junior / yeni mezun / entry level ilanlarını filtreler
- 🚫 Senior, lead, müdür gibi ilanları otomatik eler
- 📬 Anlık Telegram bildirimi
- 🚨 Scraper hataları için Telegram alarm
- 🗃️ SQLite ile mükerrer ilan kontrolü
- 🧹 30 günlük otomatik DB temizliği
- 🌙 Sessiz saat desteği (00:00–07:30 arası tarama yapmaz)
- ⌨️ `/start`, `/durum`, `/tara` komutları
- **Proxy gerektirmez** — `python-jobspy` ile LinkedIn iç API'si kullanılır

---

## Mimari

| Kaynak | Yöntem |
|--------|--------|
| **LinkedIn** | `python-jobspy` (iç API, proxy yok) |
| **Indeed TR** | `python-jobspy` (iç API, proxy yok) |
| **Kariyer.net** | `requests + BeautifulSoup4` |

---

## Hızlı Kurulum

### 1. Virtual environment oluştur

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Bağımlılıkları kur

```bash
pip install -r requirements.txt
```

> ℹ️ Playwright kurulumu **gerekmez** — `python-jobspy` kullanıyoruz.

### 3. Ortam değişkenlerini ayarla

```bash
cp .env.example .env
nano .env   # Token ve Chat ID'yi doldur
```

`.env` içeriği:

```
TELEGRAM_BOT_TOKEN=1234567890:ABCdef...
TELEGRAM_CHAT_ID=123456789
CHECK_INTERVAL_MINUTES=30
PROXY_URL=           # opsiyonel
DB_PATH=jobs.db
LOG_PATH=bot.log
```

> 💡 **Telegram Bot Token:** [@BotFather](https://t.me/BotFather)'a `/newbot` yazın.  
> 💡 **Chat ID:** [@userinfobot](https://t.me/userinfobot)'a `/start` yazın.

### 6. Botu başlat

```bash
python main.py
```

---

## Telegram Komutları

| Komut | Açıklama |
|-------|----------|
| `/start` | Bot durumu ve ilan istatistikleri |
| `/durum` | Aynı |
| `/tara` | Anlık manuel tarama başlat |

---

## Hetzner VPS — systemd ile Sürekli Çalıştırma

```bash
# 1. Kullanıcı adını düzenle
nano jobhunter.service

# 2. Service dosyasını kopyala
sudo cp jobhunter.service /etc/systemd/system/

# 3. Yeniden yükle ve etkinleştir
sudo systemctl daemon-reload
sudo systemctl enable jobhunter
sudo systemctl start jobhunter

# 4. Durumu kontrol et
sudo systemctl status jobhunter

# 5. Logları izle
sudo journalctl -u jobhunter -f
# veya
tail -f bot.log
```

---

## Proje Yapısı

```
isilan_bot/
├── .env.example          # Ortam değişkeni şablonu
├── .gitignore
├── requirements.txt
├── main.py               # Giriş noktası
├── config.py             # Ayarlar
├── database.py           # SQLite
├── notifier.py           # Telegram bildirimleri
├── scheduler.py          # APScheduler görevleri
├── bot.py                # Telegram komutları
├── jobhunter.service     # systemd service
└── scrapers/
    ├── base.py           # Ortak scraper altyapısı
    ├── kariyer.py        # Kariyer.net (requests+BS4)
    ├── linkedin.py       # LinkedIn (Playwright)
    └── indeed.py         # Indeed TR (Playwright)
```

---

## Proxy Kullanımı

LinkedIn ve Indeed IP ban'larına karşı proxy önerilir:

```
PROXY_URL=http://user:pass@proxy-host:8080
```

Ücretsiz alternatif: [Webshare.io](https://webshare.io) (10 adet ücretsiz proxy)

---

## Notlar

- **Rate Limit:** Toplu bildirimler arasına otomatik 1.5 sn bekleme eklenir.
- **Selector Kırılması:** Site HTML'si değişirse scraper hata verir ve Telegram'a alarm düşer.
- **Log Dosyası:** `bot.log` — tüm işlemler ve hatalar kaydedilir.
