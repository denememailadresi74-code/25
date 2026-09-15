#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YAŞ KATMANI — kişi şu anda hangi eşiklerin ortasında

GÖRÜLMEYEN ŞEY
    Astroloji yaşı bir SAYI olarak görür: "34 yaşındasınız". Oysa yaş bir
    sayı değil, aynı anda dönen birkaç çarkın o andaki bileşimidir.

    Herkes aynı yaşta aynı eşikten geçer — Satürn dönüşü 29'da, Jüpiter
    dönüşü 12'de, Uranüs karşıtı 42'de. Bu, astrolojinin bildiği bir
    şeydir. Ama kimse şunu sormaz:

        BU kişi ŞU ANDA kaç eşiğin ortasında?

    Bir insan 29'da yalnız Satürn dönüşünde olabilir. Bir başkası aynı
    anda Satürn dönüşü, Jüpiter dönüşü ve ay düğümü dönüşünün üstünde
    olabilir. İkisi de "29 yaşında" ama biri tek bir kapıdan, öteki üç
    kapıdan aynı anda geçiyor.

    Fark ölçülebilir ve kimse ölçmüyor.

NE HESAPLANIR
    Sekiz gelişim çevrimi, kişinin TAM YAŞINDA nerede olduğu:

      Satürn dönüşü      29.46 yıl   yapı kurma / hesap verme
      Jüpiter dönüşü     11.86 yıl   genişleme / yeniden yönelme
      Ay düğümü dönüşü   18.61 yıl   yön değiştirme
      Uranüs çeyreği     21.01 yıl   kopuş / özgürleşme
      Güneş yarım-döngü   ...        (progres Ay dönüşü 27.3 yıl)
      Neptün beşte biri  32.9 yıl    çözülme / sınır kaybı
      Plüton karesi      ~ değişken  dönüşüm baskısı
      Şi'râ çevrimi      1.46 yıl    sistemin kendi ritmi

    Her çevrim için: kaçıncı turda, tur içinde nerede (0–1), ve
    EŞİĞE YAKINLIK.

    Sonra asıl soru: kaç tanesi AYNI ANDA eşikte? Bu bir yığılma
    ölçüsüdür ve yaşın gerçek yükünü verir.

SINIR
    Yığılma "zor yıl" demek DEĞİLDİR. Aynı anda birkaç eşikte olmak,
    aynı anda birkaç kapının açık olması demektir — kimi için bu baskı,
    kimi için fırsattır. Modül yükü ölçer, işareti değil.
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Optional, Tuple

import swisseph as swe

from .astro import NatalChart, EPHFLAG, ensure_ephe
from .circular import sep

# (ad, periyot yılı, eşik anlamı, eşik payı)
# Eşik payı: turun kaçta kaçı "eşik bölgesi" sayılır.
CEVRIMLER: List[Tuple[str, float, str, float]] = [
    ("Satürn dönüşü", 29.457, "yapı kurma ve hesap verme", 0.06),
    ("Jüpiter dönüşü", 11.862, "genişleme ve yeniden yönelme", 0.08),
    ("Ay düğümü dönüşü", 18.613, "yön değiştirme", 0.07),
    ("Uranüs çeyreği", 21.008, "kopuş ve özgürleşme", 0.07),
    ("Progres Ay dönüşü", 27.321, "duygusal olgunlaşma", 0.06),
    ("Neptün beşte biri", 32.900, "çözülme ve sınır kaybı", 0.06),
    ("Şi'râ çevrimi", 1.461, "sistemin kendi ritmi", 0.10),
]


def _yas(chart: NatalChart, jd: Optional[float] = None) -> float:
    ensure_ephe()
    if jd is None:
        u = dt.datetime.utcnow()
        jd = swe.julday(u.year, u.month, u.day, u.hour + u.minute / 60.0)
    return (jd - chart.jd_ut) / 365.2422


def yas_katmani(chart: NatalChart, jd: Optional[float] = None,
                ileri_yil: float = 2.0) -> dict:
    """
    Kişinin tam yaşında hangi gelişim çevrimlerinin eşikte olduğunu ve
    kaç tanesinin çakıştığını hesaplar.
    """
    yas = _yas(chart, jd)
    kayitlar: List[dict] = []

    for ad, periyot, anlam, pay in CEVRIMLER:
        tur = yas / periyot
        tam = int(tur)
        faz = tur - tam                       # 0–1, tur içindeki yer
        # Eşiğe uzaklık: tur başı (0) ve tur ortası (0.5) eşiktir.
        # Tur başı = dönüş, tur ortası = karşıtlık — ikisi de kapı.
        d_baslangic = min(faz, 1.0 - faz)     # dönüşe uzaklık
        d_orta = abs(faz - 0.5)               # karşıtlığa uzaklık
        yakin, tip = ((d_baslangic, "dönüş") if d_baslangic <= d_orta
                      else (d_orta, "karşıtlık"))
        esikte = yakin <= pay
        # Eşiğe kaç yıl kaldı / kaç yıl geçti
        yil_fark = round((yakin if not esikte else -yakin) * periyot, 2)
        kayitlar.append({
            "cevrim": ad, "periyot": periyot, "anlam": anlam,
            "tur": tam + 1, "faz": round(faz, 3),
            "esikte": esikte, "esik_tipi": tip,
            "yakinlik": round(yakin, 4),
            "yogunluk": round(max(0.0, 1.0 - yakin / pay), 2) if esikte else 0.0,
            "yil": yil_fark,
        })

    esikte = [k for k in kayitlar if k["esikte"]]
    esikte.sort(key=lambda x: -x["yogunluk"])

    # YIĞILMA: kaç çevrim aynı anda eşikte, ne kadar yoğun
    yigilma = round(sum(k["yogunluk"] for k in esikte), 2)

    # Yaklaşanlar
    yaklasan = sorted(
        [k for k in kayitlar if not k["esikte"] and 0 < k["yil"] <= ileri_yil],
        key=lambda x: x["yil"])

    return {
        "modul": "YAŞ KATMANI — kaç eşiğin ortasında",
        "yas": round(yas, 2),
        "esikte": esikte,
        "esik_sayisi": len(esikte),
        "yigilma": yigilma,
        "seviye": _seviye(len(esikte), yigilma),
        "yaklasan": yaklasan[:3],
        "tumu": kayitlar,
        "okuma": _okuma(round(yas, 2), esikte, yigilma, yaklasan),
        "yontem": ("Yedi gelişim çevrimi kişinin TAM yaşına oranlanır. Her "
                   "çevrimde tur başı (dönüş) ve tur ortası (karşıtlık) "
                   "eşik sayılır; eşiğe yakınlık turun payına göre "
                   "ölçülür. Yığılma, aynı anda eşikte olan çevrimlerin "
                   "yoğunluk toplamıdır."),
        "sinir": ("Yığılma 'zor yıl' DEMEK DEĞİLDİR. Aynı anda birkaç "
                  "eşikte olmak, aynı anda birkaç kapının açık olması "
                  "demektir — kimi için baskı, kimi için fırsat. Modül "
                  "yükü ölçer, işareti değil."),
    }


def _seviye(n: int, yigilma: float) -> str:
    if n >= 3 or yigilma >= 2.0:
        return "yığılma"
    if n == 2 or yigilma >= 1.0:
        return "çifte eşik"
    if n == 1:
        return "tek eşik"
    return "eşik arası"


def _okuma(yas: float, esikte: List[dict], yigilma: float,
           yaklasan: List[dict]) -> str:
    if not esikte:
        p = [f"{yas} yaşında ve şu an belirgin bir gelişim eşiğinde değil. "
             "Çevrimler tur ortasında; bu, hareketsizlik değil YERLEŞME "
             "dönemidir — kurulan şey oturuyor."]
    else:
        adlar = ", ".join(f"{k['cevrim']} ({k['esik_tipi']})" for k in esikte)
        p = [f"{yas} yaşında ve {len(esikte)} eşiğin ortasında: {adlar}."]
        en = esikte[0]
        p.append(f"En yoğunu {en['cevrim']} — {en['anlam']}.")
        if len(esikte) >= 3:
            p.append("Üç ya da daha fazla çevrim aynı anda eşikte. Bu, "
                     "yaşanan yoğunluğun kişisel zayıflık değil YAPISAL "
                     "bir çakışma olduğunu gösterir; danışan 'neden her "
                     "şey aynı anda' diyorsa cevabı budur.")
    if yaklasan:
        y = yaklasan[0]
        p.append(f"Yaklaşan: {y['cevrim']} {y['esik_tipi']}ı "
                 f"{y['yil']} yıl sonra.")
    return " ".join(p)
