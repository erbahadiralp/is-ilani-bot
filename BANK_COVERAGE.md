# Banka ve iştirak takip durumu

İlan okuyucusu, program/duyuru takibi ve erişim engeli farklı durumlardır. Bankaların tamamı entegre değildir.

| Kurum | İlan kaynağı durumu | Program / duyuru takibi | Açıklama |
|---|---|---|---|
| Garanti BBVA | verified_at_last_audit | Talent Week / Data MT / Tech Talent |  |
| Akbank | verified_at_last_audit | Yok | Resmi Angular arayüzünün anonim ilan listeleme ve detay arama akışı. |
| Türkiye İş Bankası | verified_at_last_audit | Yok | Eksik GlobalSign ara sertifikası eklendi; kök sertifika ve alan adı doğrulaması açık. Resmi tüm ilanlar sayfası açıkça boş. Dolu ilan görünümü ilk yayında ayrıca denetlenmeli; pozisyon tanıtımları taranmaz. |
| Yapı Kredi | verified_at_last_audit | Yok | Resmi IK sayfasının yönlendirdiği Koç Kariyerim şirket filtresi. Yalnız bu kanaldaki ilanları kapsar; kariyerim.yapikredi.com.tr halen 503. Teknoloji iştiraki kullanıcı banka ve iştirak önceliği kapsamında eklenmiştir. |
| Yapı Kredi Teknoloji | verified_at_last_audit | Yok | Resmi IK sayfasının yönlendirdiği Koç Kariyerim şirket filtresi. Yalnız bu kanaldaki ilanları kapsar; kariyerim.yapikredi.com.tr halen 503. Teknoloji iştiraki kullanıcı banka ve iştirak önceliği kapsamında eklenmiştir. |
| QNB Türkiye | verified_at_last_audit | Yok | Resmi frontend GET akisi dogrulandi. Canli ilan listesi su anda bos; dolu satir eslemesi frontend alanlarina gore test edilir. |
| DenizBank | login_required | Yok | Resmi kariyer bağlantısı aday giriş ekranı; anonim ilan listesi doğrulanmadı. |
| ING Türkiye | verified_at_last_audit | Yok | Resmi Türkiye ilanları; sayfalama ve deneyim şartları kontrol edilir. |
| TEB | http_403 | Yok | Resmi BNP Paribas Türkiye listesi HTTP ve Chromium ile 403. Alternatif resmi APEX portalı giriş ekranı; anonim liste bulunamadı. |
| Kuveyt Türk | verified_at_last_audit | TechTalent | Resmi Katılbize ilan portalı; TechTalent programı ayrıca izlenir. |
| Türkiye Finans | login_required | Yok | Resmi kariyer portalı aday girişi gerektiriyor; anonim ilan listesi doğrulanmadı. |
| Albaraka Türk | verified_at_last_audit | Kariyer ve Yetenek Duyuruları | Resmi HRPeak panosu anonim Chromium ile açılıyor; şirket başlığı, boş durum ve ilan detayları doğrulanır. Chromium kurulmalıdır. Sayfalama görünürse eksik liste yerine hata raporlanır. |
| Fibabanka | linkedin_only | Fintern Future Talent Program | Normal ilanlar LinkedIn; Fintern resmi program sayfası ayrı izlenir. |
| Odeabank | linkedin_only | Yok |  |
| Alternatif Bank | linkedin_only | Yok | Resmi ailemize katılın sayfası 200; iş ilanları doğrudan LinkedIn şirket panosuna yönlendirilir. |
| HSBC Türkiye | verified_at_last_audit | Yok | Resmi Eightfold API: Türkiye filtre yanıtı ve global ikinci sayfa doğrulandı; ilan detayı JSON-LD okunur. Türkiye filtresi şu an 0 sonuç. |
| Ziraat Bankası | announcement_monitor_only | İşe Alım Duyuruları | Resmi İK duyuru sayfası değişiklik takibinde; mevcut öğrenci staj duyurusu aktif yeni mezun işi sayılmadı. |
| VakıfBank | announcement_monitor_only | İşe Alım Duyuruları | İşe alım duyuru sayfası değişiklik takibinde; şu an ilan yok. BT pozisyon tanıtımları açık ilan sayılmadı. |
| Halkbank | verified_at_last_audit | Yok | Resmi Yeni Mezunum ilan listesi. Genel başvuru profil filtresinden geçmez. |
| Vakıf Katılım | verified_at_last_audit | START / My Talent ve Yetenek Programları | Resmi HRPeak panosu anonim Chromium ile açılıyor; şirket başlığı, boş durum ve ilan detayları doğrulanır. Chromium kurulmalıdır. Sayfalama görünürse eksik liste yerine hata raporlanır. |
| Ziraat Katılım | verified_at_last_audit | Yok | Resmi HRPeak panosu anonim Chromium ile açılıyor; şirket başlığı, boş durum ve ilan detayları doğrulanır. Chromium kurulmalıdır. Sayfalama görünürse eksik liste yerine hata raporlanır. |
| Emlak Katılım | verified_at_last_audit | Yok | Resmi HRPeak panosu anonim Chromium ile açılıyor; şirket başlığı, boş durum ve ilan detayları doğrulanır. Chromium kurulmalıdır. Sayfalama görünürse eksik liste yerine hata raporlanır. |
| Enpara | external_boards_only | Yok | Resmi kariyer sayfası Yenibiriş Enpara aramasına yönlendiriyor; hedef son kontrolde 403. |
| Papara | http_403 | Yok | Kariyer alan adi aktif baglanti bulunamadi yaniti veriyor. Anonim Chromium ile de 403 doğrulandı. |
| iyzico | verified_at_last_audit | Yok |  |
| Paycell | no_public_listing | Yok | Resmi ana sayfada bağımsız kariyer/ilan bağlantısı bulunamadı. Turkcell kaynağı etkin; Paycell ilanlarının tamamını kapsadığı doğrulanmadı. |
| Midas | verified_at_last_audit | Yok |  |
| Param | http_403 | Yok | Resmi ana sayfanin kariyer yonlendirmesi; erisim reddedildi. Anonim Chromium ile de 403 doğrulandı. |
| Sipay | verified_at_last_audit | Yok | Resmi site güncel Hirex panosuna yönlendiriyor. Eski Talentics panosu kullanılmıyor. |
| PayTR | external_boards_only | Yok | Resmi sayfa LinkedIn ve Kariyer.net ilanlarına, ayrıca genel başvuru formuna yönlendiriyor. |
| Multinet Up | verified_at_last_audit | Yok | Resmi kariyer sayfasının FlowQ panosu; 12+2 sayfalama, şirket kimliği, başvuru açıklığı ve detay metni doğrulanır. |
| Edenred Türkiye | verified_at_last_audit | Yok | Resmi portal canlı kontrolü source_audit.json içinde. |
| BKM | no_public_listing | Yok | Resmi ana sayfa ve BKM Hakkında bağlantıları incelendi; bu sayfalarda anonim ilan listesi veya kariyer panosu bağlantısı bulunamadı. İlan entegrasyonu tamamlanmadı. |
| Intertech | linkedin_only | Yok | Resmi iş ilanları bağlantısı LinkedIn; Firsttech/Starttech programları resmi sayfada ayrı tanıtılıyor. |
| Softtech | verified_at_last_audit | Yetenek Kuşağı | Anonim Chromium okuyucusu; canlı tarayıcıda 4 ilan doğrulandı. Sayfalama toplamıyla tutarlılık ve sabit ilan kimliği kontrol edilir. Sunucuda Playwright Chromium kurulmalı. |
| Architecht | verified_at_last_audit | Yok | Resmi HRPeak panosu anonim Chromium ile açılıyor; şirket başlığı, boş durum ve ilan detayları doğrulanır. Chromium kurulmalıdır. Sayfalama görünürse eksik liste yerine hata raporlanır. |
| Aktif Bank | no_public_listing | Yok | Resmi Yetenek ve Gelişim sayfaları 200; deneyimsiz işe alım politikası var, anonim ilan listesi veya başvuru panosu bu sayfalarda yayımlanmıyor. |
| N Kolay | parent_brand | Yok | Resmi kurumsal sayfa N Kolay’ın Aktif Bank markası olduğunu doğrular. Ayrı anonim ilan panosu doğrulanmadı; Aktif Bank kaynak durumu geçerlidir. |
| AlbarakaTech Global | verified_at_last_audit | Yok | İlan metni resmi siteden okunur; başvuru bağlantısı Kariyer.net olabilir. |
| Ziraat Teknoloji | verified_at_last_audit | Yok | Resmi HRPeak panosu anonim Chromium ile açılıyor; şirket başlığı, boş durum ve ilan detayları doğrulanır. Chromium kurulmalıdır. Sayfalama görünürse eksik liste yerine hata raporlanır. Banka iştiraklerini tamamlama isteği kapsamında ek kaynak. |

Tarih ve ham/uygun ilan sayıları source_audit.json içindedir. Raporda ING Türkiye, ING kaynak adına eşleştirilir; aynı banka için ikinci okuyucu oluşturulmaz.

Softtech ve HRPeak banka okuyucuları için Chromium, İş Bankası için paketteki certificates klasörü gereklidir. Engelli kaynaklar sıfır ilan veya tamamlanmış entegrasyon olarak sayılmaz.
