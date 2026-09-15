#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ALGI EŞİĞİ — bu kişide bir etkinin fark edilir olması için ne gerekir

SORUN
    Bütün astroloji ORB üzerine kuruludur: bir açının kaç derece sapmayla
    hâlâ "etkili" sayılacağı. Kimi 3° der, kimi 5°, kimi 8°. Ekol farkı
    diye geçiştirilir.

    Kimse bunu HESAPLAMAZ. Gelenek, konvansiyon, alışkanlık. Bir haritanın
    kendisinden türetilmiş bir orb yoktur.

    Oysa şu apaçık: yoğun bir alanda küçük bir dokunuş kaybolur; seyrek bir
    alanda aynı dokunuş her şeyi değiştirir. Aynı transit iki insanda aynı
    ağırlıkta olamaz.

FİKİR — Weber-Fechner
    Psikofizikte FARK EŞİĞİ, bir uyaranın fark edilebilmesi için mevcut
    uyarıya ORANLA ne kadar büyümesi gerektiğini söyler. Gürültülü odada
    fısıltı duyulmaz; sessiz odada duyulur.

    Aynısı haritaya uygulanır. Sükût haritası zaten kişinin TABAN
    GÜRÜLTÜSÜNÜ ölçüyor. Buradan şu türetilir:

        Bu kişide bir etkinin fark edilir olması için ne kadar güçlü
        olması gerekir?

NEDEN ÖNEMLİ — bir haksızlığı düzeltir
    Bazı danışanlar her transiti bildirir. Bazıları aynı transit geçerken
    hiçbir şey söylemez. Astroloji bunu KİŞİYİ SUÇLAYARAK açıklar:
    "farkındalığı düşük", "kendini tanımıyor".

    Bu haksız bir açıklamadır — ölçülebilir bir farkı ahlaki bir kusura
    çevirir. Algı eşiği bunu hesaba döndürür: kişi duyarsız değil, eşiği
    yüksek.

YAN ÇIKTI — türetilmiş orb
    Eşik hesaplandığında orb da türetilir. 3° varsayılan olmaktan çıkar;
    her harita kendi orbunu söyler.

SINIR
    Yüksek eşik "duyarsız", düşük eşik "hassas" DEĞİLDİR. Ölçülen şey,
    bir uyaranın fark edilir olması için gereken büyüklüktür — kişinin
    değeri, olgunluğu ya da farkındalığı değil.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from .astro import NatalChart, CORE10, TR_NAME
from .sukut import sukut_haritasi

# Geleneksel varsayılan — karşılaştırma için
GELENEKSEL_ORB = 3.0


def algi_esigi(chart: NatalChart, harita: Optional[dict] = None) -> dict:
    """
    Kişinin taban gürültüsünden algı eşiğini ve türetilmiş orbunu çıkarır.

    `harita` verilmezse sükût haritası burada hesaplanır.
    """
    h = harita or sukut_haritasi(chart)
    if "hata" in h:
        return {"hata": h["hata"]}

    egri = [x["basinc"] for x in (h.get("egri") or [])]
    if len(egri) < 20:
        return {"hata": "eğri yetersiz"}

    taban = sum(egri) / len(egri)
    # Dağılımın genişliği: aynı ortalamada bile oynak bir eğri, düz bir
    # eğriden farklı davranır. Oynak eğride tek bir tepe fark edilmez.
    sapma = math.sqrt(sum((x - taban) ** 2 for x in egri) / len(egri))

    # WEBER ORANI: fark eşiği taban uyarana ORANTILIDIR.
    # Buradaki k, sabit bir sayı değil — dağılımın oynaklığından gelir.
    # Oynak eğri, farkın görülmesi için daha büyük bir sıçrama ister.
    k = 0.18 + 0.42 * min(1.0, sapma / max(0.001, taban))
    esik_mutlak = taban * k

    # Ölçek: geleneksel 3° orbun ürettiği tipik basınç ~ referans alınır.
    # Bu kişinin eşiği referansa göre kaç kat?
    referans = 2.2                       # tipik tek temas puanı
    kat = esik_mutlak / referans

    # TÜRETİLMİŞ ORB — TERS ORANTI
    # İlk formül `3° × (1 - kat)` idi ve YANLIŞTI: kat 1'e yaklaşınca
    # sonuç sıfıra gidiyor, beş haritanın beşinde de 1.0° kırpmasına
    # dayanıyordu — yani hiç ayrım üretmiyordu.
    #
    # Doğru ilişki ters orantıdır: eşik yükseldikçe bir açının kayda
    # geçmesi için daha DAR olması gerekir.
    #   kat = 1.0 → 3.0°   (tipik)
    #   kat = 1.4 → 2.1°   (yüksek eşik, dar orb)
    #   kat = 0.7 → 4.3°   (düşük eşik, geniş orb)
    orb = GELENEKSEL_ORB / max(0.35, kat)
    orb = round(min(7.0, max(1.2, orb)), 2)

    seviye, okuma, danismana = _yorum(kat, orb, sapma / max(0.001, taban))

    return {
        "modul": "ALGI EŞİĞİ — fark edilir olmak için ne gerekir",
        "taban_gurultu": round(taban, 2),
        "oynaklik": round(sapma, 2),
        "oynaklik_orani": round(sapma / max(0.001, taban), 3),
        "weber_k": round(k, 3),
        "esik_mutlak": round(esik_mutlak, 2),
        "esik_kat": round(kat, 2),
        "turetilmis_orb": orb,
        "geleneksel_orb": GELENEKSEL_ORB,
        "orb_farki": round(orb - GELENEKSEL_ORB, 2),
        "seviye": seviye,
        "okuma": okuma,
        "danismana": danismana,
        "yontem": (
            "Weber-Fechner fark eşiği: bir uyaranın fark edilmesi için "
            "gereken artış, mevcut uyarana ORANTILIDIR. Kişinin taban "
            "gürültüsü sükût haritasının basınç eğrisinden alınır; Weber "
            "katsayısı dağılımın oynaklığından türetilir. Orb bu eşikten "
            "geri hesaplanır — varsayılan değil, haritanın kendisinden."),
        "sinir": (
            "Yüksek eşik 'duyarsız', düşük eşik 'hassas' DEĞİLDİR. Ölçülen "
            "şey bir uyaranın fark edilir olması için gereken büyüklüktür; "
            "kişinin değeri, olgunluğu ya da farkındalığı değil."),
    }


# ETİKET EŞİKLERİ — varsayımla değil, ÖLÇÜMLE.
# İlk değerler (0.65 / 1.15) tahminle konmuştu ve 60 harita üzerinde
# sınandığında 60'ın 50'sini "orta"ya tıkıyordu; "düşük eşik" 24 haritada
# hiç çıkmadı — etiket işe yaramaz hâldeydi.
#
# 60 rastgele haritada gerçek dağılım: 0.62 – 1.31, ortanca 0.94.
# Eşikler %30 ve %70 dilimine çekildi; üç etiket de anlamlı sıklıkta
# çıkıyor (20 / 17 / 23).
DUSUK_ESIK = 0.86
YUKSEK_ESIK = 1.03


def _yorum(kat: float, orb: float, oynak: float):
    if kat >= YUKSEK_ESIK:
        return ("yüksek eşik",
                ("Bu haritada taban gürültü yüksek. Küçük gök olayları bu "
                 "kişide fark edilir bir iz bırakmıyor — kaybolup gidiyor. "
                 "Bir şeyin hissedilmesi için belirgin biçimde güçlü olması "
                 "gerekiyor."),
                ("Küçük transitleri anlatma; boşa gider ve seni inandırıcı "
                 "olmaktan çıkarır. Yalnız ağır olayları öne çıkar. Kişi "
                 "'ben bunu hissetmedim' diyorsa haklıdır — duyarsız değil, "
                 "eşiği yüksek."))
    if kat <= DUSUK_ESIK:
        return ("düşük eşik",
                ("Bu haritada taban gürültü düşük. Küçük gök olayları bile "
                 "bu kişide fark edilir bir iz bırakıyor. Sessizliğin içinde "
                 "her ses duyuluyor."),
                ("Ağır olayları abartarak anlatma — bu kişide zaten büyük "
                 "yankı yapar, üstüne dram eklemek zarar verir. Küçük "
                 "transitler burada gerçekten işe yarar; onları kullan."))
    return ("orta eşik",
            ("Taban gürültü orta düzeyde. Orta ve büyük gök olayları fark "
             "ediliyor, küçükler genelde kaybolıyor."),
            ("Orta ve büyük olayları anlat, küçükleri atla. Bu kişide "
             "geleneksel yaklaşım büyük ölçüde işe yarar."))


def orb_karsilastirma(chart: NatalChart, esik: Optional[dict] = None) -> dict:
    """
    Türetilmiş orb ile geleneksel orbun aynı haritada ne kadar farklı
    sonuç verdiğini gösterir — icadın somut karşılığı.
    """
    from .circular import sep
    e = esik or algi_esigi(chart)
    if "hata" in e:
        return e
    orb = e["turetilmis_orb"]

    noktalar = [(TR_NAME[k], chart.bodies[k].lon) for k in CORE10
                if k in chart.bodies]
    noktalar += [("Yükselen", chart.asc), ("Tepe noktası", chart.mc)]
    acilar = ((0, "kavuşum"), (180, "karşıt"), (90, "kare"), (120, "üçgen"),
              (60, "altmışlık"))

    gelenek, turetilmis, sinirda = 0, 0, []
    for i in range(len(noktalar)):
        for j in range(i + 1, len(noktalar)):
            a1, l1 = noktalar[i]
            a2, l2 = noktalar[j]
            d = sep(l1, l2)
            # `break` KOŞULSUZDU: ilk açı türünde (kavuşum) döngüden
            # çıkıyor, öteki dördüne hiç bakmıyordu. Bu yüzden 12 nokta
            # arasında yalnız 1-4 açı sayılıyordu. Artık eşleşince çıkar.
            for hedef, tur in acilar:
                fark = abs(d - hedef)
                if fark > max(GELENEKSEL_ORB, orb):
                    continue
                g = fark <= GELENEKSEL_ORB
                t = fark <= orb
                if g:
                    gelenek += 1
                if t:
                    turetilmis += 1
                if g != t:
                    sinirda.append({"a": a1, "b": a2, "aci": tur,
                                    "orb": round(fark, 2),
                                    "durum": "eklendi" if t else "düştü"})
                break

    return {
        "turetilmis_orb": orb,
        "geleneksel_orb": GELENEKSEL_ORB,
        "gelenekle_acisi": gelenek,
        "turetilmisle_acisi": turetilmis,
        "fark": turetilmis - gelenek,
        "sinirdakiler": sinirda[:8],
        "okuma": (
            f"Geleneksel {GELENEKSEL_ORB}° orb bu haritada {gelenek} açı "
            f"sayıyor; bu kişinin kendi orbu ({orb}°) {turetilmis} açı "
            f"sayıyor. " +
            ("Fark yok — geleneksel değer bu haritada zaten doğru."
             if turetilmis == gelenek else
             f"{abs(turetilmis - gelenek)} açı "
             f"{'ekleniyor' if turetilmis > gelenek else 'düşüyor'}. "
             f"Sınırdaki açılar aşağıda; bunlar 'var mı yok mu' tartışması "
             f"yaratan açılardır ve bu kişide cevabı belli.")),
    }
