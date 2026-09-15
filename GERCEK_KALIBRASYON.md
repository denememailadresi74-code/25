# ZÎC v13.4 — Gerçek Referans ve SİCİL Kalibrasyonu

Bu prosedür MİZAN-5 ve ŞAHİT-7'nin yüzdelik cetvellerini yaşayan danışan popülasyonuna göre yeniler. Astrolojik doğruluk ölçmez; yalnız referans dağılımının kullanılan popülasyona uyup uymadığını denetler.

## 1. Kalıcı veri dizini

Üretimde önce kalıcı veri yolunu tanımlayın:

```bash
ZIC_VERI_DIZINI=/var/data/zic
```

Bu dizinde `defter.db` ile birlikte yönetici tarafından üretilen gerçek/SİCİL referansları da tutulur:

- `mizan_quantiles_gercek.json`
- `sahit_quantiles_gercek.json`

`ZIC_VERI_DIZINI` verilmezse geriye uyum için `app/` kullanılır. Render ücretsiz web service kalıcı disk sağlamadığından `render.yaml` içindeki disk bölümü örnek olarak yorum satırındadır; kalıcı disk kullanılan planda açılmalıdır. Disk yoksa `/api/v2/defter/disaria` ile yedek alın, `/api/v2/defter/iceri` ile geri yükleyin.

## 2. Örneklem

En az **60**, tercihen **200+** birbirinden bağımsız `/api/v1/full` çıktısı kullanın. 60'ın altındaki dizin v13.4 tarafından reddedilir. Aynı kişinin tekrar analizlerini mümkünse tek kayda indirin; aksi hâlde yoğun kullanıcılar referansı gereğinden fazla etkiler.

SİCİL farklı çalışır: üretimde her gerçek analizden yalnız MİZAN/ŞAHİT **ham endeks değerlerini** ve zaman damgasını toplar. Kişi adı, doğum tarihi, koordinat ve danışman metni SİCİL'e yazılmaz.

## 3. Anonimleştirme

Dosyadan gerçek referans kuracaksanız ad, e-posta, telefon, serbest not veya başka kimlik bilgisi gerekmez. JSON'da hesap katmanları kalabilir; `girdi.ad` gibi kişi tanımlayıcı alanları silin veya anonim sıra numarasıyla değiştirin. Dosya adında danışan adı kullanmayın.

AYÂR tamponu daha da küçüktür: yalnız MİZAN/ŞAHİT yüzdelikleri ve zaman damgası tutar.

## 4. Önce mevcut referansı doğrulayın

```bash
python kalibrasyon.py --kaynak gercek --girdi ./anonim_full --n 200 \
  --dogrula app/mizan_quantiles.json --cikti gercek_dogrulama.json
```

Hedef: MİZAN eksenlerinde ortalama yaklaşık **45–55**, baskınlık yaklaşık **%15–25**. ŞAHİT merceklerinde ortalama **45–55** beklenir. AYÂR, referansın kendi taban ortalama/kuyruk oranlarını kullanarak yaşayan örneklemdeki kaymayı izler; AYÂR uyarısı endeksin veya danışanın “yanlış” olduğu anlamına gelmez.

## 5. Dosyadan yeni gerçek referans üretin

```bash
python kalibrasyon.py --kaynak gercek --girdi ./anonim_full --n 200 \
  --referans-yaz --sahit-referans --cikti kalibrasyon_gercek.json
```

Gerçek referanslar aktif `ZIC_VERI_DIZINI` içine yazılır. Her dosyada `kaynak: "gercek"`, `uretim_tarihi`, `ornek_sayisi` ve AYÂR'ın göreli karşılaştırmada kullandığı `ayar_taban` bulunur. Referans değiştiğinde AYÂR tamponu sıfırlanır; eski cetvelle toplanan sapma geçmişi yeni cetvelle karıştırılmaz.

`app/mizan_quantiles.json` ve `app/sahit_quantiles.json` sentetik yedek olarak kalır. `app/mizan_quantiles_v133.json` v13.3 referansının değişmez yedeğidir.

## 6. SİCİL'den referans kurma

`GET /api/v2/sicil/ozet` biriken anonim kayıt sayısını ve referans kurmaya kaç kayıt kaldığını gösterir. **60 kayıttan önce hiçbir havuz yüzdeliği yayınlanmaz.**

60+ kayıt olduğunda yönetici açıkça:

```text
POST /api/v2/sicil/referans-kur
```

çağrısını yapabilir. Otomatik devreye alma yoktur. Üretilen dosyalar `kaynak: "sicil"`, `uretim_tarihi` ve `ornek_sayisi` taşır; ardından AYÂR tamponu sıfırlanır.

SİCİL genel nüfus normu değildir. Yalnız bu uygulamayı kullanan danışan havuzunun dağılımıdır; havuz belli bir profile ağırlık veriyorsa referans da aynı yönde taraflı olur.

## 7. Yeni referansı sınayın

Kalıcı dizin kullanmıyorsanız varsayılan yol `app/mizan_quantiles_gercek.json` olur. Kalıcı dizin kullanıyorsanız dosyayı o dizinden verin:

```bash
python kalibrasyon.py --kaynak gercek --girdi ./anonim_full --n 200 \
  --dogrula "$ZIC_VERI_DIZINI/mizan_quantiles_gercek.json" \
  --cikti yeni_ref_dogrulama.json
```

Aynı örneklemde MİZAN ortalamalarının 45–55, baskınlıkların %15–25 bandında olması beklenir. Popülasyon zamanla değişirse AYÂR referansın yeniden değerlendirilmesini ister.

## 8. Gerçek referans yoksa

Sistem sentetik referansa düşer ve bunu `kalibrasyon_kaynagi` / `referans_bilgisi` alanlarında açıkça bildirir. Gerçek danışan verisi yokken `kaynak: "gercek"` etiketli tablo üretmeyin.

## 9. Render kalıcı disk ve ücretsiz plan yedek prosedürü

### Kalıcı disk bulunan Render planı

1. Render Dashboard → ilgili Web Service → **Disks** → **Add Disk**.
2. Disk adı örneğin `zic-veri`, mount path kesin olarak `/var/data/zic` olsun.
3. Environment bölümüne `ZIC_VERI_DIZINI=/var/data/zic` ekleyin.
4. Servisi yeniden deploy edin ve yönetici panelindeki Defter uyarısının kaybolduğunu doğrulayın.
5. Disk bağlı olsa bile saha arşivi için düzenli `/api/v2/defter/disaria` yedeği alın.

`render.yaml` içindeki disk örneği bilinçli olarak yorum satırındadır; `plan: free`
kullanılırken otomatik açılması deploy'u geçersiz kılar.

### Render Free plan

Free Web Service'te persistent disk yoktur. Bu durumda uygulama çalışır fakat
uyku, yeniden başlatma veya yeni deploy sonrası yerel SQLite dosyasının kalacağı
garanti edilmez. Yönetici paneli bu riski iki biçimde görünür kılar:

- daha önce dolu olduğu bilinen Defter boş açılırsa **“Defter sıfırlanmış olabilir
  — yedeği geri yükleyin.”** uyarısı,
- yapılandırılmış iddia sayısı 25'in katına geldiğinde **yedek indirme
  hatırlatması**.

Saha rutini:

1. Uyarı çıkmasını beklemeden her 25 iddiada **Yedeği indir** ile tek JSON dosyası alın.
2. Dosyayı danışan isimleriyle adlandırmayın; örneğin `zic_defter_yedek_20260915.json` kullanın.
3. Servis sıfırlanırsa yönetici panelindeki **Yedeği yükle** ile dosyayı seçin.
4. İçe aktarma `birlestir=true` çalışır; aynı yedeği yanlışlıkla ikinci kez seçmek
   AYÂR, SİCİL veya İddia kayıtlarını çoğaltmaz.
5. Geri yüklemeden sonra Geçmiş Okumalar sayacını ve `/api/v2/sicil/ozet`
   kayıt sayısını kontrol edin.

Yedek dosyası yapılandırılmış ölçüm/iddia kayıtlarını taşır; serbest danışman
metni, doğum tarihi, koordinat veya danışan adı kalıcı depoya yazılmaz.
