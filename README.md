# BERZAH SERVİSİ v2.0 — Mercü'l-Bahreyn

Astro Pro v9.2.4'ten ayrıştırılmış, **bağımsız hesap mikroservisi**.
FastAPI tabanlı; Render.com Web Service olarak dağıtılır. HTML/JS/AI katmanı
yoktur — bu servis yalnız **sayı ve yorum matrisi** üretir; mevcut Astro Pro
arayüzü ve AI sohbeti bunu JSON olarak tüketir (`/api/v1/ai-context`).

---

## İçerik envanteri

| Katman | Kaynak | Dosya |
|---|---|---|
| **BERZAH v2 kütle motoru** — m(P), barisentr, Φ alanı, KD/AD/Berzah (kararsız denge), mercekleme, 137.508° kurtarıcı, heksagram Hamming ikizleri, öz-modül spektrumu (surrogate p + BH-FDR), yorum matrisi | bu oturumun icadı | `app/engine_mass.py` |
| **Modül 66–74** — Kabz/Bast alanı+ekseni, Einstein–Rosen köprüleri, Olay Ufku/Boğaz, Kuramoto C, 528 Hz imza, LQC ρ/ρc, Kuantum Sıçrama takvimi, Tayy-i Mekân geçit pencereleri (S=0.45·bounce+0.30·C+0.25·ρ/ρc) | v9.2.4 `berzah.py` **AYNEN** | `app/kabzbast_v1.py` + adaptör `app/engine_kabzbast.py` |
| **16 deneme modülü** — KRN/Anti-KRN · Vahdet+H1-12 · Mizan/Sekîne/Berzah · Asabiyye (λ₂ Fiedler) · Arş Ekseni · Felek Saati · Ayna Ekseni · Devr-i Daim · Nokta-i Süveyda · Mizâc Pusulası · Vuslat Kapıları · İkbal Merdiveni · Sahib-Kırân · Nokta-i İcâbet · Nokta-i Noksan · Sevk-i Felek v2 | v9.2.4 CELL 2.8–2.30 matematiği | `app/modules_deneme.py` |
| **Kadim katman** — İsim Tecellîsi (ebced köprüsü + 1°/yıl progresyon) · Kadim Lab (Hyleg-etik, Tasyîr, Kırân-ı Ekber *gerçek efemerisle*, Mısır hudûdu, Dorotheus mütellet, İhtiyârât) · Hüviyet Mührü sentezi | CELL 2.13 / 2.28 / 2.18 | `app/modules_kadim.py` |
| **Human Design** — 64 kapı çarkı, design=88° güneş yayı, kanal-tabanlı Tip/Otorite/Tanım (v9.2 düzeltmesi korunur), profil, not-self tuzakları | v9.2.4 HD bloğu | `app/module_hd.py` |

## Web arayüzü

`/` adresinde tek dosyalık bir arayüz sunulur (`app/static/index.html`) — derleme
adımı, npm veya framework yok. Doğum verisi formu, ardından sonuçların tam dökümü.
İmza öğesi **Φ alan halkası**: zodyak üzerine potansiyel alan çizilir, yüksek alan
içeri çöker (Kara Delik kuyusu), itici (retro) kütleler dışarı sivrilir, Berzah
altın eşik olarak işaretlenir. 390px'e kadar yatay taşmasız test edildi.

## API

| Uç | İçerik |
|---|---|
| `GET /` | **web arayüzü** |
| `GET /api` | servis kartviziti (JSON) |
| `GET /healthz` | sağlık (Render health check) |
| `POST /api/v1/full` | **her şey** tek yanıtta |
| `POST /api/v1/berzah2` | yalnız v2 kütle motoru |
| `POST /api/v1/kabzbast` | yalnız 66–74 |
| `POST /api/v1/deneme` | 16 deneme modülü |
| `POST /api/v1/kadim` | İsim + Lab + Hüviyet |
| `POST /api/v1/hd` | Human Design |
| `POST /api/v1/ai-context` | AI sohbetine kompakt kanıt kartları |
| `GET /docs` | otomatik OpenAPI arayüzü |

**Örnek istek gövdesi:**
```json
{
  "name": "Danışan", "year": 1990, "month": 6, "day": 21,
  "hour": 14, "minute": 30, "lat": 40.80, "lng": 29.43,
  "tz_offset": 3, "sr_year": 2026,
  "isim": "İsa", "anne": "Fatma", "months": 18, "days": 365
}
```
`tz_offset` verilmezse `tz_name` (IANA) kullanılır; o da yoksa
timezonefinder lat/lng'den çözer.

## Render.com dağıtımı

**KRİTİK:** Repo kökündeki `.python-version` dosyası (`3.11.11`) silinmemeli.
Yoksa Render varsayılan Python 3.14'ü seçer, pydantic-core hazır wheel bulamaz,
Rust'tan derlemeye çalışır ve Render'ın salt-okunur cargo dizini yüzünden
build **başarısız olur**.

Blueprint ile: *New → Blueprint → repoyu seç* (render.yaml otomatik okunur).

Elle Web Service kurulumu:

| Alan | Değer |
|---|---|
| Language / Runtime | `Python 3` |
| Branch | `main` |
| Root Directory | *(boş bırak)* |
| Build Command | `bash build.sh` |
| Start Command | `bash start.sh` |
| Health Check Path | `/healthz` |
| Environment Variable | `PYTHON_VERSION` = `3.11.11` |

## Saat dilimi

`timezonefinder` bilinçli olarak **opsiyonel**dir (numpy+h3 çeker, build'i uzatır).
Öncelik sırası: `tz_offset` → `tz_name` (IANA, stdlib zoneinfo) → timezonefinder
(kuruluysa) → boylamdan kaba tahmin. Kullanılan yol her yanıtta `tz_kaynak`
alanında görünür; sessiz yanlış saat dilimi imkânsızdır.

`ephe/` klasöründeki üç `.se1` dosyası repoda kalırsa **SWIEPH** hassasiyeti
otomatik açılır; silinirse motor **MOSEPH**'e (dosyasız) düşer ve Chiron
dışında her şey çalışmaya devam eder.

## Kütüphane kararları

**Tutulanlar (6):** fastapi, uvicorn, pydantic, pyswisseph, timezonefinder, tzdata.

**Bilinçli ATILANLAR ve sebepleri:**
- `numpy/pandas/scipy` → tüm matematik stdlib ile yazıldı (Fiedler λ₂ için
  Jacobi özdeğer çözücü dahil). Render free-tier build 3-4 dk kısalır,
  bellek yarıya iner.
- `matplotlib/seaborn/plotly/sklearn/IPython/tqdm/tabulate/openpyxl` →
  notebook bagajı; API servisi görsel üretmez.
- `Flask/gunicorn` → FastAPI+uvicorn'a geçildi: pydantic doğrulama + otomatik
  `/docs` + async hazır.
- `requests/httpx/python-dotenv` → bu servis DIŞARIYI ARAMAZ (AI anahtarı yok,
  gateway yok); mevcut Astro Pro AI katmanı bu servisi çağırır, tersi değil.
- `geopy/reportlab/pytz` → geokodlama ve PDF mevcut uygulamanın işi;
  pytz yerine stdlib `zoneinfo`+tzdata.

## Test

```bash
python smoke_test.py     # 7 aşamalı uçtan uca duman testi (~0.4 sn)
```

## v2.1 — doğruluk denetimi ve düzeltmeler

Çekirdek astronomi bağımsız olarak doğrulandı:
- Yükselen, küresel trigonometriyle elle türetilen değerle **0.003° içinde** uyuşuyor
- Efemeris, bilinen güneş boylamıyla 0.02° içinde
- Astro Pro v9.2.4 boru hattıyla altı zorlu tarihte (1962, 1978, **1983 UTC+4**, 1990, 2005)
  fark **0.000 saniye / 0.00 yay saniyesi**

Bulunan ve giderilen altı hata:

| # | Hata | Etki | Çözüm |
|---|---|---|---|
| 1 | **Berzah sahte kök** — tam alanın kuvvet taraması 1/r² tekilliklerinde işaret değiştiriyor, denge noktası bir gezegenin tam üstüne (0.00°) oturabiliyordu | Ana modül anlamsız sonuç veriyordu | Analitik iki-deniz dengesi + tekillik yasağı (≥2.5°) + doğrulanamayınca dürüst "alan bozucu" bildirimi |
| 2 | **Gauquelin ekliptik boylamla** ölçülüyordu; artı bölgeler mundan konumda tanımlıdır | Enlemi yüksek cisimlerde kütle hatası, tüm katmanlara yayılıyordu | `swe.house_pos` ile gerçek mundan konum |
| 3 | **Yaz saati tuzakları sessizdi** — var olmayan / belirsiz saatler uyarısız 1 saat kaydırıyordu | Yılda iki saatlik pencerede sessiz hata | Her iki tuzak yakalanıp bildiriliyor (Astro Pro'nun pytz yaklaşımıyla aynı) |
| 4 | **Kutup dairesinde çöküyordu** — Placidus tanımsız, servis 422 dönüyordu | 66.5° üstü doğumlar hiç hesaplanamıyordu | Whole Sign'a otomatik düşüş |
| 5 | **Felek Saati ↔ Kadim Lab çelişkisi** — biri ortalama hareket, diğeri gerçek efemeris kullanıyordu | Jüpiter–Satürn kavuşumu iki modülde farklı çıkıyordu | Her ikisi de efemeris taraması; ikisi de 2040-10-31 |
| 6 | **Asabiyye λ₂ dejenere** — kopuk grafta λ₂ daima 0, Fiedler "kampları" rastgele | Anlamsız fay hattı bildiriliyordu | Bağlı bileşenler gerçek yapı olarak bildiriliyor, iç bağlılık en büyük blokta ölçülüyor |

Ayrıca `cusps` 12/13 elemanlı iki pyswisseph davranışına karşı savunma eklendi.

## Girdi doğrulama

`POST /api/v1/tz-check` haritayı kurmadan saat dilimini ve koordinatı denetler;
arayüz bunu yazarken canlı çağırır. Ekranda UTC karşılığı, yaz saati durumu ve
şu uyarılar görünür: var olmayan/belirsiz saat, kutup dairesi, **boylam ile saat
diliminin çelişmesi** (doğu/batı işareti hatası). Form 81 il listesi sunar ama
koordinatlar her zaman görünür ve düzenlenebilir — ilçe doğumlarında elle
ince ayar yapılabilir.

## Mimari notlar

- `ensure_ephe()`: tüm swisseph çağrıları yol-garantili tek kanaldan geçer
  (FastAPI thread havuzunda efemeris yolu kaybolması sorununa karşı).
- Kırân-ı Ekber gerçek efemeris taramasıyla bulunur (2040-10-31 · 17°56' Terazi
  doğrulandı); ortalama-hareket projeksiyonu değil.
- v1.0 motoru (`kabzbast_v1.py`) TEK SATIR değiştirilmeden taşındı — icat
  bütünlüğü korunur; tüm uyarlama adaptörde yapılır.
- Model dili semboliktir: "kara delik / LQC / 528 Hz" fiziksel nedensellik
  iddiası değildir (kaynak v9.2 notu aynen korunur).

### v2.2 — Asabiyye Matrisi

Jacobi özdeğer çözücüsü bilinen spektrumlara (P3, C4, K5) karşı **tam** doğrulandı;
10×10'da iz 7e-15 hassasiyetle korunuyor — hata çözücüde değildi. Dört kusur bulundu:

| Hata | Etki | Çözüm |
|---|---|---|
| Açı orbları 2.5/2.0/1.5° yazılmıştı; Astro Pro v9.2.4 tablosu **8/8/7/7/5** | Graf açlıktan kopuyordu (45 çiftin yalnız 6'sı bağlıydı), λ₂ hep 0, her harita "kopuk" | Orb tablosu referansla birebir hizalandı, minör açılar eklendi → 16 kenar |
| Kenar gücü sabit σ=1° Gauss'tu, orbtan bağımsız | 2°'nin ötesindeki her açı fiilen siliniyordu | Astro Pro'nun kendi eğrisi: (1−sapma/orb)^1.35 |
| Yorum eşikleri (λ₂>1.2 güçlü, >0.4 orta) yanlış ölçekteydi | 400 haritanın **397'si** "zayıf" çıkıyordu; sınıflandırma hiçbir şeyi ayırt etmiyordu | 400 haritalık referans dağılımdan yüzdelik ölçeği |
| Menteşe, kopuk grafta global Fiedler vektöründen seçiliyordu | Anlamsız cisim bildiriliyordu | En büyük blok içinden seçiliyor |

Kart artık bağlılık dilimini, bağ sayısını, en güçlü üç bağı ve yalnız kalan
cisimleri de gösteriyor. Not: orb tablosu `_aspects_to` üzerinden KRN ve
İsim Tecellîsi modüllerini de besler; onlar da bu düzeltmeden yararlandı.

### v2.3 — modül denetimi + arayüz yeniden tasarımı

`audit.py` tüm boru hattını çeşitli haritalar üzerinde koşturur (Türkiye, güney
yarımküre, kutup dairesi) ve eksik / istisna atan / boş dönen / ölü modülleri
işaretler. 40 haritalık denetim: **29/29 modül üretiliyor, ölü modül yok.**
Bulunan iki kusur giderildi:

| Hata | Çözüm |
|---|---|
| Vendor edilmiş `kabzbast_v1.py` kutup dairesinde çöküyordu (`swe.houses` korumasızdı) | Whole Sign düşüşü eklendi — artık 0 istisna |
| Kurtarıcı orbu 1.5° idi: 40 haritanın 37'sinde liste boş, "tek somut talimat" vaadi karşılanmıyordu | Orb 3°; orb dışında kalsa bile en yakın aday sapmasıyla ve kapı durumuyla her zaman bildiriliyor |

Arayüz Bauhaus/geometrik dile taşındı: kâğıt zemin + ızgara, kalın siyah kontur
ve ofset gölge, birincil renk üçlüsü. Zodyak halkası artık **unsur kodlu**
(ateş kırmızı, toprak turkuaz, hava sarı, su mavi) — süs değil bilgi taşır.
Okuma protokolü (şikâyet → sebep → karar → talimat) numaralandırıldı; numaralar
gerçek bir sıra kodladığı için gerekçelidir. Önceki krem/serif tasarım
`app/static/index_klasik.html` olarak duruyor; iki dosyayı takas ederek geri
dönülebilir.

### v2.4 — minimalist Bauhaus/Memphis

Aynı geometrik dil, sesi kısılmış hâli. Kalın konturlar, sert ofset gölgeler ve
dolu renk blokları kaldırıldı; yerini saç teli çizgiler, boşluk ve seyrek renk
vurguları aldı. Cesaret tek yere — **alan halkasına** — saklandı, çevresindeki
her şey sessiz tutuldu.

- Zemin ızgarası ve gölgeler kaldırıldı; ayırıcı olarak 1px saç teli çizgi
- Girdi alanları kutu değil, alt çizgi; odakta kırmızıya döner
- Bölüm başlıkları dolu renk bandı değil: 11px geometrik im + mono numara + ince kural
- Kart ızgarası arka planı sızdıran 2px boşlukla ayrılıyor, kenarlık yok
- Zodyak hücreleri dolu renk yerine unsur **tinti** (%12–20 opaklık); kodlama korunur
- Archivo Black yalnız iki yerde: sayfa başlığı ve çatalın sorusu

Üç tasarım da pakette; `app/static/` içinde dosyaları takas ederek geçilebilir:
`index.html` (minimalist · aktif) · `index_bauhaus_kalin.html` (kalın Bauhaus) ·
`index_klasik.html` (krem/serif).

### v2.5 — analiz modu, tam ilçe listesi, AI danışman

**Analiz modu** (başlığın hemen altında): Kişisel · Sinastri · Kompozit.
Sinastri/kompozit seçilince ikinci doğum verisi bloğu açılır.
- `app/relationship.py` — çapraz açılar, ev bindirmesi, kompozit orta nokta haritası
- **Alan bükmesi**: BERZAH'a özgü sinastri ölçüsü. Bir kişinin kütleleri ötekinin
  Φ alanına eklenir ve KD ile Berzah'ın kaç derece kaydığı ölçülür. Klasik
  sinastri açı sayar; bu ölçü *karar noktasının yerinden oynayıp oynamadığını*
  sorar.
- Kompozitte tam v2 motoru koşar: ilişkinin de kendi Kara Deliği ve Berzahı olur.

**Doğum yeri: 81 il + 1037 ilçe** (`app/data/yerler.json`, `/api/v1/yerler`).
İki bağımsız açık kaynak birleştirildi ve çapraz doğrulandı: medyan sapma
**0.26 km**, %95.2'si 5 km içinde uyuşuyor. 25 km üstü ayrışan 9 kayıt tek tek
incelendi (ör. bir kaynak Alanya'yı Antalya merkezine, diğeri Tarsus'u 50 km
kuzeye koymuştu). Koordinatlar seçimden sonra da düzenlenebilir kalır.

**12. bölüm — AI danışman** (`app/ai.py`, `/api/v1/chat`). Analiz bittiğinde
chatbox açılır ve sonucun tamamı üzerinden soru yanıtlar.
- 33 KB'lik ham analiz, danışmanlık için gereken çekirdek bulgulara süzülür
  (~2.3 KB): KD/AD/Berzah, çatal, kurtarıcı, kütleler, KRN, Vahdet, Asabiyye,
  Süveyda, Noksan, İcâbet, Mizâc, İkbal, Sahib-Kırân, Kabz/Bast, Hüviyet, HD.
- Sistem promptu okuma protokolünü zorunlu kılar ve sınır koyar: tıbbî teşhis,
  ömür/ölüm, kesin hukukî-finansal tavsiye yok; psikolojik kriz belirtisinde
  insan desteğine yönlendirme var.
- Ağ istemcisi stdlib `urllib` — yeni bağımlılık yok.
- Gateway şeması dışarıdan bilinemediği için **protokol otomatik seçilir**:
  önce OpenAI `/v1/chat/completions`, olmazsa Anthropic `/v1/messages`.
  Kimlik doğrulama iki sözleşmeyi birden gönderir (`Authorization: Bearer`
  ve `x-api-key`). `/api/v1/ai-health` kurulumu doğrular.

Bu turda ayrıca gizli bir hata yakalandı: `isim_tecellisi` içinde `min()`
anahtarsız kullanılıyordu; iki Mizan tepesi tam eşit uzaklıkta olduğunda
Python sözlükleri karşılaştırmaya çalışıp `TypeError` atıyordu.

### v2.6 — danışman seçimi ve yanıt kalitesi

**Model seçici.** Chatbox'ın üstüne açılır menü eklendi; modeller gateway'den
canlı çekilir (`GET /api/v1/ai-models` → önce `/v1/models`, olmazsa `/models`).
OpenAI ve Anthropic liste biçimlerinin ikisi de tanınır. **`AI_MODEL` ortam
değişkeni artık zorunlu değil**; yazılırsa menüde ön seçili gelir. Liste hiç
alınamazsa menü yerine serbest metin kutusu açılır.

**Yarım kalan cevaplar.** Üç ayrı sebep vardı, üçü de giderildi:

| Sebep | Çözüm |
|---|---|
| `max_tokens` 1400 idi, uzun yanıt sınırda kesiliyordu | 3000'e çıkarıldı |
| Kesilme sessizce yutuluyordu | `finish_reason` / `stop_reason` okunuyor; kesilirse **otomatik devam** isteniyor ve parçalar birleştiriliyor (en fazla 2 tur) |
| Sistem promptu bitirmeyi zorunlu kılmıyordu | "Cevabı BİTİR, yarım bırakma; kısa ama tamam cevap, uzun ve kesik cevaptan iyidir" kuralı en başa alındı |

**Ham markdown ekranda görünüyordu.** Model `#`, `**`, `---` yazıyor, arayüz
düz metin basıyordu. İki taraftan birden çözüldü: sistem promptu başlık ve
yıldız kullanımını yasaklıyor, arayüzde ise güvenli bir hafif markdown
dönüştürücü var (önce kaçışlama, sonra sınırlı etiket — XSS testi geçti).
Başlıklar silinmiyor, kalın satıra çevriliyor: silinseydi "## 1. Eşik" satırı
numaralı liste sanılıp `<li>` oluyordu.

**Danışman sesi.** Prompt yeniden yazıldı: ilk paragrafta soruya doğrudan cevap,
sonra bulguya bağlama, sonra gerçek hayattaki karşılığı, son paragrafta bu hafta
yapılabilecek tek somut adım. Rapor değil konuşma metni.

**Düşünme durumu.** Bekleme sırasında "Düşünüyorum… 0 sn" görünür; süre sayılır
ve dört saniyede bir aşama değişir (Haritayı okuyorum → Berzah'ı tartıyorum →
Kütleleri karşılaştırıyorum → Çatalı açıyorum → Somut adımı arıyorum → Cevabı
toparlıyorum).

### v2.7 — ZÎC: marka, katmanlı halka, bölüm analizleri

**Yeni ad: ZÎC.** Zîc, klasik İslam astronomisinde konum hesabı için kullanılan
tablo külliyatıdır — bu servisin yaptığı işin tam karşılığı. "Berzah" terk
edilmedi; modelin çekirdek kavramı olarak kod ve yorum içinde duruyor, yalnız
ürün adı olmaktan çıktı. Banner yeniden kuruldu: amblem + marka şeridi, tez
cümlesi, dört rakamlı özet şerit.

**Ek katman hatası.** Sinastri/kompozit modunda "Ek katmanlar" paneli tekti ve
kişi B'nin altındaydı; A'nın ebced/anne/Solar Return girdileri hiç
uygulanmıyordu. Artık **her iki kişinin kendi paneli var** ve `/api/v1/iliski`
ikisi için de İsim Tecellîsi ve Solar Return hesaplıyor (`A_isim`, `B_isim`,
`A_solar`, `B_solar`).

**Katmanlı alan halkası.** Beş katman açılıp kapanabiliyor: Φ alanı · Açılar
(sertlik kırmızı, akış turkuaz) · Evler (uçlar ve numaralar, köşeler kalın) ·
64 kapı (heksagram dilimleri + yapısal ikiz bağları) · Açısallık (Gauquelin
ağırlığını altın halka kalınlığıyla gösterir). Gezegenin üzerine gelince kütle
bileşenleri alt panelde açılıyor.

**Bölüme özel AI analizi.** 2–11 arası her bölüm başlığının sağında düğme var;
basınca sayfanın önünde oval bir modal açılıyor. Sağ üstteki çarpı, dışarı
tıklama veya Esc ile kapanıyor; yanıt kopyalanabiliyor.
Uç: `POST /api/v1/chat-bolum`.

**Zaman aşımı.** `AI_TIMEOUT` varsayılanı 60 → **120 sn**. Otomatik devam turları
için toplam süre bütçesi eklendi (`AI_TOTAL_BUDGET`, 210 sn): bütçe dolarsa
devam edilmiyor — yarım ama teslim edilmiş cevap, zaman aşımı hatasından iyidir.

**Kategori kapsamı.** Danışman bağlamı 35 kategoriden yalnız **16'sını**
taşıyordu; Mizan, Arş Ekseni, Felek Saati, Ayna Ekseni, Devr-i Daim, Sevk-i
Felek, 528 Hz, LQC, Kuramoto, Olay Ufku, Hyleg, Tasyîr, İhtiyârât, İsim
Tecellîsi, spektrum, yapısal ikizler, asal açılar, mercekleme ve Solar Return
hiç girmiyordu. Kapsam **30/33**'e çıkarıldı (kalan üçü bu haritada gerçekten
boş olan koşullu bulgular); bağlam 2.2 KB'den 6.7 KB'ye çıktı.

### v2.8 — kişiselleştirme, çoklu harita, kota dayanıklılığı

**"Herkes için aynı sonuç" — ölçüldü ve ayrıştırıldı.** Altı farklı harita
karşılaştırıldığında **sayılar 6/6 benzersiz** çıktı (KD, AD, Berzah hepsi
farklı); ama **yorum metni yalnız 3/6** benzersizdi. Sebep: çatal cümleleri
12 satırlık burç tablosundan geliyordu, Hüküm satırları ise herkes için
birebir aynı şablon metindi. Hesap doğruydu, metin genel geçerdi.

**Otomatik kişiselleştirme.** Analiz bitince arka planda `POST /api/v1/kisisellestir`
çağrılıyor; AI çekirdek bulguları okuyup Hüküm'ün dört satırını ve Çatal'ın
dört alanını **bu haritaya özgü** cümlelerle değiştiriyor. Değişen satırlar
kısa bir vurguyla beliriyor, üstte durum rozeti var. Başarısız olursa şablon
metin yerinde kalıyor ve rozet sebebini söylüyor — sessiz bozulma yok.
Jeton disiplini: bu çağrı tam bağlamı (6.7 KB) değil, süzülmüş çekirdeği
(~900 karakter) gönderiyor ve çıktısı JSON şemasıyla 700 jetona sınırlı.

**Halkada çoklu harita.** Artık natal dışında **Solar Return** haritası da
çiziliyor ve seçicinden geçiş yapılabiliyor. İlişki modunda liste: Kişi A ·
Kişi B · A'nın SR'si · B'nin SR'si · Kompozit. Her harita kendi Φ alanını,
kendi Kara Deliği'ni ve Berzah'ını gösteriyor.

**429 kota hatası — çift yakım düzeltildi.** Ekran görüntüsündeki hatada hem
`[openai]` hem `[anthropic]` 429 alıyordu: protokol otomatik seçimi, kota
hatasında da öteki şemayı deniyor ve **kotayı iki kat yakıyordu**. Kota hesap
düzeyinde olduğu için ikinci deneme hiçbir zaman işe yaramaz. Artık 429'da
anında duruluyor, mesaj Türkçeleştirilip kullanılan/limit jeton ve sıfırlanma
süresi gösteriliyor. Ayrıca genel tüketim düşürüldü: sohbet geçmişi 8→4 mesaj
ve mesaj başına 4000→1200 karakter, varsayılan `max_tokens` 3000→2200,
bölüm analizi 2000→1600.

### v2.9 — mobil kullanılabilirlik ve hata temizliği

Gerçek dokunmatik tarayıcıda 360 / 390 / 430 / 820 piksel genişliklerde ölçüldü.
Öncesinde bulunan ve giderilen kusurlar:

| Kusur | Ölçüm | Çözüm |
|---|---|---|
| AI düğmesi mobilde yalnız bir noktaya iniyordu | 21×27 px | "AI" kısa etiketi + en az 40 px yükseklik |
| Katman / harita / öneri düğmeleri | 25–28 px | `@media(hover:none)` altında en az 44 px |
| `<summary>` (ek katmanlar) | 17 px | 44 px, dikey ortalanmış |
| Girdi fontu 15 px | iOS odakta sayfayı yakınlaştırıyordu | mobilde 16 px'e sabitlendi |
| Sayısal alanlarda genel klavye | enlem/boylam için ondalık yok | `inputmode="decimal"` / `"numeric"` |
| "Üzerine gelin" ipucu | dokunmatikte hover yok | "dokunun (veya üzerine gelin)" |
| Kahraman bölümü bir tam ekran yiyordu | forma 640 px'te ulaşılıyordu | 462 px'e indi; rakamlar 2×2 ızgara |
| Form her alan tam genişlik | çok uzun kaydırma | tarih+saat, enlem+boylam yan yana (≤380 px'te tekrar tek sütun) |
| 11 bölüm arasında gezinme yoktu | sonsuz kaydırma | **yapışkan bölüm şeridi** + görünen bölümü işaretleyen IntersectionObserver + başa dön düğmesi |
| CSS'te Türkçe karakterli sınıf (`.çalışıyor`) | kırılgan; `"boş"` sınıfının karşılığı yoktu | ASCII sınıf adları |
| Kompozit modunda blok numarası 3 atlanıyordu | 2 → 4 | sıra kesintisiz sayaca bağlandı |

Doğrulama: dört genişlikte de yatay taşma yok, **40 px altı dokunma hedefi yok**,
JS hatası yok. Çekirdek regresyon korunuyor (Astro Pro ile fark 0.0000).

## v3.0 — Alan topolojisi ve dinamiği (dört yeni icat)

Model şimdiye kadar Φ alanının yalnız uç noktalarını kullanıyordu: KD, AD ve
Berzah. Bu sürüm alanın geri kalanını konuşturur. Hepsi `app/field_dynamics.py`.

**C · Havza Tayini.** Kişi çatalın hangi tarafında *yaşıyor*? Yükselen, Güneş,
Ay ve MC'den λ̇ = +dΦ/dλ ile yokuş yukarı akılır; varılan tepe havzayı verir.
Göstergeler farklı havzalara dağılmışsa çatal kuramsal değil fiilîdir.

**B · Himmet — eşik yüksekliği.** Berzah bir ayırıcıdır; geçmek enerji ister:
ΔΦ = Φ(havza tepesi) − Φ(su bölümü). İki taraf farklı çıkar — test haritasında
Jüpiter havzasından çıkmak Plüton'dan **altı kat** zor. Üstüne bariyerin zaman
içindeki dalgalanması ölçülür: **dayanıklılık** = ortalama/std, ve bariyerin
çöktüğü aylar **geçirgenlik pencereleri** olarak listelenir — danışman için
"çıkmanın en ucuz olduğu zaman".

**D · Kalıcılık diyagramı.** Φ'nin bütün kritik noktaları çıkarılıp 1B persistent
homology ile sıralanır: kalıcılık = Φ(tepe) − Φ(birleşme çukuru). Alan genliğine
bölünüp 0..1 ölçeğine indirilir; ≥0.25 yapısal, ≥0.08 sınırda. Mizan'daki
Sekîne/Berzah listeleri artık filtresiz gelmiyor.

**A · Yürüyen Berzah.** Transitler kütle ekledikçe eşik yer değiştirir. B(t)
yörüngesi, eşik hızı ve **çatallanma** anları çıkarılır: bir seçeneğin açıldığı
ya da kapandığı tarihler. `POST /api/v1/dinamik` (ayrı uçta; ana analizi
yavaşlatmaz).

### Geliştirme sırasında düzeltilen dört metodolojik hata

| Hata | Belirti | Çözüm |
|---|---|---|
| Analitik Berzah gerçek bir Φ çukuru olmayabilir | iki yandan yokuş çıkınca **aynı** tepeye varılıyor, bariyer anlamsız | bariyer daima en yakın **gerçek su bölümünden** ölçülür |
| Mutlak kalıcılık/bariyer haritalar arası kıyaslanamaz | Φ genliği haritadan haritaya değişiyor | alan genliğine bölünüp oransal ölçeğe indirildi |
| Aylık örneklemede **Ay örtüşmesi** | yılda 13 tur atan Ay 12 örnekle rastgeleye dönüyor, 24 yılda 200+ sahte çatallanma | yapısal taramada yalnız yavaş cisimler (Mars→Plüton) |
| Eşik civarında titreme | sayı 6→5→6→7 gidip geliyor | **Schmitt tetikleyici** (0.15 üst / 0.09 alt bant) + üç ay gecikmeli onay → 24 yılda 1–3 çatallanma |

Dayanıklılık ve hız bantları uydurma eşiklerle değil, 40–60 rastgele harita
üzerinde ölçülen dağılımın çeyrekliklerine oturtuldu.

Çekirdek regresyon korunuyor: Astro Pro ile fark **0.0000**.

## v3.1 — Mimari denetimi ve ŞİRÂ ÇEVRİMİ

### Denetim: 10.66 sn → 0.67 sn

Profil çıkarıldı; dört gerçek israf bulundu ve giderildi. Yapı kopuk değildi
ama pahalıydı.

| İsraf | Ölçüm | Çözüm |
|---|---|---|
| `ensure_ephe` her efemeris çağrısından önce `set_ephe_path` çalıştırıyordu | tek analizde **21.476 çağrı**, 0.5 sn | tek seferlik bayrak |
| `en_yakin_esik` ~18 kritik noktanın **hepsini** altın oran aramasıyla rafine ediyordu; 100 kez çağrılıyordu | **3.338 rafine**, 8.8 sn | yalnız gereken 3 nokta rafine edilir |
| `phi_field` sıcak yolunda `sep()` + `norm360()` fonksiyon çağrıları | **6.6 milyon** `sep()`, 5.9 sn | matematik gövdeye gömüldü |
| Solar Return haritası için tam alan topolojisi hesaplanıyordu | gereksiz ikinci tur | `full_v2(..., topoloji=False)` |
| `isim_tecellisi` Mizan ve Vahdet'i yeniden hesaplıyordu | üçüncü tekrar | hazır sonuçlar parametreyle geçirilir |

Üç mod da bir saniyenin altında: kişisel 0.67 · sinastri 0.74 · kompozit 0.98.

### Yeni icat: ŞİRÂ ÇEVRİMİ — Tarık Nefesi

**Neden Şi'râ?** BERZAH'ın çekirdeği ikili bir yapıdır: görünen ağız (Ak Delik)
ve görünmeyen yoğun merkez (Kara Delik). Gökyüzünde bunun birebir karşılığı
vardır — Şi'râ gerçek bir ikili yıldızdır. Şi'râ A gökyüzünün en parlak
yıldızı; Şi'râ B çıplak gözle görülmeyen, Güneş kütlesinde ama Dünya
büyüklüğünde bir beyaz cücedir. İkisi **50.13 yılda** bir birbirinin çevresinde
döner — insan ömrüne oturan tek gökcismi çevrimi. Necm 49'da "Şi'râ'nın Rabbi"
geçer; Târık sûresi "delip geçen yıldız"dan söz eder.

**Hesap, tabloya bakılarak değil türetilerek yapılır:**
- Şi'râ A'nın ekliptik boylamı, **özdevinim ve presesyon dahil** (Swiss
  Ephemeris sabit yıldız kataloğu). 1900'de 12°43' Yengeç → 2050'de 14°47'
  Yengeç; 150 yılda 2.07° kayar.
- Şi'râ B'nin fazı **Kepler denklemi** ile çözülür: P = 50.1284 yıl,
  e = 0.59142, T = 1994.5715 (Bond ve ark. 2017, HST astrometrisi).
  Doğrulandı: perigeonda r/a = 0.409 = 1−e, apogeonda 1.591 = 1+e.
  Yörünge çok basık olduğu için hız tekdüze değil — çevrim saat değil **nefes**.
- Osmanlı yıldıznâmesi: ebced(ad + anne adı) mod 12 → yıldız burcu ve tabiat.
- Menâzil-i kamer: Şi'râ'nın 28 ay menzilindeki yeri (Tarf).

**Sekiz alan önerisi — her biri AYRI bir ölçümden türer**, aynı sayı farklı
adlarla tekrarlanmaz:

| Alan | Kaynak büyüklük |
|---|---|
| Fikir | ayrıklık r/a (geniş = paralel fikirler, dar = tek eksen) |
| Düşünce | açısal hız dν/dt (hızlı = sıçrayan, yavaş = tek iz) |
| Duygu | doğum fazı çeyreği + Ay–Şi'râ teması |
| Plan | Tarık dönüşüne kalan süre (~50 yaşta doğum fazına dönüş) |
| Alışkanlıklar | v3.0 dayanıklılık ölçüsü |
| Kararlılık | v3.0 havza tayini + bariyer asimetrisi |
| Yaşam tarzı | Şi'râ A'nın evi ve natal temasları |
| Değişim | ayrıklığın türevi (yaklaşıyor / uzaklaşıyor) |

Beşinci ve altıncı alanlar v3.0 topolojisine bağlanır: icat mevcut modele
eklenti değil, devamıdır.

Geliştirme sırasında bir eşzamanlılık tehlikesi yakalandı: ev hesabı için
modül düzeyinde paylaşılan bir liste kullanılmıştı; FastAPI'de eşzamanlı
istekler birbirinin verisini bozardı. Parametreye çevrildi.

## v3.2 — Derin doğrulama

`verify.py`: duman testi "çöküyor mu" diye sorar, bu koşum **"doğru mu"** diye
sorar. Her modülün çıktısı bağımsız bir yoldan yeniden hesaplanır veya
matematiksel bir değişmezle sınanır. **96 kontrol**, `build.sh` içinde deploy
sırasında koşar.

Kapsam: dairesel matematik (antisya evrimselliği, L1 medyan, Rayleigh) ·
efemeris (bağımsız yükselen formülü, Solar Return dönüşü) · alan (F = dΦ/dλ
sayısal türevle, KD küresel tepe, barisentr/denge ayrımı) · heksagram (King Wen
bit tablosu, 11↔12 tersliği) · Human Design (88° güneş yayı 1e-5 hassasiyetle,
64 kapı tam kapsama, 36 kanal) · topoloji (çemberde tepe=çukur, tek küresel
tepe) · Şi'râ (Kepler yakınsaması, r/a=1∓e, **Kepler 2. yasası r²·dν/dt sabit**)
· kompozit simetrisi · ebced (محمد=92, الله=66) · yedi uç durum.

### Denetimin bulduğu

**Kodda hesaplama hatası çıkmadı.** 200 rastgele harita (Türkiye, güney
yarımküre, kutup bölgesi; 1900–2020) üzerinde sıfır istisna, sıfır değişmez
ihlali. Bulunanlar:

| Bulgu | Durum |
|---|---|
| "Barisentr hafif kütleye yakın" savı | **Testim yanlıştı.** Barisentr ağır kütleye yakındır (Güneş–Dünya barisentri Güneş içindedir); hafif kütleye yakın olan L1 denge noktasıdır. İkisi de kodda doğru; sav düzeltildi ve ayrım artık ayrıca sınanıyor. |
| Kepler artığı 3.9e-4 | **Testim yanlıştı.** Çözücünün iç artığı tam 0.0; sapma yayımlanan değerin 4 haneye yuvarlanmasından geliyordu. |
| Şi'râ çıktı hassasiyeti | **Gerçek kusur.** faz ve ayrıklık 4 haneye yuvarlanıyor, bu değerler öneri üretimine akıyordu. 6 haneye çıkarıldı. |

Sinodik dönemler bilinen değerlerle karşılaştırıldı: Jüpiter–Satürn 19.87
(bilinen 19.86), Satürn–Neptün 35.84 (35.87), Satürn–Uranüs 45.21 (45.36),
Uranüs–Neptün 172.9 (171.4) — hepsi %1 içinde.

Astro Pro regresyonu: **0.0000**. Başarım: kişisel 0.80 · sinastri 0.79 ·
kompozit 1.11 saniye.

## v3.2 — Danışan deneyimi, gerçek çark ve derin doğrulama

### Kullanıcıya sızan hatalar giderildi

| Sorun | Sebep | Çözüm |
|---|---|---|
| Ekranda `<think>` bloğu görünüyordu | bazı modeller yanıtı akıl yürütmeyle açıyor | `temizle()` tüm düşünme etiketlerini (think/thinking/reasoning/analysis) siler; kapanmamış blok da kırpılır |
| `502 unknown provider for model gpt-4o-mini` | varsayılan `AI_MODEL` gateway'de yoktu | `AI_MODEL` boşsa gateway'in listesinden ilk model **otomatik** seçilir |
| 02 Hüküm'de kırmızı ham hata kutusu | arayüz önce şablonu basıp sonra ayrı çağrı yapıyordu | kişiselleştirme **sunucuda, analizle aynı istekte** tamamlanır; başarısız olursa şablon sessizce kalır, hata kutusu yok |
| `seas_18.se1 not found` | v3.1'deki tek seferlik efemeris bayrağı, yol kaybolursa kurtulmuyordu | ilk hatada yol zorla yeniden kurulup işlem bir kez tekrarlanır; `/healthz` artık efemeris kipini bildirir |

### Danışman dili

Sistem promptu baştan yazıldı. Artık **mekanizma anlatılmıyor**: "Kara Delik
7. evde olduğu için…" veya "Güneş 3. evde" gibi cümleler yasak. Terim, derece,
ev numarası ve modül adı kullanılmıyor; hesap arka planda yapılıp ekrana yalnız
anlam ve tavsiye yazılıyor. (Danışan doğrudan teknik açıklama isterse istisna.)

### Banner

Marka yazısı **"İsa ile astrolojiye farklı bakış"**, alt metin "Bilgilerini gir,
chat box'ı kullan, dilediğini sor." Rakam bandı koddan kaldırıldı.
Buton: **"Haritamı yorumla"**.

### Alan halkası artık gerçek bir çark

Evler varsayılan açık. **11 hesaplanmış nokta** (Kara Delik, Ak Delik, Berzah,
KRN, Anti-KRN, Vahdet, Süveyda, İcâbet, Noksan, Ayna Ekseni, Şi'râ) çark
üzerinde gezegen gibi konumlanıyor ve gezegenlerle **açı yapıyor**
(`nokta_acilari`; orb, gezegen açılarının %60'ı — türetilmiş noktalara klasik
gelenekte dar orb verilir). Noktaya dokununca konumu, evi ve açıları görünüyor.

Kuşaklar çakışmayacak biçimde yeniden ayrıldı: burç 168–186, hesaplanan noktalar
146–162, gezegenler 106–140, Φ alanı 44–100. Önceki düzende gezegenlerin
görünmez tıklama alanı noktaların üstüne biniyor ve noktalar tıklanamıyordu.

### Derin doğrulama

`verify.py` — **96 kontrol**, `build.sh` içinde deploy sırasında koşar.
Duman testi "çöküyor mu", bu koşum "doğru mu" diye sorar: her modül bağımsız
bir yoldan yeniden hesaplanır veya bir değişmezle sınanır (F = dΦ/dλ sayısal
türevle, Kepler 2. yasası r²·dν/dt sabit, çemberde tepe=çukur, HD 88° güneş
yayı 1e-5 hassasiyetle, kompozit simetrisi, ebced محمد=92 …). 200 rastgele
harita üzerinde sıfır istisna, sıfır değişmez ihlali. Astro Pro regresyonu
**0.0000**.

## v3.3 — İstek denetimi: kendi kuralımı uygulamadığım yerler

v3.2'de "AI mekanizma anlatmasın, yorum versin" kuralını koydum ama üç yerde
kendim uygulamamıştım. Kod üzerinden denetleyince çıktılar:

| Boşluk | Durum |
|---|---|
| **Bölüm analizi talimatları** hâlâ terimle yazılmıştı ("Berzah çatalını aç: iki deniz neyi temsil ediyor", "Φ alanının biçimini yorumla") | 17 bölüm talimatı danışan diline çevrildi; hiçbirinde terim geçmiyor |
| **Sohbet öneri çipleri** terim soruyordu ("Berzahım ne anlatıyor?", "Kara Deliğim nasıl görünüyor?") | Sade sorularla değiştirildi. Terimle sorulunca model terimle cevaplıyordu |
| **İlişki modunda kişiselleştirme yoktu** | Sinastri ve kompozitte de Hüküm/Çatal satırları AI ile doldurulur |

### Denetimin bulduğu iki hesaplama kusuru

**Tautolojik açı.** Nokta–nokta listesinin başında "Kader Rezonansı ☍ Anti-KRN,
orb 0.00" duruyordu. Anti-KRN tanım gereği KRN+180'dir; bu bulgu değil tanımın
tekrarıdır ve listenin başına oturup gerçek bulguları aşağı itiyordu. Tanım
gereği bağlı çiftler artık atlanıyor.

**Izgara artefaktı.** İcâbet ve Noksan 1°'lik ızgarada bulunuyor, yani tam sayı
derecelere yapışıyordu. Çark üzerinde açı hesabına girince bu YAPAY tam açılar
üretiyordu. Her ikisi altın oran aramasıyla alt-derece hassasiyetine çıkarıldı:
İcâbet 314.000 → 313.672, Noksan 176.000 → 175.933; sahte tam üçgen 0.00° →
0.33° oldu.

Ayrıca **nokta–nokta açıları** eklendi (v3.2'de yalnız nokta–gezegen vardı).

## v3.4 — Rektifikasyon aracı ve halka kullanılabilirliği

### Rektifikasyon (`app/rektifikasyon.py`, `POST /api/v1/rektifikasyon`)

Modelin kendi belgesi en zayıf karnını söylüyordu: Berzah kararsız denge
noktasıdır, ±15 dakikadan sonra ev katmanı güvenilmez. Danışanların çoğunun
saati yuvarlaktır. Bu araç saati hayat olaylarından geri çözer.

**Opsiyonel.** Form içinde "Doğum saatimden emin değilim" paneli; kullanıcı
3–6 tarihli olay yazar, hesap arka planda çalışır ve sonuç Hüküm'ün üstünde
görünür.

**Puanlama** — yalnız saate DUYARLI göstergeler: yavaş transitlerin natal
köşelere kavuşum/karşıtlığı, ilerletilmiş Ay ve ASC/MC temasları, ve modele
özgü alan yüklemesi. Puan, açıklanan olay oranının karesiyle çarpılır.

**Geliştirme sırasında bulunan üç kusur:**

| Kusur | Belirti | Çözüm |
|---|---|---|
| **30° örtüşmesi** | 5 açı × 4 köşe deseni 30°'de tekrar ediyor; bozulmuş dört saatin dördü de aynı sahte çözüme (12:42) yakınsadı | Köşe temaslarında yalnız kavuşum/karşıtlık; tekrar 90°'ye (≈6 saat) çıktı, pencere dışına düştü |
| **Çoklu karşılaştırma** | Gerçek tarama 61 aday, surrogate 12 aday üzerinde yapılıyordu; daha çok adaydan alınan azami puan doğal olarak yüksek çıkıp p-değerini şişiriyordu — rastgele tarihlerle 8 denemenin 2'sinde "kesin" deniyordu | İki aşamalı tarama: anlamlılık kaba ızgarada (gerçek ve surrogate aynı aday sayısıyla), saat ince ızgarada |
| **Izgara adımı orbdan büyük** | Kaba adım 12 dk = 3° ASC, orb ise 2°; doğru saat ızgaraya düşmediğinde puanı sulanıyor, p=0.5 gibi saçma değerler çıkıyordu | Adım orba bağlandı (6 dk ≈ 1.5°) |

**Doğrulama.** Bilinen saat (14:30) bozulup geri bulunabiliyor mu: +40, −40,
+75, −75 ve −120 dakika kaydırmalarda **beşinde de 0–1 dakika hatayla** doğru
saat bulundu. Rastgele tarihlerle 10 denemede **sıfır yanlış "kesin"**.
"Kesin" demek için dört şart birden aranıyor: keskinlik ≥ 3.0, p ≤ 0.03,
en az 5 olay, açıklanan olay oranı ≥ 0.8. Sonuç belirsizse **saat
değiştirilmez**. Maliyet: analiz 0.61 → 1.33 saniye.

### Alan halkası

- Gezegene tıklayınca **açıları vurgulanıyor** (diğerleri soluklaşıyor) ve
  gezegen–gezegen ile nokta–gezegen açıları alt panelde listeleniyor
- Retrograd gezegenlerde **℞** işareti
- Katlanabilir **konum tablosu**: 10 gezegen + 11 hesaplanmış nokta, konum, ev
  ve kütle sütunlarıyla

## v3.5 — Giriş sayfası ve rol ayrımı

Girişte iki seçenekli karşılama sayfası: **Yönetici** ve **Misafir**.
Yönetici bütün modüllere erişir (14 bölüm). Misafir analiz modunu seçer,
**haritasını** ve **danışman sohbetini** görür; teknik modül dökümü
gösterilmez (2 bölüm).

### Kısıtlama gerçek, kozmetik değil

Arayüzde bölüm gizlemek kısıtlama sayılmaz — konsoldan gelen JSON okunabilirdi.
Öte yandan sohbetin iyi cevap vermesi analizin tamamına bağlı. Çözüm
`app/oturum.py`:

- Analiz **sunucuda** tutulur (bellek içi, 3 saat ömür, azami 300 oturum)
- Misafire yalnız harita çizimi için gereken alanlar gider: **54 KB → 11 KB**;
  `deneme_modulleri`, `kabzbast_v1_m66_74`, `kadim_katman`, `human_design`,
  `sira_cevrimi`, `alan_topolojisi` hiç gönderilmez
- Sohbet ve bölüm analizi **oturum kimliğiyle** çalışır; sunucu tam bağlamı
  kendi belleğinden okur, böylece misafir eksiksiz danışmanlık alır

### Yönetici parolası

`ADMIN_SIFRE` tanımlıysa "Yönetici" düğmesi parola sorar
(`POST /api/v1/rol-dogrula`); değilse giriş serbesttir ve rol yalnız görünüm
ayrımı olur. Arayüz bunu `/api/v1/rol-bilgi` ile öğrenip parola alanını yalnız
gerekliyse gösterir. **Misafir kısıtlaması parola olmadan da geçerlidir.**

### Yakalanan hata

`blok(1, …)` çağrısında `IMLER[(1-2) % 5]` hesaplanıyordu; JavaScript'te
`(-1) % 5 = -1` olduğu için erişim `undefined` dönüyor ve destructuring
"undefined is not iterable" ile patlıyordu. Misafir görünümü 1'den başladığı
için ilk kez orada ortaya çıktı. Modülo sarmalandı.

## v3.6 — Sızma testi ve güvenlik sertleştirmesi

`pentest.py` zafiyet listesi çıkarmaz, **saldırıyı dener**: 14 test, her biri
gerçek istek atar. İlk koşumda **4 açık** bulundu, hepsi kapatıldı.

| Bulgu | Ağırlık | Çözüm |
|---|---|---|
| Yönetici parolası sınırsız denenebiliyordu (12 deneme de kabul edildi) | YÜKSEK | IP başına 15 dakikada 5 deneme; başarılı girişte sayaç sıfırlanır |
| Metin alanlarında uzunluk sınırı yoktu (60.000 karakterlik ad kabul edildi) | ORTA | `max_length`: ad 80, isim 120, anne 80, model 120, olay 12 kayıt |
| Sağlık ucu API anahtarının ilk 8 karakterini gösteriyordu | ORTA | Yalnız uzunluk bildirilir; önek arama uzayını daraltıyordu |
| İstemci istediği model adını yollayabiliyordu (pahalı model → hızlı kota yakımı) | ORTA | Model gateway listesiyle sınırlanır; izinsizse varsayılana düşer |

Ayrıca bir **raporlama hatası** yakalandı: model kısıtlaması çalışıyordu ama
yanıt *istenen* modeli bildiriyordu, bu yüzden kısıtlamanın çalışıp çalışmadığı
dışarıdan anlaşılamıyordu. Artık gerçekten kullanılan model bildiriliyor.

### Eklenen korumalar

- **Erişim anahtarı** (`ZIC_ERISIM_ANAHTARI`): tanımlıysa arayüz ve API'nin
  tamamı kapanır; `/healthz` açık kalır. Bu, en büyük pratik riski kapatır —
  servis herkese açık bir URL'de duruyor ve her analiz AI kotası harcıyor.
- **Hız sınırı** (`app/limit.py`): parola 5/15dk, AI 30/saat, ağır hesap 60/saat.
- **Zamanlama güvenli parola** karşılaştırması (`secrets.compare_digest`).
- **CORS daraltılabilir** (`CORS_ORIGINS`); varsayılan `*` ama üretimde kendi
  alan adınıza kısılmalı.
- **İstem enjeksiyonu sertleştirmesi**: danışan sorusu `<danisan_sorusu>`
  içine sarılıp açıkça VERİ olarak işaretlenir; sahte etiketler ve rol
  işaretleri girdiden temizlenir; sistem promptuna değiştirilemez gizlilik
  kuralı eklendi.

### Testin dürüstçe söylediği sınırlar

İstem enjeksiyonu testi **sahte gateway** ile yapıldı; sahte sunucu sabit yanıt
döndüğü için sonuç **kesin değildir** ve gerçek modelle yeniden denenmelidir.
Ayrıca erişim anahtarı tanımlanmazsa hız sınırı kötüye kullanımı yavaşlatır
ama engellemez.

## v3.7 — İkinci sızma testi turu

Kullanıcının gönderdiği tarama scriptinden üç test uyarlandı (uçlar bu servisin
gerçek yollarına göre düzeltilerek): CORS ön kontrolü, girdi fuzzing'i ve
eşzamanlı istekle hız sınırı denemesi. **Üç yeni açık** çıktı.

| Bulgu | Ağırlık | Çözüm |
|---|---|---|
| **X-Forwarded-For sahteciliğiyle hız sınırı tamamen atlatılıyordu** — 40 parola denemesi, sıfır engelleme | KRİTİK | İki katman: (1) XFF'ye ancak `ZIC_TRUST_PROXY=1` iken güvenilir ve **en sağdan** okunur; (2) IP'den bağımsız **küresel** parola tavanı (15 dakikada 20) |
| CORS her kaynağa açıktı | ORTA | Varsayılan **kapalı**; arayüz zaten aynı kaynaktan sunuluyor. `CORS_ORIGINS` ile açıkça izin verilir |
| XSS yükü yanıtta kaçışsız yansıyordu | ORTA | Ad/isim/anne alanlarında `<` `>` girdide temizlenir (arayüzdeki `esc()` üstüne ikinci katman) |

### XFF düzeltmesinin mantığı

Önceden başlığın **en soldaki** değeri alınıyordu. O değeri istemci kendisi
yazar. Doğrusu en sağdan saymaktır: zincirin sağ ucundaki değerler isteği
gerçekten gören güvenilir vekiller tarafından eklenir, istemcinin uydurdukları
sola itilir.

Ama bu tek başına yetmez — vekil yoksa sahte başlık tek eleman olarak kalır ve
yine geçer. Bu yüzden XFF'ye yalnız `ZIC_TRUST_PROXY=1` verildiğinde güvenilir.
Üstüne, IP tabanlı her sınırın ilkece atlatılabilir olduğu kabul edilerek
parola için **kimlikten bağımsız küresel bir tavan** kondu; başlık sahteciliği
onu etkilemez. Sonuç: aynı saldırıda 40 istekten 25'i engellendi.

### Girdi fuzzing'i

Sekiz kötü girdi denendi (takvimde olmayan gün, ay 13, yıl 999999, enlem 999,
`None` boylam, geçersiz saat dilimi, XSS, 1e308): **hiçbiri 500 üretmedi**,
hepsi temiz 422 döndü.

### Hız sınırları artık ayarlanabilir

`ZIC_LIMIT_AUTH`, `ZIC_LIMIT_AI`, `ZIC_LIMIT_AGIR`, `ZIC_LIMIT_AUTH_KURESEL`
biçiminde `izin/saniye`. `0/0` kovayı kapatır — yalnız test için.

**Sonuç: 26 testin 26'sı kapalı.**

## v3.8 — Kod içi güvenlik taraması ve profesyonel çark

### Statik tarama (HTTP testinin göremediği yerler)

- `eval`, `exec`, `pickle`, `subprocess`, `os.system`, `shell=True`: **yok**
- Dosya yolları tamamen sabit; kullanıcı girdisiyle yol kurulmuyor → yol
  aşımı yok
- Dışarıya giden tek istek AI gateway'ine; adres **yalnız ortam
  değişkeninden** geliyor, kullanıcı girdisinden değil → SSRF yok
- **ReDoS**: girdi temizleme ve düşünme bloğu ayıklama düzenli ifadeleri
  20.000 karakterlik saldırı yükleriyle denendi — en kötü durum 145 ms,
  geri izleme patlaması yok
- **Eşzamanlılık**: swisseph bir C kütüphanesi ve iş parçacığı güvenliği
  garanti değil. 12 iş parçacığı, aynı girdiyle 24 eşzamanlı istek atıldı:
  **24'ü de birebir aynı sonucu** verdi. (Serileşme nedeniyle verim sınırlı:
  24 istek 17 saniye.)

### Çark profesyonelleştirildi

| Ekleme | Ayrıntı |
|---|---|
| **Burç glifleri** | Üç harfli kısaltma yerine ♈♉♊… |
| **Derece taksimatı** | 360 çizgi: 1° kısa, 5° orta, 10° uzun |
| **Derece etiketleri** | Ayrı katman (varsayılan kapalı, çark kalabalıklaşmasın) |
| **Açı ızgarası** | Profesyonel üçgen matris; sert açılar kırmızı, akış turkuaz, kavuşum siyah; her hücrede orb |
| **SVG dışa aktarım** | Çark 1000×1000 vektör olarak indirilir, beyaz zemin gömülü |

Bu turda bir yama **sessizce uygulanmamıştı** (hedef metin önceki düzenlemede
değişmişti) ve derece katmanı çalışmıyor görünüyordu; doğrulama bunu yakaladı,
düzeltildi.

## v3.9 — HUDÛD-I FELEK: deklinasyon katmanı ve küresel alan

Modelin bugüne kadarki kör noktası: Φ alanı **yalnız boylamda** hesaplanıyordu.
Gökyüzü iki boyutludur ve bu iki hataya yol açıyordu:

- Boylamda 3° yakın ama deklinasyonda 45° uzak iki cisim "kavuşum" sayılıyordu;
  gökküre üzerinde 45° ayrıdırlar.
- Boylamda hiç açı yapmayan ama aynı deklinasyonda duran iki cisim
  "ilişkisiz" sayılıyordu; klasik gelenekte bu kavuşum kadar güçlüdür.

**A · Paralel / karşıt-paralel.** Aynı deklinasyon (paralel) ya da eşit
büyüklükte zıt işaret (karşıt-paralel), orb 1°. Asıl değer **gizli bağlarda**:
boylamda hiçbir açı yapmayan ama deklinasyonda bağlı çiftler. Test haritasında
**5 gizli bağ** çıktı — model bunları şimdiye kadar hiç görmüyordu.

**B · Hudûd dışı.** Deklinasyonu tarihe ait gerçek eğikliği aşan cisim,
Güneş'in hiç ulaşamadığı bir enlemdedir: iki denizin de dışına taşmış bir
kapasite. Test haritasında Ay **+26.42°** — eğikliğin 2.98° dışında.

**C · Küresel alan Φ(α, δ).** Alan gerçek açısal ayrımla gökküre üzerinde
kurulur (`cos d = sinδ₁sinδ₂ + cosδ₁cosδ₂cosΔα`). Küresel Kara Delik boylam
okumasından saparsa tek boyutlu okuma yanıltıcıdır. Küresel Berzah, iki baskın
kütleyi birleştiren büyük çember üzerindeki en düşük Φ noktasıdır.

Sapma haritadan haritaya çok değişiyor: test setinde 1990 haritasında **0.19°**
(boylam okuması doğru), 1975 haritasında **18.7°** (boylam okuması yanıltıcı).

### Geliştirme sırasında düzeltilen üç kusur

| Kusur | Çözüm |
|---|---|
| **Güneş "hudûd dışı" çıkıyordu** — gündönümünde doğanlarda Güneş'in deklinasyonu eğikliğe tam eşit oluyor, kayan nokta hatası onu dışarı atıyordu. Fiziksel olarak imkânsız: eğiklik zaten Güneş'in azami deklinasyonudur | Güneş yapısal olarak hariç; ayrıca 0.05° pay ve 0.5° altı aşımlar "sınırda" olarak ayrı işaretleniyor |
| **Sağ açıklık atılıyordu** — ekvatoral çağrı zaten yapılıyor ama yalnız deklinasyon saklanıyordu; küresel alan için RA şart | `BodyPos.ra` eklendi |
| **Büyük çember tekilliği** — iki baskın kütle 180°'ye yakınsa aralarından sonsuz büyük çember geçer, eşik tanımsızdır | 179° üstünde eşik bildirilmiyor, sebep açıkça yazılıyor |

Sabit 23.44 kullanılmıyor: eğiklik tarihe göre hesaplanıyor (yüzyılda ~0.013°
azalır ve hudûd sınırını doğrudan belirler).

Çarkta yeni **Deklinasyon** katmanı: paralel bağlar merkezden geçen yaylarla
(gizli olanlar kalın), hudûd dışı cisimler dış halkada mor çemberle.

40 rastgele harita (dünya geneli, 1930–2020): sıfır istisna, sıfır değişmez
ihlali. Analiz süresi 0.67 → 0.80 saniye.

## v4.0 — Model yedekleme, klasik çark düzeni, misafir tasarımı

**Plan kapalı model hatası.** Gateway listesinde planın erişemediği modeller
vardı ve ilk sıradaki seçiliyordu; kullanıcı ekranda ham `403 "Model MiniMax-M2
is not available on the tok5 plan"` görüyordu. Artık 403 permission_error alan
model **kara listeye** alınıp sıradaki deneniyor (en fazla 6 aday). Model
listesinde erişilemeyenler `(plan kapalı)` etiketiyle ve seçilemez olarak
görünüyor. `ai-health` gerçekten çalışan modeli ve erişilemeyenleri bildiriyor.

**Çark klasik düzene geçti.** Önceden 0° Koç tepede sabitti — bu astronomik bir
çizim, astrolojik değil. Artık **Yükselen solda** (saat 9 yönü), **MC yukarıda**
ve 1. ev doğrudan Yükselen'den başlıyor; evler saat yönünün tersine ilerliyor.
Dört köşe (ASC/IC/DSC/MC) çizgi ve etiketle işaretli.

**Noktalara tıklama.** Gezegenlerde olan davranış hesaplanmış noktalara da
geldi: tıklayınca o noktanın açıları çarkta vurgulanıyor, diğerleri soluklaşıyor.

**Yönetici girişi.** Artık seçilince **daima parola soruyor**. Sunucuda
`ADMIN_SIFRE` tanımlı değilse bunu açıkça söylüyor — önceden sessizce içeri
alıyordu ve koruma var sanılıyordu.

**Misafir tasarımı.** Karşılama bloğu eklendi: haritanın hazır olduğu bilgisi,
üç kutuluk özet (tekrar eden tema / dile gelen yan / karar eşiği) ve ne
yapabileceğini anlatan kısa yönerge.

**Prompt.** "Haritanızda", "verilere göre", "analiz gösteriyor ki" gibi
girizgâhlar yasaklandı; hesabın varlığından bile söz edilmiyor. Yasaklı kelime
listesi eklendi (harita, gezegen, burç, ev, derece, açı, transit, modül,
deklinasyon ve bütün gezegen adları).

Ortam değişkenlerinin tamamı `RENDER_ENV.txt` dosyasında.

## v4.1 — Misafir: bütün kategoriler, sıfır teknik terim

Misafir artık **on kategoriyi de** görüyor; hiçbirinde terim geçmiyor.

| İç modül | Misafirin gördüğü |
|---|---|
| Hüküm (KD/AD/Berzah) | Tekrar eden döngün |
| Çatal | Şu an neyin arasındasın |
| Kütleler | Seni yöneten eğilim |
| Alan topolojisi | Değişime direncin |
| Hudûd-ı Felek | Görünmeyen bağların |
| Şi'râ Çevrimi | İçinde bulunduğun dönem |
| Kabz / Bast | Toparlanma mı, açılma mı |
| 16 deneme modülü | Karakter dokun |
| Kadim katman | Hayat çağın |
| Human Design | Doğal karar biçimin |

**Tek çağrı, on yorum.** Kategori başına ayrı AI isteği 10 çağrı demekti ve
kotayı hızla yakardı. Hepsi tek istekte, JSON şemasıyla üretiliyor
(`misafir_yorumlari`). Derinlik isteyen kullanıcı kartın altındaki
"Bu konuyu derinleştir" düğmesiyle yalnız o kategori için ek çağrı yapıyor.

**Terim sızıntısı üç yerden kapatıldı:**
1. Prompt — yasaklı kelime listesi (harita, gezegen, burç, ev, derece, açı,
   transit, Human Design ve bütün gezegen adları)
2. Kategori başlıkları — sunucudan tek kaynaktan geliyor
3. Çark — misafirde efsane ve nokta adları sadeleşiyor: "Kara Delik" →
   "Asıl sebep", "Vahdet" → "Toplanma noktası", "Hudûd dışı" → "Sınır dışı"

Doğrulandı: misafir görünümünde `Kara Delik`, `Ak Delik`, `Berzah`,
`Human Design`, `deklinasyon`, `Kabz`, `Hudûd` kelimelerinin **hiçbiri
geçmiyor**; yönetici görünümünde hepsi yerinde.

## v4.2 — Çark: çift çark, tam ekran, denge dağılımı

**Çift çark (bi-wheel).** Profesyonel yazılımların standardı: içeride natal,
dışarıda ikinci bir harita. Üç seçenek — Kapalı · **Bugünkü gökyüzü** ·
**Solar Return**. Dış halka zodyak bandının dışına çiziliyor, böylece iç
çarkın geometrisi hiç bozulmuyor; dış cisimler mavi, geri hareketteler
kırmızı. Transit kipinde dış–iç açı çizgileri de geliyor (sunucuda
`transit_konumlari` + `capraz_acilar_basit`, hafif tutuldu).

**Tam ekran.** Çark mobilde küçük kalıyordu. "⤢ Büyüt" düğmesi çarkı ekranı
kaplayacak biçimde açıyor; katman değişiklikleri açıkken de yansıyor.
Esc veya dışarı tıklama kapatıyor.

**Denge dağılımı.** Her profesyonel haritada bulunan üç ölçü: unsur (ateş /
toprak / hava / su), nitelik (öncü / sabit / değişken) ve yarımküre (iç–dış,
doğu–batı). Klasik yöntem cisim sayar; burada **kütleyle ağırlıklandırılıyor**
çünkü bu modelde her cismin ağırlığı farklı — ham sayım parantezde veriliyor.

### Yakalanan iki hata

**Sınıf çakışması.** Çift çark düğmelerine verdiğim `.cift` sınıfı, Çatal
bölümündeki iki sütunlu yerleşimin sınıfıyla aynıydı; seçici Çatal içeriğini
de yakalıyordu. `.ccark` olarak ayrıldı.

**`HALKA_SETI[NaN]`.** Yeni düğmeleri harita seçicisiyle aynı şeride koyunca
`.harita` sınıfına bağlı olay dinleyicisi onları da yakalıyor, `data-h`
olmadığı için `+undefined = NaN` çıkıyor ve çark çizilmiyordu. Dinleyici
artık yalnız `data-h` taşıyanlara bağlanıyor.

Ayrıca `transit` alanı sonuç sözlüğüne eklenmemişti (hesaplanıyor ama
gönderilmiyordu) — bu turda üçüncü kez aynı tuzağa düşüldü, doğrulama yakaladı.

## v4.3 — Dünya geneli doğum yeri, erişim anahtarı hatası, AI senkronizasyonu

### İl/ilçe neden çalışmıyordu

Yerelde çalışıyordu; sorun dağıtımdaydı. **Erişim anahtarı açıkken arayüzün
hiçbir `fetch` çağrısı anahtarı taşımıyordu.** Sayfaya `?anahtar=…` ile
giriliyor ama tarayıcı bu sorgu dizgesini sonraki isteklere aktarmaz. Sonuç:
`yerler`, `rol-bilgi`, `tz-check` ve analiz istekleri **401** alıyor, il
listesi boş kalıyordu. Anahtar artık bir kez okunup her isteğe
`x-zic-anahtar` başlığı olarak ekleniyor.

### Dünya geneli doğum yeri

**244 ülke · 34.695 yer**, üç kademeli seçim: Ülke → Bölge/İl → Şehir/İlçe.

- Kaynak `geonamescache` (GeoNames türevi); Türkiye için geonames'in 429
  şehri yerine **kendi 81 il / 1037 ilçelik veri setimiz** kullanılıyor
- Her kayıtta **saat dilimi** var: şehir seçilince otomatik ayarlanıyor.
  Kullanıcının saat dilimini elle bulma derdi bitti (ABD → America/Phoenix,
  Japonya → Asia/Tokyo)
- Veri **ülke başına ayrı dosyada** (`/api/v1/ulke/{kod}`); toplam 2.3 MB
  tek seferde inmiyor, yalnız seçilen ülke indiriliyor. Dizin 13 KB.

Doğrulandı: 244/244 dosya mevcut, 34.695 kaydın hepsinde saat dilimi var,
geçersiz koordinat yok.

### AI senkronizasyonu

**Öncelik özeti.** Bağlam 10 KB'a yaklaşmıştı ve model uzun metni tarayarak
okuyabiliyor. En belirleyici beş bulgu artık **bağlamın en başında** numaralı
listede.

**Yaş bağlamı.** Tavsiyenin en çok değiştiği değişken eksikti: 25 yaşındaki
birine "kariyerini yeniden kur" demekle 55'indekine demek aynı şey değil.
Yaş ve çağ (kuruluş / inşa / dönüm / hasat) bağlama eklendi.

**Terim sızıntısı denetimi.** Prompt yasaklıyordu ama modeller kuralı
çiğniyordu. Artık üretim **sonrası** denetleniyor; sızarsa uyarı sertleştirilip
bir kez daha üretiliyor. Misafir kategorilerinde sızdıran kart atlanıyor.

Denetleyici geliştirilirken bir hata yakalandı: tam kelime araması Türkçe
**ünsüz yumuşamasını** kaçırıyordu — "Kara Delik" → "Kara Deliğin" olunca
eşleşme kayboluyordu. Kök araması ve aksan normalizasyonuna geçildi;
sekiz test vakasının hepsi doğru sınıflandırılıyor.

## v4.4 — Bütünsel sentez, Davison, deklinasyon sinastrisi

### AI: bütünsel okuma

Sistemin her bölümü kendi başına doğruydu ama **hiçbiri diğerini bilmiyordu**;
danışan parçaları kendisi birleştirmek zorundaydı. **Bütünsel okuma**
(`POST /api/v1/sentez`) bir danışmanın seans sonunda yaptığı şeyi yapar:
merkezî örüntü → şu anki görünümü → **bulgular arasındaki çelişki** → hafife
alınan güç → önümüzdeki dönem → bu haftanın tek adımı. Çelişki saklanmıyor:
farklı yönler farklı şey söylüyorsa bu bir hata değil, kişinin gerçek gerilimi.

Yönetici sürümünde terim serbest ve hangi bulgunun hangi sonuca götürdüğü
gösteriliyor (denetlenebilsin); misafir sürümünde terim yasak.

**Sohbet artık ekranda ne yazdığını biliyor.** Kategori kartları ve sentez
metni sohbete `gosterilen` olarak geçiriliyor; model aynı cümleleri tekrar
etmek yerine üzerine ekliyor.

### İlişki: Davison ve deklinasyon

**Davison haritası** kompozitin tamamlayıcısıdır ve karıştırılmamalıdır:

| | Kompozit | Davison |
|---|---|---|
| Nedir | İki haritanın **konumlarının** orta noktası | Zaman ve mekân ortasında kurulmuş **gerçek** harita |
| Anlamı | İlişkinin soyut portresi — "bu ilişki nedir" | O an gökyüzü gerçekten öyleydi — "ne zaman ne yapar" |
| Transit | Tartışmalı | Uygulanabilir |

Coğrafi orta nokta **büyük çember üzerinde** hesaplanıyor. Aritmetik ortalama
yanlıştır: 179° ve −179° için 0° verir, doğrusu 180°'dir. Sapma yakın
konumlarda ihmal edilebilir, uzak çiftlerde yüzlerce kilometre olur.

**Deklinasyon sinastrisi.** İki kişi arasındaki paralel ve karşıt-paralel
temaslar. Asıl değer **gizli bağlarda**: boylamda hiç açı yapmayan, dolayısıyla
klasik sinastride görünmeyen ama aynı deklinasyon kuşağındaki çiftler. Test
çiftinde 4 gizli bağ çıktı. "Aramızda açıklayamadığımız bir şey var" denen
şeyin ölçülebilir karşılığı çoğu kez budur.

### Kritik hata: silinmiş ilişki dalı

Sinastri ve kompozit **hiç çizilmiyordu**. Sebep: v4.1'de misafir görünümü
yazılırken `ciz()` içindeki ilişki dalı yanlışlıkla silinmiş; iki mod da
kişisel çiziciye düşüp `d.berzah_v2` bulamadığı için patlıyordu.

Fark edilmemesinin sebebi ikinci bir hataydı: **hata sessizce yutuluyordu.**
Başarı yolunda durum kutusu gizleniyor, çizim sonradan patlayınca hata o gizli
kutuya yazılıyor ve ekranda hiçbir şey görünmüyordu. Artık hata daima tekrar
görünür kılınıyor.

## v4.5 — Promptların profesyonelleştirilmesi

### Denetimin bulduğu

Promptlar ölçüldü; üç gerçek boşluk çıktı:

| Boşluk | Ağırlık |
|---|---|
| **Sentez ve kişiselleştirme promptlarında tıbbî/ölüm sınırı YOKTU** — üstelik sentez en uzun ve en etkili çıktı | Kritik |
| **Belirsiz veriyle ne yapılacağı hiç yazmıyordu** — model her katmana eşit güveniyordu | Yüksek |
| Toplam **3 örnek** (few-shot); kurallar anlatılıyor ama gösterilmiyordu | Orta |

Ayrıca dört yüzey (sohbet, kartlar, sentez, kişiselleştirme) promptlarını
birbirinden bağımsız yazdığı için üslup ve kurallar ayrışmıştı.

### Çekirdek yapı

Ortak kurallar tek kaynağa toplandı; her yüzey yalnız kendi farkını ekliyor:

- `CEKIRDEK_PERSONA` — kim olduğu
- `CEKIRDEK_SINIR` — tıbbî, ömür/ölüm, hukukî-finansal, kriz, üçüncü kişi
  sınırları. **Artık dört promptun dördünde de var**
- `CEKIRDEK_USLUP` — çeviri kokmama, falcı ağzı yasağı, **genel geçer laf
  yasağı** ("Duygusal bir insansın" gibi herkese uyan cümleler)
- `CEKIRDEK_BELIRSIZ` — güven notuna uyma zorunluluğu

Prompt uzunlukları 130–392 kelimeden 361–512'ye çıktı; artış tamamen sınır,
üslup ve örneklerden geliyor.

### Güven notu — promptu veriye bağlayan katman

En değerli ekleme. Model artık **veri kalitesini biliyor**; bu bilgi zaten
hesaplanıyordu ama modele hiç söylenmiyordu:

- Doğum saati tam ya da buçuksa → "büyük olasılıkla tahmin, ev iddialarında
  temkinli ol"
- Rektifikasyon "belirsiz" ise → "ev ve köşe temelli iddiada bulunma"
- Berzah "alan bozucu" ise → "çatalı kesin ikilem gibi değil eğilim gibi anlat"
- Alanda yapısal özellik yoksa → "tek tema etrafında konuşma"
- Küresel sapma >15° ise → "kavuşum temelli yorumları zayıflat"

Doğrulandı: 14:30 doğumda 2 uyarı, 14:37 doğumda 1 uyarı üretiliyor.

### Örnekler

Her yüzeye iyi/kötü örnek çifti eklendi. En önemlisi "herkese uyan cümle"
karşıtlığı:

> ✗ "Duygusal ve sezgisel birisiniz, iç dünyanız zengindir."
> ✓ "Bir şeyi hissettiğin anda söylemiyorsun, üç gün taşıyorsun; söylediğinde
>    de olduğundan sert çıkıyor. Sorun hissetmende değil, bekletmende."

## v4.6 — CHRONO-GRAVITRON (yalnız yönetici)

Gravitasyonel rezonans ve kuantum izdüşüm matrisi konsepti, **üç katmana
ayrılarak** uygulandı. Bu ayrım modülün merkezindedir ve arayüzde de görünür:

| Etiket | Ne demek |
|---|---|
| **[Ö] ölçülen** | Gerçek fizik, doğrulanabilir sayı. Başka bir efemerisle hesaplayan aynı sonucu bulur. |
| **[H] hesaplanan** | Ölçülenin üzerine kurulan matematik. Doğru; neyi temsil ettiği model seçimi. |
| **[B] benzetme** | Fiziksel büyüklükle insan hâli arasındaki bağ. İddia değil, modelin dili. |

### [Ö] Gelgit ivmesi — ve modülün kendi itirafı

`a = 2·GM·R⊕/d³` ile her cismin Dünya yüzeyindeki gerçek gelgit ivmesi.
Sonuç **gizlenmiyor, merkeze konuyor**: Ay ve Güneş toplam gelgitin
%99.9998'ini oluşturuyor; en güçlü gezegen (Jüpiter) Ay'ın yalnız
**%0.00015'i** kadar. Doğum odasındaki ebenin çekimi Mars'ınkinden büyüktür.

Bu yüzden modül fiziksel bir NEDEN öne sürmüyor; ölçülen büyüklükleri bir
**ağırlıklandırma ölçüsü** olarak kullanıyor.

### [Ö] Barisentrik dinamik

Güneş'in Güneş Sistemi ağırlık merkezi etrafındaki gerçek hareketi
(0–2.2 güneş yarıçapı, ağırlıkla Jüpiter ve Satürn sürer).

### [H] İzdüşüm matrisi

ρ = ⟨|ψ(t)⟩⟨ψ(t)|⟩ zaman ortalamalı yoğunluk operatörü; saflık Tr(ρ²),
von Neumann entropisi, etkin kip sayısı. Hermityen özdeğerler 2N×2N gerçek
simetrik gömme ile çözülüyor.

**İki kez düzeltildi:** ilk sürümde ağırlık olarak ortalama gelgit
kullanılıyordu ve Ay+Güneş %99.99'u tuttuğu için durum iki boyuta çöküyordu
(özdeğerler `[0.74, 0.26, 0, …]`). Ay/Güneş çıkarılınca bu kez Jüpiter tek
başına baskın çıkıp rank 1 oldu (`[1.0, 0, …]`). Çözüm: ağırlık artık
**ortalama değil, pencere içindeki DEĞİŞKENLİK**. Sorulan şey "kim gerçekten
bir şey değiştiriyor" — Jüpiter'in ortalaması büyük ama otuz günde kımıldamaz;
Venüs ve Merkür oynar. Ağırlıklar dengelendi, matris gerçekten karışık oldu.

### [H] Rezonans spektrumu — fizikle doğrulandı

Kaba bir dönem ızgarası yerine **gerçek sinodik dönemler** deneniyor.
En güçlü dönem **Venüs sinodik (583.9 gün)** çıktı — fiziğin öngördüğü tam
olarak bu: Venüs uzaklığı 0.27–1.73 AB arasında 6.4 kat değişir, gelgit 1/d³
ile 265 kat oynar. Model doğru fiziği geri buluyor.

### Uygulanmayanlar ve sebebi

Konseptteki **donanım** (lazer interferometre Q-Astrolabe, biyosensör) ve
**anti-faz EM/akustik yayın** uygulanmadı: bunlar fiziksel cihazlardır, bir web
servisi bunları yapamaz ve yapıyormuş gibi göstermek yanlış olur.

**Orch-OR** (mikrotübül kuantum bilinç) kuramı tartışmalıdır; mekanizma olarak
kullanılmadı. Yalnız tutarlılık ölçen matematiksel çerçeve (yoğunluk
operatörü) ödünç alındı.

Modül **yalnız yönetici** görünümünde; misafire hiç gönderilmiyor. Tıbbî
amaçla kullanılamaz. 15 rastgele harita: sıfır istisna, sıfır değişmez ihlali.

## v4.7 — Yeni uçların sızma testi, yazdırma ve kullanım kolaylıkları

### Sızma testi: yeni uçlar

v3.7'den sonra dört yeni uç eklenmişti (`sentez`, `ulke/{kod}`,
`rektifikasyon`, `misafir-kategoriler`) ve sızma testi bunları hiç görmemişti.
On yeni test eklendi; **36 testin 36'sı kapalı**.

En kritik olan `/api/v1/ulke/{kod}`: dosya adı kullanıcı girdisinden kuruluyor,
yani klasik yol aşımı adayı. Denenen yükler ve sonuçları:

| Yük | Sonuç |
|---|---|
| `../../../etc/passwd` | 404 |
| `..%2F..%2Fetc%2Fpasswd` | 404 |
| `TR%2F..%2F..%2Fmain` | 404 |
| `....//etc/passwd` | 404 |
| `%00TR` | 200 (TR'ye süzülüyor) |
| `TRX` | 200 (iki karaktere kırpılıyor) |

Harf dışı karakterlerin süzülmesi ve iki karaktere kırpma yol aşımını
yapısal olarak imkânsız kılıyor. Oturum kimliğinin tek karakteri
değiştirildiğinde de 410 dönüyor.

### Yazdırma / PDF

Danışmanın danışana verebileceği bir şey yoktu. `@media print` kuralları
eklendi: form, düğmeler, katman araçları ve sohbet çıktıdan çıkarılıyor;
bloklar sayfa ortasından bölünmüyor; başa danışan adı, doğum anı ve ev
sistemi yazılıyor. Ek bağımlılık yok — tarayıcının "PDF olarak kaydet"
seçeneği kullanılıyor.

### Aşamalı ilerleme

Analiz 0.8–13 saniye sürebiliyor ve tek bir sabit cümle görünüyordu. Artık
aşamalar akıyor: "Efemeris okunuyor…" → "Alan taranıyor…" → "Eşik
hesaplanıyor…" → "Yorum yazılıyor…". Rektifikasyon açıkken kendi aşamaları
gösteriliyor.

### Son yerin hatırlanması

Danışman günde birkaç harita giriyor; her seferinde ülke, bölge, şehir ve
saat dilimini baştan seçmek gereksiz zaman kaybıydı. Yalnız **form
tercihleri** cihazda saklanıyor — danışan verisi değil, sunucuya hiçbir şey
gitmiyor.

### Erişilebilirlik

Durum kutusu `role="status"` ve `aria-live` ile ekran okuyuculara bildiriliyor;
giriş ve tam ekran perdeleri `role="dialog"`; klavyeyle gezinenler için
`:focus-visible` odak halkası; `prefers-reduced-motion` saygı görüyor.

### Yakalanan hata

Kopyalama işlevini eklerken `async async function` oluştu — zaten `async`
olan bir tanımın önüne bir tane daha yazılmıştı. Sözdizimi hatası tüm
betiği çökertiyor, sayfa hiç açılmıyordu. Tarayıcı testi yakaladı.

## v4.8 — Mobil kullanım: 35 ekrandan 6 ekrana

### Ölçüm önce yapıldı

Tahmin etmek yerine 390×844 ekranda ölçüldü:

| Ölçü | Önce | Sonra |
|---|---|---|
| Toplam sayfa | **35.1 ekran boyu** | **5.8 ekran** |
| 44 px altı dokunma hedefi | **68 öge** | **19 öge** |
| En uzun bölüm | 5759 px = 6.8 ekran | katlanabilir |

### Katlanabilir bölümler

Bölüm başlıkları artık düğme: dokununca açılıp kapanıyor. Dar ekranda (≤820 px)
ilk bölüm ve danışman açık başlar, kalan 15'i kapalı. Geniş ekranda hepsi açık
kalır — masaüstünde kaydırma sorun değil, kapalı başlamak orada engel olur.

Gezinme şeridine **"Tümünü aç / kapat"** eklendi. Tümü açıldığında yine 35.9
ekran: hiçbir içerik kaybolmuyor, yalnız istendiğinde görünüyor.

Başlıklar `role="button"`, `tabindex="0"` ve `aria-expanded` taşır; Enter ve
boşluk tuşuyla da çalışır. Başlıktaki AI düğmesine dokunmak katlamayı
tetiklemez.

### Dokunma hedefleri

`pointer:coarse` altında katman düğmeleri, harita seçicileri, gezinme
bağlantıları, öneri çipleri ve form alanları en az 44–46 px yüksekliğe
çıkarıldı. Kalan 19 öge çark içindeki SVG glifleridir; onların kendi görünmez
tıklama alanı zaten var.

### Sızma testi

**36/36 kapalı.** Bu turda iki test "açık" göründü ama sebebi sunucunun koşum
ortasında düşmesiydi. Bir başka yanlış alarm kendi hız sınırımdı: arka arkaya
iki pentest koşumu auth kotasını tüketip sonraki testin girişini 429'a
düşürüyor. Test altyapısının kendi gürültüsünü gerçek bulgudan ayırmak gerekti.

## v4.9 — Veri girişi denetimi: sessiz başarısızlık giderildi

Her girdi yolu tek tek sınandı: her alan değiştirilip `girdiTopla()` çıktısının
gerçekten değişip değişmediği ölçüldü, sinastride ikinci kişinin verisinin
sunucuya doğru gidip gitmediği ağ isteğinden okundu, rektifikasyon olay
satırları eklenip silinerek denendi.

**Çalışanlar:** ikinci kişi formunun tamamı (Almanya seçilince koordinat ve
`Europe/Berlin` doğru gidiyor), rektifikasyon satırları (ekle/sil/topla),
sohbet gönderisi, model seçici, ek katmanlar.

### Bulunan hata: sessiz başarısızlık

Zorunlu bir alan boşken **"Haritamı yorumla" düğmesi hiçbir şey yapmıyordu.**
Ne istek gidiyor, ne mesaj çıkıyordu — kullanıcı tıklıyor, ekran duruyordu.
Sebep: tarayıcının kendi `required` doğrulaması gönderimi engelliyor ama
uyarısını görünmeyen bir alanın yanında gösteriyordu. Üstelik `girdiTopla()`
bu durumda çöp üretiyordu: `year: 0`, `hour: 0`, `lat: null`.

Çözüm: forma `novalidate` eklendi ve doğrulama kendi kodumuza alındı. Artık
her alan gönderimden önce sınanıyor, eksik olan kırmızıya boyanıyor,
kapalı bir panelin içindeyse panel açılıp alana odaklanılıyor.

| Senaryo | Mesaj |
|---|---|
| Boş tarih | "Doğum tarihi alanı boş." |
| Boş tarih + saat | "Doğum tarihi, Doğum saati alanları boş." |
| Enlem 999 | "Enlem geçersiz." |
| Yıl 1500 | "Doğum yılı 1800–2400 arasında olmalı." |
| Sinastride B eksik | "İkinci kişi — Doğum tarihi alanı boş." (odak `tarih2`'ye gider) |

### Bulunan hata: "[object Object]"

Sunucu doğrulama hatası verdiğinde ekranda **`Hesaplanamadı: [object Object]`**
yazıyordu. FastAPI 422 yanıtında `detail` bir dizidir; doğrudan metne
çevrilince bu çıkıyor. Artık alan adı ve sebep Türkçeye çevriliyor; 401, 410,
429 ve 503 için de anlaşılır karşılıklar var.

## v5.0 — Kritik regresyon: sohbet iki sürümdür bozuktu

### Bulunan hata

**Danışman sohbeti v4.5'ten beri her istekte HTTP 500 veriyordu.**

Sebep: v4.5'te promptlar `_cekirdek()` yapısına taşınırken `_girdi_temizle`
işlevi — danışan sorusunu istem enjeksiyonuna karşı temizleyen işlev —
yanlışlıkla silindi. `danisman_yaniti` onu çağırmaya devam etti ve her
çağrıda `NameError` fırlattı.

Fark edilmemesinin sebebi ürkütücü: **hiçbir mevcut test bunu yakalayamazdı.**

| Denetim | Sonuç |
|---|---|
| `py_compile` | ✓ temiz — ad çözümlemesi çalışma anında yapılır |
| `verify.py` (96 kontrol) | ✓ 96/96 geçti — hesaplama katmanını sınıyor, AI'yi değil |
| `audit.py` | ✓ istisna yok |
| `smoke_test.py` | ✓ sistem ayakta |
| `pentest.py` | ✓ 36/36 — sohbetin 500 vermesi güvenlik açığı değil |

Tarayıcı testinde "3 balon" görünüyordu; üçüncüsü aslında hata baloncuğuydu.

### Çözüm: tanımsız ad tarayıcısı

`adtarama.py` her modülü ayrıştırıp fonksiyon gövdelerindeki serbest adları
modülün gerçek ad alanıyla karşılaştırır. Kapsam zincirini izler: iç içe
fonksiyonlar dış fonksiyonun yerellerini görebildiği için yalnız **hiçbir
kapsamda bulunmayan** adlar bildirilir.

Araç, hata kasten geri konarak doğrulandı:

```
py_compile      → ✓ TEMİZ (göremiyor)
verify.py       → 96 geçti, 0 kaldı (göremiyor)
adtarama.py     → ✗ danisman_yaniti() satır 1197 → _girdi_temizle
```

`build.sh` içine eklendi; artık her dağıtımda koşuyor.

### Ayrıca

Dört AI ucunun dördü de (sohbet, bölüm analizi, sentez, kişiselleştirme)
uçtan uca sınandı ve 200 dönüyor. Üç analiz modu (kişisel 17 bölüm, sinastri
7, kompozit 6), çift çark, tam ekran, katlama ve bölüm AI'si tarayıcıda
doğrulandı.

## v5.1 — Ön-kayıt defteri: sistemin ilk ölçüm katmanı

Dört icat eklendi ve hiçbirinin **işe yarayıp yaramadığı** bilinmiyordu.
`app/defter.py` bunu tersine çevirir: tahmin **olay olmadan önce** yazılır,
olasılık verilir, tarihi konur ve **kilitlenir**; sonuç geldiğinde puanlanır.

### Bütünlük

Tahmin metni ve olasılık oluşturulurken SHA-256 özeti alınır; sonuç
işaretlenirken yeniden hesaplanıp karşılaştırılır. Uyuşmazsa kayıt "bozulmuş"
işaretlenir ve **puanlamaya girmez**. Kurşun geçirmez değildir — amaç kötü
niyetli saldırıyı değil, **kendi kendini kandırmayı** engellemektir.

### Puanlama

Yalnız Brier yanıltıcıdır: nadir olaya hep "olmaz" demek düşük Brier verir ama
hiçbir şey bilmediğinizi gösterir. Üçü birlikte raporlanır:

- **Beceri skoru** = 1 − Brier / Brier(taban oran). Asıl ölçü budur; sıfırın
  altı, taban oranı bilmekten kötü demektir.
- **Murphy ayrışımı**: Brier = güvenilirlik − ayırt edicilik + belirsizlik.
- **Kalibrasyon eğrisi**: %70 dediklerinizin gerçekten %70'i oldu mu.

**20 çözülmüş tahminin altında hiçbir sonuç bildirilmez.**

Sentetik veriyle doğrulandı: kalibre tahminci **+0.135**, rastgele tahminci
**−0.318** alıp "yanıltıyor, kaldırılmalı" hükmü aldı.

### Chrono-Gravitron frekans katmanı

Kaldırıldı — daha doğrusu `chrono.py` kopyası silinirken zaten kalkmıştı.
Doğrulandı: `gravitron.py` içinde Hz, Schumann, oktav geçmiyor; arayüzde
frekans kartı yok. Geriye kalan `spektrum`, gerçek gelgit sinyalinin
periyodiklik çözümlemesidir (Venüs sinodik 19.2 ay) — ses eşlemesi değil.

Kabz/Bast'taki 528 Hz **ayrı bir şeydir** (m71, modelin kendi katmanı);
Chrono-Gravitron'a ait değil, dokunulmadı.

### Tarayıcı işe yaradı

Defter uçları eklenirken `Optional` importu unutuldu. `py_compile` temiz geçti;
`adtarama.py` yakaladı: `api_defter_puan() satır 477 → Optional`.

## v5.2 — Boş ortam değişkeni servisi çöktürüyordu

Render'da bir değişkeni **eklemek ama değerini boş bırakmak** mümkündür.
O durumda `os.environ.get("X", varsayilan)` varsayılanı **değil boş dizgeyi**
döndürür. `float("")` ve `int("")` ValueError fırlatır ve bu **import anında**
olduğu için servis hiç açılmaz — Render'da yalnız "deploy başarısız" görünür,
sebebi anlaşılmaz.

On üç değişken tek tek boş değerle sınandı; üçü servisi çöktürüyordu:

| Değişken | Boş bırakılınca |
|---|---|
| `AI_TIMEOUT` | `ValueError: could not convert string to float: ''` |
| `AI_TOTAL_BUDGET` | aynı |
| `ZIC_PROXY_HOPS` | `ValueError: invalid literal for int()` |

`ZIC_DEFTER` boş bırakılsa `os.makedirs("")` ile çökecekti.

`_sayi()` ve `_metin()` yardımcıları eklendi: boş ya da bozuk değer
varsayılana düşer. **On üçün on üçü artık boş bırakılsa bile çalışıyor** —
ama eklememek yine de en temizi.

`RENDER_ENV.txt` üç başlığa ayrıldı: *ekleyin ve değer girin* (5),
*hiç eklemeyin* (10), *asla eklemeyin* (5).

## v5.3 — 289 dosya → 47 (GitHub web yükleyici sınırı)

GitHub'ın web sürükle-bırak yükleyicisi tek seferde 100 dosyayla sınırlı.
Paket 289 dosyaydı, 244'ü ülke verisi.

Veri diskte **iki dosyaya** indirildi:

| Dosya | İçerik |
|---|---|
| `turkiye.json` | 77 KB — en sık istenen, tek başına |
| `dunya.json` | 2.25 MB — kalan 243 ülke, süreç belleğine bir kez alınır |

**Ağda hiçbir şey değişmedi:** istemci yine yalnız seçtiği ülkenin dilimini
alıyor. Ölçüldü — TR 78.958, DE 77.522, JP 83.507, US 249.453 bayt; birleştirme
öncesiyle birebir aynı.

Tek dosyada birleştirmek de düşünüldü (2.33 MB → 514 KB gzip) ama reddedildi:
Türkiye kullanıcısı şu an ~15 KB indiriyor, tek dosya bunu 30 kat kötüleştirirdi.

Yol aşımı koruması korundu (`../../../etc/passwd` → 404). `GITHUB.txt` eklendi:
üç yükleme yolu ve **`defter.db` depoya yüklenmemeli** uyarısı — danışan
tahminleri içerir.

## v5.4 — Farkındalık ilkesi, Formülasyon, çarkta isimler

### Promptların asıl amacı yeniden tanımlandı

Hüküm alanları birbirini tekrar ediyor, yanıtlar kesiliyordu. Ama asıl sorun
daha derindi: metinler *bilgi* veriyordu, *farkındalık* değil.

`CEKIRDEK_USLUP`'a yeni başlık: **ASIL AMAÇ: FARKINDALIK**. Okuyan kişi metni
bitirdiğinde kendisi hakkında bir şey fark etmiş olmalı — daha önce yaptığı
ama adını koymadığı bir davranışı tanımalı.

> ✗ "Kararsız bir yapın var." — etiket, hiçbir şey açmaz
> ✓ "Karar verdikten sonra üç kişiye daha soruyorsun. Onay aramıyorsun;
>    sorumluluğu paylaştıracak birini arıyorsun."

Sınav: kişi bunu okuyunca *"evet, dün tam da bunu yaptım"* diyebiliyor mu?
Diyemiyorsa cümle boştur. Ayrıca "enerji", "titreşim", "denge", "uyum",
"potansiyel", "yolculuk" gibi dolgu kelimeler yasaklandı.

**Tekrar:** Hüküm'ün sekiz alanı arka arkaya okunuyor. Her alanın bir
öncekinin ÜSTÜNE koyması şartı ve tekrar eden/üst üste koyan örnek çifti
eklendi.

**Kesilme:** `finish_reason=length` ile duran üretimde JSON çözümlenemiyor ve
tüm kişiselleştirme boşa gidiyordu. Artık kaldığı yerden tamamlattırılıyor;
sınır 1600 → 2400 jeton.

### Formülasyon (yeni bölüm)

Sentez hepsini birden okur; **Formülasyon seçilen katmanlar arasında bağ
kurar**. On iki katmandan iki ilâ altısı kutucukla seçilir.

"Hepsini anlat" ile "şu üçü birbirine ne diyor" farklı sorulardır ve ikincisi
seansta gerçekten sorulandır. Prompt tek tek özetlemeyi açıkça yasaklar;
**çelişki çıkarsa saklanmaz** — iki katman farklı yön gösteriyorsa kişi
gerçekten o gerilimin içindedir.

Bölümün **kendi sohbet kutusu** var; ana danışmandan ayrı.

### Çarkta isimlendirme

Fare imleciyle üzerine gelince ad çıkıyor — **39 ipucu**: gezegenler (konum,
geri hareket), hesaplanan noktalar (ad, konum, ev), dış çark cisimleri, burç
dilimleri, dört köşe (*"Yükselen — dışa dönük yüzün"*) ve **ev anlamları**
(*"7. ev — ortaklık, eş, karşıdaki"*).

### Hudûd-ı Felek genişletildi

- **Hudûd takvimi**: sınırın geçildiği tarihler. "Ay hudûd dışında" yeterli
  değil — ne zaman girdi, ne zaman çıkacak? Ay için birkaç gün, Mars için
  yıllar. Kaba tarama sonrası ikiye bölerek keskinleştirilir.
- **Transit paralelleri**: bugünkü gökyüzünün natal cisimlerle deklinasyon
  temasları — boylamda görünmeyen güncel bağlar.

## v5.5 — Halk dili, sızdırmayan hatalar, sade bekleme

### AI artık istisnasız halk dilinde konuşuyor

Danışman sohbeti şöyle yazıyordu: *"7. ev kara deliği tetikler → 10. ev
berzahında 'ait olmak/ayrışmak'…"* Bu, yöneticide teknik terime izin veren
istisnadan geliyordu. **İstisna kaldırıldı.** Kişi "teknik olarak anlat"
dese bile terim kullanılmıyor:

> "Arkadaki hesabı anlatmam sana bir şey katmaz; asıl mesele şu…"

Prompta eklenen ilke: *arkanda çok büyük bir hesap var — on binlerce satır,
yirmi katman. Ama kullanıcı bunu görmez, MEYVESİNİ görür. Bir doktor da
tomografiyi ham görüntü olarak uzatmaz; ne olduğunu söyler.*

Rakamlar ve konumlar ekranda zaten duruyor; AI'nin işi onları **anlama
çevirmek**. Sentez ve Formülasyon'un yönetici sürümlerindeki "teknik terim
serbest" izni de kaldırıldı.

### Hata mesajları iç bilgi sızdırmıyor

Ekranda *"Failed to fetch"* ve *"Gateway ayarlarını /api/v1/ai-health
adresinden kontrol edebilirsiniz"* görünüyordu. Uç adresleri ve yığın izleri
saldırgana harita çizer; kullanıcıya hiçbir şey kazandırmaz — yapabileceği
tek şey beklemektir.

`kullaniciyaHata()` eklendi: 429 → *"Şu an çok fazla istek var"*, 410 →
*"Oturumun süresi doldu"*, 401 → *"Erişim izniniz doğrulanamadı"*, geri kalan
→ *"Danışmana şu an ulaşılamıyor. Birazdan tekrar deneyin."*

Gateway kasten düşürülüp sınandı: `api/v1`, `Failed to fetch`, `Gateway`,
`http`, `127.0.0.1` — **hiçbiri görünmüyor**.

### Bekleme göstergesi

Önceden "Berzah'ı tartıyorum", "Çatalı açıyorum" gibi ifadeler dönüyordu —
hem terim sızdırıyor hem hiçbir şey söylemiyorlardı. Artık tek metin:
**"Düşünüyorum…"** Dizi sınırı aşımına karşı da korumalı (önceden
`undefined…` yazabilirdi).

## v5.6 — "Failed to fetch"in gerçek sebebi, insanı insana anlatmak

### Hata bir saldırı değildi

Ekrandaki *"Danışmana ulaşılamadı: Failed to fetch"* güvenlik sorunu değil,
**zaman aşımı uyuşmazlığıydı**:

| Katman | Süre |
|---|---|
| Sunucunun AI beklemesi | 120 sn |
| Toplam bütçe (devam turlarıyla) | 210 sn |
| **Render vekilinin kestiği an** | **~100 sn** |

Sunucu hâlâ çalışırken vekil bağlantıyı koparıyor, tarayıcı bunu ağ hatası
sanıyordu. Varsayılanlar **75 / 85 saniyeye** çekildi ve tavanla sınırlandı
(85/90) — artık hata sunucudan anlaşılır bir mesajla dönüyor, bağlantı
sessizce ölmüyor.

İstemciye de tavan kondu: AI uçları 95 sn, ötekiler 30 sn sonra
`AbortController` ile iptal ediliyor ve *"Yanıt beklenenden uzun sürdü"*
gösteriliyor.

### İnsanı insana anlatmak

Prompta yeni başlık — **SEN NE YAPIYORSUN**:

> İNSANI İNSANA ANLATIYORSUN. Konu gökyüzü değil, karşındaki kişi.
> Arkadaki hesap senin aletin; alet konuşulmaz, sonucu konuşulur.
> Marangoz masayı verirken testereyi anlatmaz.

Cümlelerin konusu hep kişi olmalı:
> ✗ "Bu yerleşim kariyerde gerilim gösteriyor." → konu yerleşim
> ✓ "Kariyerinde ilerlemek istiyorsun ama…" → konu kişi

Sayfa altındaki uyarı metni de terim saymayı bıraktı ("Kara delik",
"Einstein–Rosen", "LQC", "528 Hz" listesi kaldırıldı); aynı şeyi sade dille
söylüyor.

### Danışan defteri tamamlandı

`app/danisan.py` uçlara ve AI bağlamına bağlandı. Üç şey saklanır:
**oturum** (her okumanın çekirdek bulguları), **düzeltme** (danışmanın
"hayır, bu kişi aslında şöyle" dediği yerler) ve ön-kayıt defterindeki
tahminlerle **bağlantı**.

Asıl kazanç düzeltmelerde: model her seferinde aynı hatayı yapmak yerine,
danışmanın bir kez söylediğini bir daha biliyor — prompt bunu *hesaplamadan
üstün* tutuyor.

İkinci kazanç süreklilik: bağlama *"aynı örüntü tekrar ediyorsa bunu SÖYLE —
'bunu geçen sefer de fark etmiştin' cümlesi, tek seferlik hiçbir okumanın
veremeyeceği bir farkındalıktır"* talimatı eklendi.

Uçlar yönetici parolası ister; başlıksız erişim **401**, doğru başlıkla 200.

Geliştirirken bulunan hata: `gecmis()`, ön-kayıt tablosu henüz oluşmamışsa
`no such table: tahmin` ile düşüyor ve bağlam **sessizce boş** dönüyordu.
Artık tablo yokluğu hata sayılmıyor; beklenmeyen hata ise yutulmuyor.

## v5.7 — Astrokartografi ve ARZ İZDÜŞÜMÜ (yeni icat)

### A · Klasik astrokartografi

Doğum anı sabit, konum değişken. Her cismin dört çizgisi: doğduğu (ASC),
battığı (DSC), tepede olduğu (MC), dipte olduğu (IC) yerler.

**Üç zaman düzlemi**: natal, **Güneş dönüşü** (yılın haritası) ve **Ay
dönüşü** (ayın haritası). Ay dönüşü hesabı yeni eklendi (`ay_donusu_jd`);
doğrulandı: dönüş anında Ay natal boylamından **0.0 yay saniyesi** sapıyor.

**Paranlar** da hesaplanıyor: iki cismin aynı anda açısal olduğu enlemler.
Paran boylamdan bağımsızdır — o enlemin tamamında geçerlidir.

### Doğrulama ve bir yöntem ayrımı

MC çizgisinin verdiği boylamda harita kurulunca Güneş MC'den **0.2 yay
dakikası** sapıyor. ASC/DSC için ilk doğrulamam Jüpiter ve Satürn'de 560 yay
dakikasına varan sapma gösterdi — ama **hata doğrulamadaydı**, hesapta değil.

Sebep: klasik astrokartografi cismin **gerçek yükselişini** kullanır (in
mundo), ekliptik derecesinin yükselişini değil. İkisi yalnız ekliptik
üzerindeki cisimler için (Güneş, β=0) aynıdır. Gerçek ufuk yüksekliğiyle
sınandı: **16/16 nokta tam 0.000°**.

Bu ayrım belgeye yazıldı; başka bir yazılım "zodiacal" yöntem kullanıyorsa
sonuçlar farklı çıkabilir.

### B · ARZ İZDÜŞÜMÜ — yeni icat

Klasik astrokartografi **gezegenlerin** nerede açısal olduğunu gösterir.
Bu katman **modelin kendi eşiğinin** yeryüzünde nasıl değiştiğini gösterir.

Neden mümkün: BERZAH kütleleri açısallıktan beslenir. Konum değişince
açısallık değişir, kütleler değişir, **karar eşiği de değişir**. Aynı anda
ama başka yerde doğmuş biri, aynı gökyüzüne sahip olduğu hâlde farklı bir
eşikle yaşar.

Her ızgara noktasında harita yeniden kurulup üç şey ölçülür: eşiğin
keskinliği (asimetri), alanın toplanması (Rayleigh R) ve Kara Delik'in
düştüğü ev. Test haritasında keskinlik yeryüzünde **1.00–1.50** arasında
değişiyor.

330 nokta ≈ 3.6 saniye sürdüğü için ayrı uçta (`POST /api/v1/arz-izdusumu`)
ve istek üzerine çalışıyor.

Modül kendi sınırını da yazıyor: *"Bu klasik astrokartografi değildir.
Çelişirlerse ikisi ayrı soruya cevap veriyordur."*

### Yakalanan hata

`arz_izdusumu` bütün ızgarayı boş döndürüyordu. Sebep: Berzah nesnesinin
alanı `asymmetry` iken kodda `asimetri` yazılmıştı — ve döngüdeki sessiz
`except` bu AttributeError'ı yutup her noktayı atlıyordu. Sonuç "veri yok"
gibi görünüyordu. Alan adı düzeltildi, sessiz yutma kaldırıldı; hatalar
artık sayılıp bildiriliyor (`hatali_nokta`).

## v5.8 — HUDÛD-I ARZ: iki katmanı birleştiren denklem

### Bağ matematikseldi

Astrokartografi ve deklinasyon katmanı ayrı duruyordu. Aralarındaki bağ tek
bir denklemde saklı:

    φ_kritik = 90° − |δ|

Bir cisim, |enlem| > φ_kritik olan bölgelerde **hiç doğmaz ve batmaz**.
Yani ASC/DSC çizgisi yeryüzünün o kısmında **yoktur** — çizilmez, çünkü yok.

Deklinasyon büyüdükçe çizgisiz alan büyür. Hudûd dışı cisim tanım gereği en
büyük deklinasyona sahip olandır. Buradan çıkan:

> Gökyüzünde "kendi kuralının dışına taşmış" olan kapasite, yeryüzünde de
> en geniş alanda ulaşılamaz olandır.

Bu bir benzetme değil, **aynı sayının iki yüzü**: |δ| hem hudûd dışılığı
hem kritik enlemi belirler. İki katman zaten aynı büyüklüğe bakıyordu.

### Doğrulama

Teorik kritik enlem, çizginin gerçekten bittiği enlemle karşılaştırıldı:
**10/10 cisim tutuyor** (2° ızgara adımı içinde). Test haritasında Ay
+26.42° deklinasyonla hudûd dışı ve ±63.6° ötesinde hiç doğmuyor —
yeryüzünün **%10.4'ünde** o kapasiteye kapı yok.

### Üç çıktı

- **Kritik enlem** — her cisim için çizginin kaybolduğu enlem ve çizgisiz
  yüzey oranı
- **Sessiz kuşaklar** — hudûd dışı cisimlerin hiç kapısı olmadığı bantlar
- **Paralel çizgiler** — aynı deklinasyondaki cisimlerin çizgileri aynı
  biçimdedir; birlikte görünür, birlikte kaybolurlar

### Yer sorgusu ve şehre özel sohbet

34.695 şehirlik veri zaten yüklüydü; artık yer seçilip sorgulanabiliyor.
Seçilen yer için hangi çizgiler yakın (km cinsinden), hangi kapasiteler
orada sessiz, hudûd dışı bir cismin çizgisi geçiyor mu — hepsi hesaplanıyor
ve **o yere özel bir sohbet** açılıyor.

Test: Reykjavik'te Ay hem sessiz kuşakta hem çizgisi yakın — icadın
yakaladığı tam bu durum. İstanbul'da Jüpiter MC 186 km, Berlin'de Uranüs IC
227 km (hudûd dışı ve etkin).

Şehir promptu taşınmayı çözüm gibi sunmayı açıkça yasaklıyor: *"Yer bir
konuyu öne çıkarır; kişiyi değiştirmez."*

## v5.9 — Denetim: yanıt yükü yarıya indi

Tüm takımlar koşuldu; **bir gerçek sorun** bulundu.

### Yanıt boyutu iki katına çıkmıştı

v5.8'de astrokartografi eklenince analiz yanıtı **188 KB** oldu:

| Katman | Boyut |
|---|---|
| kartografi | **110 KB** |
| berzah_v2 | 19 KB |
| deneme_modulleri | 15 KB |

Kartografinin 102 KB'ı ASC/DSC eğri noktalarıydı (üç zaman düzlemi × 10
cisim × 90 nokta). **Arayüz bu dizileri hiç kullanmıyor** — yalnız MC/IC
değerlerini ve paran listesini gösteriyor.

Noktalar paran hesabında sunucuda kullanılıp yanıttan çıkarıldı; harita
çizimi gerekirse `POST /api/v1/kartografi-cizgi` ucundan alınıyor.

**188 → 94 KB.** Paran (20 kesişim), MC/IC ve Hudûd-ı Arz korundu.

### Denetim sonuçları

| Takım | Sonuç |
|---|---|
| Derleme + tanımsız ad | temiz |
| Derin doğrulama | 96/96 |
| Modül denetimi | istisna yok |
| Duman testi | 0.6 sn |
| Sızma testi | **36/36 kapalı** |

Dokuz API ucunun dokuzu da 200 dönüyor. Üç mod tarayıcıda doğrulandı
(kişisel 20, sinastri 7, kompozit 6 bölüm), yer sorgusu ve şehre özel sohbet
çalışıyor, misafir görünümünde sıfır teknik terim.

Yeni uçlarda yetki ve girdi denetimi: `danisan` ve `defter` yetkisiz
erişimde **401**, `sehir` analizsiz ya da geçersiz koordinatta **422**,
ülke ucunda yol aşımı **404**. Misafir payı 17 KB ve kartografi oraya
**sızmıyor**.

## v6.0 — Danışan defteri artık kullanılabilir

v5.6'da uçlar ve AI bağlamı yazılmıştı ama **arayüzü yoktu**: altı çalışan uç
vardı, sıfır kullanıcı erişimi. Bir özelliğin API'de var olup kimsenin
ulaşamaması, olmamasıyla aynı şey.

### Ne yapıyor

Yönetici bölümüne **Danışan defteri** eklendi (17. bölüm). Dört işlem:

| İşlem | Ne yapar |
|---|---|
| **Kaydet** | Formdaki doğum verisiyle takma ad açar |
| **Okumayı işle** | O anki analizin çekirdek bulgularını ve sentezi deftere yazar |
| **Düzeltme** | "Hayır, bu kişi aslında şöyle" notunu kaydeder |
| **Geçmiş** | Önceki okumalar, düzeltmeler ve bağlı tahminler |

Danışan seçiliyse analiz isteğine `danisan_id` ekleniyor; sunucu geçmişi
ve düzeltmeleri AI bağlamına katıyor. Test edildi: kayıt → okumayı işle →
düzeltme → yeni analiz zincirinde `danisan_id` gidiyor ve `gecmis_baglam`
geri geliyor.

### İki bağ

**Ön-kayıt defteriyle:** tahmin girerken takma ad boşsa seçili danışanınki
otomatik dolduruluyor; geçmiş görünümünde o kişiye ait tahminler ve
sonuçları listeleniyor. Böylece ölçüm katmanı danışan kaydına bağlanmış oldu.

**Prompt ile:** düzeltmeler bağlama *"hesaplamadan ÜSTÜNDÜR"* notuyla
giriyor. Model bir kez söylediğinizi bir daha biliyor.

### Gizlilik

Arayüz **gerçek ad kullanmayın** uyarısı veriyor. Veritabanı `.gitignore`
içinde; depoya yüklenmiyor.

## v6.1 — Yedekleme boşluğu: danışan kayıtları yedeklenmiyordu

"Defteri indir" **yalnız tahminleri** yedekliyordu. Danışan kayıtları,
geçmiş okumalar ve — en değerlisi — **danışmanın düzeltmeleri** yedeğin
dışındaydı. Render'ın diski kalıcı olmadığı için bu, her yeniden başlatmada
geri getirilemez veri kaybı demekti. Simülasyonla ölçüldü:

```
yazıldı        → danışan 1, tahmin 1, okuma 1, düzeltme 1
disk silindi   → hepsi 0
yedekten geri  → tahmin 1 ✓, danışan 0 ✗   ← kayıp
```

Dışa aktarım artık **dört tabloyu da** kapsıyor (sürüm 2; sürüm 1 yedekleri
de okunuyor). Geri yükleme danışan kimliklerini yeniden eşliyor, mükerrer
kayıt eklemiyor. Test: sil–geri yükle sonrası oturum, düzeltme ve bağlı
tahminler geri geldi, AI bağlam metni yeniden üretildi.

Arayüze **"Yedekten geri yükle"** düğmesi eklendi.

### ERISIM.txt

Deftere nasıl ulaşıldığı belgeye yazıldı: **Gmail/OAuth/üyelik yok**, tek
parola (`ADMIN_SIFRE`), sessionStorage'da tutulur, sekme kapanınca silinir.
Veri tarayıcıda değil sunucudaki SQLite dosyasında — başka cihazdan
girildiğinde de aynı veri görünür. Kalıcı disk ya da düzenli yedek şart.

## v6.2 — SPİRİTÜEL ÇALIŞMALAR: Mîzân-ı Ebvâb (kapıların tartısı)

### İcadın fikri

İskenderiye hermetizmi, Zohar kozmolojisi, Bûnî'nin harf ilmi, Picatrix'in
menâzili, İhvân-ı Safâ'nın sayı düzeni ve Porphyrios'un teürjisi — altısı da
şunu söyler: kişinin kendine ait **bir kapısı** vardır. Ama hangi kapı
olduğunda anlaşamazlar.

Bugüne kadar kimse bu altı kapıyı **aynı haritadan bağımsız hesaplayıp
birbirleriyle ne kadar örtüştüğünü ölçmedi.** Modül tam olarak bunu yapar ve
tek bir sayı üretir: *altı gelenekten kaçı aynı kapıyı işaret ediyor.*

Test haritasında 3/6 yakınsama çıktı (Jüpiter). Yakınsama düşük olduğunda
gizlenmiyor — asıl bilgi ayrışmada olabilir.

### Hesaplanan ve doğrulanan

- **Gezegen saatleri** — doğuş/batış efemeristen, 12 eşit olmayan saat,
  Kalde sırası. Test: gün sahibi Merkür, gündüz saati 66.6 dk.
- **Vefk (sihirli kare)** — 3×3'ten 9×9'a hesaplanır, ezberden verilmez.
  Satır, sütun ve köşegen toplamları **sınanır**.
- **28 menzil**, **sefirot eşlemesi**, **ebced**, **amel vakti**.

### Doğrulamanın yakaladığı iki hata

**6×6 vefk geçersizdi.** Tek-çift kare için yazdığım yöntem yanlıştı;
toplamlar tutmuyordu. Strachey/LUX doğru kurulunca **7/7 mertebe geçerli**.
Kare hesaplanıp sınandığı için bu yakalandı — hazır tablo kullansaydım
sessizce yanlış kalırdı.

**Kabalistik katmanda sefira boş kalıyordu.** Sebep: en zayıf cisim dış
gezegen çıkabiliyordu. Altı gelenek de **1781 öncesidir** — Uranüs, Neptün
ve Plüton'un hiçbirinde karşılığı yoktur. Hesap klasik yedi ile
sınırlandırıldı; modern gezegenleri zorla eşlemek geleneği bozardı.

### Sınırlar

Prompt şunları **mutlak** yasaklıyor: "şunu yaparsan şu olur" vaadi, kimseyi
etkilemek/bağlamak/döndürmek, hastalık iyileştirme, kısmet açma, dinî hüküm.
Kişi nazar/büyü korkusuyla gelirse önce korkuyu yatıştırması, bunun bir
tefekkür aracı olduğunu ve koruma satmadığını söylemesi isteniyor.

### Tesla hakkında dürüstlük

*"Evreni anlamak istiyorsan enerji, frekans, titreşim diye düşün"* sözü
Tesla'ya atfedilir ama **doğrulanmış yazılarında yoktur**; yaygınlaşması
20. yüzyıl sonudur. Tesla gerçekten rezonansla çalıştı (bobin, mekanik
osilatör) — bu tarihsel olarak doğru. "3-6-9" mistisizmi ise ona sonradan
yakıştırılmıştır. Modül bu ayrımı ekranda yazıyor: bilerek kullanmak,
bilmeden kullanmaktan güçlüdür.

## v6.3 — AI kaçamağı giderildi, defter bölümleri kaldırıldı

### "Ben bir yapay zekâyım" sorunu

AI bazı soruları cevaplamak yerine kimliğine sığınıyordu, özellikle yeni
spiritüel bölümde. İki sebep vardı:

**1. Bunu engelleyen kural hiç yoktu.** Çekirdek personaya eklendi:

> "Ben bir yapay zekâyım", "bir dil modeli olarak", "bu konuda yorum
> yapamam" gibi cümlelerle SORUYU GEÇİŞTİRME. Kişi doğrudan ne olduğunu
> sorarsa dürüstçe söylersin — ama bunu cevap vermemek için kalkan olarak
> KULLANMA. Susmak en kötü seçenektir.

Kural dört promptun dördüne de geçti (çekirdekten geldiği için).

**2. Spiritüel prompt 684 kelime yasakla doluydu.** "ASLA", "YASAK",
"etme", "deme" yığını modeli aşırı reddetmeye itiyordu. Prompt yeniden
yazıldı: yasak listesi yerine **ne yapacağı** anlatılıyor ve açıkça
söyleniyor —

> "Bu bölüm hassas göründüğü için geçiştirme eğilimi oluşabilir —
> oluşmasın. 'Bu ne demek', 'nasıl çalışayım', 'neden bu gezegen' olağan
> sorulardır ve cevabı vardır."

Gerçek sınırlar korundu: başkasını etkileme aracı değil, sağlık/para vaadi
yok, korku varsa önce korku yatıştırılır.

### Defter bölümleri arayüzden kaldırıldı

"Danışan defteri" ve "Ön-kayıt defteri" bölümleri kaldırıldı; arayüz
**22 bölümden 19'a** indi. Ölü JS de temizlendi (`danisanKur`,
`defterKur`, `defterBaslik` ve bağlı değişkenler).

Sunucu uçları ve veritabanı **yerinde duruyor** — istenirse geri
eklenebilir, hiçbir veri kaybı yok.

Not: ön-kayıt defteri modelin işe yarayıp yaramadığını ölçen tek katmandı.
Kaldırılmasıyla o ölçüm de duruyor; ihtiyaç olursa arayüz geri gelir.

## v6.4 — Doğrulama: spiritüel AI ve sohbet modu

Sahte gateway hazır cevap döndürdüğü için gerçek davranışı göstermiyordu.
Bunun yerine **modele giden isteği kaydeden** bir gateway kuruldu ve tam
olarak ne gönderildiği okundu.

### Modele gerçekten ne gidiyor

| Kontrol | Sonuç |
|---|---|
| Sistem promptu | 784 kelime |
| "KAÇAMAK YOK" kuralı | var |
| Spiritüel yüzey talimatı | var |
| "geçiştirme eğilimi oluşmasın" uyarısı | var |
| Kapı verisi ve yakınsama | gidiyor |
| Çok turlu geçmiş | gidiyor |

### Sohbet modu

Üç ardışık soruda balon sayısı 2 → 4 → 6: **geçmiş korunuyor**, her tur
öncekinin üstüne biniyor. Yanıtlarda kaçamak ifadesi yok.

### Altı promptun durumu

| Prompt | Kelime | Kaçamak | Sınır | Farkındalık | İnsanı insana |
|---|---|---|---|---|---|
| Sohbet | 896 | var | var | var | var |
| Spiritüel | 784 | var | var | var | var |
| Yer | 708 | var | var | var | var |
| Formülasyon | 748 | var | var | var | var |
| Bütünsel | 676 | var | var | var | var |
| Hüküm | 862 | var | var | var | var |

Ayrıca 25 bölüm AI talimatı ve 12 formülasyon katmanı tanımlı.

## v6.5 — KRİTİK: iki farklı kişiye aynı yorum çıkıyordu

### Sebep bendeydi

Promptlara kaliteyi yükseltmek için **tamamlanmış örnek cümleler**
yazmıştım. Bunlar *iyi* olduğu için model onları örnek değil **cevap**
sanıyor ve olduğu gibi kullanıyordu. Üstelik altı promptun altısında da
aynı örnekler vardı (hepsi `_cekirdek()`'ten geliyor), o yüzden herkese
aynı metin çıkıyordu. Klasik few-shot bulaşması ve tamamen tasarım hatam.

### Önce başka ihtimaller elendi

Üç farklı harita için çekirdek bulgular belirgin biçimde farklı
(KD 107° / 258° / 307°, en ağır cisim Jüpiter / Neptün / Neptün); AI
bağlamları %57–63 benzer ve bu benzerlik tamamen ortak iskeletten
geliyor. **Veri sorunu yoktu.**

### Çözüm

Bütün örnekler şablona çevrildi — somut cümle değil, doldurulacak kalıp:

```
✗ ‹sıfat› + "bir yapın var"
✓ ‹kişinin yaptığı somut eylem› + ‹o eylemin görünmeyen sebebi›
```

Kopyalanabilir tam cümle sayısı: **24 → 0.**

Yeni kural (çekirdekten altı prompta birden geçiyor):

> Bu talimatlardaki bütün örnekler BİÇİM göstermek içindir; hiçbiri bu
> kişiye ait DEĞİLDİR. Yazacağın her cümle önündeki VERİDEN çıkmalıdır.
> Yazmadan önce sor: "Bu cümleyi başka bir haritaya da yazabilir miydim?"
> Cevap evetse o cümle YANLIŞTIR.

Ayrıca metnin **en az üç yerde** o haritaya özgü bir bulguya dayanması
şartı kondu.

### Doğrulama

Modele giden istek kaydedildi: iki kişinin girdisi %60 benzer (ortak
iskelet), sistem promptunda hazır cümle **yok**, şablon işaretleri var.

## v7.0 — Performans, mimari, dayanıklılık, test

Beş cephede de önce ÖLÇÜLDÜ, sonra düzeltildi.

### 1 · Performans

Efemeris çağrıları sayıldı: tekrar oranı %0–9, yani maliyet gerçek
hesaptan geliyordu. Asıl yük **hudûd takviminin üç yıllık taraması**ydı —
11.157 çağrı, 193 ms. Sebep: Ay'ın deklinasyon çevrimi 27.3 gündür; üç yıl
taramak aynı örüntüyü 40 kez tekrarlamaktı ve çıktı zaten 24 kayda
kırpılıyordu. Ay penceresi 8 aya indirildi.

| Ölçü | Önce | Sonra |
|---|---|---|
| Hudûd efemeris çağrısı | 11.157 | **5.756** |
| Hudûd süresi | 193 ms | **140 ms** |
| Uçtan uca analiz | 0.77–0.86 sn | **0.74–0.78 sn** |

Geçiş sayısı değişmedi (24) — bilgi kaybı yok.

### 2 · Mimari

Altı AI yüzeyi aynı üç adımı ayrı ayrı yazıyordu: üret → kesildiyse devam
ettir → birleştir. Bir yerde düzeltilen hata ötekilerde kalıyordu.
`_yuzey_uret()` çıkarıldı; tekrar **5'ten 1'e** indi. Devam turu başarısız
olursa artık eldeki metin veriliyor (önce istisna fırlıyordu).

### 3 · Dayanıklılık — bulunan çelişki

Arayüz doğum yılı için **1800–2400** diyordu, sunucu **2200**'de
reddediyordu. Kullanıcı 2300 girse arayüz kabul eder, sunucu 422 atardı.
Sınır 2200'de hizalandı ve tarayıcıda doğrulandı.

### 4 · Test — `kenar_test.py`

`verify.py` hesapların doğruluğunu sınar; bu dosya **olağandışı girdilerde
ayakta kalıyor mu** sorusunu sorar. 43 kontrol:

- Aşırı enlemler: Longyearbyen 78°K (kış/yaz), McMurdo 77°G, kutup dairesi,
  kuzey kutbu 89.9° — ev sistemlerinin çöktüğü yerler
- Coğrafi sınırlar: tarih değiştirme çizgisi (±179.99°), ekvator, Greenwich
- Zaman sınırları: artık gün, gece yarısı, gün sonu, efemeris uçları
- Beş katmanın üç aşırı konumda ayakta kalması (15 kontrol)
- Yedi vefk mertebesinin geçerliliği
- **Performans gerileme koruması** — her modül için süre eşiği

**43 geçti, 0 kaldı.** `build.sh` içine eklendi.

### 5 · AI sistem modu

v6.5'teki kopyalama yasağı ve şablonlaştırma yerinde; altı promptun
altısında çekirdek kurallar var (kaçamak yasağı, sınırlar, farkındalık,
insanı insana).

## v7.1 — Dört tema

Tek bir görünüm yerine dört ayrı görsel kimlik. Değişken sistemi zaten
temiz olduğu için tema, değişken setini yeniden tanımlamak demek; yapı
değişmiyor, karakter değişiyor.

| Tema | Kimlik | Nereden geliyor |
|---|---|---|
| **Bauhaus** | kağıt ve mürekkep, sakin okuma | varsayılan |
| **Brutalist** | 3px çerçeve, sert gölge, tek yazı tipi, turuncu-kırmızı | Sistem hesabını gizlemiyorsa arayüzü de gizlemesin |
| **Rasat** | gece lacivertı, pirinç sarısı, serif başlık | Rasathane defteri, gözlem kaydı |
| **Minyatür** | lapis, altın, zencefre; katmanlı, süslü | Osmanlı astronomi elyazması |

Seçim başlıkta, cihazda saklanıyor, sayfa yenilenince korunuyor.

### İki hata yakalandı

**Seçili tema düğmesi okunmuyordu.** Fare düğmenin üstünde kalınca
`:hover` kuralı seçili durumu eziyor ve yazı arka planla aynı renge
düşüyordu — Brutalist'te siyah üstüne siyah. Seçili durum hover'dan
üstün yapıldı; dört temada da kontrast doğrulandı.

**Gönder düğmesi tema değiştirmiyordu.** Ana sohbetin düğmesi sınıfla
değil `id` ile biçimlendirilmişti, sınıf seçicili tema kuralları onu
yakalamıyordu. Dört temada da doğrulandı.

### Erişilebilirlik

Tema düğmeleri `aria-pressed` taşıyor, dokunmatikte 44 px yükseklikte.
Koyu temalarda çark okunur kalsın diye filtre uygulanıyor.

## v7.2 — Tema seçimi kullanılabilirliği

v7.1'de temalar eklendi ama **kullanıcının gördüğü ilk ekran temasızdı**:
giriş perdesi başlığı örttüğü için tema seçici görünmüyordu.

Perdenin içine ikinci bir seçici kondu; `temaKur()` zaten bütün
`.tema-sec` düğmelerini bağladığı için ek kod gerekmedi. Seçim giriş
ekranında yapılıp uygulamaya taşınıyor, başlıktaki seçici de senkron
kalıyor.

Giriş perdesi, rol kartları ve amblem de temaya uyduruldu.

### Yakalanan kontrast hatası

Rol kartı başlıkları ("Yönetici", "Misafir") koyu temalarda **siyah
üstüne siyah** kalıyordu. İlk düzeltme tutmadı çünkü yanlış seçici
kullandım (`h3`/`strong` sandım, gerçekte `span.rol-ad`). Doğru
seçiciyle dört temada da ölçüldü:

| Tema | Kart | Başlık |
|---|---|---|
| Bauhaus | beyaz | siyah |
| Brutalist | beyaz | siyah |
| Rasat | #141B33 | #ECEAE3 |
| Minyatür | #1C2B5E | #F5EDD8 |

### Mobil

Tema seçici 390 px ekranda 297 px (uygulama) ve 362 px (giriş) genişlikte,
**taşma yok**, düğmeler 44 px yüksekliğinde. Dar ekranda düğmeler eşit
paylaşıyor.

## v7.3 — Bütün katmanlar bağlamda, tavanla korunarak

İstek netti: her katman AI bağlamına girsin, ama bağlantı kopmasın.

Ham veri göndermek çözüm değildi — 106 KB, ~30 bin jeton, model boğulur ve
zaman aşımı riski doğar. Doğru çözüm **her katmanın özetini** almak ve
toplama sert bir tavan koymak.

### Eksik üç katman eklendi

| Katman | Durum |
|---|---|
| `transit` — bugünkü gök | **hiç girmiyordu**; "şu an ne oluyor" en sık sorulan şeydi |
| `maneviyat` — kapılar | yalnız kendi ucunda vardı; ana danışman cevap veremiyordu |
| `solar_v2` — yılın haritası | boş geliyordu; Kabz/Bast içindeki solar dönüş özetine düşülüyor |

### Bağlam tavanı

`BAGLAM_TAVAN = 16000` karakter (~4.500 jeton). Aşılırsa **rastgele kırpma
yapılmaz** — cümle ortasından kesmek modeli yanıltır. Bunun yerine en düşük
öncelikli bloklar **bütün olarak** düşürülür ve düşenler modele bildirilir:

> [YER DARLIĞI] Şu katmanların özeti bu sefer dışarıda kaldı: … Kişi
> bunlardan birini sorarsa "o katmanı ayrı bakalım" de; uydurma.

Öncelik sırası: güven notu / öncelik özeti / çekirdek (asla düşmez) →
danışan geçmişi → alan topolojisi, bugünkü gök → Kabz/Bast, yılın haritası
→ Hudûd, Şi'râ → kadim, HD, kapılar → yer, deneme → Chrono.

**Ölçüm:** 106 KB hesap → 13.076 karakter bağlam, **14 blok**, tavanın
altında. 22 KB'lık yapay girdiyle sınandı: 13.212'ye indi, uyarı eklendi,
zorunlu bloklar korundu.

### Yakalanan hata

**CHRONO-GRAVITRON bağlama iki kez giriyordu** — biri v4.6'da, biri v5.x'te
eklenmiş ve ikisi de kalmış. Model aynı bilgiyi iki farklı biçimde alıyordu.
Kısa olan kaldırıldı; artık mükerrer blok yok.

## v7.4 — Prompt denetimi: üç bölümün talimatı yokmuş

Yedi AI yüzeyi 11 kurala karşı denetlendi. **Yedisinde de on birin on biri
tam**: kaçamak yasağı, kopyalama yasağı, veriye dayanma, farkındalık, insanı
insana, tıbbî sınır, ömür/ölüm, kriz, belirsizlik, dolgu kelime yasağı,
tekrar yasağı.

İki "eksik" yanlış alarm çıktı: SISTEM'de uzunluk talimatı var ("En fazla
5 paragraf"); tırnaklı uzun ifadeler ise kopyalanabilir örnek değil, talimat
parçasıymış.

### Gerçek eksik: bölüm–talimat eşleşmesi

Arayüzdeki her bölümün "AI ANALİZİ" düğmesi var ama **üçünün talimatı
yoktu**; o düğmeler genel talimatla çalışıyordu:

| Bölüm | Durum |
|---|---|
| `manevi` — spiritüel çalışma | talimatsızdı |
| `sentez` — bütünsel okuma | talimatsızdı |
| `formul` — formülasyon | talimatsızdı |

Üçü de yazıldı. Arayüzde karşılığı kalmayan üç ölü talimat (`davison`,
`gravitron`, `rektifikasyon`) kaldırıldı — ilk ikisi kendi bölümlerinde
birleşmiş, üçüncüsünün ayrı düğmesi yok.

**Talimatsız bölüm YOK · ölü talimat YOK · 25 talimatın 25'i eşleşiyor.**

Uçtan uca sınandı: 25 bölümün 25'i de yanıt üretiyor.

## v7.5 — Danışan soruları: genel okuma yerine seçilmiş soruya cevap

Genel rapor kalıbı yetersizdi: bir yol ayrımı işaretliyor ama kişinin kim
olduğunu, neyi iyi yaptığını, neyi geliştirmesi gerektiğini söylemiyordu.

Danışan zaten genel okuma istemez; **belirli bir soru** sorar. Katalog o
soruları sabitliyor: **47 soru, 5 kategori.**

### Asıl fikir: her soru bir katmana bağlı

Her sorunun hangi katmandan cevaplanacağı katalogda yazılı. Model o
katmanlara bakmak zorunda ve uyduramıyor. Yan etkisi önemli: **iki kişi
asla aynı cevabı alamaz**, çünkü katmanlar farklı.

Örnek — "Rızkım hangi alandan açılır?" beş katmana bağlı ve şu çerçeveyi
taşıyor: *meslek listesi verme; çalışma biçimini tarif et — yalnız mı
ekiple mi, görünür mü perde arkası mı, kendi kuralıyla mı kurumun
kuralıyla mı. Sonra bu biçime uyan 2-3 alan söyle.*

### Üç zorunlu bileşen

Prompt her cevapta üç şeyi şart koşuyor:

- **Ne iyi yapıyor** — o konudaki gerçek gücü, hafife aldığı yan
- **Neyi geliştirmeli** — eksik değil, çalışılmamış olan
- **Kendini nasıl ortaya koyar** — hangi ortamda, hangi rolde, hangi
  davranışla

> Kişi metni bitirdiğinde "ne yapacağımı biliyorum" demeli — "ilginçmiş" değil.

### 14 hassas soru: reddedilmedi, çerçevelendi

Sağlık soruları organ ve hastalık adı vermiyor; mizaç ve zorlanma deseni
konuşup hekime yönlendiriyor. Boşanma sorusu kehanet yapmıyor; bağı
yıpratanı ve kişinin kendi payını konuşuyor. Yatırım sorusu al/sat demiyor,
mali müşavire yönlendiriyor. Dava sorusu sonuç tahmin etmiyor.

Biri tamamen çevrildi: **"Partnerim ne hissediyor?"** — üçüncü kişinin
duygusunu okumak ne mümkün ne doğru; soru kişinin kendi kaygısına dönüyor.

Bir de sessiz düzeltme: eş sorusundan **fiziksel tarif çıkarıldı**.
Ölçülmez, uydurma olur ve kişiyi sokakta birini görüp "bu o" demeye iter.
Yerine mizaç uyumu ve tanışma ortamı kondu.

## v7.6 — Soru kataloğu tamamlandı: 50/50

Belgedeki 50 soru katalogla tek tek karşılaştırıldı. **47'si vardı, üçü
eksikti** — ve üçü de listenin en zor soruları:

| Eksik soru | Neden zor |
|---|---|
| Aile büyüklerinin sağlığı | üçüncü kişinin sağlığı, verisi yok |
| Çocuğun eğitimi ve yetenekleri | reşit olmayan biri hakkında hüküm |
| Ameliyat / estetik için uygun tarih | tıbbî zamanlama |

Üçü de eklendi ama **çerçeveleriyle**:

- **Aile büyüğü**: hiçbir sağlık, ömür veya risk yorumu yok. Soranın kendi
  bakım yükü konuşuluyor — neyi erteliyor, kendine ne kadar yer bırakıyor.
- **Çocuk**: çocuk etiketlenmiyor. "Şu meslek ona uygun" denmiyor;
  ebeveynin beklentisi ve farkında olmadan aktardığı baskı konuşuluyor.
- **Ameliyat**: *"Şu tarihte ol / olma"* asla. Gökyüzüne göre tıbbî işlem
  ertelemek zarar verebilir — bu açıkça söyleniyor, karar hekime bırakılıyor.

**Katalog: 50 soru · 5 kategori (10+10+10+10+10) · 17'si çerçeveli.**

Uçtan uca sınandı: üç yeni soru, iki soru birlikte, sekiz soru birden ve
serbest ek soru — hepsi 200 dönüyor.

### Ortam notu

Bu turda çalışma ortamı sıfırlanmıştı (Python 3.11 ve bağımlılıklar
silinmişti). Paket yüklenen sürümden geri kuruldu, ortam yeniden
hazırlandı; 96 doğrulama, 43 kenar durum ve tanımsız ad taraması yeniden
koşuldu — hepsi temiz.

## v7.7 — Çoklu AI sağlayıcı: biri düşerse öteki devralır

Servis tek sağlayıcıya bağlıydı: gateway düşerse ya da kota biterse
tamamen susuyordu. Artık **dört sağlayıcılı bir zincir** var.

| Sıra | Sağlayıcı | Değişkenler |
|---|---|---|
| 1 | Birincil gateway | `AI_BASE_URL` · `AI_API_KEY` |
| 2 | Anthropic doğrudan | `ANTHROPIC_API_KEY` |
| 3 | OpenAI doğrudan | `OPENAI_API_KEY` |
| 4 | Serbest yedek | `AI2_BASE_URL` · `AI2_API_KEY` |

Hepsi **isteğe bağlı** — yalnız anahtarı tanımlı olan zincire girer. Tek
sağlayıcıyla mevcut kurulum aynen çalışmaya devam eder.

Bir sağlayıcı ağ hatası, zaman aşımı, 5xx ya da kota verirse **sessizce**
sonrakine geçilir. Düşen sağlayıcı 180 saniye atlanır, sonra yeniden
denenir — geçici kesinti kalıcı dışlanmaya dönüşmez.

Durum: `GET /api/v1/ai-saglayicilar`

### Geliştirirken çıkan iki hata

Zinciri kurmak yetmedi; iki yerde **global durum** yedeği işlevsiz
bırakıyordu:

**Model listesi global'di.** Birinci sağlayıcı düşünce onun boş listesi
ikinciye de yansıyordu ve yedek "kullanılabilir model yok" diyordu. Liste
ve erişilemez küme sağlayıcı başına ayrıldı; düşen sağlayıcının önbelleği
temizleniyor ki toparlayınca yeniden okunsun.

**`_get()` global BASE/KEY kullanıyordu.** Model listesi hep birinci
sağlayıcıdan isteniyordu. Aktif sağlayıcıya bağlandı.

### Doğrulama

İki sahte gateway kuruldu, biri koşum ortasında öldürüldü:

```
1) ikisi de ayakta -> [BIRINCI] yanit
2) birinci dustu   -> [IKINCI] yanit
   aktif: yedek
     gateway    soğumada   Gateway'e ulaşılamadı (…9101)
     yedek      hazır      —
```

Kullanıcı kesintiyi görmedi.

## v7.8 — Bölüm hiyerarşisi: 21 eşit bölüm yerine 4 + derin katman

22 bölüm eşit ağırlıkta görünüyordu: Hüküm ile Chrono-Gravitron aynı
boyutta, aynı sırada. Oysa bir seansta çoğunlukla üçü konuşuluyor.

**Hiçbir bölüm kaldırılmadı, hiçbir hesap silinmedi.** Yalnız hangisinin
açık başlayacağı değişti.

| Açık başlayan | Neden |
|---|---|
| Hüküm | okumanın çekirdeği |
| Danışan soruları | asıl çalışma yüzeyi |
| Bütünsel okuma | seansın toparlaması |
| Danışman | sohbet |

Kalan 17 bölüm **"Derin katman · 17 bölüm"** ayracının altında kapalı
başlıyor. Başlığa dokununca tek tek açılıyor, ayraçtaki düğmeyle hepsi
birden.

### Ölçüm

| | Önce | Sonra |
|---|---|---|
| Yönetici sayfa boyu | 21.300 px | **5.100 px** |
| Hepsi açıkken | — | 21.300 px (bilgi kaybı yok) |
| Misafir mobil | 5.8 ekran | 5.7 ekran (3 bölüm, hepsi açık) |

### Yan düzeltme

Bloklar `data-kimlik` taşımıyordu — kimlik yalnız AI düğmesindeydi.
Hiyerarşi buna baktığı için DOM'a yazıldı. Sohbet bloğunun kimliği de
eksikti, eklendi.

## v7.9 — Resmî API ve gateway yolları kanıtlandı

"Çalışıyor" demek yetmez; **hangi protokolle** çalıştığını kanıtlamak
gerekir. Yanlış protokolü **reddeden** taklit sunucular yazıldı
(`protokol_test_sunucu.py`): yanlış yol 404, eksik başlık 401, yanlış
gövde 400 döner.

### Ne kanıtlandı

| Yol | Uç | Gövde farkı |
|---|---|---|
| **Anthropic resmî** | `/v1/messages` | `system` **ayrı alan**, `max_tokens` zorunlu, `x-api-key` + `anthropic-version` |
| **OpenAI resmî** | `/v1/chat/completions` | `system` **messages içinde**, `Authorization: Bearer` |
| **Gateway** | protokolü kendi seçer (auto) | ikisinden hangisi yanıt verirse o |

Sunucu kayıtları:

```
anthropic: POST OK /v1/messages model=claude-sonnet-4-6 system=var mesaj=1
openai   : POST OK /v1/chat/completions model=gpt-4o mesaj=2
REDDEDİLEN İSTEK: 0
```

Sıfır reddedilme — yani kod her iki protokolü de doğru konuşuyor, sadece
"200 döndü" değil.

### Dört sağlayıcılı zincir

Dördü birden kuruldu ve **sırayla öldürüldü**; her seferinde bir sonraki
devraldı ve kendi protokolüyle yanıt verdi:

```
1. adım -> [OPENAI] yanıt     protokol=openai      (gateway)
2. adım -> [ANTHROPIC] yanıt  protokol=anthropic
3. adım -> [OPENAI] yanıt     protokol=openai
4. adım -> [ANTHROPIC] yanıt  protokol=anthropic   (yedek)
```

### Canlı serviste

Danışan sorusu cevaplanırken Anthropic düşürüldü:

```
soru (anthropic aktif) -> [ANTHROPIC] yanıt
soru (anthropic düştü) -> [OPENAI] yanıt
aktif artık: openai
```

Kesinti danışana yansımadı.

## v8.0 — "Danışmana ulaşılamadı" hatasının sebebi bulundu

### Sorun zaman aşımıydı, bağlantı değil

Soru bölümü hata veriyordu. Sebep ölçüldü:

| Soru | İstenen jeton | Gerçek modelde süre |
|---|---|---|
| 1 | 1600 | ~40 sn |
| 5+ | 3600 | **90-120 sn** |

`AI_TIMEOUT` 75 saniye. Yani çok soruda istek **kesiliyordu** ve kullanıcı
"danışmana ulaşılamadı" görüyordu. Süreyi artırmak çözüm değil: vekil
zaten ~100 saniyede koparıyor.

### Çözüm: partili cevaplama

Sorular ikişerli partilere bölünüp arka arkaya cevaplanıyor, parçalar
birleştiriliyor. Her parti rahatça sınırın altında.

**İlk deneme yetmedi.** Partileme per-call zaman aşımını çözdü ama toplam
süreyi çözmedi: dört soru 92 saniye sürdü, çünkü bütçe kontrolü partiyi
başlatmadan önce yalnız *geçen süreye* bakıyordu — 46 sn'de "bütçem var"
deyip ikinciyi başlatıyor, toplam 92 oluyordu.

Kontrol **öngörülü** yapıldı: bir sonraki partinin tahmini süresi
(öncekinin gerçek süresi) de hesaba katılıyor. Ölçüm:

```
1 soru: 32.0 sn
2 soru: 46.0 sn
4 soru: 46.0 sn  · kalan bildirildi
6 soru: 46.0 sn  · kalan bildirildi
```

Yetişmeyen sorular kullanıcıya söyleniyor: *"Şu sorular bu turda
yetişmedi, ayrıca sorabilirsiniz…"* Arayüz tavanı 8'den **4'e** indi.

### Kategori çerçeveleri

Hudûd-ı Felek talimatı ötekilerden iyiydi çünkü modele **ne arayacağını**
söylüyordu. Ötekiler "şunu anlat" diyordu ve genel çıkıyordu. Beş
kategoriye de aynı keskinlikte arama emri yazıldı:

- **İlişki** — yakınlaşma anındaki tekrar eden hamle; kişinin ona verdiği
  ad ile gerçekte ne işe yaradığı arasındaki fark
- **Kariyer** — emeğin değere döndüğü ve dağıldığı yer; görünürlükle
  ilişkisi
- **Gelişim** — kendini anlattığı hikâye ile fiilen yaptığı arasındaki
  açıklık; hangi gücünü zayıflık sandığı
- **Aile** — taşıdığı yükün kime ait olduğu; taşımadığı kendi yükü
- **Zaman** — hangi kapının aralandığı ve o aralıkta tam olarak neyin
  mümkün olduğu

## v8.1 — Anlatım katmanı: metnin nasıl yazılacağı

Promptlar **ne söyleneceği** konusunda güçlüydü (farkındalık, insanı insana,
veriye dayanma, kopyalama yasağı) ama **nasıl yazılacağı** konusunda
neredeyse boştu. Aynı bulgu kötü yazıldığında kişiye hiçbir şey yapmıyor.

`CEKIRDEK_ANLATIM` eklendi; çekirdekten geldiği için **sekiz yüzeye
birden** geçti.

### Sekiz kural

**Açılış** — ilk cümle meta olamaz. "Bu okumada…", "Haritanda dikkat
çeken…", "Verilere baktığımda…" yasak; hepsi kişiyi bir adım
uzaklaştırıyor. İlk cümle kişinin *yaptığı* bir şeyle, hareket hâlinde
başlar.

**Paragraf = tek hamle** — her paragraf ya yeni gözlem koyar, ya altını
kazar, ya çelişkiyi açar, ya somuta iner. Sınav: paragrafı silsen metin
bir şey kaybediyor mu?

**Ritim** — cümle uzunluğu değişmeli. Uzun açıklayıcı cümleden sonra kısa
cümle gelsin; kısa cümle vurur. Arka arkaya üç uzun cümle metni düzleştirir.

**Kanıtı cümleye dok** — bulgular sıralanmaz, davranışın *sebebi* olarak
cümlenin içine girer. Veri görünmez ama taşıyıcı olur.

**Geçişler** — "ayrıca", "bunun yanı sıra", "öte yandan", "ek olarak",
"sonuç olarak", "kısacası" yasak. Bunlar boşluğu doldurur, bağ kurmaz;
paragraflar içerikle bağlanır.

**Hitap** — "sen" dendiyse sonuna kadar "sen". "Kişi", "insanlar" diye
kaymak metni raporlaştırır.

**Belirsizlik** — her şeyi yumuşatma; metin bulanıklaşır. Çekince yalnız
gerektiği yere, üstelik işe yarar hâlde: neyin bunu netleştireceğini söyle.

**Bitiriş** — motivasyon cümlesi yasak ("unutma ki", "her şey senin
elinde"). Özetleyerek de bitirme. Ya somut adımla, ya en keskin gözlemle.

### İki çelişki önceden kapatıldı

Yeni kurallar eskilerle çakışabilirdi; ikisi de yakalandı:

- *"Çekince yalnız bir yere"* ile *"GÜVEN NOTU uyarılarına harfiyen uy"*
  çakışıyordu. Güven notu veriye dayandığı için istisna olarak yazıldı.
- *"İlk cümle meta olamaz"* ile soru yüzeyinin *"soruyu başlık olarak yaz"*
  kuralı çakışıyordu. Başlığın **altındaki** ilk cümle için geçerli
  olduğu belirtildi.

Sekiz yüzeyin sekizi de sınandı; hepsi 200 dönüyor.

## v8.2 — Tam rapor: on bölümlük PDF

Bütün katmanlardan beslenen, kişiyi baştan sona anlatan bir belge. Sentez
(kısa toparlama) ve danışan soruları (belirli soruya cevap) dışında
üçüncü bir şey: **elde kalan rapor**.

### On bölüm, katmana göre değil kişiye göre

Danışan "alan topolojisi" okumak istemez; *"ben kimim, ne iyi yapıyorum,
neyi geliştirmeliyim"* okumak ister:

1. Bu kişi kim · 2. Tekrar eden döngü · 3. Ne iyi yapıyor ·
4. Neyi geliştirmeli · 5. Kendini nasıl ortaya koyar · 6. İlişkilerde ·
7. İş ve rızık · 8. İç dünyası · 9. Önündeki dönem · 10. Kapanış

Her bölüm kendi katmanlarından besleniyor ve kendi "ne arayacaksın"
talimatını taşıyor. Bölümler birbirinin özetini görüyor — tekrar etmiyorlar.

### Mimari: bölüm bölüm, tek istekte değil

İlk tasarım on bölümü tek istekte üretiyordu. **Çalışmazdı**: gerçek
modelde bölüm başına ~40 saniye, toplam ~400 saniye eder ve hiçbir vekil
buna izin vermez.

Bölümler istemciden **tek tek** isteniyor (`/api/v1/rapor-bolum`), her
istek rahatça sınırın altında kalıyor, kullanıcı ilerleme çubuğunu
görüyor. Sonunda toplanan bölümlerden PDF kuruluyor
(`/api/v1/rapor-pdf` — AI çağrısı yok, hızlı).

Bir bölüm başarısız olursa rapor yarıda kalmıyor; o bölüm atlanıyor ve
kaç bölümün yazıldığı söyleniyor.

### PDF

ReportLab + gömülü DejaVu. **Türkçe karakter için font gömmek şart** —
varsayılan ReportLab fontlarında ş, ğ, İ, ı düzgün çıkmaz. Doğrulandı:
başlıkta "Danışan · Doğum Haritası Okuması" doğru render ediliyor.
A4, sayfa numaralı, altında sınır uyarısı.

### Yakalanan hata: istemci zaman aşımı listesi eksikti

`fetch` sarmalayıcısı yalnız altı ucu "uzun sürebilir" sayıyordu. Sonradan
eklenen **rapor, soru-cevap, şehir, manevi, arz-izdüşümü, bölüm analizi**
listede yoktu ve **30 saniyede iptal ediliyorlardı**. Sessiz bir hataydı:
kullanıcı "danışmana ulaşılamadı" görüyor ama sebebi sunucu değil kendi
tarayıcısıydı. Liste tamamlandı.

## v8.3 — İki rapor türü ve PDF dizgi denetimi

### Karakter denetimi — temiz

"Türkçe çalışıyor" demek yetmez; tüm harfler ve tipografi tuzakları
sınandı:

```
çğıİöşüÇĞÖŞÜ – — … ° → • ﬁ ﬂ  →  EKSİK KARAKTER: yok
bozuk kutu (□ / �): 0
```

Gömülü DejaVu doğru çalışıyor. ReportLab'ın varsayılan fontlarında bunlar
bozulurdu.

### İki rapor türü

**Danışan raporu** — sessiz okunmak için. Tam cümleler, iki yana yaslı
dizgi, 10.7 punto, elde kalacak belge.

**Anlatım metni** — danışmanın seansta **sesli okuması** için. Bu bambaşka
bir iştir: yazılı iyi olan cümle okunduğunda kötü olabilir; uzun cümlede
nefes biter, yan cümlecikte dinleyen kaybolur.

Prompt farkı: kısa cümle, yan cümlecik yığmama, sayı/oran sayma
("üçte biri kadar" de), bir paragraf = bir nefeslik düşünce.

Dizgi farkı: 12.2 punto, satır aralığı 20 (göz satır kaçırmasın), **iki
yana yaslama yok** — düzensiz kelime aralığı sesli okumada takılmaya
yol açar.

### Sahne yönergeleri

Danışmanın seansta ihtiyacı yalnız metin değil. Dört yönerge, gövdeden
görsel olarak ayrılmış kutularda:

| Yönerge | Ne yapar |
|---|---|
| **[DUR]** mavi | Burada dur, şu açık uçlu soruyu sor |
| **[İZLE]** yeşil | Danışanın yüzünde/sesinde şuna bak |
| **[DİKKAT]** kırmızı | Bu bölümde yapılabilecek en olası hata |
| **[ARKA PLAN]** gri | Teknik dayanak — **bil ama söyleme** |

Son ikisi önemli: danışman dayanağı bilmeli ki soru gelirse
cevaplayabilsin, ama sesli söylemeyecek.

PDF'in altında ayrıca uyarı var: *"DANIŞMAN NÜSHASI — danışana verilmez.
Köşeli parantezli satırlar sesli OKUNMAZ."* Dosya adı da ayrı
(`_anlatim.pdf` / `_okuma.pdf`).

## v8.4 — Anlatım metni akıcılaştırıldı, vurgu hatası düzeltildi

### Bulunan hata: vurgu görünmüyordu

Anlatım metninde vurgulanacak kelime `*yıldız*` içine alınıyor ve italik
olması gerekiyordu. Ama PDF'te **yalnız düz ve kalın kesim kayıtlıydı**;
`<i>` etiketi sessizce düz yazıya düşüyordu.

Sonuç: danışman sesli okurken hangi kelimeyi vurgulayacağını göremiyordu.
İşlevsel bir kayıp — vurgu anlatımda süs değil, araç.

Dört kesim de kaydedildi (düz, kalın, eğik, kalın-eğik) ve görsel olarak
doğrulandı.

### Akıcılık: prompt "ne yapılmayacağını" biliyordu, akıcılığı bilmiyordu

Eski prompt kısa cümle, yan cümlecik yığmama, sayı saymama diyordu —
hepsi yasak. Konuşmanın kendi zanaatı yoktu. Eklendi:

**Girizgâh** — sesli girişte kapı açılır ("Şunu fark ettim…"), ama bölümde
bir kez.

**Köprü** — önceki bölümden gelerek gir. Kopuk bölümler dinleyende "konu
değişti" hissi yaratıp dikkati düşürüyor.

**Vurgu** — çeviren kelimeyi yıldız içine al, en fazla iki üç yerde.

**Duraklama** — sert cümleden sonra kısa sessizlik: üç nokta ya da "Bunu
bir düşün."

**Ritim** — uzun, kısa, kısa, sonra uzun. Üç kısa cümle telgraf gibi
çıkar; üç uzun cümle dinleyeni kaybeder.

**Konuşma dili** — devrik cümle serbest ("Kolay değil bu."), "ve" yerine
nokta; ama "yani/işte/aslında" doldurmaları iki yerden fazla olmasın.

Son kural: *"Yazdıktan sonra kendi kendine oku: nefes bittiği yerde
cümleyi böl, dilin dolandığı yeri değiştir."*

### Köprü için bağlam genişletildi

Bölümler bağımsız üretiliyor ve öncekinden yalnız 200 karakterlik özet
taşınıyordu — köprü kurmaya yetmiyordu. Anlatım türünde bölüm başına 520,
toplam 3200 karaktere çıkarıldı. Danışan raporunda eski değerler korundu;
orada köprü gerekmiyor, tekrar önleme yetiyor.

## v8.5 — Denetim: altı uç sızma testinde hiç yoktu

Hızlı bir özellik dizisinden sonra kapsamlı denetim yapıldı ve gerçek bir
boşluk çıktı: **rapor, rapor-bolum, rapor-pdf, soru-cevap, manevi ve sehir
uçlarının hiçbiri sızma testinde yoktu.** Eklenip test edilmemişlerdi.

On dört test yazıldı; hepsi kapalı çıktı ama yazılmadan bunu bilmek
mümkün değildi.

| Sınanan | Sonuç |
|---|---|
| Rapor analizsiz / sıra taşması / negatif sıra | 422 |
| **PDF dosya adı enjeksiyonu** (3 varyant) | temizleniyor |
| PDF işaretleme enjeksiyonu (`<font size=99>`) | çökmüyor |
| PDF bölümsüz | 422 |
| Soru geçersiz kod / 40 kod | 503 / 422 |
| Şehir geçersiz koordinat (3 varyant) | 422 |
| Manevi analizsiz | 422 |

Dosya adı enjeksiyonu en kritik olanıydı: `ad` alanı doğrudan
`Content-Disposition` başlığına giriyor. `../../etc/passwd`,
`a"; filename="x.exe` ve satır sonu enjeksiyonu (`\r\n`) denendi; üçü de
temizleniyor.

**TOPLAM: 50 test, 0 açık.**

### Test altyapısında bulunan hata

Yeni testleri eklerken `istek()` yardımcısını yeniden yazdım ve iki
parametreyi kaybettim: üçüncü dönüş değeri **süre** olmalıydı (zamanlama
sızıntısı testi buna dayanıyor) ve `zaman` parametresi vardı. Pentest
üçüncü adımda çöküyordu.

Kendi test aracını bozmak sinsi bir hata: testler "çalışıyor" görünürken
aslında hiç koşmuyordu. İkisi de geri kondu, imza tam korundu.

## v8.6 — Defter katmanı koddan tamamen kaldırıldı

v6.3'te arayüzden kaldırılmıştı, sunucu tarafı "gerekirse geri gelir" diye
duruyordu. Artık koddan da silindi.

**Kaldırılanlar:** `app/defter.py` (17.7 KB), `app/danisan.py` (9.6 KB),
10 uç, 5 şema sınıfı, arayüzdeki ölü JS ve `ERISIM.txt`.

| | Önce | Sonra |
|---|---|---|
| Modül | 27 | **25** |
| Uç | 47 | **37** |

Silinen uçlar 404 dönüyor; ana akış (analiz, soru, rapor, sentez) 200.
21 bölüm, sıfır JS hatası.

Bununla birlikte **ön-kayıt/Brier ölçümü ve danışan geçmişi de gitti** —
modelin isabetini ölçen tek katman buydu. `ZIC_DEFTER` ortam değişkeni
artık kullanılmıyor; Render'dan silinebilir.

## v8.7 — Söküm sonrası denetim

Defter kaldırıldıktan sonra bağlam bütünlüğü ve ölü referanslar denetlendi.

### Bağlam eksiksiz

AI'ye giden 14 bloğun 14'ü yerinde:

```
GÜVEN NOTU · ÖNCE BUNLARI OKU · ÇEKİRDEK · ALAN TOPOLOJİSİ ·
DENEME MODÜLLERİ · KABZ/BAST · KADİM KATMAN · HUDÛD-I FELEK ·
BUGÜNKÜ GÖK · KAPILAR · YER · ŞİRÂ ÇEVRİMİ · CHRONO-GRAVITRON ·
HUMAN DESIGN

EKSİK: yok · MÜKERRER: yok · 12.510/16.000 karakter
```

Söküm bağlamdan hiçbir şey düşürmemiş.

### Bulunan tek kalıntı

`CozumInput` şeması duruyordu ama hiçbir uç kullanmıyordu — defterin
"tahmin çözme" ucuyla birlikte sahipsiz kalmış. Kaldırıldı.

### Denetim sonuçları

| Takım | Sonuç |
|---|---|
| Derleme + tanımsız ad | temiz |
| Derin doğrulama | 96/96 |
| Kenar durum | 43/43 |
| **Sızma testi** | **50/50 kapalı** |
| 16 uç canlı sınama | hata yok |
| Tarayıcı (masaüstü + mobil) | JS hatası yok |

Yönetici 21 bölüm, doğru dört bölüm açık; misafir mobil 3 bölüm, yatay
taşma yok, yasak terim yok.

## v8.8 — Tekrarlar bağlandı, katmanlar birbirine bağlandı

İki ölçülebilir sorun vardı.

### 1 · Aynı nokta birden çok blokta tekrarlıyordu

Ölçüldü: bir haritada **11 konum birden çok blokta** geçiyordu, bazıları
üç kez (ÇEKİRDEK + ALAN TOPOLOJİSİ + KADİM KATMAN). Model bunu üç ayrı
bulgu sanıp aynı şeyi üç kez söyleyebiliyor ya da ağırlığını üçe
katlıyordu.

Çözüm silmek değil, **bağlamak**. İlk geçiş olduğu gibi kalıyor;
sonrakiler `(aynı nokta — ÇEKİRDEK)` diye işaretleniyor. Sonuna da not
düşülüyor:

> Bu AYRI bir bulgu DEĞİLDİR; aynı noktanın başka bir açıdan görünüşüdür.
> İki kez sayma, ama örtüşmeyi kullan: birden çok katmanın aynı noktayı
> göstermesi o noktanın ağırlığını artırır.

Test haritasında **13 tekrar bağlandı.**

### 2 · Katmanlar yan yana duruyordu, bağlı değildi

Bağlam 14 bloğu yan yana veriyordu; modelin aralarındaki bağı kendi
bulması gerekiyordu. Bulduğunda iyi oluyor, bulamadığında katmanları tek
tek özetleyip bırakıyordu.

Artık bağ **sunucuda hesaplanıp** modele veriliyor — ve çekirdekten
ÖNCE, üçüncü blok olarak. Beş bağ hesaplanıyor:

| Bağ | Ne söyler |
|---|---|
| Altı geleneğin yakınsaması | 4+ örtüşme → yaslan; 2 ve altı → tek kapıya yaslanma |
| Hudûd dışı kapasite × karar eşiği | Kontrol edilemeyen yan karar anında devrede mi |
| Dönem yönü × çatal | Kişi kendi dönemine karşı mı çalışıyor |
| Doğal karar biçimi × karar eşiği | Kararı yanlış yerden mi veriyor — *en işe yarar bulgu* |
| Şikâyet evi × sebep evi | Aynıysa yeri biliyor çözümü bilmiyor; farklıysa **yanlış yere bakıyor** |

Üç farklı haritada 3, 4 ve 4 bağ üretti — her birinde farklı içerikle.

Bağlam 13.560/16.000 karakter, 16 blok, eksik ve mükerrer yok.

## v9.0 — Beş konfor iyileştirmesi

### 1 · Oturum sürekliliği — en önemlisi

Analiz, sohbet, sentez ve yazılmış rapor bölümleri sayfa yenilenince
**tamamen kayboluyordu**. Bir saatlik seans tek bir yenilemeye kurban
gidiyordu.

Artık üretilen her şey cihazda saklanıyor; sayfa açıldığında giriş
ekranında *"Yarım kalmış oturum: … · 10 rapor bölümü"* çıkıyor.
Sunucuya hiçbir şey gönderilmiyor, 12 saatten eski yedek atılıyor.

Test: 10 bölümlük rapor yazıldı → sayfa yenilendi → devam edildi →
**21 bölüm ve 10 rapor bölümü geri geldi.**

### 2 · Tek giriş çubuğu

AI'ye sekiz ayrı kapı vardı. Sayfanın altında sabit duran tek bir çubuk
eklendi: yazdığın metin içeriğine göre doğru yüzeye yönlendiriliyor,
ilgili bölüm açılıp oraya kaydırılıyor. Sekiz kapı bire indi, hepsi
çalışmaya devam ediyor.

### 3 · Rapor akarken görünüyor

Önceden on bölüm arka planda yazılıyor, sonunda PDF iniyordu. Artık her
bölüm bitince ekranda beliriyor: sen okurken sonraki yazılıyor.

İki kazanç daha: her bölümün yanında **"Yeniden yaz"** düğmesi var
(önceden ya hepsi ya hiçbiri), ve hata olursa yazılan bölümler
kaybolmuyor — düğmeye tekrar basınca kaldığı yerden devam ediyor.
PDF ayrı bir adım oldu; beğendiğinde alıyorsun.

### 4 · Sunum kipi

Danışana ekran gösterirken: 26 punto başlık, 17 punto gövde, tek sütun
760 px, AI düğmeleri ve gezinme gizli.

### 5 · Yan içindekiler

21 bölüm için sabit liste; hangi bölümde olduğun vurgulanıyor, tıklayınca
kapalı bölüm açılıp oraya gidiliyor. 1400 px altında gizleniyor.

### AI dayanıklılığı

Sağlayıcı zincirinin tamamı düşerse, soğumalar yok sayılarak **bir tur
daha** deneniyor. Geçici kesinti bütün seansı düşürmüyor.

### Yol boyunca yakalanan üç hata

**Kurulum çağrıları eksikti** — `girisCubuguKur()` iki yerde
çağrılmıyordu; çubuk bazı akışlarda hiç oluşmuyordu.

**Devam şeridi giriş perdesinin altında kalıyordu.** Önce z-index ile
çözmeye çalıştım, bu sefer şerit giriş kartlarını örttü. Doğru çözüm
şeridi perdenin **içine** koymaktı — kullanıcı zaten orada seçim yapıyor.

**Mobilde "başa dön" düğmesi gönder düğmesini yutuyordu.** İkisi aynı
köşede sabit; yukarı düğmesi tıklamayı kesiyordu. Konum ayrıldı.

## v8.9 — Yan içindekiler, sunum kipi, akan rapor

### Ölçüm hatam ve sonucu

Oturum sürekliliğini "yok" diye ölçüp eklemeye kalktım. **Zaten vardı** —
`localStorage.setItem(OTURUM_ANAHTAR, …)` değişkenle yazıldığı için
literal arayan taramam görmedi.

Eklediğim ikinci kopya `OTURUM_ANAHTAR`'ı yeniden tanımladı ve
**betiğin tamamı çöktü**: sayfa açılıyor ama hiçbir düğme çalışmıyordu.
Duplike kaldırıldı, çağrılar mevcut `oturumYedekle()`'ye bağlandı.

Ders: bir özelliğin yokluğunu kanıtlamak varlığını kanıtlamaktan zordur;
tek bir grep deseni yeterli değil.

### Eklenenler

**Yan içindekiler** — 21 bölümün listesi solda sabit; tıklayınca ilgili
bölüme gider ve kapalıysa açar. Kaydırdıkça hangi bölümde olduğun
işaretlenir. 1180 px altında gizlenir.

**Sunum kipi** — danışana ekran gösterirken: başlık 26 px, gövde 17 px,
tek sütun 820 px, içindekiler/başlık/AI düğmeleri gizli. Sağ altta
düğme, çıkış için Esc.

**Akan rapor** — bölümler bittikçe ekranda görünüyor; her bölümün yanında
**"yeniden yaz"** düğmesi var. Önceden ya hepsi ya hiçbiriydi; bir bölüm
kötü çıkarsa baştan başlamak gerekiyordu. PDF, yeniden yazılanlar dahil
son hâlden kuruluyor.

**Baskı desteği** — `@media print` ile gezinme ve düğmeler gizleniyor.

### Doğrulama

21 bölüm, 21 içindekiler bağlantısı, sunum kipi açılıp Esc ile kapanıyor,
sohbet 3 balon, oturum yedeği yazılıyor, yenileme sonrası devam şeridi
çıkıyor — **sıfır JS hatası, sıfır HTTP hatası.**

## v9.0 — Çelişki paneli ve önden hazırlanan sorular

### Çelişkiler (AI çağrısı yok)

Katmanların birbirini **tutmadığı** yerler ayrı bir bölümde toplanıyor.
Örtüşme zaten veriliyordu; asıl bilgi çoğu zaman çelişkidedir.

Beş çelişki hesaplanıyor, hepsi mevcut veriden:

| Çelişki | Ne yakalar |
|---|---|
| Beklemek mi, bırakmak mı | Karar biçimi "bekle" derken eşik "terk et" diyorsa |
| Yakın ama zor | Eşik dibinde ama çıkış direnci yüksekse |
| Gelenekler anlaşamıyor | Yakınsama 2 ve altındaysa |
| Dengesizlik var ama taşan yok | Asimetri yüksek, hudûd dışı cisim yok |
| Yaşanan yer ile karar yeri ayrı | Havza ile eşik farklı yerdeyse |

Her çelişki üç parça veriyor: bir yan, öbür yan, **ne yapmalı**. Test
haritasında 3 çelişki çıktı. Bağlama da giriyor (`[ÇELİŞKİLER]` bloğu).

### Önden hazırlanan sorular

Seansta her soru 40 saniye bekletiyordu. Artık analiz biter bitmez bu
harita için **en olası üç sorunun** cevabı arka planda yazılıyor;
tıklandığında anında geliyor.

Sorular rastgele değil, bulgulara göre seçiliyor: şikâyet ile sebep farklı
evdeyse "tekrar eden kalıp", kariyer evleri baskınsa "rızık", karar biçimi
beklemeyi gerektiriyorsa "kendi işim" öne çıkıyor.

**Hata vermiyor.** Gateway tamamen kapalıyken sınandı: analiz 22 bölüm
çalıştı, çelişki paneli göründü (AI gerektirmiyor), hazır sorular sessizce
"tıkla" durumuna düştü ve **kullanıcıya hiçbir hata gösterilmedi**.
Tıklandığında normal yoldan üretiliyor.

Sıralı çalışıyor, hız sınırını zorlamıyor.

### Yakalanan hata

`sorular.py` içinde `Any` importu eksikti — `onerilen()` çalışma anında
patlayacaktı. `adtarama.py` yakaladı; `py_compile` görmezdi.

## v9.1 — Anında arama ve direnç haritası

İkisi de **AI çağrısı gerektirmiyor** — hata riski yok, bekleme yok,
maliyet yok.

### Anında arama

Danışan bir şey söylüyor ve senin o an bilmen gereken şey "bu haritada var
mı, nerede?" Şu ana kadar bunun için sohbete yazıp beklemek gerekiyordu.

Sağ üstte sabit bir arama kutusu. **Ağa hiç gitmiyor** — bölümlerin
ekrandaki metni üzerinde çalışıyor. Sonuç: hangi bölümlerde kaç kez
geçtiği, bağlamıyla birlikte. Tıklayınca o bölüme gidiyor ve kapalıysa
açıyor. `Ctrl/⌘+K` ile odaklanır, `Esc` ile kapanır.

Ölçüm: "karar" → 6 bölüm, **458 ms**, sıfır ağ isteği.

### Direnç haritası

Danışmanın seansta en çok işine yarayan bilgi: **bu kişi neye itiraz
edecek.** Sistem bunu zaten biliyordu, söylemiyordu.

Beş durum hesaplanıyor; her biri "kapatır" ve "açar" olarak ikiye ayrılmış:

| Ne zaman | Örnek |
|---|---|
| Kaçış biçimini konuşurken | Yanlış refleksi yüzüne söylemek kapatır; hamle tarafından söylemek açar |
| Adım önerirken | "Hemen yap" kapatır; koşul vermek açar |
| Karar konusunu açarken | "Karar ver" kapatır; "ne zaman kapattın" açar |
| Değişimden söz ederken | Hızlı dönüşüm vaadi kapatır; küçük tekrarlanabilir adım açar |
| Asıl sebebi açarken | Şikâyeti atlamak kapatır; önce tanıyıp köprü kurmak açar |

Bağlama da giriyor (`[DİRENÇ]` bloğu), yani AI de bu dile göre yazıyor.

### Yakalanan iki hata

`icindekilerKur` **iki kez tanımlanmıştı** — bir önceki turda eklediğim
kopya, zaten var olanın üstüne binmişti. Duplike kaldırıldı.

Temizlik sırasında `aramaKur` tanımı da silindi ve arama kutusu hiç
oluşmadı; geri kondu. Ders: duplike temizlerken blok sınırını daraltmak
gerekiyor, yoksa yanındaki sağlam kod da gidiyor.

## v9.2 — Rapor uzunluğu, anlatıcı dili ve PDF tasarımı

### Neden kısa çıkıyordu — üç sebep

**1. Talimat kısa tutuyordu.** Prompt "3-5 paragraf" diyordu. **6-9**'a
çıkarıldı, gerekçesiyle: *"Bu bir rapor bölümü, bir not değil. Kişi bunu
elinde tutacak, belki yıllar sonra tekrar okuyacak."*

**2. Jeton sınırı dardı.** 1500 jeton Türkçe için yetmiyordu — Türkçe
jeton-yoğun bir dildir. **2100**'e (anlatım 2200), devam turu 600 → 900.

**3. Anlatı zanaatı yalnız sesli metinde vardı.** Girizgâh, köprü, ritim
kuralları `ANLATIM_SISTEM`'e yazılmıştı; danışan raporunda hiçbiri yoktu.
Rapor bölüm bölüm üretildiği için bölümler kopuk çıkıyordu.

### Anlatıcının dili (yeni)

Danışan raporuna kendi zanaat bölümü yazıldı:

- **Bağlantı** — önceki bölümden gelerek gir; bölümler arasında görünmez
  bir iplik olsun. *"Kopuk bölümler dosya olur, anlatı olmaz."*
- **Somutluk** — bir yanı anlatırken görüldüğü ANI tarif et: nerede, ne
  yaparken, kime karşı. Okuyan sahneyi görmeli.
- **Genişlet, sıralama** — bir bulguyu söyleyip geçme. *"Dört bulguyu
  sıralamaktansa bir bulguyu dört yönden anlatmak daha çok işe yarar."*
- **Ritim** — uzun açıklamadan sonra tek cümlelik kısa paragraf; okuyan
  orada durur.
- **Ses** — metin boyunca aynı ses: kişiyi tanıyan, ciddiye alan,
  gerektiğinde sert ama asla küçümsemeyen. *"Ne rapor memuru ne falcı."*

### PDF tasarımı

| | Önce | Sonra |
|---|---|---|
| Kapak | yok — başlık gövdeye yapışık | ayrı kapak sayfası, üstte kalın çizgi |
| İçindekiler | yok | kapakta numaralı liste |
| Bölüm | üçte bir sayfa sonu | her bölüm yeni sayfada, `01` numarası |
| Kenarlık | 22 mm (satır 100+ karakter) | **26 mm** — satır ~78 karakter |
| Altbilgi | düz metin | ince ayraç çizgisi + numara |

Satır uzunluğu okunabilirliği belirler: A4'te dar kenarlıkla göz satır
kaçırır.

Test: 10 bölüm → **11 sayfa**, kapak + içindekiler doğru, Türkçe
karakterler ve italik vurgu render ediliyor.

## v9.3 — Tasarım denetimi: üç görünmez hata

Ekran görüntüsü almadan fark edilmeyecek üç hata vardı.

### 1 · Gezinme çubuğu temaya bağlı değildi

Koyu temalarda (Rasat, Minyatür) üst gezinme çubuğu **beyaz kalıyor** ve
ekranı ortadan kesiyordu. Değişkenlere bağlandı; dört temada da ölçüldü:

```
bauhaus   rgb(255,255,255)     rasat     rgb(19,26,48)
brutalist rgb(255,255,255)     minyatur  rgb(26,39,87)
```

### 2 · Arama kutusu okunmuyordu

Koyu zeminde yer tutucu metin neredeyse görünmezdi. Zemin, gölge ve
placeholder rengi temaya bağlandı. Konumu da 14 px'ten 78 px'e indirildi —
başlıkla çakışıyordu.

### 3 · Kendi eklediğim kural içindekiler numaralarını sildi

Yan içindekiler numaraları CSS sayacıyla (`counter(ic)`) üretiyordu.
Geçen turda eklediğim `.icindekiler a` kuralı bunu ezdi ve numaralar
kayboldu. Çakışan kural kaldırıldı, özgün tasarım korundu.

**Bu üçüncü kez oluyor:** var olan bir şeyin üstüne yenisini yazıyorum.
Ders: bir bileşene dokunmadan önce o bileşenin zaten nasıl çözüldüğüne
bakmak gerekiyor.

### Renk ilişkileri sıkılaştırıldı

**Rasat** — zemin derinleştirildi (#0B1020 → #090D1A), yüzeyle arasındaki
fark küçültüldü (katman hissi için fark küçük olmalı), pirinç
doygunlaştırıldı (#C9962E → #D4A03A) ki koyu zeminde sönmesin. Metin saf
beyaz değil (#E8E6DF) — saf beyaz koyu zeminde göz yorar.

**Minyatür** — lapis koyulaştırıldı ki altın üstünde parlasın; krem metin
sarıya kaydırıldı, çünkü elyazması kâğıdı beyaz değildir.

### Ortak ince ayar

Geçiş yumuşatma (ani renk değişimi ucuz görünür), seçim rengi, klavye
odak halkası, koyu temada yazı yumuşatma (koyu zeminde harfler olduğundan
kalın görünür), koyu temada kartlara iç ışık.

Ayrıca sabit alt çubuk sayfa sonundaki içeriği örtüyordu — 96 px alt
boşluk eklendi.

## v9.4 — Tam denetim

On başlıkta denetlendi; **iki gerçek eksik** bulundu ve düzeltildi.

### Bulunan 1: üç bölümün AI talimatı yoktu

Son turlarda eklenen **çelişki, direnç ve danışan soruları** bölümlerinin
"AI ANALİZİ" düğmesi vardı ama kendi talimatları yoktu; genel talimatla
çalışıyorlardı. Üçü de yazıldı. Talimat sayısı 25 → 28.

Bu ikinci kez oluyor: bölümü ekleyip talimatını yazmayı atlıyorum.

### Bulunan 2: bağlam tavanı daralmıştı

Çelişki ve direnç blokları eklenince bağlam **15.160/16.000** oldu — %95.
Altı farklı harita ölçüldü; en dolu 14.990, yani pay yalnız **%6**. Yeni
bir katman ya da yoğun bir harita blok düşürürdü.

Tavan **19.000**'e çıkarıldı (~5.400 jeton) — hem pay bırakıyor hem her
modelin bağlamına rahat sığıyor. Altı haritanın hiçbirinde blok düşmüyor.

### Denetim tablosu

| Başlık | Sonuç |
|---|---|
| Derleme + tanımsız ad | temiz |
| Derin doğrulama | 96/96 |
| Kenar durum | 43/43 |
| Duman testi | 0.5 sn |
| **Sızma testi** | **50/50 kapalı** |
| Sürüm tutarlılığı | sunucu = arayüz |
| Ölü kod | import 0, şema 0, talimat 0 |
| 15 uç canlı | hata yok |
| Bağlam | 18 blok, mükerrer yok |
| Tarayıcı (masaüstü + mobil) | JS/HTTP hatası yok |

Analiz 0.75–0.79 sn · 106 KB · 14 katman. Misafir payı 16 KB, sızıntı yok.
Yönetici 23 bölüm, misafir mobilde 3 bölüm ve sıfır yatay taşma.

## v9.5 — Dosya bölme ve anlatım metninde kenar notu

### index.html bölündü

4.287 satır, 216 KB tek dosyaydı. Son üç turda üç kez kendi yazdığımın
üstüne yazdım: `OTURUM_ANAHTAR` çakışması, `icindekilerKur` duplikesi,
içindekiler numaralarını silen kural. Tesadüf değildi — dosya boyutunun
sonucuydu.

| Dosya | Satır | Boyut |
|---|---|---|
| `index.html` | 195 | 10 KB |
| `stil.css` | 1.077 | 56 KB |
| `uygulama.js` | 3.023 | 148 KB |

Bölme sırasında **kritik bir eksik yakalandı**: sunucuda `/static/` ucu
yoktu, yalnız `index.html` sunuluyordu. Bölünce stil ve betik 404 dönerdi
— yani uygulama tamamen çalışmazdı. Uç eklendi, dosya adı düzenli ifadeyle
temizleniyor, dizin dışına çıkış 404.

Doğrulandı: stil ve betik 200 ve doğru MIME türüyle geliyor, yol aşımı 404,
23 bölüm ve dört tema çalışıyor, sohbet 3 balon.

### Anlatım metninde kenar notu

Sahne yönergeleri metnin AKIŞINI KESİYORDU: sesli okurken göz konuşma
metninden kopuyor, sonra yerini arıyordu.

Artık iki sütun: solda konuşma metni kesintisiz akıyor (%62), sağda
yönergeler (%36), aralarında ince ayraç çizgisi. Yönerge yazı boyutları
dar sütuna göre küçültüldü.

Danışan raporu tek sütun kaldı — orada yönerge yok, bölmeye gerek yok.

## v9.6 — PDF kapağında natal çark ve danışman adı

Doğum haritası raporunda **haritanın kendisi yoktu**. Kişi "haritam nerede"
diye sorar ve haklıdır.

Çark doğrudan ReportLab ile çiziliyor — SVG dönüşümü ek bağımlılık ve font
sorunu getirirdi. Baskı için tasarlandı: renk yerine çizgi kalınlığı ve gri
tonu ayrım yapıyor, siyah-beyaz yazıcıda da okunuyor. Burç bölmeleri, ev
sınırları (köşe evleri kalın), cisimler ve ASC/MC vurgusu.

### İlk çizimde iki hata

**Burçlar ters yönde ilerliyordu.** Boğa'dan sonra Koç geliyordu; İkizler
gelmeliydi. İşaret hatası (`180 - x` yerine `180 + x`). Çarkta yön yanlış
olunca ev sıraları da ters okunur — sessiz ama ciddi bir hata. Ekran
görüntüsü almasam fark edilmezdi.

**Cisimler üst üste biniyordu.** Eşik 7° ve adım 11 px yetmiyordu; dört
cisim aynı bölgede çakışıyordu. Eşik 13°'ye, adım 14 px'e çıkarıldı ve
cisimler boylama göre sıralanarak yerleştiriliyor.

### Danışman adı

Kapakta danışman adı görünüyor. Kaynak: istek gövdesindeki `danisman`
alanı ya da `ZIC_DANISMAN` ortam değişkeni. Boşsa kapakta ad çıkmaz,
rapor yine üretilir.

Çark çizilemezse (veri eksik, hesap hatası) sessizce atlanıyor — belge
her hâlükârda üretiliyor.

## v9.7 — "Her yer hata" — kök sebep: jeton talebi zaman aşımını aşıyordu

Üretimde her yerde hata çıkıyordu: sohbet "yanıt beklenenden uzun sürdü",
bölüm analizi "danışmana ulaşılamıyor", misafir "okumalar üretilemedi".

**Sebep tek ve ölçülebilirdi.** İstenen jeton sayısı, zaman aşımına
sığmıyordu:

| Çağrı | İstenen jeton | Gerçek süre (~32 j/sn) | Sınır |
|---|---|---|---|
| Misafir kategoriler | **3200** | ~100 sn | 75 sn |
| Bütünsel okuma | 2600 | ~81 sn | 75 sn |
| Sohbet | 2200 | ~69 sn | 75 sn |

Üstteki ikisi her seferinde, üçüncüsü sık sık kesiliyordu.

### Çözüm: jeton tavanı süreden hesaplanıyor

```
tavan = TIMEOUT × 0.80 × 32 jeton/sn
```

75 saniye için **1920 jeton** — yaklaşık 60 saniye, sınırın altında.
Hiçbir çağrı bunu aşamıyor; `guvenli_jeton()` her istekte kırpıyor.

`AI_TIMEOUT` değiştirilirse tavan da kendiliğinden değişir — elle ayar
gerekmiyor.

### Misafir yorumları partilendi

Bütün kategoriler tek çağrıdaydı. Üçerli partilere bölündü; bir parti
başarısız olursa ötekiler yine yazılıyor — misafir hiç okuma göremez
durumdan çıktı.

### Ölçüm

Gerçekçi yavaş modelde (30 ms/jeton ≈ 33 jeton/sn):

```
sohbet   200 (57.6 sn)     ← önce ~96 sn, kesiliyordu
bölüm    200 (57.6 sn)
sentez   200 (57.6 sn)
```

### Mobilde sabit öğe yığılması

Beş sabit öğe aynı köşede üst üste biniyordu: yukarı düğmesi, sunum kipi,
arama kutusu, alt giriş çubuğu, gezinme şeridi. Alttaki tıklanamıyordu.

Dar ekranda yeniden düzenlendi: arama akışa girdi, sunum kipi ve yukarı
düğmesi alt çubuğun üstünde yan yana, gezinme şeridi üste alındı.
**Çakışma: yok. Yatay taşma: 0 px.**

## v9.8 — Misafir tarafı sadeleştirildi

Sonuç ekranı zaten temizdi ama **form ekranında yedi teknik terim** vardı:
Berzah, Kara Delik, Placidus, UTC, "yaz saati", "yuvarlaksa", "tahmindir".
Misafir daha bilgilerini girmeden iç terminolojiyle karşılaşıyordu.

### Kaldırılanlar (yalnız misafirde)

| Alan | Önce | Sonra |
|---|---|---|
| Mod açıklaması | "Kara Delik, Ak Delik ve Berzah kişinin kendi alanından çıkar" | "Doğum bilgilerinizi girin, okumanız çıksın." |
| Saat uyarısı | "Ev katmanı ±15 dakikadan sonra güvenilmez; Berzah kararsız denge noktasıdır" | "Doğum saatiniz ne kadar kesinse okuma o kadar isabetli olur." |
| Ev sistemi seçici | görünür (Placidus…) | gizli |
| Rektifikasyon paneli | görünür | gizli |
| Doğum anı önizlemesi | UTC, saat dilimi kodu, koordinat | yalnız yerel saat |
| Düğme | "Haritamı yorumla" | **"Okumamı çıkar"** |

### Yaklaşım

Hesap DEĞİŞMİYOR — yalnız görünürlük. Alanlar `data-teknik` ve `data-terim`
ile işaretlendi; `misafirSadelestir()` role göre gizliyor. Yönetici hepsini
görmeye devam ediyor.

Doğrulandı: misafir formunda ve sonucunda **sıfır teknik terim**; yönetici
tarafında Berzah, Kara Delik, Placidus ve 23 bölüm yerinde.

## v10.0 — LUNASYON TAKVİMİ: ay hafta hafta neyi açıyor

Sistem şimdiye kadar yalnız **"bugünkü gök"** veriyordu — anlık bir kesit.
Oysa astrolog zamanın YAPISIYLA çalışır: her yeni ay bir konu açar, her
dolunay olgunlaştırır, tutulmalar aylara yayılan kapılar açar. Bu eksikti.

### Ne hesaplanıyor

Bir yıllık takvim — test haritasında **24 olay, 5 tutulma**:

| | Sayı |
|---|---|
| Yeni ay | 10 |
| Dolunay | 9 |
| Güneş tutulması | 2 |
| Ay tutulması | 3 |

Her olay için: tarih, **natal ev**, solar ev, natal noktalara temaslar
(kavuşum/karşıt/kare/üçgen, orb'la) ve **ağırlık** — o olayın bu kişi için
ne kadar belirleyici olduğu (0–10).

Yeni ay ve dolunay, Ay–Güneş farkının 0° ve 180°'yi kestiği an olarak ikiye
bölmeyle saniye hassasiyetinde bulunuyor. Tutulmalar Swiss Ephemeris'in
kendi arayıcılarından — yaklaşık hesap değil gerçek geometri.

### Yakalanan hata: modüler sarmal tuzağı

İlk koşumda **bütün olaylar "yeni ay" çıktı**, tek bir dolunay yoktu.
Hesap doğruydu (0° ve 180° kesişimleri tam), etiket yanlıştı.

Sebep: sapma işlevi farkı [-180,180) aralığına indirger ve bu aralık
180°'de +180'den −180'e **atlar**. İşaret değişimine bakan ikiye bölme, bu
atlamayı da "sıfır geçişi" sanıyordu — 0° arayan çağrı dolunayları buluyor
ve onları yeni ay diye etiketliyordu.

Çözüm: bulunan anın gerçekten hedefe yakın olduğu sınanıyor. Şimdi
10 yeni ay / 9 dolunay doğru ayrılıyor.

### Haftalık okuma

Takvimde bir satıra dokununca o olayın **bu kişide neyi görünür kıldığı**
yazılıyor. Prompt türe göre ayrışıyor:

- **Yeni ay** bir şey başlar demek DEĞİL — bir konu gündeme gelir;
  görmezden gelinirse kaybolmaz, ertelenir.
- **Dolunay** bir şey biter demek DEĞİL — olgunlaşır, saklanan
  saklanamaz hâle gelir.
- **Tutulma** aylara yayılır ama "kader anı" dili kurulmaz; kapı aralanır,
  kişi girer ya da girmez.

Mutlak sınır: *"Şu gün şu olacak" ASLA. Gök olayı olay üretmez; var olan
bir konunun görünürlük kazandığı aralığı gösterir.*

Ayrıca korkutma yasağı — tutulma dili özellikle korkutucu kullanılır.

### Bölüm numarası çakışması

Lunasyon eklenirken `Ham veri` ile aynı numarayı aldı ve bölüm hiç
çizilmedi. Numaralar yeniden sıralandı: 22 bölüm, çakışma yok.
Ayrıca blok yanlışlıkla `index.html`'e yazılmıştı — dosya bölmesinden
sonra render kodu `uygulama.js`'te. Doğru dosyaya taşındı.

## v10.1 — Lunasyon: solar dönüş, kategori bağı, öneriler ve sohbet

Takvim tek başına "10 Ekim'de yeni ay var" der — bu bir bilgi parçasıdır,
tavsiye değil. Beş katman eklendi.

### 1 · Solar dönüş entegrasyonu

Aynı gök olayı **natal ve solar haritada farklı eve düşer** ve astrologun
kullandığı asıl ayrım budur: konunun *dış görünüşü* ile *bu yılki
karşılığı*.

24 olayın 24'ünde solar ev dolu. Örnek:
`2026-09-26 dolunay · natal 12. ev (geri çekilme) · solar 11. ev (çevre ve
gelecek)` — sistem bunu ayrıca söylüyor: *"konu iki yerden birden geliyor."*

**Yakalanan hata:** `kabzbast_v1.solar_return` Türkçe cisim anahtarı
bekliyor (`bodies['Güneş']`), `build_chart` İngilizce veriyor
(`bodies['Sun']`) — doğrudan çağrı `KeyError` atıyordu. Uyumlu bir
`solar_donus()` sarmalayıcısı yazıldı.

### 2 · Kategori bağı

Her lunasyon, sistemdeki **hangi analiz kategorisini uyandırdığını**
hesaplıyor. İki yoldan: düştüğü ev → hayat alanı → kategoriler; değdiği
nokta → o noktanın baskın olduğu katman. Tutulmalarda puan ×1.4.

Örnek: *2027-02-06 güneş tutulması → Hüküm, Alan topolojisi, Yer.*

### 3 · Otomatik öneriler (AI'sız)

Hesaplanmış bağdan türeyen somut öneriler. Türe göre ayrışıyor: yeni ay
"bakman yeterli", dolunay "saklanan görünür oluyor", tutulma "bu bir an
değil bir dönem". Dar orb'lu temaslar ayrıca işaretleniyor. Ağırlık
düşükse *"seansta öne çıkarmaya gerek yok"* diyor.

### 4 · AI okuması

Önerilerin üstüne geliyor — onları tekrarlamıyor, *neden öyle ve kişide
nasıl görünür* diye açıyor.

### 5 · Sohbet

Her olay için kendi sohbet kutusu, geçmişi koruyarak. Test: iki turda
4 balon.

Prompt sınırı: *"Şu gün şu olacak" ASLA. Tutulma dili korkutucu
kullanılır — kullanma. Kapı aralanır, kişi girer ya da girmez.*

## v10.2 — Kategori bağı gerçekten tamamlandı

Sorulduğunda saymak gerekti: **bağlı olduğunu sandığım eşleme eksikti.**

| | Önce | Sonra |
|---|---|---|
| Arayüzdeki bölüm | 26 | 26 |
| Lunasyona bağlı | **14** | **22** |
| Yanlış kod | 2 | 0 |

### Bulunan üç hata

**1. Yanlış kod adı.** `gravitron` ve `yer` yazılmıştı ama arayüzde bunlar
`chrono` ve `kartografi`. Yanlış kod, o bölümü hiç uyandırmıyordu —
sessiz bir kopukluk: sistem "bu kategoriye bak" diyor ama öyle bir
kategori yok.

**2. Sekiz bölüm hiç bağlı değildi:** Alan halkası, Alanın kenarları,
Yürüyen Berzah, Ham veri, Direnç, Sinastri, Kompozit, Alan topolojisi.
Hepsi eklendi.

**3. AI hangi kategoriye bakacağını bilmiyordu.** `bag.kategoriler`
hesaplanıp veriye konuyordu ama promptta buna dair tek kelime yoktu —
model onu görmezden gelebilirdi. `UYANAN KATMANLAR` bölümü eklendi:

> O katmanlara dön, oradaki bulguyu bu olayla BİRLEŞTİR. Katmanın adını
> anma — bulgusunu kullan.

### Ölçüm

Bir yıl boyunca **18 farklı kategori** uyanıyor; her olay kendi üçlüsünü
çağırıyor. Örnek: *17 Ağustos ay tutulması, natal ve solar 9. ev →
Yer · astrokartografi, Şi'râ çevrimi, Spiritüel çalışma.*

Bağlanmayan dört bölüm bilinçli: Formülasyon, Bütünsel okuma, Danışan
soruları ve Lunasyonun kendisi — bunlar analiz katmanı değil, araç.

## v10.3 — Tema revizyonu

Ekran görüntüsüyle bakınca üç sorun net görüldü. Temaları hızlı yazmış,
görsel olarak yeterince denetlememiştim.

### 1 · Amblem temaya ait değildi

Sayfanın en görünür öğesi sabit Bauhaus renklerindeydi: kırmızı, mavi,
sarı. Lacivert zeminde (Rasat, Minyatür) yabancı duruyordu — tema
değişiyor, logo değişmiyordu.

Amblem CSS değişkenlerine bağlandı; her tema kendi paletinden veriyor:

```
bauhaus   #E0301E    rasat     #E4694A
brutalist #FF3B00    minyatur  #C4362C
```

### 2 · Kartlar zeminden ayrılmıyordu

Zemin ile yüzey arasındaki fark 2–3 tondu; kart bir kutu gibi değil,
aynı düzlemde bir dikdörtgen gibi duruyordu. Koyu temalara üstten ışık
alan dolgu, ince kenar ve derin gölge eklendi. Açık temada da hafif
kenar ve gölge var.

### 3 · İki kart tek kutu gibi görünüyordu

`gap:2px` ve kapsayıcının kendi çerçevesi yüzünden "Yönetici" ve
"Misafir" tek bir kutunun ikiye bölünmüş hâli gibi duruyordu. Kapsayıcı
şeffaflaştırıldı, aralık **16 px**'e çıkarıldı — artık iki ayrı seçenek
olarak okunuyor.

### Ek düzeltmeler

- **Tıklanabilirlik**: kartlara ok işareti, hover'da hafif yükselme ve
  kenar vurgusu. Koyu temada dolgu değişimi yerine kenar vurgusu
  kullanıldı — dolgu değişimi koyu zeminde ucuz görünüyor.
- **Hiyerarşi**: amblem küçültüldü (44 px), başlık öne çıktı, alt başlık
  soluklaştırıldı. Göz artık başlıktan kartlara iniyor.
- **Tema seçici** üstte asılı durmaktan çıkıp alta indi ve
  soluklaştırıldı; seçim anı değil, ayar.

## v10.4 — Yüzen öğeler de temaya bağlandı

Tema revizyonu bloklarda ve kartlarda yapılmıştı ama **yüzen öğeler**
dışarıda kalmıştı: arama kutusu ve sunum kipi düğmesi dört temada da
aynı görünüyordu.

| Tema | Arama kutusu |
|---|---|
| Bauhaus | 1 px kenar, yumuşak gölge |
| **Brutalist** | **3 px siyah kenar, 5 px sert gölge**, odakta sarı |
| Rasat / Minyatür | 1 px kenar, derin gölge, 2 px yuvarlama |

Sunum kipi düğmesi de aynı ayrımı alıyor: brutalist'te sert gölge ve
basılınca kayma, koyu temalarda derin gölge.

Arama kutusu kenardan biraz içeri alındı (14 → 20 px) — ekran kenarına
yapışık duruyordu.

Doğrulandı: dört temada da kenar kalınlığı ve gölge farklı, arama 6
sonuç veriyor, 24 bölüm ve sıfır JS hatası.

## v10.5 — SÜKÛT HARİTASI: gökyüzünün sustuğu aralıklar

### İcadın fikri

Astrolojinin tamamı **neyin aktif olduğu** üzerine kuruludur. Her kitap,
her yazılım, her danışman "şu transit geliyor" der.

Kimse **suskunluğu** ölçmez.

Oysa bir yılın her günü aynı yoğunlukta değil. Bazı aralıklarda gökyüzünde
kişinin haritasına değen hiçbir şey yok. O aralıklar boşluk değil,
**ölçülebilir bir olgu**.

### Asıl değeri: yanlışlama aracı

Danışan "her şey üst üste geldi" dediğinde astrolog transitlere bakar ve
bir şey bulur — çünkü herhangi bir güne bakılırsa hep bir şey bulunur.

Sükût haritası tersini yapar: şikâyet edilen dönem **sessiz bir aralığa**
düşüyorsa, sebep gökyüzü değildir.

> Astrolojide herhangi bir güne bakılırsa hep bir şey bulunur; bu modül
> bulunmayacağı zamanları söyler.

Astrolojide böyle bir araç yok.

### Nasıl ölçülüyor

Yılın her iki gününde, gökteki dokuz cismin on iki natal noktaya yaptığı
temaslar puanlanıyor (gezegen ağırlığı × açı ağırlığı × orb yakınlığı).
Ortaya bir **basınç eğrisi** çıkıyor. Test haritasında 186 örnek,
basınç 4.63–13.22.

### İki kalibrasyon hatası — ölçüm yakaladı

**1. Ay taban gürültüsü üretiyordu.** 27 günde bir tur atıp her natal
noktaya ayda bir değiyor. Eğriyi düzleştirip sessiz aralıkları görünmez
yapıyordu. Çıkarıldı.

**2. Eşik ortalamaya oranlıydı ve HİÇ aralık bulamadı.** "Ortalamanın
%45'i" (4.11) eğrinin minimumunun (4.72) altında kalıyordu. Sebep: taban
gürültüsü yüksek olduğu için ortalama da yüksek çıkıyor. Eşik kişinin
**kendi dağılımının yüzdelik dilimine** çevrildi — alt %22 sükût, üst %20
sıkışma. Artık her haritada anlamlı sonuç veriyor.

### Çıktı

Test haritasında 4 sessiz aralık (64 gün, yılın %18'i), 6 sıkışık aralık.
İkinci bir haritada 62 gün ve farklı tarihler — kalıp değil, hesap.

Arayüzde: basınç eğrisi (sessiz yeşil, sıkışık kırmızı), aralık listesi,
**yanlışlama sorgusu** (tarih gir, o dönem sessiz miydi) ve AI yorumu.

### Dürüstlük

Sükût "iyi", sıkışma "kötü" değil. Sükût aralığında kişi kendi başınadır —
kimine rahatlama, kimine boşluk. Prompt bunu açıkça yasaklıyor:
*"Sessiz aralığı 'rahat geçecek' diye ÇEVİRME."*

## v10.6 — ALGI EŞİĞİ: haritanın kendi orbu

### Sorun

Bütün astroloji **orb** üzerine kuruludur — bir açının kaç derece sapmayla
hâlâ etkili sayılacağı. Kimi 3° der, kimi 5°, kimi 8°. Ekol farkı diye
geçiştirilir.

**Kimse bunu hesaplamaz.** Gelenek, konvansiyon, alışkanlık. Bir haritanın
kendisinden türetilmiş bir orb yoktur.

Oysa şu apaçık: yoğun bir alanda küçük bir dokunuş kaybolur; seyrek bir
alanda aynı dokunuş her şeyi değiştirir.

### Fikir — Weber-Fechner

Psikofizikte **fark eşiği**, bir uyaranın fark edilmesi için mevcut uyarana
oranla ne kadar büyümesi gerektiğini söyler. Gürültülü odada fısıltı
duyulmaz.

Sükût haritası zaten kişinin **taban gürültüsünü** ölçüyordu. Weber
katsayısı dağılımın oynaklığından türetiliyor, eşik tabana oranlanıyor,
orb eşikten geri hesaplanıyor.

### Bir haksızlığı düzeltir

Bazı danışanlar her transiti bildirir, bazıları aynı transitte hiçbir şey
söylemez. Astroloji bunu **kişiyi suçlayarak** açıklar: "farkındalığı
düşük", "kendini tanımıyor".

Bu haksızdır — ölçülebilir bir farkı ahlaki bir kusura çevirir. Algı eşiği
onu hesaba döndürür: **kişi duyarsız değil, eşiği yüksek.**

### Ölçüm — beş harita

| Harita | Eşik | Orb | Açı sayısı |
|---|---|---|---|
| A | 1.11× | 2.7° | 9 → 9 |
| B | 0.96× | 3.14° | 6 → 6 |
| C | 1.29× | 2.32° | 10 → **8** |
| D | 1.36× | 2.21° | 13 → **11** |
| E | 0.74× | 4.04° | 5 → **8** |

Orb 2.21° ile 4.04° arasında değişiyor; bir haritada 3 açı ekleniyor,
başkasında 2 açı düşüyor. Sınırdaki açılar ayrıca listeleniyor — bunlar
"var mı yok mu" tartışması yaratan açılardır ve artık cevabı belli.

### İki hata — ölçüm yakaladı

**1. Orb formülü tersti.** `3° × (1 − kat)` yazmıştım; kat 1'e yaklaşınca
sonuç sıfıra gidiyor ve **beş haritanın beşinde de 1.0° kırpmasına
dayanıyordu** — yani hiç ayrım üretmiyordu. Doğru ilişki ters orantı:
`3° / kat`.

**2. Açı sayımında `break` koşulsuzdu.** İlk açı türünde (kavuşum)
döngüden çıkıyor, öteki dördüne hiç bakmıyordu. 12 nokta arasında yalnız
1–4 açı sayılıyordu; şimdi 5–13.

### Sınır

Prompt açıkça yasaklıyor: *"Yüksek eşik 'duyarsız', düşük eşik 'hassas'
DEĞİLDİR. Ölçülen şey uyaranın görünmesi için gereken büyüklüktür;
kişinin değeri, olgunluğu ya da farkındalığı değil."*

## v10.7 — Algı eşiği: etiket kalibrasyonu

İcat, adversaryal sınamalardan geçirildi. Üçü temiz, biri gerçek bir
sorun gösterdi.

### Geçen sınamalar

**Kararlılık** — aynı kişi, 1 dakika fark: orb 2.70° → 2.72°, fark
**0.02°**. Doğum saatindeki küçük belirsizlik eşiği bozmuyor.

**Ayrım gücü** — 12 rastgele harita: orb 2.14°–4.18°, standart sapma 0.53.
**Kırpma sınırına dayanan: 0/12.** Formül gerçekten ayrım üretiyor.

**Yer duyarlılığı** — Gebze/İstanbul/Konya/Reykjavik: 2.43°–2.79°. Ev
sınırları değişince eşik oynuyor ama uçmuyor.

### Bulunan sorun: etiketler ölçüme değil tahmine dayanıyordu

24 haritada **"düşük eşik" hiç çıkmadı**. Eşikler (0.65 / 1.15) tahminle
konmuştu.

60 harita üzerinde gerçek dağılım ölçüldü: **0.62 – 1.31, ortanca 0.94**.
Mevcut eşikler 60'ın 50'sini "orta"ya tıkıyordu — etiket işe yaramaz
hâldeydi.

E�ikler %30 ve %70 dilimine çekildi (**0.86 / 1.03**). Sonuç:

| | Önce | Sonra |
|---|---|---|
| Düşük eşik | 3/60 | **20/60** |
| Orta eşik | 50/60 | 17/60 |
| Yüksek eşik | 7/60 | 23/60 |

30 haritalık bağımsız sınamada üç seviye de çıkıyor (13/12/5).

**Ders:** bir eşik değeri, dağılımı ölçülmeden konmamalı. Sayı "makul"
görünüyor diye doğru olmuyor.

### Maliyet

Algı eşiği **0.03 sn**, sükût haritası **0.03 sn** — pratikte bedava.

## v11.0 — Chrono-Gravitron çıktı, DURAKLAMA İZİ girdi

### Neden çıktı

Ölçüm net bir tablo verdi: Chrono-Gravitron **10 KB hesaplanıyor, bağlama
601 karakter giriyor.**

Asıl sorun boyut değildi. Bu modül gravitasyonel ayrışmayı hesaplıyordu —
ve sistemin kendisi *"yerçekiminin nedensel rolü yok"* diyordu. Yani
**dürüstlüğünü kanıtlamak için var olan bir modüldü**: bir açıklama, modül
kılığında.

Danışman "gravitasyonel ayrışma 0.73" cümlesiyle ne yapacak? Hiçbir şey.
Dürüstlük bir cümleyle söylenir, on kilobaytlık bir katmanla değil.

### Yerine gelen: Duraklama İzi

Gezegenler yılda birkaç kez **durur** — geri dönmeden ve ileri dönmeden
önce hızları sıfırlanır. O anda hareketsizdirler. Bir natal noktanın
üzerinde durursa, o temasın en yoğun hâlidir: geçip gitmez, orada kalır.

Doğumdan bugüne bakıldığında:
- Bazı noktalar üzerinde **defalarca durulmuştur** — o yan işlenmiş
- Bazılarına **hiç dokunulmamıştır** — ham kalmış, sınanmamış

Kimse bunu bir ömür yapısı olarak haritalamıyor.

### Ne açıklıyor

Aynı yaştaki iki insan neden bazı konularda olgun, bazılarında toy?
Astroloji buna "gelişmemiş gezegen" der ve **yine kişiyi suçlar.** Oysa
ölçülebilir bir sebep var: o noktaya henüz gelinmemiş.

Danışman için doğrudan kullanılabilir: işlenmiş noktada kişinin geçmişi
vardır, dinle. Ham noktada toydur, tavsiye verirken bunu bil. Yaklaşan
ilk temas gerçek bir haberdir.

### Yakalanan hata — sükût haritasının aynısı

İlk sürümde Merkür ve Venüs dahildi ve **"el değmemiş nokta" hiç
çıkmıyordu** — yani icadın çekirdeği çalışmıyordu.

Sebep: Merkür 29 yılda ~174 kez durur, burçlar kuşağında ortalama 2°
aralıkla. 2.5° orbla her natal noktayı vuruyordu. Sükût haritasında Ay'ı
çıkarma sebebiyle aynı: **hızlı cisim taban gürültüsü üretir, sinyal
değil.**

Mars'tan dışarısı bırakıldı, orb 1.5°'ye indi. Sonuç yaşa göre anlamlı:

| Yaş | İşlenmiş | Ham kalan |
|---|---|---|
| 29 | 11 | 1 (Plüton) |
| 48 | 11 | 1 (Satürn) |
| 61 | 12 | 0 |

Yaşla birlikte her yan işleniyor — beklenen davranış.

### Söküm sırasında dört kırık

Toplu silme yine iz bıraktı: `main.py`'de yarım `try` bloğu, `ai.py`'de
yetim bağlam bloğu, arayüzde açık kalmış bir yorumun içine düşen yeni
kod, ve silinen bloğun yetim `}` kapanışı. Dördü de onarıldı.

**Ders:** bir modül sökerken referansları silmek yetmiyor; derleyici ve
tarayıcı ayrı ayrı sınanmalı.

### Maliyet

Analiz 1.82 sn (önce 0.79) — duraklama taraması 1 saniye ekliyor. Yük
106 → 100 KB düştü. Bağlam %79 → %77.

## v11.1 — Hesap denetimi ve ölü alan adı temizliği

### Bütün hesaplar bağımsız doğrulandı

Ham Swiss Ephemeris çağrılarıyla karşılaştırıldı:

| Sınanan | Sapma |
|---|---|
| On cismin boylamı | **0** (10/10 birebir) |
| ASC, MC, on iki ev sınırı | **0** |
| Yeni ay anları | Ay−Güneş farkı **0.00000°** |
| Duraklama anları | hız 1e-8 – 1e-10 °/gün |

Tutulmalar da doğrulandı: 17 Şubat 2026 halkalı güneş, 3 Mart 2026 tam ay,
12 Ağustos 2026 tam güneş — üçü de gerçek, bilinen tutulmalar.

### Bulunan boşluk: ölü alan adları

Altı harita üzerinde tarandığında `hamle` ve `kacis` alanlarının
**0/6 dolduğu** görüldü. Motor bu adları hiç üretmiyor; doğru adlar
`berzah_hamlesi` ve `yanlis_refleks`.

Kod her yerde yedekli yazılmıştı (`get("hamle") or get("berzah_hamlesi")`)
— yani sessiz veri kaybı YOKTU. Ama ölü yedek, yanlış adı arayan yeni bir
kodun sessizce boş dönmesine izin verirdi. Kaldırıldı.

Somut etkisi: direnç haritasında *"Aynı şeyi hamle tarafından söyle:
'İstisnayı tanımak'"* maddesi artık dolu geliyor.

## v11.2 — Deneme modülleri: 16 döküm yerine 4 okuma

### Ölçüm

Blok 2427 karakterdi, **satır başına 151.** O satırlar okuma değil,
etiketli veri dökümüydü:

> `KRN: 03°50' Başak · 5. ev · skor 66 (orta) · Anti-KRN 03°50' Balık`

151 karakterde bir teknik anlatılmaz. Model 16'sını aynı anda
yorumlamak zorunda kalıyor ve çoğunu atlıyordu.

### Üç sıralama denemesi — üçü de başarısız

Kaydediliyor ki tekrar denenmesin:

1. **Elle alan adı** — her tekniğe özel ölçü yazdım, adları TAHMİN
   ettim. Dört teknik 0.00 aldı çünkü aradığım anahtar yoktu; zayıf
   oldukları için değil.
2. **Mutlak doluluk** — çok sayısal alan içeren Asabiyye her haritada
   tavan puan aldı. Ölçü gücü değil, **ayrıntılılığı** ölçüyordu.
3. **Oransal doluluk** — ölçek-bağımsız oldu ama **beş haritada da aynı
   dört teknik** seçildi. Sıfır ayrım.

### Asıl bulgu

Üçüncü denemenin gösterdiği şey önemli: **bu modüllerde haritaya özel
güç sinyali yok.** Hepsi her haritada dolu çıktı üretiyor; "burada bir
şey bulamadım" hâlleri yok. Doluluk modülün kendi özelliği, haritanın
değil.

Sahte bir sıralama üretmek yerine seçim **açıkça editöryel** yapıldı.
Kriter: *bir teknik seansta kullanılabilir bir şey söylüyor mu?*

Seçilenler: **KRN** (davranışa bağlanıyor), **Asabiyye** (reis/yalnız —
ilişkisel ve somut), **İkbal** (zamanlanabilir), **Vuslat**
(zamanlanabilir). Kalan on iki teknik için eleme sebebi tek tek yazıldı.

### Sonuç

| | Önce | Sonra |
|---|---|---|
| Blok | 2427 karakter | **1204** |
| Satır başına | 151 | **236** |
| Teknik | 16 döküm | **4 okuma** |
| Bağlam | %79 | **%70** |

Dört teknik artık ne söylediğini açıklıyor — örneğin Asabiyye yalnızca
yüzde vermiyor, *"reis iç düzeni kuran yan, yalnız kalan kişinin kendi
içinde dışladığı yan"* diye anlatıyor.

### Yol boyunca iki anahtar hatası

`ikbal`/`vuslat` yazmıştım, gerçek adlar `ikbal_merdiveni` ve
`vuslat_kapilari`. Sonra alt alanlarda `tarih`/`deger` yazdım, gerçek
adlar `ay`/`irtifa` — çıktıda `None` görünüyordu. İkisi de ölçümle
yakalandı.

## v11.3 — CEVAPLANABİLİRLİK: kanıt eşit değildir

### Kategori denetimi

18 bağlam bloğu ölçüldü. **Şi'râ Çevrimi 2067 karakterle en büyüktü** —
çekirdekten bile büyük. İçeriği:

> `Şi'râ B doğumda: faz 0.063188 · ayrıklık 0.603371 · hız 2.214942`

Altı ondalıklı yörünge parametresi. Model bunu danışan diline çeviremez —
deneme modüllerinin aynı sorunu. **2067 → 187 karakter**; yorumlanabilir
üç şey bırakıldı (doğum evresi, bugünkü evre, aradaki fark).

### Yeni icat — bir bölüm değil, konuşma ayarı

Astroloji her soruya **aynı güvenle** cevap verir. Danışan ilişkisini
sorar, cevap gelir. Kökünü sorar, cevap gelir.

Oysa bir harita her konuda aynı miktarda veri taşımaz. Bazı alanlarda
birden çok bağımsız katman aynı şeyi söyler; bazılarında tek zayıf iz
vardır ya da katmanlar çelişir. **Danışan ikisini ayırt edemez, çünkü
ikisi de aynı kendinden emin dille gelir.**

Cevaplanabilirlik haritası her hayat alanı için kaç BAĞIMSIZ katmanın söz
söylediğini ve birbirlerini tutup tutmadığını sayar:

```
çok katman + uyum    → güçlü:     açık konuş, yaslan
çok katman + çelişki → gerilimli: çelişkiyi göster, taraf tutma
az katman            → zayıf:     az söyle, boşluğu doldurma
```

**Bu bir bölüm üretmez.** Doğrudan AI promptuna girer — hem çekirdek
persona kuralı olarak (`KANIT EŞİT DEĞİLDİR`), hem bağlamın en başında
harita-özel talimat olarak. Yani sistemin **bütün yüzeylerinde** çalışır
ve modelin nasıl konuştuğunu değiştirir.

Test haritasında: görünürlük **güçlü** (4 bağımsız kanıt türü), gündelik
düzen ve aile **zayıf** (tek tür).

Çekirdek kuralın kilit cümlesi: *"Zayıf bir alanda uzun konuşmak, güçlü
alanda söylediklerinin de güvenini düşürür. Astrolojinin en sessiz
zayıflığı budur: kanıtın eşit olmadığını kabul etmemek."*

### Yol boyunca üç kırık

Girinti iki kez bozuldu (blok yanlış `if` içine düştü), bir kez de
`cevaplanabilirlik` kendi kendine referans verdi — önceki `duraklama_izi`
eklemesi aynı satıra girmişti. Üçü de ölçümle yakalandı.

### Bağlam

%79 → **%66.** Şi'râ sıkıştırması ve deneme seçimi birlikte ~3.000
karakter kazandırdı; yeni blok 1.074 karakter aldı.

## v11.4 — TEMAS AÇISI: okumanın geçtiği kanal

### Görülmeyen değişken

Sistem kişinin yapısını on beş katmanda ölçüyordu. Ölçmediği tek şey,
okumanın **geçtiği kanal**: danışmanın kendisi.

Astrolojide sinastri var ama yalnız romantik ya da ailevi ilişki için
kullanılıyor. **Kimse danışman–danışan ilişkisini hesaplamıyor.** Oysa
aynı doğru cümle, iki farklı danışmanın ağzından iki farklı şey olur:
birinden duyulur, ötekinden duyulmaz.

Bu danışmanın iyiliğiyle ilgili değil — geometriyle ilgili, ve geometri
hesaplanabilir.

### Dört uyarı

| Uyarı | Ne yakalar |
|---|---|
| **Yansıma** | Çatal aynıysa danışman kendi meselesini danışanda okur — en sinsi hata |
| **Kör nokta** | Danışanın bir yanı danışmanda karşılıksızsa hafife alınır |
| **Sert temas** | Dar zorlu açı: söz ağırlaşır, yanlışsa daha çok kırar |
| **Zayıf/yoğun kanal** | Az temasta sezgi yanıltır; çok temasta ayrım zorlaşır |

### Prompttan çalışıyor

Bir bölüm üretmiyor. İki yerden giriyor: çekirdek persona kuralı
(`KANALIN KENDİSİ`) ve bağlamda harita-özel uyarılar. Bütün yüzeylerde
modelin nasıl yazdığını değiştiriyor.

Kurulum: `ZIC_DANISMAN_DOGUM="1997-09-27 20:41,40.8022,29.4306"`.
Tanımsızsa sessizce atlanır.

### Yakalanan hata: saat dilimi

İlk sürümde danışman haritası `tz_offset=0.0` ile kuruluyordu — **UTC
olarak**, yani üç saat kaymış. Hata şuradan çıktı: danışman **kendi
haritasını** okuduğunda "yansıma yok" diyordu. Aynı harita farklı çatal
veremez.

Düzeltildikten sonra: kendi haritasında 30 temas ve **yansıma VAR**;
yabancı haritada 15 temas, yansıma yok. Ayrım doğru.

### Sınır

Bu bir uyum puanı değil. *"Kötü temas diye bir şey yoktur; farkında
olunmayan temas vardır."*

## v11.5 — Kritik eksik: beş icadın hiç testi yoktu

### Bulunan

Envanter çıkarılınca görüldü: son sürümlerde eklenen **beş modülün hiç
testi yoktu.**

```
sukut              ✗    esik               ✗
cevaplanabilirlik  ✗    temas              ✗
lunasyon           ✗    duraklama          ✓ (tek istisna)
```

Aynı hata **üçüncü kez** oluyor: özelliği ekleyip testini yazmayı
atlamak. v8.5'te altı uç, v10.2'de sekiz kategori bağı, şimdi beş modül.

### Eklenen testler

**Derin doğrulama: 96 → 115.** On dokuz yeni kontrol, hepsi geçiyor.
Bunlar sadece "çalışıyor mu" demiyor; daha önce **gerçekten yaşanmış
hataları** koruma altına alıyor:

| Kontrol | Hangi hatayı önlüyor |
|---|---|
| Yeni ay ve dolunay AYRI etiketleniyor | Modüler sarmal tuzağı (v10.0) |
| Eşik minimumun ÜSTÜNDE | Sükût hiç aralık bulamıyordu (v10.5) |
| Orb kırpma sınırına dayanmıyor | Beş haritada da 1.0° çıkıyordu (v10.6) |
| Açı sayımı makul | Koşulsuz `break` (v10.6) |
| Hızlı gezegen dışarıda | Merkür taban gürültüsü (v11.0) |
| Aynı harita yansıma tetikliyor | Saat dilimi kayması (v11.4) |

**Sızma testi: 50 → 58.** Sekiz yeni test; `sukut`, `esik`,
`lunasyon-sohbet` ve `onerilen-sorular` uçları artık kapsanıyor. Hepsi
kapalı.

### Sistem envanteri

**Sekiz icat** (astrolojide karşılığı yok): Hudûd-ı Arz, Mîzân-ı Ebvâb,
Lunasyon takvimi, Sükût haritası, Algı eşiği, Duraklama izi,
Cevaplanabilirlik, Temas açısı.

**Çekirdek motor:** BERZAH v2, Swiss Ephemeris, dairesel istatistik,
Hudûd-ı Felek, Şi'râ, Kabz/Bast + solar dönüş, kadim katman,
Human Design, 16 deneme tekniği, astrokartografi, rektifikasyon.

31 modül · 47 uç · 14.077 satır · 14 AI yüzeyi · 32 bölüm talimatı ·
50 soru · 4 tema · 1.393 satır test.

## v11.6 — Sessiz kayıp düzeltildi, YAŞ KATMANI eklendi

### Bulunan eksik: yılın haritası bağlama hiç girmiyordu

Her katmanın bağlama ulaşıp ulaşmadığı tek tek denetlendi. On altı
katmanın on beşi geçiyordu; **`solar_v2` geçmiyordu.**

Sebep bir katman derinlik farkıydı: kod `sv["berzah"]` arıyordu, gerçek
yapı `sv["berzah_v2"]["berzah"]`. `sr_year` verilse bile "Yılın haritası"
bloğu hiç oluşmuyordu.

**Sessiz kayıp:** hata yok, uyarı yok, blok yok. Ancak katman-bağlam
eşleştirmesi yapılınca görüldü.

Düzeltildikten sonra blok doluyor ve bir de yorum kuralı eklendi:
*"Natal ile aynı şeyi söylüyorsa konu olgunlaşıyor, farklı söylüyorsa yıl
kişiyi kendi kalıbının dışına çağırıyor."*

### Yeni icat: YAŞ KATMANI

Astroloji yaşı bir **sayı** olarak görür. Oysa yaş, aynı anda dönen
birkaç çarkın o andaki bileşimidir.

Herkes aynı yaşta aynı eşikten geçer — bu bilinir. Sorulmayan şu:

> **Bu kişi ŞU ANDA kaç eşiğin ortasında?**

Biri 29'da yalnız Satürn dönüşünde olabilir; bir başkası aynı anda
Satürn dönüşü, Jüpiter karşıtlığı, düğüm karşıtlığı ve progres Ay
dönüşünün üstünde. İkisi de "29 yaşında" ama biri tek kapıdan, öteki
dört kapıdan geçiyor.

Yedi çevrim ölçülüyor: Satürn (29.46), Jüpiter (11.86), Ay düğümü
(18.61), Uranüs çeyreği (21.01), progres Ay (27.32), Neptün beşte biri
(32.9), Şi'râ (1.46). Her birinde tur başı **dönüş**, tur ortası
**karşıtlık** eşiği sayılıyor.

| Yaş | Eşik | Seviye |
|---|---|---|
| 28.96 | **4** | yığılma |
| 48.59 | 1 | tek eşik |
| 61.19 | **0** | eşik arası |
| 16.48 | 2 | çifte eşik |

### Neden bu değerli

Danışan *"neden her şey aynı anda"* dediğinde astroloji genelde kişisel
bir açıklama arar. Yığılma ölçülünce cevap şu olur: **kişisel zayıflık
değil, yapısal çakışma.** Bunu söylemek tek başına rahatlatıcıdır.

Tersi de: eşik yoksa *"bir şey olmuyor"* şikâyeti hareketsizlik değil,
**yerleşme** olarak okunur.

Prompta girer (`YAŞIN YÜKÜ` çekirdek kuralı) ve okumanın **tonunu**
belirler — üç ve üstü eşikte büyük hedef verilmez, küçük adım önerilir.

### Test

**115 → 120.** Astrolojik doğrulama dahil: 29 yaşındaki haritada Satürn
dönüşünün eşikte çıkması sınanıyor.

## v11.7 — İcat denetimi: cevaplanabilirlik modeli susturuyordu

Dokuz icat tek tek gözden geçirildi: maliyet, ayırt edicilik, kalibrasyon.

### Maliyet — hepsi ucuz

| İcat | Süre |
|---|---|
| Duraklama izi | 0.91 sn |
| Lunasyon | 0.04 sn |
| Sükût, Algı eşiği | 0.02 sn |
| Cevaplanabilirlik, Temas, Yaş | ~0.00 sn |
| **Toplam** | **1.00 sn** |

### Ayırt edicilik — biri hariç hepsi geçti

Altı haritada ölçüldü. Sükût oranı, algı eşiği orbu, duraklama ham
noktaları ve yaş eşiği hepsi farklı değerler üretiyor.

**Cevaplanabilirlik şüpheliydi**: "güçlü alan sayısı" yalnız 1–2
çıkıyordu. Ama asıl soru sayı değil, HANGİ alanların güçlü olduğuydu —
ve orada 11 alanın 8'i en az bir haritada güçlü çıkıyor. Ayrım var.

### Bulunan gerçek hata: zayıf oranı çok yüksekti

Sekiz haritada ölçüldü: **ortalama %57 alan "zayıf"**, bir haritada
**%82**. Yani model hayat alanlarının yarısından fazlasında *"az söyle,
boşluğu doldurma"* komutu alıyordu.

Bu, dürüstlük olmaktan çıkıp **susmaya** dönerdi. Danışan bir konu
sorduğunda cevabın ince gelmesi, icadın amacına aykırı.

Ayrıca **"gerilimli" seviyesi hiç çıkmıyordu** — gerilim sayacı çelişki
metninde alan adı arıyordu ama çelişkiler alan adıyla yazılmıyor.

E�ikler yeniden kalibre edildi:

| | Önce | Sonra |
|---|---|---|
| Güçlü | %14 | **%32** |
| Orta | %29 | **%38** |
| Zayıf | **%57** | **%31** |
| Zayıf aralığı | %36–82 | **%18–36** |

Zayıf artık istisna, kural değil.

### Koruma testi

**120 → 122.** İki yeni kontrol: zayıf oranı yarıyı geçmiyor, ve her
haritada en az bir güçlü alan var. Bu kalibrasyon bir daha sessizce
bozulamaz.

## v11.8 — Pratik temalar ve yazı boyutu

Mevcut dört tema **estetik iddia** taşıyordu (Bauhaus, Brutalist, Rasat,
Minyatür). Günlük kullanım için tasarlanmamışlardı.

Üç tema **işe göre** eklendi:

| Tema | Ne için |
|---|---|
| **Okuma** | Uzun metin. Sıcak kırık beyaz (saf beyaz göz yorar), satır aralığı 1.78, ölçü 74 karakter, vurgu renkleri kısık — metin öne çıksın |
| **Gece** | Akşam seansı. Mavi bileşen düşük tutuldu; zemin siyah değil koyu gri-kahve, çünkü siyah ekranda beyaz metin hâlelenir |
| **Karşıtlık** | Yorgun göz, projeksiyon, kötü ekran. Saf siyah-beyaz, 2–3 px kenar, 16.5 px yazı, renk yalnız işlev için |

### Yazı boyutu — temadan bağımsız

En çok işe yarayan erişilebilirlik ayarı: kişi sevdiği temayı bırakmadan
yazıyı büyütebiliyor. Üç kademe (16 / 17.5 / 19.5 px), başlıkta **A A A**
düğmeleri.

### Klavye kısayolu

Seansta fareyle düğme aramak zaman kaybı:

- **Alt+T** — yedi tema arasında döner
- **Alt+A** — yazı boyutunu büyütür

### Doğrulama

Yedi temanın hepsi ölçüldü; zemin, metin rengi, kart boyu ve satır
aralığı temaya göre değişiyor. Okuma temasında satır aralığı 28.48 px
(ötekilerde 25.6), karşıtlıkta yazı 16.5 px. Üç boyut kademesi ve iki
kısayol çalışıyor. Sıfır JS hatası.

## v12.0 — SARSMA TESTİ: hangi bulgu saat hatasına dayanır

### Kategori değerlendirmesi

Yirmi beş kategori beş öbeğe ayrılıyor: **YAPI 10, ZAMAN 7, META 5,
PRATİK 2, MEKÂN 1**.

Değerlendirme bir şeyi gösterdi: hepsi **tek bir sayıya** dayanıyor —
doğum saati.

### Sorun

Astroloji bunu bilir ve *"saatiniz kesin mi"* diye sorar. Sonra cevap ne
olursa olsun **bütün bulguları aynı güvenle** anlatır.

Oysa bulgular eşit değil:

- **Burç konumları** saat hatasına neredeyse duyarsız. Güneş bir derece
  için bir gün ister.
- **Ev konumları** çok duyarlı. Yükselen dört dakikada bir derece yürür;
  on beş dakika bir evi tamamen değiştirebilir.

Yani bir okumanın yarısı sağlam, yarısı kumun üstünde olabilir ve
danışan ikisini ayırt edemez.

### İcat

Harita **sarsılıyor**: doğum saati ±5, ±15, ±30 dakika kaydırılıp her
seferinde yeniden hesaplanıyor. Hangi bulgunun değiştiği sayılıyor.

| Sınıf | Anlamı |
|---|---|
| **Sağlam** | Hiç değişmiyor — okumanın omurgası |
| **Dayanıklı** | ±30'da değişiyor — saat kabaca doğruysa geçerli |
| **Kırılgan** | ±15'te değişiyor — çekinceyle söyle |
| **Kum** | ±5'te değişiyor — **söyleme** |

Karşılaştırma sayısal değil **kategorik**: burç, ev, tür. Derece farkı
zaten olacak; önemli olan yorumun değişmesi.

### Test haritasında

```
sağlam 16 · dayanıklı 8 · kırılgan 5 · kum 2   → sağlamlık 0.74
```

Somut bulgu: **Tepe noktası burç sınırında** — beş dakikalık hata onu
değiştiriyor. Bu, danışmanın bilmesi gereken tam olarak şu tür bir
bilgidir.

### Prompttan çalışıyor

Çekirdek kural (`NEYİN ARKASINDA DURABİLİRSİN`) on dört yüzeye birden
giriyor, artı bağlamda harita-özel talimat. Zorunlu blok — asla düşmüyor.

Cevaplanabilirlikten farklı bir eksen: o *"hangi alanda veri güçlü"*
der, bu *"hangi bulgu saat hatasına dayanır"* der.

### Test

**122 → 127.** İki astrolojik doğrulama dahil: burçların sağlam
(15 bulgu), evlerin kırılgan (7 bulgu) çıkması sınanıyor. Maliyet 0.2 sn.

## v12.1 — KAYIP ZAMAN ve DÖNÜŞ NOKTASI

### 1 · Kayıp zaman — hangi yıllar sessiz geçti

Sükût haritası bir yılı ölçüyordu. Aynı hesap doğumdan bugüne yayıldı.

Danışan *"şu yıllarım kayıp"* dediğinde astrolojinin söyleyecek bir şeyi
yok — o dönemin transitlerine bakılır ve bir şey bulunur, çünkü herhangi
bir döneme bakılırsa hep bir şey bulunur.

Bu modül tersini yapıyor: o yıllarda gökyüzünde gerçekten az şey
olduğunu **ölçüyor**. "Kayıp" hissi ölçülünce kişisel kusur olmaktan
çıkıyor.

Test haritasında sessiz yaşlar: **4, 10–11, 14–18**. Yoğun: 2, 21, 25–26, 28.
Maliyet **0.0 sn** — analize doğrudan girdi.

### 2 · Dönüş noktası — bir daha gelmeyecek kapılar

Yavaş gezegenler bir natal noktaya ömürde bir ya da iki kez gelir.
Plüton bir turu 248 yılda tamamlar.

Astroloji *"transit geçti"* der. **"Bu bir daha olmayacak" demez.**

Test haritasında 82 kapı tarandı; **6'sı bir daha gelmeyecek** —
örneğin Uranüs–Ay üçgeni, son 2017'de yaşandı.

Bu zamanlama değil **ağırlık** bilgisi: tekrar etmeyecek bir aralık,
tekrar edecek olandan farklı okunur.

Maliyet **3.5 sn** olduğu için ayrı uçta (`/api/v1/donus-noktasi`) —
kartografinin arz izdüşümüyle aynı kalıp. Ana analizi ikiye katlardı.

### Test

**127 → 132.** Beş yeni kontrol.

## v12.2 — Darboğaz kaldırıldı, doğruluk aynı

### Profil

Analiz 1.87 sn sürüyordu. Katman katman ölçüldü:

```
duraklama    0.887s  ███████████████████ %51
full_v2      0.281s  ██████ %16
deneme(16)   0.199s  ████ %11
sarsma       0.165s  ███ %9
hudud        0.141s  ███ %8
gerisi       0.080s  █ %5
```

**Duraklama izi tek başına yarısından fazlası.**

### Sebep

29 yıllık tarama günlük adımla yapılıyordu: **63.462 efemeris çağrısı.**

### Doğruluğu bozmadan hızlandırma — ölçümle

Kaba adım duraklama kaçırır mı? Ölçüldü:

> Mars en hızlı duran gezegendir ve iki ardışık duraklaması arasındaki
> **en kısa aralık 60 gün** (40 yıllık taramada). Yani 60 günden kısa
> her adım güvenlidir.

5, 8, 10 ve 15 günlük adımlar denendi — **dördü de aynı 427 duraklamayı
buluyor, sıfır kayıp.**

**10 gün** seçildi: güvenli sınırın altıda biri. İkiye bölme aşaması
değişmedi, tam an hâlâ saniye hassasiyetinde (bölme derinliği 28→34).

### Sonuç

| | Önce | Sonra |
|---|---|---|
| Duraklama modülü | 0.89 sn | **0.26 sn** |
| Tam analiz | 1.87 sn | **1.22 sn** |
| Efemeris çağrısı | 63.462 | **6.346** |

**Doğruluk birebir aynı:** 308 duraklama, 38 temas, 11 işlenmiş yan,
1 ham nokta — hepsi değişmedi.

### Koruma testi

**132 → 133.** Tarama adımının 60 günü geçmediği sınanıyor; biri
"daha da hızlandıralım" diye adımı büyütürse test yakalar.

### Ayrıca

`Kayıp zaman: hızlı cisim dışarıda` testi metin araması yapıyordu ve
kırılgandı. Doğrudan modülün cisim listesine bakacak şekilde
düzeltildi.

## v12.3 — Gereksiz kategori silindi, YAKINSAMA ÇEKİRDEĞİ geldi

### Silinen: Yürüyen Berzah

Zamanlama katmanı sayısı beşe çıkmıştı: Lunasyon, Yaş katmanı, Dönüş
noktası, Kabz/Bast, Yürüyen Berzah. Sonuncusu en zayıfıydı —
**bağlama hiç girmiyordu**, yalnız arayüzde duruyordu.

Kaldırıldı. Ölü talimatlar (`chrono`, `dinamik`) da temizlendi.
Bölüm 29 → 23.

### Yerine gelen: Yakınsama Çekirdeği

Bağlamın en başında **"ÖNCE BUNLARI OKU — en belirleyici beş bulgu"**
diye bir blok vardı. Model onu ilk okuyor ve en çok ona yaslanıyordu.

O beş bulgu **elle seçiliyordu**: kodda sabit liste — şikâyet, sebep,
eşik türü, kaçış refleksi, yaşanan havza. Hangi harita olursa olsun
aynı beşi.

Sorun: bir haritada en belirleyici şey kaçış refleksi olabilir,
başkasında hiç önemli olmayabilir. Sabit liste bunu göremez.

**Yeni yöntem:** bulguyu elle seçmek yerine **yakınsamayı ölç.** Her
katmanın ürettiği davranış ifadeleri yedi eksende toplanıyor; puan
**kaynak TÜRÜ** sayısına dayanıyor — tek tür içindeki tekrar bir kez
sayılıyor, yoksa aynı hesaptan türeyen alt bulgular yapay yakınsama
üretir.

Test haritasında çekirdek: *"karar anında geri çekilme — 2 bağımsız
katman (direnç haritası, karar eşiği, çelişki) aynı yeri gösteriyor."*
Tek kaynaklılar ayrıca işaretleniyor: *"bunlara az yaslan."*

### Yol boyunca dört hata

1. Toplu silme **Kabz/Bast'ı da götürdü** — geri yüklendi, blok sınırları
   kesinleştirilerek yeniden yapıldı.
2. Yakınsama `sonuc` sözlüğü kurulmadan çağrılıyordu.
3. Taşınırken **`return sonuc`'un on satır sonrasına** düştü — hiç
   çalışmıyordu.
4. `except Exception: pass` hatayı **sessizce yutuyordu**; bu yüzden 3.
   madde fark edilmedi. Artık hata görünür yazılıyor.

Dördüncüsü en önemlisi: sessiz yutma, bir bloğun bağlama hiç girmemesine
yol açtı ve kimse fark etmezdi.

### Test

**133 → 136.** Yakınsamanın kaynak türünü saydığı (tekrar şişirmediği)
ayrıca sınanıyor.

## v12.4 — HAMLE PENCERESİ: silinen katmanın yerine

Yürüyen Berzah çatalın ne zaman tetiklendiğini söylüyordu — **tarif.**
Yerine gelen modül ne yapılabileceğini söylüyor — **karar.**

### Cevaplanmayan soru

Sistem kişiyi on dokuz katmanda tarif ediyor, zamanı yedi katmanda
ölçüyor. Ama danışanın **asıl sorduğu şeyi** cevaplamıyordu:

> "Bunu yapmalı mıyım, ne zaman?"

Astrolojide seçim (elektional) dalı var ama **geneldir** — "sözleşme
için iyi gün", "Merkür geri değilken imzala". Herkes için aynı.

Kimse seçimi **kişinin kendi yapısına göre** hesaplamıyor.

### İcat

"İyi gün" diye bir şey yok. Bir hafta, **yapılacak işin türüne** göre
uygundur — ve bu kişinin alan yapısına bağlıdır.

Beş hamle türü ayrıştırıldı: **Başlatmak · Bitirmek · Bağlanmak ·
Çekilmek · Söylemek.** Her hafta her tür için ayrı puanlanıyor.

Puan iki kaynaktan:
- **Yapısal taban** — karar eşiği türü, Kabz/Bast evresi, yaş eşiği
  yığılması
- **Haftalık** — o haftaya düşen lunasyon türü ve evi, sükût basıncı

### Test haritasında

```
Taban eğilim: Çekilmek 1.3 · Bitirmek 1.0 · Başlatmak −0.8 · Bağlanmak −0.8
```

*Karar eşiği itici: bitirmek doğal, bağlanmak zorlu.*
*Dört gelişim eşiği açık: yeni yük almak yerine var olanı taşımak gerçekçi.*

Pencereler: Başlatmak 7–13 Kasım (yeni ay, 6. ev) · Bitirmek 26 Eylül–2
Ekim (dolunay, 12. ev) · Söylemek 21–27 Kasım (dolunay, 1. ev).

### Prompta giriyor

Çekirdek kural `NE ZAMAN SORUSU` on dört yüzeye birden. Üç sert sınır:

- *"Bu hafta yap" DEME; "bu hafta daha az sürtünmeyle olur" de.*
- *KÖTÜ HAFTA YOKTUR — her hafta bir şeye uygun, başka şeye değil.*
- *"Uygun zaman" demek "kolay" demek değildir.*

Maliyet **0.03 sn** (1.29 → 1.32). Test **136 → 140.**

## v12.5 — SEANS KİPİ · ve v12.4'ün kırık gönderildiğinin itirafı

### Önce: v12.4 KIRIK gönderildi

Tarayıcıda sınanınca çıktı: **hiçbir bölüm çizilmiyordu.**

Sebep: v12.3'te Yürüyen Berzah bölümü silinirken, o blokta tanımlı
`konum`, `eks` ve `net` değişkenleri de gitti — ama **Kabz/Bast bloğu
onları kullanıyordu.** `ciz()` "konum is not defined" ile çöktü.

API 200 dönüyordu, 140 test yeşildi, sözdizimi temizdi. Ama ekran boştu.
Tarayıcı testi yapmadan paketlemiştim.

Üç değişken Kabz/Bast'ın kendi verisinden yeniden türetildi; 26 bölüm
geri geldi.

**Koruma eklendi:** `verify.py` artık `ciz()` içindeki değişkenlerin
tanımlı olduğunu sınıyor. Aynı sınıf hata bir daha sessizce geçemez.
Test **140 → 146.**

### Asıl iş: Seans kipi

Sorun renk ya da tema değildi. 23 bölüm **teknik adına** göre diziliydi
(Hüküm, Alan halkası, Hudûd-ı Felek…). Danışan karşındayken hangi
tekniğin ne tuttuğunu hatırlamak gerekiyordu.

Seans kipi aynı veriyi **seansın anına** göre diziyor:

| Adım | İçerik |
|---|---|
| **Açılış** | Omurga (yakınsama) · şikâyet/sebep · çatal · yaşın yükü |
| **Dinlerken** | Büyük arama kutusu · çelişkiler |
| **Söylerken** | Ne kapatır/ne açar · nerede konuş/sus · saat kesin değilse söyleme |
| **Kapanırken** | Hangi hafta hangi hamle · bu hafta tek adım |

Ölçüm: **6.8 ekran → 2.6 ekran.** Teknik bölümler kaybolmuyor;
"Tüm katmanlar" ile geri geliyor (26 bölüm).

Sağ altta `Seans kipi` düğmesi, kısayol **Alt+S**.

## v12.6 — Dört yeni sağlayıcı ve hata teşhisi

### "Danışmana şu an ulaşılamıyor" — sebebi

Bu mesaj arayüzde **503** geldiğinde çıkar. 503 ise zincirdeki
**bütün sağlayıcılar düştüğünde** üretilir.

Tek sağlayıcıyla (yalnız `AI_API_KEY`) çalışıyorsanız, o ağ geçidi
kapandığı ya da kotası dolduğu an sistem durur. Sebep sizin kodunuzda
değil, zincirin tek halkalı olmasında.

### Eklenen dört sağlayıcı

Hepsi OpenAI protokolü konuşuyor, mevcut katman zaten destekliyordu:

| Sağlayıcı | Varsayılan model |
|---|---|
| DeepSeek | `deepseek-chat` |
| Google Gemini | `gemini-2.0-flash` |
| NVIDIA NIM | `meta/llama-3.3-70b-instruct` |
| Kimi / Moonshot | `kimi-k2-0905-preview` |

Zincir yediye çıktı: gateway → anthropic → openai → deepseek →
gemini → nvidia → kimi. Anahtarı olmayan zincire girmez.

Her sağlayıcı kendi varsayılan modelini kullanıyor — gateway'in model
listesi ötekilerde geçersizdir. `DEEPSEEK_MODEL` gibi değişkenlerle
değiştirilebilir.

### Yakalanan iki hata

**1. Sağlayıcı adresi geçmiyordu.** `_openai_cagir` ve
`_anthropic_cagir` sağlayıcıyı `_istek`'e iletmiyordu; hangi sağlayıcı
denenirse denensin **küresel aktif olanın adresine** gidiyordu. Zincir
görünüşte vardı ama gerçekte tek adrese çakılıyordu.

**2. Hata metni sabit `BASE` yazıyordu.** Üç ayrı sağlayıcı düştüğünde
üçü de gateway'in adresini gösteriyor, teşhis tamamen yanıltıcı
oluyordu.

Düzeltmeden sonra:
```
gateway   düştü   gateway: ulaşılamadı (http://…:9999)
deepseek  düştü   deepseek: ulaşılamadı (http://…:9998)
gemini    düştü   gemini: ulaşılamadı (http://…:9301)
```

### Yeni teşhis ucu

`POST /api/v1/saglayici-sina` her sağlayıcıyı **tek tek** sınıyor ve
hangisinin hangi hatayla düştüğünü söylüyor. Normal `cagir()` zinciri
gezip tek birleşik hata döndürüyordu; hangisinin neden düştüğü
kayboluyordu.

Ayrıntılı kurulum: `RENDER_ENV.txt`.

## v12.7 — Anlatım yapısı: üç kip, birinci tekil kişi, dil bilgisi

Çekirdek anlatım bölümü baştan yazıldı. Bu bölüm **on dört yüzeye
birden** girdiği için değişiklik bütün sistemi etkiliyor.

### 1 · Birinci tekil kişi

Okuma artık BEN diliyle yazılıyor. Danışman konuşur, sistem konuşmaz.

| | |
|---|---|
| ✓ | "Haritanda beni durduran şey şu:" |
| ✓ | "Bunu söylerken tereddüt ediyorum, çünkü veri ince." |
| ✗ | "Bu haritada görülmektedir." |
| ✗ | "Sistem şunu tespit etmiştir." |

Gerekçe prompta yazıldı: *"Birinci tekil kişi sorumluluğu üstlenmek
demektir. 'Görüyorum' diyen geri adım da atabilir; 'görülmektedir'
diyen atamaz."*

### 2 · Üç anlatım kipi

| Kip | Nerede | Kural |
|---|---|---|
| **Betimleyici** | karakter, potansiyel | Davranışı tarif et, sıfat yığma |
| **Açıklayıcı** | teknik bilgi, transit | Önce olay, sonra karşılığı; derece verme |
| **Öyküleyici** | gelecek, döngüler | Yay kur ama olay uydurma |

Her kipe doğru/yanlış örnek çifti kondu.

### 3 · On anlatım bozukluğu

Anlama dayalı: gereksiz sözcük, yanlış anlam, yanlış yer, anlamca
çelişen sözcükler, mantık-sıralama, anlam belirsizliği.
Yapıya dayalı: özne–yüklem uyuşmazlığı, öge eksikliği, yüklem
eksikliği, tamlama yanlışlığı.

Her biri örnekle: `✗ "geri iade etmek" → ✓ "iade etmek"`.

**Dikkat edilen nokta:** "anlamca çelişen sözcükler" kuralı sistemin
çekince kurallarıyla çakışabilirdi. Prompta açıkça yazıldı:
*"Bu kural çekinceyi YASAKLAMAZ. 'Olabilir' tek başına doğrudur;
yasak olan 'kesinlikle' ile birlikte kullanmaktır."*

### Ölçüm

| | Önce | Sonra |
|---|---|---|
| Anlatım bölümü | 328 kelime | 721 kelime |
| Sistem promptu | — | 2.273 kelime |
| Talimat/veri oranı | 1.69 | **1.05** |

Oran düzeldi çünkü aynı turda deneme modülleri ve Şi'râ sıkıştırılmıştı.

Test **146 → 156.** Yeni kontroller: üç kip tanımlı mı, on bozukluk
kuralı var mı, birinci tekil kuralı bütün yüzeylere giriyor mu, ve
çekince yasağının yanlışlıkla eklenmediği.
