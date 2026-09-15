#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
İLİŞKİ KATMANI — Sinastri ve Kompozit.

SİNASTRİ : İki harita üst üste konur. Kimin gezegeni kimin evine düşüyor,
           hangi çapraz açılar kuruluyor, ve BERZAH modeline özgü olarak:
           A'nın kütlesi B'nin alanını nasıl büküyor (karşılıklı Φ katkısı).

KOMPOZİT : İki haritanın orta noktalarından üçüncü bir harita kurulur —
           ilişkinin kendi haritası. Kompozit haritada tam v2 motoru koşar;
           yani ilişkinin de kendi Kara Deliği, Ak Deliği ve Berzahı olur.

Not: Kompozit haritada hız ve deklinasyon ortalanır; retrogradlık ancak
     her iki cisim de retro ise korunur (klasik uygulamayla uyumlu).
"""
from __future__ import annotations
import math
from dataclasses import replace
from typing import Dict, List, Optional, Sequence, Tuple

import swisseph as swe

from .astro import (NatalChart, BodyPos, CORE10, TR_NAME, EPHFLAG, ensure_ephe,
                    _evler, jd_to_iso, chart_at_jd)
from .circular import norm360, sep, signed_sep, fmt_lon, sign_of, house_of
from .engine_mass import compute_masses, phi_field, find_kd_ad, find_berzah2, full_v2
from .modules_deneme import _ASPECTS, _orb_gucu, NURANI_W

# Sinastride ağırlığı olan klasik temas kalıpları
_ILISKI_ONEM = {
    frozenset({"Sun", "Moon"}): ("Güneş–Ay teması", "klasik evlilik açısı: biri kimlik, biri bakım"),
    frozenset({"Venus", "Mars"}): ("Venüs–Mars teması", "çekim ekseni; arzu ile değerin buluşması"),
    frozenset({"Sun", "Venus"}): ("Güneş–Venüs", "beğeni ve onaylanma"),
    frozenset({"Moon", "Venus"}): ("Ay–Venüs", "şefkat, evcimenlik"),
    frozenset({"Moon", "Saturn"}): ("Ay–Satürn", "güven mi soğukluk mu — ilişkinin taşıyıcı kirişi"),
    frozenset({"Venus", "Saturn"}): ("Venüs–Satürn", "kalıcılık ile kısıtlanma aynı açıda"),
    frozenset({"Sun", "Saturn"}): ("Güneş–Satürn", "otorite dengesi"),
    frozenset({"Moon", "Pluto"}): ("Ay–Plüton", "duygusal yoğunluk, sahiplenme"),
    frozenset({"Venus", "Pluto"}): ("Venüs–Plüton", "dönüştürücü çekim, kıskançlık riski"),
    frozenset({"Mars", "Saturn"}): ("Mars–Satürn", "itki ile fren; öfkenin birikme yeri"),
    frozenset({"Sun", "Uranus"}): ("Güneş–Uranüs", "özgürlük ile bağlılık gerilimi"),
    frozenset({"Moon", "Uranus"}): ("Ay–Uranüs", "tahmin edilemezlik, ani mesafe"),
    frozenset({"Venus", "Neptune"}): ("Venüs–Neptün", "idealleştirme; hayal kırıklığı riski"),
}
_EV_ANLAM = {
    1: "kimliğine dokunuyor — 'seninle başka biri oluyorum'",
    2: "değer ve kaynak alanına giriyor",
    3: "gündelik dile ve düşünceye yerleşiyor",
    4: "eve, köke, aidiyete yerleşiyor",
    5: "oyuna, yaratıma, flörte düşüyor",
    6: "günlük düzene ve hizmete düşüyor",
    7: "doğrudan ortaklık evine — ilişkinin ta kendisi",
    8: "ortak kaynak, borç, teslimiyet ve kriz alanı",
    9: "anlam ve inanç alanını genişletiyor",
    10: "kariyer ve toplumsal görünüm alanına",
    11: "gelecek ve çevre tasavvuruna",
    12: "görünmeyene — geri çekilme, feragat, sabotaj",
}


# ============================================================================
# SİNASTRİ
# ============================================================================
def capraz_acilar(a: NatalChart, b: NatalChart, ad_a: str, ad_b: str,
                  limit: int = 18) -> List[dict]:
    """A'nın cisimleri ile B'nin cisimleri arasındaki açılar (Astro Pro orbları)."""
    hedefler_a = {k: a.bodies[k].lon for k in CORE10}
    hedefler_a["Asc"] = a.asc; hedefler_a["MC"] = a.mc
    hedefler_b = {k: b.bodies[k].lon for k in CORE10}
    hedefler_b["Asc"] = b.asc; hedefler_b["MC"] = b.mc

    out = []
    for ka, la in hedefler_a.items():
        for kb, lb in hedefler_b.items():
            d = sep(la, lb)
            for nm, glif, ang, orb, w, majör in _ASPECTS:
                o = abs(d - ang)
                if o <= orb:
                    guc = w * _orb_gucu(o, orb)
                    if guc <= 0:
                        break
                    onem = _ILISKI_ONEM.get(frozenset({ka, kb}))
                    out.append({
                        "a": f"{ad_a} {TR_NAME.get(ka, ka)}",
                        "b": f"{ad_b} {TR_NAME.get(kb, kb)}",
                        "aci": nm, "glif": glif, "orb": round(o, 2),
                        "guc": round(guc, 3), "major": majör,
                        "baslik": onem[0] if onem else None,
                        "anlam": onem[1] if onem else None,
                    })
                    break
    out.sort(key=lambda x: (-(1 if x["baslik"] else 0), -x["guc"]))
    return out[:limit]


def ev_bindirmesi(kaynak: NatalChart, hedef: NatalChart,
                  ad_kaynak: str, ad_hedef: str) -> List[dict]:
    """Kaynağın gezegenleri hedefin hangi evine düşüyor."""
    out = []
    for k in CORE10:
        ev = house_of(kaynak.bodies[k].lon, hedef.cusps)
        if ev:
            out.append({"gezegen": f"{ad_kaynak} {TR_NAME[k]}",
                        "ev": ev, "kimde": ad_hedef,
                        "anlam": _EV_ANLAM[ev]})
    # sahne kalabalığı: en çok gezegen alan ev
    sayim: Dict[int, int] = {}
    for r in out:
        sayim[r["ev"]] = sayim.get(r["ev"], 0) + 1
    if sayim:
        yogun = max(sayim, key=lambda e: sayim[e])
        for r in out:
            r["yogun_ev"] = (r["ev"] == yogun and sayim[yogun] >= 3)
    return out


def alan_bukmesi(a: NatalChart, b: NatalChart, ad_a: str, ad_b: str) -> dict:
    """
    BERZAH'a özgü sinastri ölçüsü: A'nın kütleleri B'nin Φ alanına eklenince
    B'nin Kara Deliği ve Berzahı NEREYE KAYIYOR? Kayma büyükse o kişi, ötekinin
    yanında başka bir insan olur — bu, klasik sinastrinin ölçmediği şeydir.
    """
    ms_a = compute_masses(a)
    ms_b = compute_masses(b)

    def kayma(kendi, otekinin):
        kd0, _ = find_kd_ad(kendi)
        b0 = find_berzah2(kendi)
        birlesik = list(kendi) + list(otekinin)
        kd1, _ = find_kd_ad(birlesik)
        b1 = find_berzah2(birlesik)
        return {
            "KD_yalniz": fmt_lon(kd0), "KD_birlikte": fmt_lon(kd1),
            "KD_kaymasi": round(sep(kd0, kd1), 2),
            "Berzah_yalniz": fmt_lon(b0.lon) if b0 else None,
            "Berzah_birlikte": fmt_lon(b1.lon) if b1 else None,
            "Berzah_kaymasi": round(sep(b0.lon, b1.lon), 2) if (b0 and b1) else None,
        }

    ka = kayma(ms_b, ms_a)   # A, B'nin alanını ne kadar büküyor
    kb = kayma(ms_a, ms_b)   # B, A'nın alanını ne kadar büküyor

    def yorum(k):
        v = k["Berzah_kaymasi"] if k["Berzah_kaymasi"] is not None else k["KD_kaymasi"]
        if v is None:
            return "ölçülemedi"
        if v < 3:
            return "alan neredeyse değişmiyor — kişi bu ilişkide kendisi kalıyor"
        if v < 15:
            return "alan gözle görülür bükülüyor — kararlar farklı yerden veriliyor"
        return "alan baştan kuruluyor — kişi bu ilişkide başka biri oluyor"

    return {
        f"{ad_a}_alanini_bukuyor": ka | {"yorum": yorum(ka)},
        f"{ad_b}_alanini_bukuyor": kb | {"yorum": yorum(kb)},
        "yontem": ("Bir kişinin kütleleri ötekinin Φ alanına eklenir ve KD ile "
                   "Berzah'ın kaç derece kaydığı ölçülür. Klasik sinastri açı "
                   "sayar; bu ölçü karar noktasının yerinden oynayıp oynamadığını "
                   "sorar."),
    }


def sinastri(a: NatalChart, b: NatalChart,
             ad_a: str = "A", ad_b: str = "B") -> dict:
    acilar = capraz_acilar(a, b, ad_a, ad_b)
    majör = [x for x in acilar if x["major"]]
    destek = sum(x["guc"] for x in acilar if x["aci"] in ("Üçgen", "Altmışlık", "Kavuşum"))
    sinav = sum(x["guc"] for x in acilar if x["aci"] in ("Kare", "Karşıt"))
    toplam = destek + sinav
    return {
        "mod": "Sinastri",
        "kisiler": {"A": ad_a, "B": ad_b},
        "capraz_acilar": acilar,
        "onemli_temaslar": [x for x in acilar if x["baslik"]][:6],
        "ev_bindirmesi": {
            f"{ad_a}_gezegenleri_{ad_b}_evlerinde": ev_bindirmesi(a, b, ad_a, ad_b),
            f"{ad_b}_gezegenleri_{ad_a}_evlerinde": ev_bindirmesi(b, a, ad_b, ad_a),
        },
        "alan_bukmesi": alan_bukmesi(a, b, ad_a, ad_b),
        "denge": {
            "destek": round(destek, 2), "sinav": round(sinav, 2),
            "major_aci": len(majör),
            "oran": round(destek / sinav, 2) if sinav > 0 else None,
            "okuma": ("akış baskın — kolay ama uyarıcı gerilim az" if sinav > 0 and destek / sinav > 1.8
                      else "sınav baskın — çekim güçlü, sürtünme de güçlü" if sinav > 0 and destek / sinav < 0.6
                      else "dengeli — hem taşıyan hem zorlayan bağ var"),
        },
    }


# ============================================================================
# KOMPOZİT
# ============================================================================
def kompozit_harita(a: NatalChart, b: NatalChart,
                    etiket: str = "Kompozit") -> NatalChart:
    """
    Orta nokta kompoziti. Her cisim için kısa yay ortası alınır;
    ASC/MC de aynı şekilde. Ev uçları kompozit ASC/MC'den türetilir
    (Whole Sign temeli: coğrafi konum ortalaması anlamlı olmadığı için
    kompozitte kutupsal ev sistemleri güvenilir değildir).
    """
    def orta(x: float, y: float) -> float:
        return norm360(x + signed_sep(y, x) / 2.0)

    bodies: Dict[str, BodyPos] = {}
    for k, ba in a.bodies.items():
        bb = b.bodies.get(k)
        if bb is None:
            continue
        bodies[k] = BodyPos(
            key=k, name_tr=ba.name_tr,
            lon=orta(ba.lon, bb.lon),
            lat=(ba.lat + bb.lat) / 2.0,
            speed=(ba.speed + bb.speed) / 2.0,
            decl=(ba.decl + bb.decl) / 2.0,
            retro=(ba.retro and bb.retro),
        )
    asc = orta(a.asc, b.asc)
    mc = orta(a.mc, b.mc)
    vertex = orta(a.vertex, b.vertex)
    # Whole Sign: ASC'nin burcunun 0. derecesinden başlayan 12 eşit ev
    kok = (int(asc // 30)) * 30.0
    cusps = [norm360(kok + 30 * i) for i in range(12)]
    return NatalChart(label=etiket, jd_ut=(a.jd_ut + b.jd_ut) / 2.0,
                      lat=(a.lat + b.lat) / 2.0, lng=(a.lng + b.lng) / 2.0,
                      tz_offset=0.0, bodies=bodies, asc=asc, mc=mc,
                      vertex=vertex, cusps=cusps,
                      house_system="W (kompozit — eşit ev)",
                      tz_source="kompozit: iki haritanın orta noktası")


def kompozit(a: NatalChart, b: NatalChart,
             ad_a: str = "A", ad_b: str = "B") -> dict:
    ch = kompozit_harita(a, b, f"{ad_a} & {ad_b}")
    v2 = full_v2(ch)
    return {
        "mod": "Kompozit",
        "kisiler": {"A": ad_a, "B": ad_b},
        "harita": {
            "ASC": fmt_lon(ch.asc), "MC": fmt_lon(ch.mc),
            "ev_sistemi": ch.house_system,
            "gezegenler": [{"cisim": ch.bodies[k].name_tr,
                            "konum": fmt_lon(ch.bodies[k].lon),
                            "ev": ch.house(ch.bodies[k].lon)}
                           for k in CORE10 if k in ch.bodies],
        },
        "berzah_v2": v2,
        "okuma": ("Kompozit, ilişkinin kendi haritasıdır. Buradaki Kara Delik "
                  "ilişkinin tekrar eden şikâyet kaynağı, Berzah ise çiftin "
                  "birlikte verdiği kararın düştüğü eşiktir — kimsenin tek "
                  "başına çözemeyeceği yer."),
        "uyari": ("Kompozit haritada hız ve deklinasyon ortalamadır; bu yüzden "
                  "kütle formülünün hız bileşeni natal haritadaki kadar anlamlı "
                  "değildir. Ev sistemi eşit evdir."),
    }


# ============================================================================
# DAVISON — zaman-mekân orta noktası haritası
# ============================================================================
def _kuresel_orta_nokta(lat1: float, lon1: float,
                        lat2: float, lon2: float) -> Tuple[float, float]:
    """
    İki konumun GERÇEK coğrafi orta noktası (büyük çember üzerinde).

    Enlem/boylamın aritmetik ortalamasını almak yanlıştır: boylam sarmalı
    (179° ve -179° ortalaması 0° çıkar, oysa doğru cevap 180°'dir) ve küre
    eğriliği yüzünden sapma yüzlerce kilometreyi bulabilir.
    """
    r = math.radians
    f1, l1, f2, l2 = r(lat1), r(lon1), r(lat2), r(lon2)
    dl = l2 - l1
    bx = math.cos(f2) * math.cos(dl)
    by = math.cos(f2) * math.sin(dl)
    f3 = math.atan2(math.sin(f1) + math.sin(f2),
                    math.sqrt((math.cos(f1) + bx) ** 2 + by ** 2))
    l3 = l1 + math.atan2(by, math.cos(f1) + bx)
    return math.degrees(f3), (math.degrees(l3) + 540) % 360 - 180


def davison(a: NatalChart, b: NatalChart,
            ad_a: str = "A", ad_b: str = "B") -> dict:
    """
    DAVISON HARİTASI — kompozitten farklıdır ve tamamlayıcısıdır.

      Kompozit : iki haritanın KONUMLARININ orta noktası. Var olmayan bir an;
                 ilişkinin soyut portresi.
      Davison  : iki doğumun ZAMAN ve MEKÂN orta noktasında kurulmuş GERÇEK
                 bir harita. O anda gökyüzü gerçekten öyleydi; dolayısıyla
                 transit ve ilerletme uygulanabilir — kompozitte bu tartışmalı.

    İkisi ayrı şey söylediğinde bu bir çelişki değil, iki farklı sorunun
    cevabıdır: kompozit "bu ilişki nedir", Davison "bu ilişki ne zaman ne
    yapar" sorusuna bakar.
    """
    jd = (a.jd_ut + b.jd_ut) / 2.0
    lat, lng = _kuresel_orta_nokta(a.lat, a.lng, b.lat, b.lng)
    ch = chart_at_jd(jd, lat, lng, f"Davison {ad_a}&{ad_b}", a.house_system)
    v2 = full_v2(ch, topoloji=False)
    # aritmetik ortalamayla farkı — yöntemin neden önemli olduğunu gösterir
    duz_lat, duz_lng = (a.lat + b.lat) / 2.0, (a.lng + b.lng) / 2.0
    sapma_km = math.hypot((lat - duz_lat) * 111.0,
                          (lng - duz_lng) * 111.0 * math.cos(math.radians(lat)))
    return {
        "an": jd_to_iso(jd),
        "konum": {"enlem": round(lat, 4), "boylam": round(lng, 4),
                  "aritmetik_ortalamadan_sapma_km": round(sapma_km, 1)},
        "harita": {"ASC": fmt_lon(ch.asc), "MC": fmt_lon(ch.mc),
                   "ev_sistemi": ch.house_system,
                   "gezegenler": [{"cisim": ch.bodies[k].name_tr,
                                   "konum": fmt_lon(ch.bodies[k].lon),
                                   "ev": ch.house(ch.bodies[k].lon),
                                   "retro": ch.bodies[k].retro}
                                  for k in CORE10]},
        "berzah_v2": v2,
        "okuma": ("Davison gerçek bir andır: o gün gökyüzü tam olarak böyleydi. "
                  "Bu yüzden ilişkinin zamanlaması buradan okunur — kompozit "
                  "ilişkinin ne olduğunu, Davison ne zaman ne yapacağını söyler."),
        "yontem": ("Zaman: iki doğum anının ortası. Mekân: iki konumun büyük "
                   "çember üzerindeki gerçek orta noktası (aritmetik ortalama "
                   f"değil — bu haritada aradaki fark {sapma_km:.0f} km)."),
    }


# ============================================================================
# DEKLİNASYON SİNASTRİSİ — boylamda görünmeyen bağlar
# ============================================================================
def deklinasyon_sinastri(a: NatalChart, b: NatalChart,
                         ad_a: str = "A", ad_b: str = "B",
                         orb: float = 1.0) -> dict:
    """
    İki kişi arasındaki paralel / karşıt-paralel temaslar.

    Klasik sinastri yalnız boylama bakar. Aynı deklinasyon kuşağındaki iki
    cisim, boylamda 100° uzak olsa bile birbirine bağlıdır. Bu, "aramızda
    açıklanamayan bir bağ var" denen şeyin ölçülebilir karşılığıdır.
    """
    from .hudud import egiklik
    from .modules_deneme import _ASPECTS

    def boylam_var(l1: float, l2: float) -> bool:
        d = sep(l1, l2)
        return any(abs(d - ang) <= ob for _n, _g, ang, ob, _w, _m in _ASPECTS)

    out: List[dict] = []
    for ka in CORE10:
        for kb in CORE10:
            b1, b2 = a.bodies[ka], b.bodies[kb]
            fp, fk = abs(b1.decl - b2.decl), abs(b1.decl + b2.decl)
            tur, o = (None, None)
            if fp <= orb:
                tur, o = "paralel", fp
            elif fk <= orb:
                tur, o = "karşıt-paralel", fk
            if not tur:
                continue
            gizli = not boylam_var(b1.lon, b2.lon)
            out.append({"a": f"{ad_a} {b1.name_tr}", "b": f"{ad_b} {b2.name_tr}",
                        "tur": tur, "orb": round(o, 2), "gizli": gizli,
                        "dekl_a": round(b1.decl, 2), "dekl_b": round(b2.decl, 2)})
    out.sort(key=lambda x: (-int(x["gizli"]), x["orb"]))
    gizli = [x for x in out if x["gizli"]]
    eps = egiklik(a.jd_ut)
    oob_a = [a.bodies[k].name_tr for k in CORE10
             if k != "Sun" and abs(a.bodies[k].decl) > eps + 0.05]
    oob_b = [b.bodies[k].name_tr for k in CORE10
             if k != "Sun" and abs(b.bodies[k].decl) > eps + 0.05]
    return {
        "temaslar": out[:14], "gizli_baglar": gizli[:8],
        "gizli_sayi": len(gizli),
        "hudud_disi": {ad_a: oob_a, ad_b: oob_b},
        "okuma": ("Deklinasyonda bağ yok — bu ilişkide görünenden fazlası yok."
                  if not gizli else
                  f"{len(gizli)} GİZLİ bağ: bu çiftler boylamda hiç açı yapmıyor, "
                  "yani klasik sinastride görünmezler; ama aynı deklinasyon "
                  "kuşağında oldukları için birlikte hareket ederler. "
                  "'Açıklayamadığımız bir bağ var' denen şey çoğu kez budur."),
        "yontem": f"Orb {orb}°. Paralel: aynı işaretli eşit deklinasyon. "
                  "Karşıt-paralel: eşit büyüklükte zıt işaret.",
    }
