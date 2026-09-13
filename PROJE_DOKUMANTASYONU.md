# Job Hunter — Proje dokümantasyonu ve devam rehberi

Belge tarihi: **10 Eylül 2026**. Bu belge yerel çalışma kopyasındaki gerçek kod ve kayıtlı denetimlere dayanır. Sunucudaki kurulumun durumunu göstermez. Eski PROJE.md, README ve TRACKING açıklamaları tarihsel bilgiler içerebilir; davranış için kod, kapsam için güncel audit dosyaları esas alınmalıdır.

## 1. Amaç ve kullanıcı profili

Türkiye'de yeni mezun bir bilgisayar mühendisine uygun iş ilanlarını ve erken kariyer programlarını takip edip Telegram üzerinden bildirmek. LinkedIn ve Indeed aramalarına ek olarak şirketlerin resmi kariyer siteleri ve yönlendirdikleri işe alım platformları okunur. Kullanıcı böylece doğrudan şirketin başvuru sayfasına ulaşabilir.

Öncelikli roller Java backend / Spring Boot, Python, veri bilimcisi ve data engineer. Diğer yazılım, frontend, full stack, .NET, mobil, QA, DevOps, cloud, makine öğrenmesi, siber güvenlik, embedded ve SAP/ABAP rolleri de erken kariyer kanıtıyla kapsamda. Uzman yardımcısı ve graduate / management trainee / genç yetenek programları ayrıca kabul edilir.

Bot başvuru yapmaz, CV göndermez ve şirket hesaplarına giriş yapmaz. İlanı bulur, filtreler, kalıcı kaydeder ve bağlantısını bildirir. Açılışı hızlı haber verme hedefi periyodik taramayla karşılanır; gerçek zamanlı push veya sıfır gecikme garantisi yoktur.

## 2. Kapsam ve öncelikler

Ana radar `turkiye_yeni_mezun_sirket_takip_listesi.md` dosyasıdır. Kullanıcının sildiği şirketler tekrar eklenmemeli. `extra_source=true`, kullanıcının açıkça istediği liste dışı kaynak istisnasıdır: Codeway, AlbarakaTech Global, Yapı Kredi Teknoloji, Ziraat Teknoloji ve Koç Topluluğu örneklerdir.

Önce bankalar ve iştirakleri, sonra büyük teknoloji şirketleri hedeflendi. Son istekler Hepsiburada, Trendyol, Demirören, Doğuş, Koç; Microsoft Türkiye, Google Türkiye, Amazon/AWS Türkiye, Oracle Türkiye ve IBM Türkiye. Koç'un Arçelik/Beko, Ford ve diğer şirketleri ile ASELSAN, TUSAŞ gibi sanayi/savunma şirketleri de kapsam hedefidir. Hedefe alınmış olmak entegrasyonun bittiği anlamına gelmez.

## 3. Kayıtlı güncel durum

| Ölçü | Değer | Önceki kayıt |
|---|---:|---:|
| Radar şirket adı | 301 | 301 |
| Etkin resmi ilan kaynağı | 96 | 78 |
| Son kayıtlı kontrolü başarılı etkin kaynak | 96 | 78 |
| Etkin kaynağa eşleşen radar adı | 108 | 85 |
| Adresi kayıtlı, entegrasyonu tamamlanmamış radar adı | 36 | 33 |
| Kaynak adresi henüz eşleşmeyen radar adı | 146 | 183 |
| Son başarılı kontrollerde ham kayıt | 1310 | 1082 |
| Aynı kontrollerde profile uygun kayıt | 15 | 13 |
| Program / duyuru / ilan sayfası monitörü | 14 | 12 |

Kaynak: `SOURCE_COVERAGE.md`, `source_audit.json`, `program_audit.json`. Sayılar 10 Eylül 2026 tarihli tam denetimden gelir; 108 etkin kaynağın tamamı okundu. Denetim sırasında yalnız Microsoft kaynağı, aynı gün tekrarlanan denetimler nedeniyle HTTP 429 döndürdü; Nokia'nın Oracle pod adresi de bir kez geçici DNS hatası verdi. İkisi de tek başına yeniden çalıştırıldığında başarılı okundu ve kayıt bu son sonuçları içerir. Hedefli denetim `source_audit.json` dosyasını eski kayıtlarla birleştirerek yazdığı için tam denetim sürerken çalıştırılmamalıdır; aksi halde biten kayıtlar geri alınır. Bu bir geliştirme ortamı ölçümüdür, sunucu sağlık göstergesi değildir. Grup panoları birden fazla şirketi kapsar; şirketin farklı adları aynı kaynağa eşleşebilir. Kaynak sayısı şirket sayısına eşit değildir.

1310 ham kayıt, 1310 benzersiz yeni mezun ilanı değildir. Kıdemli, kapsam dışı, öğrenci programı ve başka panoda da bulunan kayıtlar içerir. 15 uygun kayıt da her taramada sabit kalmaz. 108/108 başarı bütün 301 şirketin bittiği anlamına gelmez. Gerçek sıfır ilan başarılı sonuç olabilir; bozuk sayfa sıfır ilan sayılmaz — bu oturumda eklenen boş panolar portalın kendi boş-durum metniyle veya sıfır sonuç sayımıyla doğrulanmıştır.

**Sunucu farkı (13 Eylül 2026):** Yerel Türkiye IP'sinden 108 kaynak başarılı okunuyordu. Almanya'daki VPS'ten 12 kaynak her taramada hata verdiği için kapatıldı (`verification_status: blocked_from_server`). Bunların 10'u HRPeak'in Cloudflare arkasındaki SaaS ön yüzünde (Aksigorta, Albaraka Türk, Architecht, BİM, HDI Sigorta, Innova, Mapfre Sigorta, Vakıf Katılım, Vodafone Türkiye, Ziraat Teknoloji) ve hepsi aynı Cloudflare adreslerine çözümleniyor; kendi sunucusunda barınan HRPeak kaynakları (ROKETSAN, Ziraat Katılım, Emlak Katılım) etkilenmiyor. Kuveyt Türk ve Türk Telekom Türkiye dışı trafiğe yanıt vermiyor. Tablodaki sayılar kapatma sonrasıdır. Bot Türkiye IP'li bir makineye taşınırsa bu kaynaklar yeniden etkinleştirilebilir.

**Indeed:** Indeed Türkiye API'si VPS'ten proxy olmadan çalışıyor (HTTP 200). Ancak Türkiye'de bu profile uygun ilan çok az: İngilizce "junior ..." sorguları son yedi günde sıfır sonuç veriyor; Türkçe yeni mezun sorgularında çıkan ilanların hiçbiri yeni mezun yazılım ilanı değildi (yönetici asistanı, 5+ yıl yazılım müdürü, satış mühendisi). Bu yüzden Türkçe sorgu eklenmedi; LinkedIn ana kaynaktır.

## 4. Dosya haritası

| Dosya | Görev |
|---|---|
| `main.py` | Ayar kontrolü, DB/scheduler, ilk tarama, Telegram polling |
| `config.py` | Ortam değişkenleri, loglama, arama sorguları |
| `scheduler.py` | Saatler, çakışma kilitleri, kayıt ve teslim döngüsü |
| `bot.py` | /start, /durum, /tara |
| `database.py` | SQLite, tekrar önleme, kalıcı kuyruk, program durumu |
| `notifier.py` | Telegram HTTP gönderimi ve tekrar deneme |
| `watchlist.py` | Radar, ad normalizasyonu, profil filtresi |
| `companies.json` | Resmi kaynak adresleri, adapter türleri ve ayarlar |
| `programs.json` | Sayfa değişikliği monitörleri |
| `scrapers/company_scraper.py` | Ortak ATS ve şirkete özel okuyucular |
| `scrapers/program_scraper.py` | Seçili içeriklerin değişiklik takibi |
| `scrapers/jobspy_scraper.py` | LinkedIn/Indeed sorguları |
| `scrapers/kariyer.py` | Varsayılan kapalı doğrudan Kariyer.net |
| `scrapers/kariyer_mail.py` | İsteğe bağlı salt okunur IMAP |
| `scrapers/base.py` | Ortak hata yakalama ve yardımcılar |
| `scrapers/*_browser.py` | HRPeak, Softtech, Amazon için Chromium |
| `scrapers/verified_tls.py`, `certificates/` | İş Bankası sertifika zinciri desteği |
| `tools/discover_sources.py` | Toplu ATS parmak izi keşfi (kariyer sayfası → pano) |
| `tools/probe_boards.py` | Aday kariyer adreslerinde gerçek ilan listesi arama |
| `tools/sweep_platforms.py` | SF CSB / HRPeak platformlarını alan adı üzerinden tarama |
| `tools/sweep_ats_boards.py` | Lever/Greenhouse/Ashby/SmartRecruiters kimlik denemesi |
| `tools/discover_browser.py` | Chromium ile JS portallarında ATS ve ilan API'si yakalama |
| `tools/propose_selectors.py` | Kariyer sayfasındaki tekrar eden ilan kartlarından generic seçici önerisi |
| `tools/check_kariyer_mail.py` | İş Habercisi e-postasını çevrimdışı .eml veya salt okunur IMAP ile sınar |
| `tools/verify_candidates.py` | Aday kaynakları gerçek okuyucuyla toplu doğrulama |
| `tools/seed_domains.py` | Radar adı → resmi ana site eşlemesi; keşif girdisi üretir |
| `tools/add_sources.py` | Aday kayıtları companies.json'a ekler/günceller |
| `tools/` | Keşif, audit, rapor, radar eşitleme, paketleme |
| `tests/` | Filtre, DB, kuyruk ve adapter regresyon testleri |
| `SOURCE_COVERAGE.md`, `BANK_COVERAGE.md` | Genel/banka kaynak durumları |
| `TRACKING.md`, `SERVER_UPDATE.md` | Tarihsel ilerleme ve sunucu aktarımı |
| `.source-audit/` | Yerel keşif çıktıları; pakete dahil değil |
| `dist/job-bot-update.zip` | Güncelleme paketi |

## 5. Çalışma akışı

```text
Zamanlayıcı veya /tara
  ├─ JobSpy: LinkedIn + Indeed → profil filtresi
  └─ Şirket döngüsü
       ├─ Resmi ilanlar → liste/sayfalama/detay → profil filtresi
       ├─ Program sayfaları → içerik özeti → değişiklik olayı
       └─ İsteğe bağlı e-posta → doğrudan ilan linkleri → başlık filtresi
                              ↓
                    SQLite kalıcı bildirim kuyruğu
                              ↓
                       Telegram gönderimi
                              ↓
                  Başarılıysa işaretle; değilse tekrar
```

`main.py` token/chat ayarlarını kontrol eder, DB'yi hazırlar, scheduler'ı başlatır, durum mesajı gönderir ve ilk taramaları çalıştırır. Ardından polling ile komut dinler. `python main.py` denetim komutu değildir; gerçek ayarlar varsa DB'yi değiştirir ve bildirim gönderir.

Şirketler dört işçiyle eşzamanlı okunur. Her kaynağın okuyucu durumu ayrıdır; bir hata diğerlerini durdurmaz. Hata veren kaynağın yarım sonucu tam başarı sayılmaz. Şirket, program ve mail okuyucuları şirket döngüsünde sırayla çalışır. Kilitler aynı döngünün üst üste binmesini önler; uzun tarama sırasında yeni tetikleme yeni tam tarama başlatmayabilir.

## 6. Gerçek çalışma saatleri

Saat dilimi **Europe/Istanbul**. Tablo `scheduler.py` tetikleyicilerini gösterir.

| İş | Plan |
|---|---|
| Şirket + program + IMAP | Gece dahil 24 saat, varsayılan 15 dakika aralık |
| Bekleyen bildirimler | 2 dakika aralık; şirket döngüsü sonunda da denenir |
| LinkedIn/Indeed gündüz | 08:00–18:45; her saatin 00, 15, 30, 45. dakikası |
| LinkedIn/Indeed akşam | 19:00, 19:45, 20:00, 20:45, 21:00, 21:45, 22:00, 22:45, 23:00, 23:45 |
| LinkedIn/Indeed gece | 00:00–07:59 planlı tarama yok |
| /tara | Gece kısıtını aşar; şirket döngüsünü de çalıştırır |
| DB temizliği | Pazartesi 08:05; bildirilmiş 3650 günden eski kayıtlar |

Akşam planı kesintisiz 45 dakika değildir: cron dakika 0,45 kullanır. Eski yorumlardaki gece hiç tarama yok ifadesi şirket/programlar için geçersizdir. DB fonksiyonunun varsayılanı 30 gün olsa da scheduler 3650 gün geçirir. Bekleyen bildirimler temizlenmez.

`COMPANY_INTERVAL_MINUTES` varsayılan 15, alt sınır 5 dakikadır. Ağ, tarama ve gönderim süresi gecikmeye eklenir. E-posta yöntemi ayrıca İş Habercisi teslim sıklığına bağlıdır.

## 7. Uygunluk filtresi

Merkez karar `watchlist.relevant(title, description)` fonksiyonudur. Türkçe karakterler ve harf büyüklüğü normalize edilir. Bu kural tabanlı filtredir; anlamı kusursuz anlayan bir dil modeli değildir.

Önce senior/lead gibi başlıklar ve algılanan açık 3+ yıl deneyim koşulları elenir. Tanınan programlar, genel graduate/MT/genç yetenek ve uzman yardımcısı ifadeleri ayrıca değerlendirilir. Normal roller için teknoloji başlığı VE junior/yeni mezun kanıtı gerekir.

Kanıt başlıkta veya açıklamada açık yeni mezun kabulü, deneyim aranmaması, 0–1/0–2 yıl gibi ifadeler olabilir. Deneyim belirtilmemesi kanıt değildir. Junior çalışanlara mentorluk yapma ifadesi adayın junior olduğunu göstermez.

| Örnek | Yaklaşım |
|---|---|
| Junior Java Developer | Teknoloji ve erken kariyer kanıtıyla kabul |
| Backend Developer + açık yeni mezun kabulü | Desteklenen açıklama ifadesiyle kabul |
| Senior Data Engineer | Kıdem nedeniyle eleme |
| Software Engineer + en az 3 yıl | Deneyim nedeniyle eleme |
| Software Engineer + deneyim bilgisi yok | Belirsizlik nedeniyle eleme |
| Uzman Yardımcısı / Uzm. Yrd. | Teknoloji şartı olmayan ayrı kural |
| Management Trainee / Graduate Program | Teknoloji şartı olmayan program kuralı |

Genel program kuralı teknoloji dışı MT ilanlarını da getirebilir. Bütün kaynaklarda tek kapsamlı öğrenci sınıflandırıcısı yoktur; TUSAŞ gibi bazı okuyucular açık staj/burs türlerini ayırır. Başlığı yalnız Engineer olan veya yeni mezun kabulünü farklı ifade eden ilanlar kaçabilir. 3+ yılın tercih olarak yazılması da kurala takılabilir. Düzeltmeler gerçek örnek ve anlamlı testle yapılmalıdır.

## 8. LinkedIn ve Indeed kapsamı

Bütün ilanlar alınmaz. 27 hedef sorgu, sorgu başına 15 sonuç, son 7 gün ve İstanbul/Türkiye ayarı kullanılır. LinkedIn açıklaması alınması istenir; ardından ortak filtre uygulanır. Sorgular arasında bekleme ve sorgu başına hata izolasyonu vardır.

Resmi şirket taraması radar dosyasına bağlıdır. LinkedIn/Indeed sonuçları aynı şirket whitelist'ine kilitli değildir; profile uyan başka işverenler gelebilir. Sonuç sınırı, sıralama, konum ve erişim kapsamı etkiler. Bu ortamda gerçek LinkedIn/Indeed → Telegram uçtan uca akışı yeniden doğrulanmadı.

**Bilinen kütüphane hatası (python-jobspy 1.1.80):** LinkedIn açıklaması çekilirken ilan sayfasında "Seniority level" alanı yoksa kütüphane `None.lower()` ile çöker ve tek ilan bütün sorguyu düşürür. Açıklama getirme önceden kapalıyken bu yol hiç çalışmadığı için hata görünmüyordu; açıldıktan sonra sunucuda bütün LinkedIn/Indeed sorguları `'NoneType' object has no attribute 'lower'` hatası verdi. `scrapers/jobspy_scraper.py` eksik alanı boş metne çeviren hedefli bir yama uygular ve LinkedIn ile Indeed'i ayrı çağırır; böylece bir sitenin hatası diğerinin sonuçlarını silmez. Kütüphane sürümü yükseltilirse yamanın hâlâ gerekip gerekmediği kontrol edilmelidir.

## 9. Kaynağı nasıl buluyor ve doğruluyorum?

1. Güncel radar, companies.json ve kapsam raporundaki mevcut kaydı okuyorum. Yapılmış entegrasyonu yeniden keşfetmiyorum.
2. Şirketin resmi ana sitesindeki kariyer/İK bağlantısını izliyorum. Harici ATS varsa resmi yönlendirmeyi kanıt olarak kaydediyorum.
3. Aday adresi `tools/source_probe.py` ile okuyorum: HTTP durumu, son adres, başlık ve içerik incelenir. Araç dört işçiyle kamuya açık çıktıları `.source-audit/` altında saklar.
4. Sayfanın gerçek ilan listesi olduğuna bakıyorum. HTTP 200 veren challenge, giriş ekranı, kapanmış pano veya tanıtım sayfası ilan kaynağı değildir.
5. HTML kartları, JobPosting JSON-LD, kamuya açık API veya normal anonim tarayıcı ağ isteklerinden şema çıkarıyorum.
6. Uygun mevcut ATS adapterini kullanıyorum; farklı şemada dar kapsamlı yeni okuyucu geliştiriyorum.

Açık şirket dizinleri geçmişte aday adres bulmak için kullanıldı; resmi doğrulamanın yerini tutmaz. Üretim botu internette şirket arayıp kendi kendine güvenilir yeni adapter geliştirmez. Geliştirme sırasında kaynak keşfi yapılır; bot tanımlanmış kaynakları periyodik okur.

### Liste, sayfalama ve boş durum

API/HTML yapısı, toplam kayıt, sayfa numarası/offset, sonraki sayfa ve tekrarlanan kimlikler kaynağın yapısına göre kontrol edilir. Eksik sayfalama bütün ilanların okunduğu yanılgısını yaratır. Kart bulunmaması yalnız doğrulanmış boş-durum metni/alanı varsa sıfır kabul edilir; bozulmuş seçici hata olmalıdır.

Gerçek örnekler: Multinet FlowQ offset alanı satır değil sayfa numarası çıktı; 12+2 kayıtla doğrulandı. Microsoft'ta yanlış API 403 verirken resmi PCSx araması çalıştı. Google göreli ilan bağlantıları yanlış köke ekleniyordu; `link_base_url` desteği eklendi. HRPeak'te desteklenmeyen çok sayfalı görünüm tespit edilirse eksik sonuç yerine hata üretilir; tam HRPeak sayfalaması henüz yok.

### Detay, şirket, ülke ve tarih

Gerektiğinde açıklama HTML/JobPosting JSON-LD veya detay API'sinden okunur. Bazı API'ler tam açıklamayı listede verir; ayrı detay isteği her zaman gerekmez. HTML detayları kısa süreli önbelleğe alınır.

Kaynağa göre şirket/marka kimliği, ilan ID'si, URL alan adı, Türkiye konumu, aktiflik, görünürlük ve tarihler kontrol edilir. Global panoda bilinmeyen lokasyon Türkiye sayılmaz. `local_only` ancak yerel kapsam doğrulanmışsa kullanılır. Son başvuru tarihi okunabiliyorsa kapanmış ilan elenir.

Her adapter aynı alanları sunmaz; her kaynakta aynı düzeyde doğrulama yapıldığı iddia edilmemelidir. Sıfır ilanlı kaynağın dolu liste davranışı yalnız sentetik testle sınanmış olabilir.

### HTTP, tarayıcı ve TLS

Önce basit HTTP/JSON kullanılır. Dinamik kamuya açık sayfalarda Playwright Chromium devreye girer. HRPeak, Softtech ve Amazon örneklerdir. Normal anonim oturum kullanılır; sabit çerez, kullanıcı hesabı veya kiralık proxy gerekmez. CAPTCHA çözülmez.

Amazon tarayıcı içinden aynı origin üzerindeki `/api/jobs/search?is_als=true` aramasını kullanır. Türkiye filtresi uygulanır, açıklama/nitelikler yanıttan alınır. SF kimlikli `[TITLE HERE]` placeholder açıkça ayrılır; gerçek ilan kabul edilmez.

İş Bankası'nda eksik ara sertifika desteği eklendi; SSL doğrulaması kapatılmadı. Kamuya açık sertifika kullanılır, kök ve alan adı doğrulaması korunur. Browser'ın çalışması veya HTTP'nin 403 vermesi tek başına IP ban kanıtı değildir.

### URL ve tekrarlar

Desteklenen takip parametreleri/fragment temizlenir, ilan kimliği korunur. Okuyucu URL tekrarlarını ayırır. DB normalde URL'nin MD5 özetini kimlik yapar; özel `dedup_key` varsa onu kullanır. Hash burada güvenlik için değil tekrar tanımak içindir.

LinkedIn ve şirket sitesindeki farklı URL'ler anlamsal birleştirilmez. Grup ve alt şirket panosu aynı canonical URL'yi döndürürse tekrar önlenebilir. Audit ham toplamları çalışma zamanı tekrar önlemesiyle aynı ölçü değildir.

## 10. Program açılış takibi nasıl çalışıyor?

14 monitör Softtech, Turkcell, OBSS, Kuveyt Türk, Fibabanka, Vakıf Katılım, VakıfBank, Ziraat Bankası, Garanti BBVA, Albaraka Türk, Bimser, Figopara ve ASELSAN sayfalarını kapsar. Bimser ile Figopara program değil pozisyon sayfası değişikliği monitörüdür; tekil ilan adapteri değildir.

ASELSAN'ın iki monitörü (Öğrenci & Yeni Mezun, NBMT Programı) HTML yerine şirketin kendi içerik API'sini okur. Bunun nedeni ASELSAN kariyer sitesinin sunucu tarafında hiç içerik döndürmemesi ve iş başvurusunun giriş gerektiren ayrı bir portala yönlendirilmesidir; anonim ilan listesi yoktur. JSON kaynaklarda yalnız yapılandırılan dildeki `title`/`html` alanları özetlenir; kayıt kimliği ve `updatedAt` gibi her yayında değişen alanlar dışarıda bırakılır, aksi halde içerik değişmeden sahte değişiklik olayı üretilirdi.

Seçili içerik ve başvuru linkleri normalize edilip SHA-256 özeti alınır. Menü/script gibi alakasız bölümler dışarıda tutulur. Kuveyt Türk'te belirli görsellerin baytları, Garanti'de seçilmiş gömülü program verileri de izlenir.

İlk başarılı okuma sessiz başlangıç kaydıdır. Sonraki farklı özet, DB içinde durum ve bildirim olayıyla atomik kaydedilir. Hatalı okuma eski sağlıklı durumu silmez. A → B → A geçişi tekrar olay üretebilir.

Mesaj **PROGRAM SAYFASI DEĞİŞTİ** der; kesin başvuru açılışı demek değildir. Kapanış, tarih veya koşul değişikliği de olabilir. İlk kurulumda zaten açık program yalnız bu monitörden açılış bildirimi üretmez. Bimser/Figopara'nın mevcut açık boş durumları doğrulanmıştır.

## 11. Kariyer.net için proxy olmadan seçenek

Doğrudan okuyucu `KARIYER_ENABLED=false` ile kapalıdır. Hata sonrası süreç içi bekleme erişim engelini çözmez. 403'ün sebebi ayrıca incelenmelidir; otomatik olarak IP ban denmez.

Alternatif `KariyerMailScraper`, kullanıcının İş Habercisi e-postalarını ayrı IMAP klasöründen salt okunur okur. `BODY.PEEK[]` kullanır; mesaj silmez veya okunmuş işaretlemez. Son 100 mesajdaki doğrudan HTTPS kariyer.net/is-ilani/ linkleri alınır ve başlık filtresi uygulanır. Kariyer.net'e ilan tarama isteği gönderilmez. Okuyucu `scheduler.py` içindeki şirket döngüsüne zaten bağlıdır ve `KARIYER_IMAP_HOST` boşken sessizce boş liste döner.

Ayarlar: `KARIYER_IMAP_HOST`, `KARIYER_IMAP_USER`, `KARIYER_IMAP_PASSWORD`, `KARIYER_IMAP_FOLDER`. Dördü de doldurulmalıdır; host doluyken diğerlerinden biri eksikse okuyucu hata verir. Kullanıcı ayrı klasör kuralını kendisi kurmalıdır.

### Doğrulama durumu ve bilinen risk

Gerçek bir hesap veya gerçek bir İş Habercisi e-postası bu ortamda hiç görülmedi; şablon doğrulanmamıştır. Ayrıştırıcının kabul kuralı dardır: bağlantı `https` olmalı, alan adı tam olarak `kariyer.net` veya `www.kariyer.net` olmalı, yol `/is-ilani/` ile başlamalı ve bağlantı metni buton yazısı olmamalıdır.

**Asıl risk budur:** toplu gönderim e-postaları ilan başlıklarını çoğu zaman `email.kariyer.net/r/...` gibi takip/yönlendirme adresleriyle verir. Okuyucu yönlendirme çözmediği için böyle bir e-postadan sıfır ilan çıkarır ve bu sessiz bir başarısızlıktır — kaynak hata vermez, sadece hiçbir şey bulmaz. Bu yüzden ayar yapmadan önce gerçek bir e-posta ile şablon sınanmalıdır.

`tools/check_kariyer_mail.py` bu sınamayı kimlik bilgisi olmadan yapar: kaydedilmiş bir `.eml` dosyasını okur ve her bağlantıyı kabul/ret gerekçesiyle listeler, ardından profil filtresinden hangilerinin geçtiğini gösterir. Takip adresleri "farklı alan adı" gerekçesiyle listelenir; çıktıda ilan başlıkları bu grupta toplanıyorsa ayrıştırıcı o şablona uyarlanmadan IMAP kurulumu yapılmamalıdır. Aynı araç `--imap` ile salt okunur bağlantıyı, klasör adının birebir eşleşmesini ve klasördeki mesaj sayısını da doğrular.

Hız İş Habercisi teslim sıklığına bağlıdır; bot e-posta gelmeden ilanı göremez. Bu kaynaktan gelen kayıtlarda işveren adı e-postada güvenilir biçimde bulunmadığı için "E-postadaki ilan" olarak yazılır ve yalnız başlık filtresi uygulanır (açıklama metni yoktur), bu da şirket sitesi kaynaklarına göre daha kaba bir eleme demektir.

## 12. Kalıcı kuyruk ve hata davranışı

Yeni ilan `notified=0` ve JSON payload ile SQLite'a yazılır. Telegram başarısından sonra bildirilmiş yapılır; hatada kuyrukta kalır. Teslim döngüsü ilk başarısız mesajda durur, sonraki mesajlar gecikebilir.

Gönderici bir çağrıda üç deneme yapar; 429'da Telegram bekleme süresini kullanır. İlanlar arasında 1,5 saniye bekler. Kaynak hata alarmları süreç belleğinde kaynak başına altı saatle sınırlandırılır; yeniden başlatma belleği sıfırlar.

DB migration eski kayıtları bildirilmiş kabul ederek geçmişin yeniden gönderilmesini önler. Bekleyenler temizlenmez. Telegram kabulünden sonra yerel işaretlemeden önce süreç çökerse nadiren tekrar bildirim olabilir; kesin tek-sefer garantisi yoktur. Durum ekranındaki son kayıt zamanı bütün kaynakların son başarılı taraması değildir.

## 13. Entegrasyon adımları

1. Radar ve kullanıcının ek kaynak isteğini kontrol et.
2. Resmi kariyer → ATS yönlendirmesini kanıtla.
3. Liste, detay, Türkiye/şirket sınırı, sayfalama, boş durum ve tarihleri belirle.
4. Mevcut adapter uygunsa companies.json yapılandır; değilse company_scraper.py ve gerekiyorsa ayrı browser yardımcısı geliştir.
5. Kaynak adı, type, URL, seçiciler/API parametreleri, aliases ve ülke kapsamını ekle. `enabled=true` doğrulama kanıtı değildir.
6. Yeni davranış için anlamlı regresyon testi ekle: yanlış ülke/marka, eksik sayfa, tekrar ID, kapalı ilan veya bozuk yanıt.
7. Gerçek okuyucuyla hedefli canlı audit yap; hata veren/yarım kaynağı tamamlandı sayma.
8. Uygun linkleri, program varsa ayrıca monitörü denetle.
9. Kapsam ve devam notlarını güncelle, paketi yeniden oluştur.

Desteklenen okuyucular arasında Lever, Greenhouse, Ashby, Workday, SmartRecruiters, Eightfold, FlowQ, Hirebridge, PCSx, Savunma Kariyer, SuccessFactors CSB, genel HTML ve şirkete özel adapterler bulunur. Yeni ayarların alan adları için benzer mevcut JSON kaydı ve okuyucunun gerçek kodu esas alınmalıdır.

## 14. Test ve audit komutları

Proje kökünde bağımlılıkların kurulu olduğu Python kullanılmalı. Windows'ta python yerine `.\.venv\Scripts\python.exe` yazılabilir.

```sh
python -B -m unittest discover -s tests -q
python tools/audit_companies.py "Google Türkiye" "Microsoft Türkiye"
python tools/audit_companies.py
python tools/audit_programs.py
python tools/audit_job_links.py
python tools/report_coverage.py
python tools/report_banks.py
python watchlist.py
python tools/sync_watchlist.py
python tools/build_release.py
# Kaynak keşif hattı (yalnız kamuya açık sayfaları okur; add_sources dışında ayar dosyası yazmaz):
python tools/seed_domains.py            # .source-audit/seeds.json üretir
python tools/discover_sources.py .source-audit/seeds.json --workers 16
python tools/probe_boards.py .source-audit/seeds.json --workers 14
python tools/sweep_platforms.py .source-audit/seeds.json --workers 24
python tools/sweep_ats_boards.py .source-audit/seeds.json
python tools/discover_browser.py .source-audit/seeds.json   # JS portalları için Chromium
python tools/propose_selectors.py .source-audit/career_pages.json
python tools/check_kariyer_mail.py ornek.eml   # kimlik bilgisi gerekmez
python tools/check_kariyer_mail.py --imap      # .env ile salt okunur bağlantı denemesi
python tools/add_sources.py aday_kayitlar.json
python tools/verify_candidates.py "Şirket Adı"
```

`audit_companies.py` gerçek okuyucuyu dört işçiyle çalıştırır; tarih, durum, ham/uygun sayı ve ilanları yazar. Seçili denetim eski kayıtlarla birleştirilir; argümansız denetim bütün etkin kaynakları yeniler. Adlar companies.json ile tam eşleşmeli; yanlış adda hiçbir hedef seçilmeyebilir. Çıktıda gerçekten hedef satırın denetlendiğini kontrol et.

`audit_programs.py` gerçek sayfayı okur fakat DB olayını test karşılığıyla değiştirir; gerçek DB/Telegram kullanmaz. `audit_job_links.py` uygun URL erişimini ve başlığı kontrol eder; bu tek başına ilan hâlâ açık veya filtre kesin doğru demek değildir. Audit araçları rapor dosyası yazar ama başvuru/bildirim göndermez.

Otomatik testler filtre, DB migration, kuyruk, program değişimi, şema, sayfalama ve ülke/marka sınırlarını kontrol eder. Canlı audit gerçek sitenin erişim/şemasını kontrol eder. Biri diğerinin yerine geçmez. Başarı kayıtları elle yazılmaz; sorun düzeldikten sonra okuyucu yeniden çalıştırılır.

`source_probe.py` keşif aracıdır; her iç içe API şemasını anlamaz. Gösterdiği basit kayıt sayısı nihai okuyucu kanıtı değildir. `sync_watchlist.py` dosya değiştirir, kaldırılan şirketleri ayarlara yansıtır, kaynakları otomatik etkinleştirmez. Testler geçince yeni değişiklik yoksa sürekli aynı testleri tekrarlamak gerekmez.

## 15. Son eklenen kaynaklar

10 Eylül 2026 oturumunda otomatik keşif hattıyla eklenen ve canlı denetimden geçen kaynaklar:

| Kaynak | Tür | Son kayıtlı gözlem |
|---|---|---|
| Gratis | successfactors_csb | Resmi Gratis Kariyer CSB panosu; 84 ilan, dört sayfa |
| Yaşar Holding | successfactors_csb | Resmi Yaşar Kariyer CSB panosu; 12 ilan |
| Coşkunöz (+ Coşkunöz Holding) | successfactors_csb | Grup kariyer sitesi; 7 ilan, kart yerleşimi |
| Arkas | successfactors_csb | Resmi Arkas kariyer sitesi; 1 ilan |
| Borusan Holding | successfactors_csb | Resmi Borusan Kariyer grup panosu; 6 ilan |
| Çalık Holding | successfactors_csb | Resmi Çalık kariyer sitesi; 3 ilan |
| Kalyon Holding (+ Kalyon Enerji) | successfactors_csb | Resmi Kalyon kariyer sitesi; 4 ilan |
| Martur Fompak | successfactors_csb | Resmi kariyer sitesi; 5 ilan, tablo yerleşimi |
| sahibinden.com | successfactors_csb | Sahibinden Bilgi Teknolojileri panosu; 15 ilan, 1 uygun |
| ROKETSAN | hrpeak_browser | Resmi ROKETSAN Kariyer HRPeak panosu; 6 ilan |
| BİM | hrpeak_browser | Resmi BİM Kariyer HRPeak panosu; 3 ilan |
| Vodafone Türkiye | hrpeak_browser | HRPeak panosu; doğrulanmış boş durum |
| Aksigorta, HDI Sigorta, Mapfre Sigorta | hrpeak_browser | HRPeak panoları; doğrulanmış boş durum |
| Çimsa | generic | Resmi Çimsa Kariyerim ilan kartları; 9 ilan |
| Farplas | generic | Resmi açık pozisyon tablosu; 5 ilan, işveren sütunu doğrulanır |
| Oyak Renault | workday | Renault Group Workday panosu; ülke facet'i uygulanır |
| BP Türkiye | workday | BP Workday panosu; Türkiye facet'iyle 5 ilan |
| Strategy& | workday | PwC Workday panosu; deneyimli kariyer sitesi |
| Continental Türkiye | smartrecruiters | Continental AG panosu; country=tr filtresi |
| Türk Telekom | hrpeak_browser | Resmi başvuru portalındaki HRPeak listesi; doğrulanmış boş durum |
| Anadolu Grubu | successfactors_csb | Resmi Anadolu Kariyerim grup panosu; 17 ilan, 1 uygun |
| CEVA Logistics | successfactors_csb | CMA CGM grup panosu; ülke facet'i TR ile 8 ilan |
| Alp Aviation | generic | Resmi Alp Havacılık İK portalı; 1 ilan, işveren etiketi doğrulanır |
| Deloitte | successfactors_browser | Deloitte Türkiye yönlendirmesindeki klasik SF portalı; 25 ilan |
| Mercedes-Benz Otomotiv | successfactors_browser | Mercedes-Benz Türkiye yönlendirmesindeki klasik SF portalı; 1 ilan |
| Honeywell | oracle_cloud | Oracle Recruiting Cloud; Türkiye facet'i ile 2 ilan |
| Nokia Türkiye | oracle_cloud | Oracle Recruiting Cloud; doğrulanmış sıfır Türkiye ilanı |
| Oracle Türkiye | oracle_cloud | Oracle Recruiting Cloud; doğrulanmış sıfır Türkiye ilanı |

Bu oturumdan önce eklenmiş kaynaklar (Koç Topluluğu grup panosu, Microsoft, Google, Amazon/AWS, TUSAŞ, Getir, Hitit, Sovos, Innova, Bimser/Figopara monitörleri) değişmedi; ayrıntıları `SOURCE_COVERAGE.md` içindedir.

Yeni `oracle_cloud` okuyucusu Oracle Recruiting Cloud aday deneyimi API'sini okur. Ülke süzmesi `selectedLocationsFacet` coğrafya kimliğiyle yapılır; Türkiye düğümü **300000000469842**'dir ve bu kimlik üç kiracıda da aynı çalışır. Kimlik, Honeywell'in 1350 ilanının tamamı sayfalanıp tek Türkiye ilanının `GeographyId` alanı okunarak bulundu — facet listesi yalnız en çok ilan verilen ilk on konumu döndürdüğü için Türkiye orada hiç görünmüyor. Okuyucu her yanıtta sunucunun `SelectedLocationsFacet` değerini gönderdiğiyle karşılaştırır; eşleşmezse hata verir, çünkü facet sessizce düşerse bütün dünya listesi Türkiye sanılırdı.

Nokia ve Oracle'ın sıfır dönmesi facet hatası değildir: 606 ve 2211 ilanın tamamı sayfalanarak hiçbirinin Türkiye'de olmadığı doğrulandı. Bu kaynaklar boş oldukları için değil, açıldıklarında ilanı yakalayacakları için etkin bırakıldı.

Klasik SuccessFactors okuyucusu artık arama düğmesini birden fazla adla dener (`İş Ara`, `Search Jobs`, `Ara`, `Search`); aynı portal kiracıya göre Türkçe veya İngilizce düğme gösteriyor ve tek ada bağlı olmak Deloitte ile Mercedes-Benz'i dışarıda bırakıyordu.

Deloitte ve Mercedes-Benz kaynaklarının kapsam kanıtı diğerlerinden zayıftır ve bu bilinçli bir tercihtir: klasik SF portalı ilan başına konum alanı yayınlamıyor, tarayıcıda da boş geliyor. Türkiye kapsamı tekil ilandan değil, şirketin resmi Türkiye kariyer sayfasından bu kiracıya yapılan yönlendirmeden geliyor. Kapsam dışı bir ilan görülürse `local_only` kaldırılmalıdır.

Türk Telekom'un portalı HRPeak'in ikinci temasını kullanır: başlık `.page-menu-title` yerine `.menuSayfa`, boş durum `.no-record` yerine `.kayitBulunamadi` sınıfındadır. Okuyucu artık iki temayı da tanır; şirket adı doğrulaması ve boş-durum metni koşulu her iki temada da aynen uygulanır.

Yeni `successfactors_csb` okuyucusu SAP SuccessFactors Career Site Builder sitelerinin `/search/` sayfasını okur. Üç yerleşim desteklenir: `startrow` ile sayfalanan tablo yerleşiminde sonuç etiketi (`Sonuçlar 1 – 25 - 84` / `Results 1 – 25 of 84`) satır sayısıyla karşılaştırılır; kart yerleşiminde sunucudan gelen "N İşten 1-N arasındakiler gösteriliyor" / "Showing 1 to N of N Jobs" sayımı bulunan ilan linkleriyle eşleşmezse eksik liste yerine hata üretilir; sonuç etiketi olmayan tablo yerleşiminde (Anadolu Grubu) arama tablosu dururken boş dönen ilk sayfa listenin sonu sayılır, tablo da yoksa hata üretilir. Global panolarda `search_params` ile CSB ülke facet'i (`optionsFacetsDD_country`) uygulanır; facet'in gerçekten çalıştığı dönen ilanların konum metniyle doğrulanmalıdır — MediaMarkt'ta aynı parametre filtre uygulamadığı için o pano eklenmedi. Sayım ifadesi hiç bulunamazsa kaynak sıfır ilan saymaz, hata verir.

Grup panoları (Borusan, Çalık, Kalyon, Coşkunöz, Yaşar, Anadolu Grubu) birden fazla grup şirketinin ilanını aynı panoda yayınlar; ilan başlığındaki işveren ayrımı yapılmaz, ilanlar yapılandırılan grup adıyla bildirilir. Boş dönen panolar bugünün fotoğrafıdır; yarın dolabilir.

## 16. Bankaların durumu

Bütün bankaların ilanları etkin değildir. Erişilebilir okuyucular ve resmi alternatifler eklendi; giriş veya erişim engelleri ayrı kaydedildi. Banka bazındaki güncel kayıt `BANK_COVERAGE.md` içindedir.

İş Bankası, HSBC, Softtech ve HRPeak kullanan banka/iştiraklerde doğrulanmış okuyucular var. Yapı Kredi'nin sorunlu ana portalı yerine resmi Koç Kariyerim alternatifi kullanılıyor. Ziraat Bankası ve VakıfBank duyuruları sayfa değişikliğiyle izleniyor.

DenizBank/Türkiye Finans giriş akışları, TEB/BNP erişim/giriş engelleri ve Enpara'nın Yenibiriş yönlendirmesinde 403 gibi eksikler sürüyor. LinkedIn'e yönlendiren sayfa bağımsız ilan entegrasyonu değildir. Paycell/N Kolay gibi markalarda ana şirket okuyucusunun bütün marka ilanlarını kapsadığı varsayılmıyor.

## 17. Kaldığımız yer ve devam listesi

Aşağıdaki hedefler bu oturumda incelendi fakat üretim adapteri tamamlanmadı. Her satır kayıtlı canlı gözleme dayanır:

| Hedef | Durum ve sonraki iş |
|---|---|
| Oracle Türkiye | Resmi Recruiting Cloud `recruitingCEJobRequisitions` ucu 200 dönüyor ve 2221 ilan sayıyor. Ülke facet'i yalnız en çok ilan verilen ülkeleri listeliyor, `location`/`workLocationCountryCode` finder parametreleri filtre uygulamıyor, sayfa boyutu 25'te sabit. Türkiye'ye inmek için 89 sayfa okumak gerekir; doğru facet kimliği bulunmadan eklenmedi |
| IBM Türkiye | Resmi `www-api.ibm.com/search/api/v2` ucu bool sorgu kabul ediyor ve 1997 kayıt sayıyor fakat `_source`/`fields` isteklerine rağmen yalnız belge kimliği dönüyor; ilan başlığı, adresi ve ülkesi alınamadı. Kariyer arayüzünün gerçek veri çağrısı çözülmeli |
| ASELSAN | Çözüldü (kısmen): anonim ilan listesi yok — iş başvurusu `login.aselsan.com.tr` giriş ekranına gidiyor. Erken kariyer içeriği şirketin kendi API'sinden okunuyor ve iki program monitörü eklendi. Tekil ilan adapteri hâlâ mümkün değil |
| HAVELSAN | `kariyer.havelsan.com.tr` (Havelsan KOVAN) Chromium'da da ilan verisi çağrısı üretmedi; liste giriş sonrası yükleniyor olabilir |
| Turkish Airlines | `careers.turkishairlines.com/acik-pozisyonlar` sayfası düz HTTP ile açılıyor fakat ilan listesi JS ile geliyor; Chromium'da WAF "Erişim engellendi" döndürdü ve tekrarlanan isteklerde bağlantı sıfırlandı. Otomatik erişim engelli sayılmalı |
| FNSS | `kariyer.fnss.com.tr` aday girişi istiyor; anonim ilan listesi yok |
| Şişecam | Kariyer sitesi `careers.sisecam.com` SuccessFactors CSB fakat Cloudflare doğrulaması (HTTP 403 / "Bir dakika lütfen") döndürüyor |
| Mercedes-Benz | Resmi Türkiye kariyer sayfasında SuccessFactors kiracısı `mercedes02` bulundu; markalı CSB adresi tespit edilemedi, global `karriere.mercedes-benz.com` 403 veriyor |
| STM, TEI, Doğuş Otomotiv, Madame Coco, Anadolu Isuzu, İGA, Tekfen, Akkök | Kariyer sayfaları açılıyor fakat ne ATS yönlendirmesi ne de ilan veri çağrısı görüldü; ilanlar LinkedIn'e veya giriş isteyen portallara yönlendiriliyor |
| ASAŞ | `career.cflex.com` adresi ASAŞ'a değil Constantia Flexibles'a ait; yanlış eşleşme olarak elendi |
| Türk Telekom | Resmi `turktelekomkariyer.com.tr` sitesi açılıyor; ilan listesi sunucu tarafında gelmiyor |
| Doğuş Otomotiv, AXA Sigorta, TEI | `kariyer.<alan adı>` portalları 200 dönüyor fakat ilan listesi JS ile yükleniyor |
| Şişecam, Madame Coco, Autoliv Türkiye | Kariyer siteleri bulundu; ilan verisinin kaynağı çözülmedi (Autoliv Teamtailor tabanlı, global pano, Türkiye filtresi gerekir) |
| MediaMarkt, LG Electronics, Siemens/Siemens Energy, DHL, Honeywell | Global panolar erişilebilir fakat Türkiye filtresi güvenilir değil. MediaMarkt'ta CSB `optionsFacetsDD_country=TR` parametresi kabul edilip filtre uygulanmıyor (dönen ilanlar Polonya/Avusturya); ülke süzmesi kanıtlanmadan eklenmedi. Aynı parametre CEVA'da çalıştığı doğrulandığı için o kaynak eklendi |
| Mercer | Resmi Marsh McLennan Workday panosu erişilebilir; aynı ilan yolu birden fazla kayıtta döndüğü için mevcut Workday okuyucusu eksik liste yerine hata veriyor |
| Eczacıbaşı Holding | Resmi kariyer sitesi SuccessFactors CSB fakat `/search/` sayfası sunucu tarafında ilan veya sayım döndürmüyor; dolu/boş ayrımı doğrulanmadı |
| Borusan Holding / Enerjisa Üretim Peoplise | Peoplise başvuru panosu anonim erişimde giriş ekranı veriyor. Borusan için CSB panosu ayrıca bulundu ve eklendi; Enerjisa Üretim için anonim liste yok |
| Brisa, Madame Coco, Mitsubishi Electric Türkiye | Kariyer sayfaları açılıyor fakat açık pozisyon bölümü doğrudan Kariyer.net firma profiline veya LinkedIn'e yönlendiriyor; bağımsız ilan listesi yok |
| Toyota Motor Manufacturing Türkiye | Resmi `toyotatr.com/acik-pozisyonlar` sayfası ilanı tek parça serbest metin olarak yayınlıyor; tekil ilan bağı ve kimliği yok. Sayfa değişikliği monitörü mümkün fakat mevcut içerik üretim elemanı alımı olduğu için profil dışı; eklenmedi |
| Sabancı Holding | Koç'takine benzer bir grup ilan panosu yok; kariyer sayfası LinkedIn'e yönlendiriyor. Grup şirketleri (Brisa, Çimsa, Kordsa, Teknosa, CarrefourSA, Enerjisa) ayrı ayrı çalışılmalı; Çimsa bu oturumda kendi sitesinden eklendi |
| Simon-Kucher | Cornerstone OnDemand kariyer sitesi kullanıyor; herkese açık arama ucu kimlik doğrulaması istiyor (HTTP 401), sayfa JS ile yükleniyor |
| MediaMarkt | Türkiye'ye özel alt site (`/MediaMarktTR/`) var fakat sunucu tarafında ilan döndürmüyor; ülke facet parametresi de filtre uygulamıyor |
| Demirdöküm | Vaillant Group'un ülke bazlı panosu (`jobs.vaillant-group.com/Turkey/`) açılıyor fakat SuccessFactors CSB işaretleri taşımıyor; ilan listesinin kaynağı çözülmedi |
| Kariyer.net e-posta yolu | `KariyerMailScraper` kod olarak hazır ve şirket döngüsüne bağlı; kullanıcı IMAP kimlik bilgisi paylaşmak istemediği için kurulmadı. Şablon doğrulaması `tools/check_kariyer_mail.py` ile kimlik bilgisi olmadan yapılabilir |
| Hepsiburada, Demirören, Doğuş Teknoloji, Koç iştirakleri | Önceki oturumdan devam eden hedefler; bu oturumda çalışılmadı |

Trendyol ve daha önce bağlanan şirketleri yeniden yapma; mevcut kayıtlarını kullan. Keşif çıktıları `.source-audit/discovered.json`, `boards.json`, `platform_sweep.json` ve `ats_sweep.json` içindedir; bunlar pakete girmez ve tarihli gözlemdir.

## 18. Hız ve doğruluk yaklaşımı

Önceki yöntem şirket başına tek tek keşifti: kaynak ara, aç, incele, dene, ekle. 3,5 günde yaklaşık 78 kaynak bu şekilde toplandı. Yeni yöntem aynı işi dört aşamalı toplu bir hatta böler ve tek oturumda 30 kaynak ekledi. Hızlanma, keşfi otomatikleştirmekten gelir; doğrulama adımı kısaltılmaz.

**1. Toplu keşif — `tools/discover_sources.py`.** Şirket adı ve resmi ana site adresinden oluşan bir tohum listesini alır, ana sayfayı okur, kariyer bağlantılarını iki adım derinliğe kadar izler ve sayfa kaynağındaki ATS adres imzalarını arar (Lever, Greenhouse, Ashby, Workday, SmartRecruiters, SuccessFactors, HRPeak, Recruitee, Teamtailor, Workable, Peoplise, FlowQ, Taleo, iCIMS ve diğerleri). JS içine gömülü adresler de yakalanır. 183 şirket 16 işçiyle birkaç dakikada tarandı; 41'inde ATS izi çıktı.

**2. Gerçek pano arama — `tools/probe_boards.py`.** ATS izi çıkmayan şirketlerde kariyer alt adreslerini ve yaygın yolları dener, sayfayı ilan listesi kanıtlarına göre sınıflandırır: SuccessFactors CSB işaretleri, JobPosting JSON-LD, HRPeak imzası, aynı alan adına giden üçten fazla ilan bağlantısı. Giriş ekranı ayrıca işaretlenir.

**3. Platform taraması — `tools/sweep_platforms.py`.** Türkiye'de en yaygın iki platformu şirket alan adı üzerinden dener: `kariyer./careers./ik./jobs.` gibi alt adlarda SuccessFactors CSB `/search/` sayfası ve HRPeak `/jobs` listesi. Önce DNS çözümlemesi yapılır, yalnız var olan adresler HTTP ile denenir; 2013 aday adresten 294'ü çözümlendi.

**4. Gerçek okuyucuyla doğrulama — `tools/verify_candidates.py`.** Aday kayıt `enabled=false` olarak `companies.json`'a yazılır ve üretimdeki gerçek okuyucuyla çalıştırılır. Kayıt yalnız okuyucu hatasız çalışır, sayfalama/sayım tutarlıysa ve şirket kimliği doğrulanırsa etkinleştirilir. HTTP 200 alan adres kanıt sayılmaz; bu araç DB'ye yazmaz, Telegram'a mesaj göndermez.

Hızın asıl kaynağı ATS ailelerini tek tek şirket yerine küme olarak çözmektir. SuccessFactors Career Site Builder tek okuyucuyla dokuz şirket açtı; HRPeak imzası altı şirket açtı. Bir aile çözüldüğünde sonraki şirket dakikalar sürer.

Sonuç vermeyen iki yol da kayda geçmelidir, aynı işin tekrar denenmemesi için.

Birincisi marka alan adı tahminidir. Çimsa (`cimsakariyerim.com`) ve Şişecam (`sisecamkariyerim.com`) bu kalıba uyduğu için `<şirket>kariyerim.com`, `<şirket>kariyer.com`, `kariyer<şirket>.com` gibi türevler ve dört ek alt ad kalan 157 şirket üzerinde tarandı: 3611 aday adresten 181'i çözümlendi, hiçbiri yeni pano vermedi. Bu iki alan adı zaten kariyer sayfası taramasıyla bulunmuştu; tahmin adım olarak bir şey eklemedi.

İkincisi ATS pano kimliği tahminidir: `tools/sweep_ats_boards.py` şirket adından türetilen kimliklerle Lever/Greenhouse/Ashby/SmartRecruiters panolarını dener. 1204 denemede beş eşleşme çıktı ve bunların dördü aynı adı taşıyan başka şirketlerdi (n11 → Hollanda'da bir firma, "kale" → New York'ta bir girişim). Kimlik tahmini resmi kariyer sayfasından gelen yönlendirme kadar güvenilir değildir; bu yol yalnız resmi kanıtla birlikte kullanılmalıdır.

**5. Tarayıcı destekli keşif — `tools/discover_browser.py`.** Düz HTTP'nin boş döndüğü JS tabanlı portallarda anonim Chromium sayfayı açar, ATS yönlendirmelerini render edilmiş DOM'dan okur ve sayfanın kendi XHR/fetch yanıtlarını yapısal olarak eler: bir yanıt ancak kayıtlarında hem başlık hem de konum/departman gibi ikinci bir iş alanı varsa ilan listesi sayılır. Bu eleme olmadan çerez onayı ve içerik yönetimi çağrıları ilan sanılıyordu. Anadolu Grubu'nun SuccessFactors panosu ve ASELSAN'ın içerik API'si bu adımda bulundu.

**6. Seçici önerisi — `tools/propose_selectors.py`.** Kariyer sayfasındaki aynı imzalı, her biri tek ilan bağı taşıyan kardeş blokları sayar ve `generic` adapter için seçici önerir. Öneri adaydır; yine gerçek okuyucuyla doğrulanır.

Paylaşılan platform sunucularına dikkat edilmelidir: bu oturumda `*.hrpeak.com` üzerinde 24 işçiyle yapılan tarama HTTP 429 hız sınırına takıldı ve mevcut HRPeak kaynakları da bir süre okunamadı. `sweep_platforms.py` artık aynı platform sunucusuna tek eşzamanlı istek gönderir ve istekler arasında bekler. Bu kilidin yalnız bilinen platform alan adlarına uygulanması şarttır: adres sonekine bakan genel bir kural Türkiye'deki bütün `.com.tr` adreslerini `com.tr` kökü altında tek kuyruğa sokar ve taramayı saatlerce uzatır. Ayrıca `*.hrpeak.com` her alt adrese aynı genel sayfayı döndürür; şirket başlığı eşleşmediği sürece kanıt üretmez, bu yüzden varsayılan taramada denenmez (`--shared` ile açılır). Tarayıcı gerektiren kaynaklar daha yavaştır; 108 kaynağın tam denetimi yaklaşık 100 saniye sürdü.

## 19. Ayarlar

Gerekli gizli alanlar `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`. `DB_PATH` varsayılan jobs.db, `LOG_PATH` varsayılan bot.log. Şirket aralığı `COMPANY_INTERVAL_MINUTES`, doğrudan Kariyer.net anahtarı `KARIYER_ENABLED`. IMAP isteğe bağlıdır.

`.env.example` içindeki eski `CHECK_INTERVAL_MINUTES`, `QUIET_START`, `QUIET_END` mevcut scheduler'ı yönetmez. `PROXY_URL` bütün okuyucuların proxy kullandığı anlamına gelmez; JobSpy çağrısına otomatik aktarılmaz. Ayarı değiştirirken kodda kullanıldığı nokta kontrol edilmelidir.

Yerel ortam Python 3.14 sanal ortamıdır. requirements.txt bazı bağımlılıklarda alt sınır kullanır; tam kilit dosyası değildir. Sunucuda sürüm çözümlemesi, OS ve browser bağımlılıkları ayrıca doğrulanmalıdır. Gizli .env değerleri bu belgeye veya pakete konmaz.

## 20. Sunucuya aktarım

Sunucunun yolu, servis adı ve çalışan Python sürümü burada doğrulanmadı. Mevcut kurulumuna uyarlayarak:

1. Botu mevcut servis/yöntemle durdur.
2. Bot klasörünü, .env ve DB_PATH ile belirtilen DB'yi yedekle. SQLite yedeğini süreç durduktan sonra al.
3. Yeni ZIP'i bot klasörüne aç; .env, DB ve sanal ortamı silme.
4. Mevcut sanal ortamda requirements.txt kur.
5. Chromium'u botu çalıştıran kullanıcı için kur; Linux sistem bağımlılıkları yetki isteyebilir.
6. Testleri ve sunucudan canlı audit'leri çalıştır. Yerel DNS/IP başarısı sunucuyu garanti etmez.
7. Mevcut servisle başlat; loglar ve /durum ile kontrol et.

```sh
python -m pip install -r requirements.txt
python -m playwright install --with-deps chromium
python -B -m unittest discover -s tests -q
python tools/audit_companies.py
python tools/audit_programs.py
python tools/audit_job_links.py
# Aşağıdaki komut gerçek DB/Telegram kullanır:
python main.py
```

Windows browser kurulumu `python -m playwright install chromium`. Tarayıcı gerektiren 7 etkin kaynak vardır: 3 HRPeak panosu (ROKETSAN, Ziraat Katılım, Emlak Katılım), 3 klasik SuccessFactors portalı (Softtech, Deloitte, Mercedes-Benz Otomotiv) ve Amazon. Linux'ta Chromium iki adımda kurulur: sistem kütüphaneleri `sudo ... playwright install-deps chromium`, tarayıcının kendisi ise botu çalıştıran kullanıcıyla `playwright install chromium`; ikinci adım `sudo` ile çalıştırılırsa tarayıcı root kullanıcısına iner ve servis onu bulamaz. Git ile güncelleme adımları `SERVER_UPDATE.md` içindedir. İş Bankası için certificates klasörü de gereklidir; artık depodadır.

İlk taramada DB'de olmayan mevcut uygun ilanlar da bildirilir; bunlar o anda yeni yayınlanmış olmak zorunda değildir. Programların ilk okuması sessiz başlangıçtır. İki davranış farklıdır. Gerçek Telegram ve sunucu uçtan uca doğrulaması kullanıcı ortamında yapılmalıdır.

## 21. Paketleme ve bütünlük

`tools/build_release.py` açık izin listesiyle dosyaları paketler. `RELEASE_MANIFEST.json` her dosyanın SHA-256 değerini içerir. Kod, testler, araçlar, JSON ayar/audit dosyaları, radar, dokümanlar ve kamuya açık sertifika dahil edilir. .env, DB, log, venv, browser binary ve .source-audit dahil edilmez.

Kod değişince eski ZIP kendiliğinden güncellenmez. Paketleme aracı tekrar çalıştırılmalı; yeni dokümanlar izin listesine eklenmelidir. ZIP sağlamlık testi kaynakların canlı başarısı veya sunucu dağıtımı yerine geçmez.

## 22. Açık sınırlamalar ve bakım

- Tam radar bitmedi; banka engelleri ve büyük şirket keşifleri açık.
- Sayfa değişikliği kesin program açılışı değildir.
- Kural tabanlı filtre yanlış eleme veya teknoloji dışı program kabulü yapabilir.
- Farklı URL'li aynı ilan anlamsal olarak birleştirilmez.
- Bazı gerçek boş/çok sayfalı durumlar görülmedi; HRPeak desteklenmeyen sayfalamada hata verir.
- Audit tarihli yerel kanıttır, sürekli sunucu sağlık garantisi değildir.
- Gerçek IMAP hesabı ve LinkedIn/Indeed/Telegram uçtan uca doğrulaması burada tamamlanmadı.
- İncelenen Telegram komut akışında çağıran chat/kullanıcı için açık yetki kontrolü yok. TELEGRAM_CHAT_ID bildirim hedefidir; tek başına komut erişim kontrolü değildir. Paylaşılan kullanım öncesi ayrıca ele alınmalı.
- Eski belgeler ve kod yorumlarında farklı saat/sayılar bulunabilir; gerçek kod ve güncel audit esas alınır.
- Sunucuya dağıtım, gerçek Telegram gönderimi veya iş başvurusu yapılmadı.
- Tarayıcı gerektiren kaynak sayısı bu oturumda 9'dan 18'e çıktı (14 HRPeak, 3 klasik SuccessFactors, Amazon). Sunucuda Chromium kurulu değilse bu kaynaklar hata verir; tarama süresi de bu kaynaklarla artar.
- Paylaşılan işe alım platformlarına yoğun eşzamanlı istek hız sınırı tetikler. HRPeak bu oturumda 429 döndürdü ve mevcut kaynaklar geçici olarak okunamadı; keşif araçları platform başına tek eşzamanlı istekle çalıştırılmalıdır.
- Yeni eklenen grup panolarında (Borusan, Çalık, Kalyon, Coşkunöz, Yaşar) ilanın hangi grup şirketine ait olduğu ayrılmaz; bildirim yapılandırılan grup adıyla gider.
- Global panolarda güvenilir Türkiye süzmesi hâlâ açık bir sorundur; SuccessFactors CSB `locationsearch` parametresi denenen sitede tutarsız sonuç verdi.

Devam eden geliştirmede kapsam audit araçlarıyla; davranış değişiklikleri kod, test ve bu belgeyle birlikte güncellenmelidir.
