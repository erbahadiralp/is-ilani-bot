> 10 Eylül 2026 güncel durum: 108 etkin kaynak / 108 başarılı son denetim; 1310 ham / 15 uygun kayıt; 14 sayfa monitörü. Güncel kapsam, browser gereksinimleri ve kalan işler [PROJE_DOKUMANTASYONU.md](PROJE_DOKUMANTASYONU.md) içindedir; aşağıdaki eski sayılar tarihsel olabilir.

# Şirket ve yeni mezun takibi

Bu değişiklik altyapıyı genişletir; bütün radar şirketlerinin entegrasyonunun tamamlandığı anlamına gelmez. Ayrıntılı eksikler SOURCE_COVERAGE.md dosyasındadır. `python watchlist.py` güncel kapsamı JSON olarak gösterir. `companies.json` mevcut kariyer kaynaklarını, `programs.json` ayrı program sayfalarını içerir. Kaynak adresi olmayan şirketler otomatik taranmaz. Softtech Yetenek Kuşağı, Turkcell GNÇYTNK ve OBSS New Graduate sayfalarının seçicileri canlı okumayla doğrulandı.

- LinkedIn/Indeed mevcut JobSpy üzerinden devam eder. Sorgulara yeni mezun/graduate/genç yetenek/MT ve software/.NET/DevOps eklendi. Mevcut İstanbul lokasyonu korunur. Java/backend/Spring Boot, Python/data scientist/data engineer ve diğer yazılım alanları ayrı junior/new-grad sorgularıyla aranır.
- Normal ilanlarda teknoloji rolü VE junior/yeni mezun kanıtı zorunludur. LinkedIn açıklamaları da okunur: açık yeni mezun kabulü veya 0–1/0–2 yıl ifadeleri kabul edilir. Genel graduate/MT/genç yetenek programları ve uzman yardımcısı başlıklarında teknoloji zorunlu değildir. Senior başlıklar ve algılanan açık 3+ yıl alt sınırları elenir. Dil tabanlı kurallar bütün deneyim şartlarını anlayamaz; açıklaması olmayan belirsiz başlıklar elenir.
- Şirket, program ve isteğe bağlı e-posta kontrolleri gece dahil COMPANY_INTERVAL_MINUTES (varsayılan 15) aralıkla çalışır. Tarama süresi ve kaynak gecikmesi bu aralığa eklenebilir; gerçek zaman garantisi yoktur. LinkedIn/Indeed eski gündüz/akşam programıyla devam eder.
- Lever, Greenhouse, Ashby, Workday, SmartRecruiters ve siteye özel HTML/API okuyucuları kullanılır. Türkiye ülke/lokasyon filtresi uygulanır; global kaynaklarda konumu belirsiz ilanlar elenir. HTML detaylarında JobPosting JSON-LD son başvuru tarihi okunur. Baykar ve SmartRecruiters sayfalaması toplam ilan sayısıyla kontrol edilir. Boş sayfa ile bozuk seçici ayrılır; kaynak hataları loglanır. Her sitenin JS ve sayfalama yapısı ayrıca bağlanmalıdır.
- Program sayfası ilk okumada baz alınır, bildirim gönderilmez. Sonraki metin/başvuru linki değişiklikleri 'program sayfası değişti' bildirimi üretir; kapanış/koşul değişikliği de olabilir. Açılışı kesin olarak sınıflandırmaz. Aynı URL'nin sonraki değişiklikleri tekrar bildirilir. Boş/bozuk okumalar baz durumu değiştirmez.
- Gönderimler SQLite kuyruğuna kaydedilir, başarısız Telegram gönderimleri iki dakikada bir tekrar denenir. Gönderimden hemen sonra süreç çökerse nadiren tekrar bildirim olabilir. Eski veritabanı kayıtları tekrar bildirilmez. Kayıt tutma süresi on yıldır; bekleyen bildirimler temizlenmez.

## Kariyer.net: proxy olmadan e-posta yolu

Resmi yardım: https://www.kariyer.net/yardim/ — İş Habercisi ve E-Posta Bildirimleri.

1. Kariyer.net hesabında hedef aramalar için İş Habercisi bildirimlerini aç.
2. E-posta sağlayıcında bu iletileri yalnızca bu iş için ayrılmış klasöre taşıyan kural oluştur.
3. .env içindeki KARIYER_IMAP_HOST, KARIYER_IMAP_USER, KARIYER_IMAP_PASSWORD ve KARIYER_IMAP_FOLDER alanlarını doldur. Sağlayıcının desteklediği uygulama parolasını kullan. OAuth gerektiren hesaplar için ayrıca OAuth adaptörü gerekir.
4. Botu yeniden başlat. Klasör salt okunur açılır; e-postalar okunmuş işaretlenmez veya silinmez. Son 100 iletideki doğrudan HTTPS kariyer.net/is-ilani/ bağlantıları alınır; reklam yönlendirmeleri çözülmez. Gerçek e-posta örneğiyle ayrıştırıcı henüz doğrulanmadı. Mail şablonu veya hacim bu sınırlara uymuyorsa adaptör geliştirilmelidir.

Bu yol Kariyer.net'e tarama isteği göndermez, gecikme İş Habercisi teslim sıklığına bağlıdır. E-posta bağlantısı bu ortamda yapılandırılmadı.

Doğrudan tarama KARIYER_ENABLED=false ile kapalıdır. Açılırsa hata veya erişim doğrulamasında tarama durur ve süreç içinde altı saat bekler. Yeniden başlatma bu beklemeyi sıfırlar. Bu davranış erişim engelini çözmez. HTTP 403 tek başına IP ban kanıtı değildir; çalıştırılan sunucuda HTTP durumu ve challenge içeriği incelenmelidir.

## Doğrulama ve çalıştırma

`python -B -m unittest discover -s tests -v` filtre, mükerrer kayıt, DB migration, program değişim durumu ve başarısız gönderim tekrarını harici servis olmadan sınar. 43 test başarılıdır; okuyucu şemaları, sayfalama, ülke/marka filtreleri ve kapanmış ilanlar da sınanır. Canlı kaynak sonuçları SOURCE_COVERAGE.md ve source_audit.json içindedir.

Şirket okuyucuları için gerekli bağımlılıklar kuruldu ve canlı okumalar yapıldı. Kontroller dört şirketi eşzamanlı işler: `python tools/audit_companies.py`; belirli şirket adları argüman olarak verilebilir. Her kontrol sonunda kapsam raporu yenilenir.

Sunucuya dağıtım yapılmadı, gerçek Telegram bildirimi gönderilmedi. Dağıtımda Python dosyalarıyla birlikte companies.json, programs.json ve orijinal şirket Markdown dosyası da kopyalanmalı; sunucudaki .env ve SQLite veritabanı korunmalıdır. requirements.txt kurulup bot yeniden başlatıldığında etkin kaynaklar taranır. İlk taramada daha önce veritabanında olmayan mevcut uygun ilanlar da bildirilir; program sayfalarının ilk okuması sessiz baz kaydıdır.

Akşam cron mevcut haliyle her saatin 00 ve 45. dakikasında çalışır (19:00–23:45); kesintisiz 45 dakika aralık değildir.

Workday yalnızca ilan araması için herkese açık POST uçlarını kullanır; başvuru göndermez. Ülke filtresi bulunmayan portallarda yayımlanan şehir filtresinden tanınan Türkiye lokasyonları seçilir; tanınmayan lokasyon etiketleri için kapsam garanti edilmez. PwC, Mastercard, Unilever ve Salesforce için ayrı erken kariyer panoları da okunur.

Kaynak keşfinde Feashliaa/job-board-aggregator açık şirket dizininden aday adresler kullanıldı (https://github.com/Feashliaa/job-board-aggregator; veri lisansı CC BY-NC 4.0). Bot bu dizinden ilan almaz; etkin kaynaklar doğrudan resmi ATS üzerinden doğrulanır. Dizin adresleri eski olabildiği için başarılı HTTP yanıtı tek başına yeterli sayılmaz.

Öncelik: bankalar, banka teknoloji iştirakleri ve yazılım/veri şirketleri. Akbank resmi anonim ilan API’si bağlandı; Profesyonelim kategorisi elenir, yeni mezun teknoloji ilanlarında detay ve son başvuru tarihi kontrol edilir. İş Bankası sertifika zinciri, Yapı Kredi 503, Architecht ve TEB/BNP erişim engeli nedeniyle henüz etkin değildir. Intertech ve Doğuş Teknoloji resmi iş ilanı bağlantılarını LinkedIn’e yönlendirir.

Kuveyt Türk Katılbize ilanları sayfalı olarak bağlandı. TechTalent ve Fibabanka Fintern resmi program sayfaları eklenerek program sayısı beşe çıktı; canlı okuma DB/Telegram kullanılmadan doğrulandı. TechTalent içerik görsellerinin bayt özeti de izlenir, aynı adresli görselin değişmesi kaçırılmaz. Uzm.Yrd kısaltması uzman yardımcısı filtresine dahildir. Softtech genel ilan listesi halen entegrasyon bekler; Yetenek Kuşağı program takibi etkindir.

Güncelleme: güncel radar 301 şirket adına indirildi; liste dışındaki 15 etkin kaynak kapatıldı. Şirket ve program okuyucuları güncel listeyi çalışma anında da uygular. Üretim şirket taraması dört izole okuyucuyla eşzamanlıdır. Sunucu güncelleme adımları SERVER_UPDATE.md içindedir.

Kullanıcının açık isteğiyle Codeway ve AlbarakaTech Global `extra_source=true` olarak ek kaynaklardır; Markdown dışında olsalar da taranır ve sync_watchlist tarafından kapatılmaz. Codeway eski Lever yerine resmi ana sitenin yönlendirdiği Ashby üzerinden okunur (16 ilan). Picus Security Lever kaynağı da eklendi (8 ilan). AlbarakaTech 2 ilan; bu üç kaynağın son kontrolünde uygun ilan yok. Toplam 54 etkin kaynak için başarılı kontrol kaydı vardır.

9 Eylül: Banka ve iştirakleri bitmeden diğer teknoloji şirketlerine geçilmeyecek. Ziraat Bankası İK duyuruları ve VakıfBank bankacılık ilanları sayfaları, doğru sayfa başlığı ve kapsamlı içerik alanı kontrol edilerek değişiklik takibine eklendi; canlı okuma DB/Telegram olmadan doğrulandı. Bunlar açık ilan okuyucusu değildir. Enpara resmi kariyer bağlantısı Yenibiriş aramasına gider. DenizBank aday girişi gerektirir. Softtech genel ilan servisi anonim denemede hata sayfası döndürdü; Yetenek Kuşağı izlenir, normal ilan okuyucusu halen kapalıdır. BANK_COVERAGE.md banka özelindeki durumu gösterir.

9 Eylül son kontrol: 59 etkin kaynağın başarılı canlı denetim kaydı var (942 ham, 13 uygun ilan; farklı zamanlı son kontrollerin toplamı). Yapı Kredi Koç Kariyerim 0 ilan, Yapı Kredi Teknoloji 2 ilan/0 uygun. Şirket filtresi başka marka döndürürse kaynak hata verir. Garanti Talent Week/Data MT/Tech Talent sayfası gömülü detaylarla izlenir; 9 program/duyuru monitörü. Eski başvuru tarihleri yeni ilan sayılmaz. 43 test başarılı. Yapı Kredi özel portalı 503 ve diğer banka engelleri sürer; tüm bankalar tamamlandı denemez.

9 Eylül banka devamı: HSBC Eightfold API okuyucusu (Türkiye 0), İş Bankası eksik ara sertifika zinciri tamamlanarak resmi liste (0), Softtech Chromium/SuccessFactors okuyucusu (4/0 uygun) eklendi ve canlı doğrulandı. 62/62 etkin kaynak için başarılı son kontrol; 946 ham, 13 uygun (farklı zamanlı kontroller toplamı). Softtech için Chromium kurulumu zorunlu; SERVER_UPDATE.md güncellendi. Engelli kaynakların en son durumları companies.json/BANK_COVERAGE.md içindedir.

9 Eylül Albaraka devamı: Resmi ana sitenin yönlendirdiği Albaraka İnsan Kıymetleri #kariyer bölümü değişiklik takibinde. Mevcut duyuru sadece 4. sınıf öğrencilerine yönelik olduğundan yeni mezun işi sayılmadı; ilk okuma sessizdir. Yapılandırılmış başvuru bağlantıları, bağlantı metni tıklayın olsa da hash hesabına alınır. 10 program/duyuru sayfası, 62 etkin ilan kaynağı ve 48 başarılı test. Banka raporu tools/report_banks.py ile kaynak adları/aliases üzerinden üretilir; ING Türkiye’nin yanlış needs_source görünmesi düzeltildi. BKM ve N Kolay için doğrulanmamış ilan kaynağı etkinleştirilmedi.


## 9 Eylül 2026 — banka kaynaklarının toplu tamamlanması

Bu turda altı HRPeak kaynağı etkinleştirildi: Architecht (3 ilan), Albaraka Türk (1), Ziraat Teknoloji, Vakıf Katılım, Ziraat Katılım ve Emlak Katılım (son dört kaynak açıkça 0 ilan). HTTP istemcisinin 403/204/DNS hataları normal anonim Chromium ile çözüldü; liste ve detay aynı tarayıcı oturumunda okunur. Proxy veya oturum açma kullanılmadı. Son iki listedeki boş durum, Architecht ve Albaraka'nın dolu görünümüyle aynı okuyucuda sınandı. Çok sayfalı HRPeak görünümü desteklenmediğinde eksik kapsam başarılı sayılmaz.

Multinet Up'ın resmi FlowQ panosu eklendi: API'de offset satır sayısı değil sayfa numarasıdır; 12+2 toplam 14 ilan ve detayları canlı doğrulandı. Kapalı/dahili ilanlar elenir. Paycell'in resmi sitesinde bağımsız iş panosu bulunamadığı kayda alındı; Turkcell'in tüm Paycell ilanlarını kapsadığı iddia edilmedi.

Son kayıtlı kaynak denetimleri: 69/69 başarılı, 964 ham / 13 uygun ilan. Farklı saatlerdeki son denetimlerin toplamıdır. Uygun bağlantılar 13/13; program okuyucuları 10/10; otomatik testler 51/51. Program denetimi gerçek veritabanını veya Telegram'ı kullanmaz. Sunucuya kurulum yapılmadı.

TEB'in BNP sayfası normal Chromium'da da 403; resmi alternatif APEX giriş ekranı. DenizBank ve Türkiye Finans anonim tarayıcıda da giriş/captcha ekranı. Yapı Kredi ana kariyer sitesi 503 bakım ekranı; resmi Koç Kariyerim alternatifi etkin. Papara WordPress alan adı bağlantı hatası, Param servis sağlayıcı engeli tarayıcıda da doğrulandı. Enpara'nın resmi yönlendirdiği Yenibiriş 403. Bu kısıtlar tamamlanmış ilan entegrasyonu sayılmaz.
