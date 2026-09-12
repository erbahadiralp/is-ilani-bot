# Sunucu güncellemesi (git ile)

Güncel durum (10 Eylül 2026): 108 etkin kaynak, 108 başarılı son denetim; 1310 ham / 15 uygun kayıt; 14 sayfa monitörü. Ayrıntılı kapsam ve kalan işler [PROJE_DOKUMANTASYONU.md](PROJE_DOKUMANTASYONU.md) içindedir.

Bu belge güncellemenin GitHub'dan `git pull` ile alınmasını anlatır. Yollar `jobhunter.service` dosyasındaki değerlere göre yazıldı (`/home/youruser/isapp`, sanal ortam `venv/`). Sunucunda farklıysa komutlarda kendi yolunu kullan.

`.env`, veritabanı (`*.db`), `bot.log`, `venv/` ve `.source-audit/` git tarafından izlenmez. `git pull` bu dosyalara dokunmaz; mevcut Telegram ayarların ve bildirim geçmişin korunur.

## 0. Bilgisayarında: pushlamadan önce

Yeni dosyaların tamamı commit'e girmelidir. `scheduler.py` şu an git'te olmayan `scrapers/program_scraper.py`, `scrapers/kariyer_mail.py` ve `watchlist.py` dosyalarını içe aktarır; bunlar eksik kalırsa bot sunucuda açılırken `ModuleNotFoundError` ile durur.

```sh
git add -A                 # "git commit -am" YENI dosyalari eklemez, kullanma
git status                 # .env, *.db, bot.log listede OLMAMALI
git commit -m "Kaynak genisletme: 108 resmi kaynak"
git push origin main
```

## 1. Sunucu git deposu mu?

```sh
cd /home/youruser/isapp
git status
```

`not a git repository` hatası alırsan kurulum daha önce ZIP ile yapılmıştır. Bu durumda "İlk kez git'e geçiş" bölümünü uygula, sonra 2. adımdan devam et.

Depo özelse sunucunun GitHub'dan okuyabilmesi için kendi erişimi olmalıdır (salt okunur deploy key önerilir). Bu anahtar yalnız sunucuda durur; kimseyle paylaşılmaz.

## 2. Botu durdur ve yedek al

```sh
sudo systemctl stop jobhunter
mkdir -p ~/isapp-yedek
cp .env ~/isapp-yedek/.env
cp jobs.db ~/isapp-yedek/jobs-$(date +%F).db     # .env içindeki DB_PATH farklıysa o dosyayı kopyala
```

Veritabanını bot durduktan sonra kopyala; çalışırken alınan SQLite kopyası tutarsız olabilir.

## 3. Güncellemeyi çek

```sh
git status --short
git pull --ff-only origin main
```

`git status --short` çıktısında dosya görürsen önce ne olduğuna bak. En sık neden, sunucuda daha önce denetim araçlarının çalıştırılmış olmasıdır; bunlar izlenen rapor dosyalarını yeniden yazar ve `pull` işlemini engeller. Yalnız rapor dosyalarıysa sunucudaki kopyayı atıp devam edebilirsin:

```sh
git restore source_audit.json program_audit.json job_link_audit.json SOURCE_COVERAGE.md BANK_COVERAGE.md
git pull --ff-only origin main
```

`companies.json` veya kod dosyalarında yerel değişiklik görürsen silmeden önce incele. Kaynak kapatma gibi değişiklikleri sunucuda değil bilgisayarında yapıp pushlamak, sonraki çekmelerde çakışmayı önler.

## 4. Bağımlılıkları kur

```sh
venv/bin/python --version                          # 3.10 veya üzeri olmalı
venv/bin/python -m pip install -r requirements.txt
```

## 5. Chromium'u kur (18 kaynak için gerekli)

Tarayıcı gerektiren 18 kaynak vardır: 14 HRPeak panosu, 3 klasik SuccessFactors portalı (Softtech, Deloitte, Mercedes-Benz Otomotiv) ve Amazon. Chromium iki adımda kurulmalıdır:

```sh
sudo venv/bin/python -m playwright install-deps chromium   # sistem kütüphaneleri, yönetici yetkisiyle
venv/bin/python -m playwright install chromium             # tarayıcının kendisi, botu çalıştıran kullanıcıyla
```

İkinci komutu `sudo` ile çalıştırma. Playwright tarayıcıyı komutu çalıştıran kullanıcının ev dizinine (`~/.cache/ms-playwright`) indirir; `sudo` ile kurulursa tarayıcı root'a gider ve `youruser` kullanıcısıyla çalışan servis onu bulamaz. `playwright install --with-deps chromium` komutunu tek başına `sudo` ile çalıştırmak aynı hataya yol açar.

Chromium kurulmazsa yalnız bu 18 kaynak hata verir; diğer kaynakların taraması sürer.

`certificates/` klasörü artık depodadır ve `git pull` ile gelir. İçinde İş Bankası için herkese açık GlobalSign ara sertifikası bulunur; özel anahtar yoktur.

## 6. Başlatmadan önce doğrula

Bu komutlar Telegram'a mesaj göndermez ve botun veritabanını açmaz:

```sh
venv/bin/python -B -m unittest discover -s tests -q
venv/bin/python tools/audit_companies.py
venv/bin/python tools/audit_programs.py
venv/bin/python tools/audit_job_links.py
```

Beklenen: 64 test başarılı; denetimde 108 kaynak. Sunucunun IP ve DNS koşulları yerelden farklıdır; bazı siteler sunucudan 403 veya 429 dönebilir. Tek bir kaynağın hatası taramayı durdurmaz, ancak o kaynak için en fazla altı saatte bir Telegram hata uyarısı gelir. Kalıcı hata veren bir kaynak varsa bilgisayarında `companies.json` içinde `enabled` değerini `false` yapıp pushla.

Denetimler rapor dosyalarını yeniden yazar. Bir sonraki `git pull` öncesinde 3. adımdaki `git restore` komutunu çalıştır.

## 7. Başlat ve izle

```sh
sudo systemctl start jobhunter
sudo systemctl status jobhunter
tail -f bot.log
```

Telegram'da `/durum` ile kontrol et.

İlk taramada ne beklenir: mevcut veritabanıyla devam ettiğin için eski ilanlar tekrar bildirilmez. Bu güncellemeyle eklenen kaynaklarda o an açık olan ve profile uyan ilanlar veritabanında bulunmadığı için bir kez bildirilir; bunlar o an yayınlanmış olmak zorunda değildir. Yeni eklenen iki ASELSAN program monitörünün ilk okuması sessiz başlangıç kaydıdır, bildirim üretmez.

## İlk kez git'e geçiş (sunucu ZIP ile kurulduysa)

```sh
sudo systemctl stop jobhunter
cd /home/youruser
mv isapp isapp-eski
git clone https://github.com/erbahadiralp/isapp.git isapp
cp isapp-eski/.env isapp/
cp isapp-eski/jobs.db isapp/                       # DB_PATH farklıysa o dosyayı kopyala
mv isapp-eski/venv isapp/venv                      # veya isapp içinde yeni: python3 -m venv venv
```

Ardından 4. adımdan devam et. Her şey çalıştıktan sonra `isapp-eski` klasörünü silebilirsin.

`jobhunter.service` dosyası da depodadır. Servis tanımını değiştirmediysen yeniden kopyalaman gerekmez. Değiştirdiysen:

```sh
sudo cp jobhunter.service /etc/systemd/system/jobhunter.service
sudo systemctl daemon-reload
```

## Geri alma

Güncelleme sorun çıkarırsa:

```sh
sudo systemctl stop jobhunter
git log --oneline -5                               # önceki commit kimliğini bul
git reset --hard <onceki-commit>
cp ~/isapp-yedek/jobs-<tarih>.db jobs.db           # yalnız veritabanı bozulduysa
sudo systemctl start jobhunter
```

`git reset --hard` izlenen dosyalardaki yerel değişiklikleri siler; `.env` ve veritabanı izlenmediği için etkilenmez.

## Bilinçli olarak kapalı bırakılanlar

- `KARIYER_ENABLED=false` kalmalı; doğrudan Kariyer.net taraması kapalıdır.
- `KARIYER_IMAP_*` alanları boş kalmalı. E-posta okuyucusu kod olarak hazırdır fakat bu alanlar boşken hiçbir bağlantı kurmaz.
