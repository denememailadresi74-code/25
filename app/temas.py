#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEMAS AÇISI — bu okuma bu danışmandan bu kişiye nasıl varır

GÖRÜLMEYEN DEĞİŞKEN
    Sistem kişinin yapısını on beş katmanda ölçüyor. Ölçmediği tek şey,
    okumanın GEÇTİĞİ KANAL: danışmanın kendisi.

    Astrolojide sinastri vardır ama yalnız romantik ya da ailevi ilişki
    için kullanılır. Kimse DANIŞMAN–DANIŞAN ilişkisini hesaplamaz. Oysa
    aynı doğru cümle, iki farklı danışmanın ağzından iki farklı şey olur:
    birinden duyulur, ötekinden duyulmaz.

    Bu, danışmanın iyi ya da kötü olmasıyla ilgili değildir. Geometriyle
    ilgilidir — ve geometri hesaplanabilir.

NE HESAPLANIR
    Danışmanın natal haritası ile danışanınki arasındaki temas yapısı,
    ama İLİŞKİ olarak değil AKTARIM KANALI olarak okunur:

    · ORTAK ZEMİN — hangi konularda aynı dili konuşuyorlar. Burada
      danışman sezgisiyle doğruyu bulur; anlatması kolaydır.

    · KÖR NOKTA — danışanın belirgin bir yanı danışmanın haritasında
      karşılıksızsa, danışman onu HAFİFE ALMA eğilimindedir. Kendisinde
      olmayan şeyi küçümsemek insanidir.

    · YANSIMA RİSKİ — danışanın çatalı danışmanınkiyle aynıysa, danışman
      kendi meselesini danışanda okur. En sinsi hata budur; sistemin
      "kendi hikâyeni anlatma" kuralı tam burada çiğnenir.

    · SERT TEMAS — dar orblu zorlu açılar. Ne kötüdür ne iyidir: söz
      ağırlaşır. Aynı cümle daha çok yer eder, yanlışsa daha çok kırar.

NEDEN PROMPTA GİRER
    Bu bir bölüm değil, bir UYARI KATMANIDIR. Modele "bu danışman burada
    hafife alabilir, burada kendi meselesini karıştırabilir" der. Yani
    okumanın nasıl yazılacağını değiştirir — hangi noktada ekstra
    dikkat gerektiğini söyler.

SINIR
    Bu bir uyum puanı DEĞİLDİR. "Bu danışman bu kişiye uygun/uygun değil"
    denmez. Ölçülen şey, hangi noktalarda ekstra dikkat gerektiğidir.
    Kötü temas diye bir şey yoktur; farkında olunmayan temas vardır.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .astro import NatalChart, CORE10, TR_NAME
from .circular import sep

ACILAR = ((0, "kavuşum", 1.0, "yumuşak"), (180, "karşıt", 0.9, "sert"),
          (90, "kare", 0.85, "sert"), (120, "üçgen", 0.6, "yumuşak"),
          (60, "altmışlık", 0.4, "yumuşak"))
ORB = 3.0


def _noktalar(ch: NatalChart) -> List[Tuple[str, float]]:
    n = [(TR_NAME[k], ch.bodies[k].lon) for k in CORE10 if k in ch.bodies]
    n += [("Yükselen", ch.asc), ("Tepe noktası", ch.mc)]
    return n


def temas_acisi(danisman: NatalChart, danisan: NatalChart,
                danisan_v2: Optional[dict] = None,
                danisman_v2: Optional[dict] = None) -> dict:
    """
    Danışman–danışan aktarım kanalını hesaplar.

    `*_v2` verilirse çatal karşılaştırması da yapılır (yansıma riski).
    """
    dm, dn = _noktalar(danisman), _noktalar(danisan)

    temaslar: List[dict] = []
    for ad_a, la in dm:
        for ad_b, lb in dn:
            d = sep(la, lb)
            for hedef, tur, pay, cins in ACILAR:
                fark = abs(d - hedef)
                if fark <= ORB:
                    temaslar.append({
                        "danisman": ad_a, "danisan": ad_b, "aci": tur,
                        "cins": cins, "orb": round(fark, 2),
                        "guc": round(pay * (1 - fark / ORB), 2)})
                    break
    temaslar.sort(key=lambda x: -x["guc"])

    yumusak = [t for t in temaslar if t["cins"] == "yumuşak"]
    sert = [t for t in temaslar if t["cins"] == "sert"]

    # KÖR NOKTA: danışanın hangi noktası danışmanda hiç karşılık bulmuyor
    degen = {t["danisan"] for t in temaslar}
    kor = [ad for ad, _l in dn if ad not in degen]

    # YANSIMA RİSKİ: aynı çatal
    yansima = None
    if danisan_v2 and danisman_v2:
        c1 = ((danisan_v2.get("berzah") or {}).get("catalin_adi") or
              (danisan_v2.get("berzah") or {}).get("catalin_cumlesi"))
        c2 = ((danisman_v2.get("berzah") or {}).get("catalin_adi") or
              (danisman_v2.get("berzah") or {}).get("catalin_cumlesi"))
        if c1 and c2 and str(c1).strip() == str(c2).strip():
            yansima = str(c1)

    return {
        "modul": "TEMAS AÇISI — okuma bu kanaldan nasıl varır",
        "temas_sayisi": len(temaslar),
        "yumusak": len(yumusak), "sert": len(sert),
        "en_guclu": temaslar[:5],
        "en_sert": sert[:3],
        "kor_noktalar": kor,
        "yansima_catali": yansima,
        "uyarilar": _uyarilar(temaslar, sert, kor, yansima),
        "okuma": _okuma(temaslar, yumusak, sert, kor, yansima),
        "yontem": (f"Danışman ve danışanın on iki noktası arasındaki "
                   f"temaslar {ORB}° orbla taranır. Sinastri gibi hesaplanır "
                   f"ama İLİŞKİ olarak değil AKTARIM KANALI olarak okunur: "
                   f"nerede kolay anlaşılır, nerede hafife alınır, nerede "
                   f"danışman kendi meselesini karıştırır."),
        "sinir": ("Bu bir uyum puanı DEĞİLDİR. 'Bu danışman bu kişiye "
                  "uygun/uygun değil' denmez. Kötü temas diye bir şey "
                  "yoktur; farkında olunmayan temas vardır."),
    }


def _uyarilar(temaslar, sert, kor, yansima) -> List[dict]:
    """Prompta girecek somut uyarılar."""
    u: List[dict] = []
    if yansima:
        u.append({
            "tur": "yansıma",
            "agirlik": "yüksek",
            "metin": (f"Danışmanla danışanın çatalı AYNI: «{yansima}». "
                      "Danışman kendi meselesini bu kişide okuma "
                      "eğilimindedir — en sinsi hata budur. Bu konuda "
                      "söylenen her şeyi bir kez daha sına: bu kişinin "
                      "verisinden mi geliyor, yoksa tanıdık geldiği için mi?")})
    if kor:
        u.append({
            "tur": "kör nokta",
            "agirlik": "orta",
            "metin": ("Danışanın şu yanları danışmanın haritasında "
                      "karşılıksız: " + ", ".join(kor[:4]) +
                      ". Kendisinde olmayan şeyi hafife almak insanidir — "
                      "bu yanları anlatırken fazladan yer ver, geçiştirme.")})
    if sert and sert[0]["orb"] <= 1.2:
        t = sert[0]
        u.append({
            "tur": "sert temas",
            "agirlik": "orta",
            "metin": (f"Dar sert temas: danışmanın {t['danisman']} yanı "
                      f"danışanın {t['danisan']} yanıyla {t['aci']} "
                      f"(orb {t['orb']}°). Bu konuda söz AĞIRLAŞIR — aynı "
                      "cümle daha çok yer eder, yanlışsa daha çok kırar. "
                      "Burada tartma, kesme.")})
    if len(temaslar) <= 3:
        u.append({
            "tur": "zayıf kanal",
            "agirlik": "orta",
            "metin": ("İki harita arasında az temas var. Sezgiye güvenme; "
                      "bu kişide 'anladım' hissi yanıltıcı olabilir. "
                      "Veriye sıkı sıkı bağlı kal.")})
    elif len(temaslar) >= 14:
        u.append({
            "tur": "yoğun kanal",
            "agirlik": "düşük",
            "metin": ("İki harita çok temas hâlinde. Anlaşma kolay olur ama "
                      "ayrım zorlaşır: danışmanın kendi tepkisi ile "
                      "danışanın hâli birbirine karışabilir.")})
    return u


def _okuma(temaslar, yumusak, sert, kor, yansima) -> str:
    p = [f"{len(temaslar)} temas: {len(yumusak)} yumuşak, {len(sert)} sert."]
    if temaslar:
        t = temaslar[0]
        p.append(f"En güçlüsü {t['danisman']}–{t['danisan']} {t['aci']} "
                 f"(orb {t['orb']}°).")
    if yansima:
        p.append(f"DİKKAT: çatal aynı — «{yansima}».")
    if kor:
        p.append("Karşılıksız kalan: " + ", ".join(kor[:3]) + ".")
    return " ".join(p)
