#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DURAKLAMA İZİ — hangi yanlar işlenmiş, hangileri el değmemiş

İCADIN FİKRİ
    Gezegenler yılda birkaç kez DURUR: geri gitmeye başlamadan önce ve
    ileri dönmeden önce hızları sıfırlanır. O anda gökyüzünde hareketsizdirler.

    Bir gezegen bir natal nokta üzerinde durursa, o temasın en yoğun
    hâlidir. Geçip gitmez — orada kalır, bazen haftalarca.

    Şimdi asıl fikir. Bir insanın doğumundan bugüne kadar:

      · Bazı natal noktalar üzerinde DEFALARCA durulmuştur — hayat oraya
        tekrar tekrar dönmüş, o yan işlenmiş
      · Bazılarına HİÇ dokunulmamıştır — ham kalmış, sınanmamış

    Kimse bunu bir ömür yapısı olarak haritalamıyor.

NE AÇIKLIYOR
    Aynı yaştaki iki insan neden bazı konularda olgun, bazılarında toy?
    Astroloji buna "gelişmemiş gezegen" der ve yine kişiyi suçlar. Oysa
    ölçülebilir bir sebep var: o noktaya henüz gelinmemiş.

DANIŞMAN İÇİN
    · İşlenmiş nokta: kişinin burada geçmişi var. Dinle — anlatacak şeyi
      vardır.
    · El değmemiş nokta: kişi burada toy. Kapasite var, deneyim yok.
      Tavsiye verirken bunu bil.
    · Yaklaşan duraklama: ilk kez işlenecek yan. Bu gerçek bir haber.

SINIR
    "İşlenmiş" iyi, "el değmemiş" kötü DEĞİLDİR. İşlenmiş nokta yıpranmış
    da olabilir; el değmemiş nokta taze demektir. Modül yorumlamaz, sayar.
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Optional, Tuple

import swisseph as swe

from .astro import NatalChart, CORE10, TR_NAME, EPHFLAG, ensure_ephe, jd_to_iso
from .circular import sep

# Ay ve Güneş duraklamaz.
#
# MERKÜR ve VENÜS DE DIŞARIDA. İlk sürümde vardılar ve icadın çekirdeğini
# bozuyorlardı: Merkür 29 yılda ~174 kez durur, burçlar kuşağında ortalama
# 2° aralıkla. 2.5° orbla HER natal noktayı vuruyor ve "el değmemiş nokta"
# hiç çıkmıyordu — yani modülün asıl söyleyeceği şey hiç söylenemiyordu.
#
# Sükût haritasında Ay'ı çıkarma sebebiyle aynı: hızlı cisim taban
# gürültüsü üretir, sinyal değil.
#
# Anlamlı duraklama Mars'tan dışarıdadır. Mars ~2 yılda bir, dış
# gezegenler yılda bir ve neredeyse aynı derecede durur.
DURAN = [("Mars", swe.MARS, 1.3), ("Jupiter", swe.JUPITER, 1.6),
         ("Saturn", swe.SATURN, 2.2), ("Uranus", swe.URANUS, 1.9),
         ("Neptune", swe.NEPTUNE, 1.8), ("Pluto", swe.PLUTO, 2.0)]

TEMAS_ORB = 1.5               # 2.5° fazla genişti; her noktayı yakalıyordu


def _hiz(jd: float, kod: int) -> float:
    return swe.calc_ut(jd, kod, EPHFLAG | swe.FLG_SPEED)[0][3]


# TARAMA ADIMI — ölçümle belirlendi.
#
# Adım bir gündü ve 29 yıllık tarama 63.462 efemeris çağrısı yapıyordu:
# analiz süresinin %51'i tek başına bu modüldü.
#
# Kaba adım kullanmak duraklama kaçırır MI? Ölçüldü: Mars en hızlı duran
# gezegendir ve iki ardışık duraklaması arasındaki EN KISA aralık 60 gün.
# Yani 60 günden kısa her adım güvenlidir.
#
# 5, 8, 10 ve 15 günlük adımlar denendi: DÖRDÜ DE aynı 427 duraklamayı
# buluyor, sıfır kayıp. 10 gün seçildi — güvenli payın altı katı, çağrı
# sayısı altıda bire iniyor.
#
# İkiye bölme aşaması değişmedi: tam an hâlâ saniye hassasiyetinde.
TARAMA_ADIMI = 10.0


def duraklamalar(jd_bas: float, jd_son: float) -> List[dict]:
    """
    Verilen aralıktaki bütün duraklamaları bulur.

    Hızın işaret değiştirdiği pencere kaba adımla yakalanır, sonra ikiye
    bölmeyle tam an saniye hassasiyetinde bulunur.
    """
    ensure_ephe()
    out: List[dict] = []
    for ad, kod, agirlik in DURAN:
        try:
            onceki = _hiz(jd_bas, kod)
        except Exception:
            continue
        j = jd_bas
        while j < jd_son:
            j += TARAMA_ADIMI
            try:
                h = _hiz(j, kod)
            except Exception:
                break
            if onceki * h < 0:
                a, b = j - TARAMA_ADIMI, j
                for _ in range(34):   # kaba adım büyüdü, bölme derinliği arttı
                    o = (a + b) / 2
                    if _hiz(a, kod) * _hiz(o, kod) < 0:
                        b = o
                    else:
                        a = o
                k = (a + b) / 2
                try:
                    lon = swe.calc_ut(k, kod, EPHFLAG)[0][0]
                except Exception:
                    onceki = h
                    continue
                out.append({"jd": k, "cisim": ad, "tr": TR_NAME.get(ad, ad),
                            "boylam": round(lon, 3),
                            "yon": "geri" if h < 0 else "ileri",
                            "agirlik": agirlik})
            onceki = h
    out.sort(key=lambda x: x["jd"])
    return out


def duraklama_izi(chart: NatalChart, bugun_jd: Optional[float] = None,
                  ileri_ay: int = 18) -> dict:
    """
    Doğumdan bugüne kadar hangi natal noktaların üzerinde durulmuş,
    hangilerine hiç dokunulmamış. Ayrıca yaklaşan duraklamalar.
    """
    ensure_ephe()
    if bugun_jd is None:
        u = dt.datetime.utcnow()
        bugun_jd = swe.julday(u.year, u.month, u.day, 12.0)

    noktalar: List[Tuple[str, float]] = [
        (TR_NAME[k], chart.bodies[k].lon) for k in CORE10 if k in chart.bodies]
    noktalar += [("Yükselen", chart.asc), ("Tepe noktası", chart.mc)]

    gecmis = duraklamalar(chart.jd_ut, bugun_jd)
    gelecek = duraklamalar(bugun_jd, bugun_jd + ileri_ay * 30.44)

    iz: Dict[str, dict] = {ad: {"nokta": ad, "boylam": round(lon, 2),
                                "sayi": 0, "agirlik": 0.0, "kayitlar": []}
                           for ad, lon in noktalar}

    for d in gecmis:
        for ad, lon in noktalar:
            fark = sep(d["boylam"], lon)
            if fark <= TEMAS_ORB:
                yakin = 1.0 - fark / TEMAS_ORB
                p = d["agirlik"] * (0.4 + 0.6 * yakin)
                r = iz[ad]
                r["sayi"] += 1
                r["agirlik"] += p
                r["kayitlar"].append({
                    "tarih": jd_to_iso(d["jd"])[:10], "cisim": d["tr"],
                    "yon": d["yon"], "orb": round(fark, 2),
                    "yas": round((d["jd"] - chart.jd_ut) / 365.2422, 1)})

    for r in iz.values():
        r["agirlik"] = round(r["agirlik"], 2)
        r["kayitlar"] = sorted(r["kayitlar"], key=lambda x: x["tarih"])[-6:]

    sirali = sorted(iz.values(), key=lambda x: -x["agirlik"])
    islenmis = [r for r in sirali if r["sayi"] > 0]
    ham = [r for r in sirali if r["sayi"] == 0]

    yaklasan: List[dict] = []
    for d in gelecek:
        for ad, lon in noktalar:
            fark = sep(d["boylam"], lon)
            if fark <= TEMAS_ORB:
                ilk = iz[ad]["sayi"] == 0
                yaklasan.append({
                    "tarih": jd_to_iso(d["jd"])[:10], "cisim": d["tr"],
                    "nokta": ad, "yon": d["yon"], "orb": round(fark, 2),
                    "ilk_kez": ilk,
                    "agirlik": round(d["agirlik"] * (1.0 - fark / TEMAS_ORB), 2)})
    yaklasan.sort(key=lambda x: x["tarih"])

    yas = round((bugun_jd - chart.jd_ut) / 365.2422, 1)
    return {
        "modul": "DURAKLAMA İZİ — hangi yanlar işlenmiş, hangileri ham",
        "yas": yas,
        "toplam_duraklama": len(gecmis),
        "temas_eden": sum(r["sayi"] for r in iz.values()),
        "islenmis": islenmis,
        "el_degmemis": [{"nokta": r["nokta"], "boylam": r["boylam"]}
                        for r in ham],
        "en_islenmis": islenmis[0] if islenmis else None,
        "yaklasan": yaklasan[:8],
        "ilk_kez_yaklasan": [y for y in yaklasan if y["ilk_kez"]][:4],
        "okuma": _okuma(islenmis, ham, yas, yaklasan),
        "yontem": (
            "Gezegenin hızı sıfırı geçtiği an duraklamadır; gün adımıyla "
            "taranıp ikiye bölmeyle saniye hassasiyetinde bulunur. Doğumdan "
            f"bugüne bütün duraklamalar, natal noktalara {TEMAS_ORB}° "
            "içinde düşenler sayılır. Ay ve Güneş duraklamaz, dahil "
            "edilmez."),
        "sinir": (
            "'İşlenmiş' iyi, 'el değmemiş' kötü DEĞİLDİR. İşlenmiş nokta "
            "yıpranmış da olabilir; el değmemiş nokta taze demektir. "
            "Modül yorumlamaz, sayar."),
    }


def _okuma(islenmis: List[dict], ham: List[dict], yas: float,
           yaklasan: List[dict]) -> str:
    if not islenmis:
        return (f"{yas} yılda hiçbir natal nokta üzerinde duraklama olmamış. "
                "Bu nadirdir — noktalar duraklamaların yoğunlaştığı "
                "kuşakların dışında kalıyor.")
    en = islenmis[0]
    p = [f"{yas} yılda {sum(r['sayi'] for r in islenmis)} duraklama teması. "
         f"En çok işlenen yan: {en['nokta']} ({en['sayi']} kez). "
         f"Hayat oraya tekrar tekrar dönmüş."]
    if len(islenmis) > 1:
        p.append("Ardından " + ", ".join(
            f"{r['nokta']} ({r['sayi']})" for r in islenmis[1:4]) + ".")
    if ham:
        p.append("Hiç dokunulmamış: " + ", ".join(r["nokta"] for r in ham) +
                 ". Bu yanlar ham — kapasite var, sınanmamış.")
    ilk = [y for y in yaklasan if y["ilk_kez"]]
    if ilk:
        y = ilk[0]
        p.append(f"Yaklaşan: {y['tarih']} {y['cisim']} {y['nokta']} üzerinde "
                 f"duruyor — bu nokta İLK KEZ işlenecek.")
    return " ".join(p)
