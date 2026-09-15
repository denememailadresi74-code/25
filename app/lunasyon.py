#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LUNASYON TAKVİMİ — ay hafta hafta neyi açıyor

NEDEN GEREKLİ
    Bir astrolog lunasyon takvimi olmadan çalışamaz. Sistem şimdiye kadar
    "bugünkü gök" veriyordu — anlık bir kesit. Oysa danışanla konuşulan
    şey zamanın YAPISI:

      · Her YENİ AY bir konu açar (hangi konuyu? düştüğü eve göre)
      · Her DOLUNAY bir konuyu olgunlaştırır ya da patlatır
      · TUTULMALAR altı aylık kapılar açar, sıradan lunasyondan farklıdır
      · Aynı gökyüzü olayı NATAL ve SOLAR haritada FARKLI evlere düşer

    Bu modül bir yıllık lunasyonları hesaplar, her birini hem natal hem
    solar dönüş haritasına oturtur, natal noktalara temaslarını bulur ve
    HAFTA HAFTA gruplar.

HESAPLAMA
    Yeni ay / dolunay: Ay–Güneş açısal farkının 0° ve 180°'yi kestiği anlar,
    ikiye bölme ile 1 saniyeden hassas bulunur.
    Tutulmalar: Swiss Ephemeris'in kendi tutulma arayıcıları (tahmin değil,
    gerçek geometri).

SINIR
    Lunasyon bir OLAY ÜRETMEZ. Zaten var olan bir konunun görünürlük
    kazandığı zaman aralığını gösterir. "O gün şu olacak" denmez.
"""
from __future__ import annotations

import datetime as dt
import math
from typing import Any, Dict, List, Optional, Tuple

import swisseph as swe

from .astro import NatalChart, CORE10, TR_NAME, EPHFLAG, ensure_ephe, jd_to_iso
from .circular import norm360, sep

AY_SIN = 29.530588853          # sinodik ay


# ============================================================================
# LUNASYON BULMA
# ============================================================================
def _fark(jd: float) -> float:
    """Ay − Güneş açısal farkı (0–360)."""
    ay = swe.calc_ut(jd, swe.MOON, EPHFLAG)[0][0]
    gun = swe.calc_ut(jd, swe.SUN, EPHFLAG)[0][0]
    return norm360(ay - gun)


def _kesisim(jd_bas: float, hedef: float, pencere: float = 2.0) -> Optional[float]:
    """
    Ay–Güneş farkının `hedef` dereceyi kestiği anı ikiye bölerek bulur.

    SARMAL TUZAĞI: sapma işlevi farkı [-180,180) aralığına indirger ve bu
    aralık 180°'de +180'den -180'e ATLAR. İşaret değişimine bakan ikiye
    bölme, bu atlamayı da "sıfır geçişi" sanıyordu. Sonuç: 0° arayan çağrı
    DOLUNAYLARI da buluyor ve onları "yeni ay" diye etiketliyordu — hesap
    doğru, etiket yanlıştı.

    Çözüm: bulunan anın gerçekten hedefe yakın olduğu SINANIR. Atlama
    noktasında sapma büyük kalır ve aday reddedilir.
    """
    def sapma(j):
        return ((_fark(j) - hedef + 180) % 360) - 180

    a, b = jd_bas, jd_bas + pencere
    fa, fb = sapma(a), sapma(b)
    if fa * fb > 0:
        return None
    for _ in range(48):
        o = (a + b) / 2
        fo = sapma(o)
        if fa * fo <= 0:
            b, fb = o, fo
        else:
            a, fa = o, fo
        if abs(b - a) < 1e-6:          # ≈ 0.1 saniye
            break
    k = (a + b) / 2
    # Gerçekten hedefte miyiz, yoksa sarmal atlaması mı?
    if sep(_fark(k), hedef) > 1.0:
        return None
    return k


def lunasyonlar(jd_bas: float, ay_sayisi: int = 13) -> List[dict]:
    """Verilen andan itibaren yeni ay ve dolunayları sırayla bulur."""
    ensure_ephe()
    sonuc: List[dict] = []
    j = jd_bas
    son = jd_bas + ay_sayisi * AY_SIN + 2
    while j < son:
        for hedef, tur in ((0.0, "yeni ay"), (180.0, "dolunay")):
            k = _kesisim(j, hedef, 1.2)
            if k and k > jd_bas and all(abs(k - x["jd"]) > 0.5 for x in sonuc):
                lon = swe.calc_ut(k, swe.MOON, EPHFLAG)[0][0]
                sonuc.append({"jd": k, "tur": tur, "boylam": lon})
        j += 1.0
    sonuc.sort(key=lambda x: x["jd"])
    return [x for x in sonuc if x["jd"] <= son]


def tutulmalar(jd_bas: float, ay_sayisi: int = 13) -> List[dict]:
    """
    Güneş ve ay tutulmaları. Swiss Ephemeris'in kendi arayıcıları kullanılır;
    yaklaşık hesap değil gerçek geometridir.
    """
    ensure_ephe()
    son = jd_bas + ay_sayisi * AY_SIN
    cikti: List[dict] = []

    j = jd_bas
    for _ in range(20):
        try:
            bayrak, veri = swe.sol_eclipse_when_glob(j, EPHFLAG, 0)
        except Exception:
            break
        k = veri[0]
        if k > son:
            break
        tam = "tam" if bayrak & swe.ECL_TOTAL else (
            "halkalı" if bayrak & swe.ECL_ANNULAR else "parçalı")
        cikti.append({"jd": k, "tur": "güneş tutulması", "cesit": tam,
                      "boylam": swe.calc_ut(k, swe.SUN, EPHFLAG)[0][0]})
        j = k + 10

    j = jd_bas
    for _ in range(20):
        try:
            bayrak, veri = swe.lun_eclipse_when(j, EPHFLAG, 0)
        except Exception:
            break
        k = veri[0]
        if k > son:
            break
        tam = "tam" if bayrak & swe.ECL_TOTAL else (
            "yarıgölge" if bayrak & swe.ECL_PENUMBRAL else "parçalı")
        cikti.append({"jd": k, "tur": "ay tutulması", "cesit": tam,
                      "boylam": swe.calc_ut(k, swe.MOON, EPHFLAG)[0][0]})
        j = k + 10

    cikti.sort(key=lambda x: x["jd"])
    return cikti


# ============================================================================
# HARİTAYA OTURTMA
# ============================================================================
def _ev_no(cusps: List[float], boylam: float) -> Optional[int]:
    """Boylamın hangi eve düştüğü."""
    if not cusps or len(cusps) < 12:
        return None
    for i in range(12):
        a = cusps[i] % 360
        b = cusps[(i + 1) % 12] % 360
        if a <= b:
            if a <= boylam < b:
                return i + 1
        else:                          # 0° sarmalı
            if boylam >= a or boylam < b:
                return i + 1
    return None


def _temaslar(chart: NatalChart, boylam: float, orb: float = 3.0) -> List[dict]:
    """Lunasyonun natal noktalara temasları (kavuşum, karşıt, kare, üçgen)."""
    acilar = ((0, "kavuşum"), (180, "karşıt"), (90, "kare"), (120, "üçgen"))
    out: List[dict] = []
    hedefler = [(TR_NAME[k], chart.bodies[k].lon) for k in CORE10
                if k in chart.bodies]
    hedefler += [("Yükselen", chart.asc), ("Tepe noktası", chart.mc)]
    for ad, lon in hedefler:
        d = sep(boylam, lon)
        for a, tur in acilar:
            fark = abs(d - a)
            if fark <= orb:
                out.append({"nokta": ad, "aci": tur, "orb": round(fark, 2)})
                break
    out.sort(key=lambda x: x["orb"])
    return out


def _hafta_no(jd: float, jd_bas: float) -> int:
    return int((jd - jd_bas) // 7) + 1


def solar_donus(natal: NatalChart, yil: Optional[int] = None,
                lat: Optional[float] = None,
                lng: Optional[float] = None) -> Optional[NatalChart]:
    """
    Solar dönüş haritası.

    `kabzbast_v1.solar_return` Türkçe cisim anahtarı bekliyor
    (`bodies['Güneş']`), `build_chart` ise İngilizce veriyor (`bodies['Sun']`)
    — doğrudan çağrı KeyError atıyordu. Burada astro'nun kendi
    `solar_return_jd` yardımcısı kullanılır ve harita yeniden kurulur.
    """
    from .astro import solar_return_jd, build_chart
    import datetime as _dt
    import swisseph as _swe
    try:
        y = yil or _dt.datetime.utcnow().year
        jd = solar_return_jd(natal, y)
        if not jd:
            return None
        la = natal.lat if lat is None else lat
        lo = natal.lng if lng is None else lng
        yy, mm, dd, saat = _swe.revjul(jd)
        return build_chart(int(yy), int(mm), int(dd), int(saat),
                           int((saat % 1) * 60), la, lo, tz_offset=0.0,
                           label="Solar dönüş",
                           house_system=getattr(natal, "house_system", "P"),
                           jd_ut_override=jd)
    except Exception:
        return None


def lunasyon_takvimi(natal: NatalChart, solar: Optional[NatalChart] = None,
                     jd_bas: Optional[float] = None,
                     ay_sayisi: int = 12) -> dict:
    """
    Bir yıllık lunasyon takvimi: her olay natal ve solar haritaya oturtulur,
    natal temasları bulunur, haftalara bölünür.
    """
    ensure_ephe()
    if jd_bas is None:
        u = dt.datetime.utcnow()
        jd_bas = swe.julday(u.year, u.month, u.day, u.hour + u.minute / 60.0)

    olaylar = lunasyonlar(jd_bas, ay_sayisi) + tutulmalar(jd_bas, ay_sayisi)
    olaylar.sort(key=lambda x: x["jd"])

    # Tutulma ile aynı güne düşen sıradan lunasyon elenir — aynı olaydır
    temiz: List[dict] = []
    for o in olaylar:
        tut = "tutulma" in o["tur"]
        if not tut and any("tutulma" in x["tur"] and abs(x["jd"] - o["jd"]) < 0.6
                           for x in olaylar):
            continue
        temiz.append(o)

    n_cusps = list(getattr(natal, "cusps", []) or [])
    s_cusps = list(getattr(solar, "cusps", []) or []) if solar else []

    kayitlar: List[dict] = []
    for o in temiz:
        lon = o["boylam"]
        k = {
            "an": jd_to_iso(o["jd"]),
            "tarih": jd_to_iso(o["jd"])[:10],
            "tur": o["tur"],
            "cesit": o.get("cesit"),
            "boylam": round(lon, 3),
            "natal_ev": _ev_no(n_cusps, lon),
            "solar_ev": _ev_no(s_cusps, lon) if s_cusps else None,
            "temaslar": _temaslar(natal, lon),
            "hafta": _hafta_no(o["jd"], jd_bas),
        }
        k["agirlik"] = _agirlik(k)
        k["bag"] = kategori_bagi(k)
        k["oneriler"] = oneri_uret(k, k["bag"])
        kayitlar.append(k)

    # Haftalara böl
    haftalar: Dict[int, List[dict]] = {}
    for k in kayitlar:
        haftalar.setdefault(k["hafta"], []).append(k)

    return {
        "modul": "LUNASYON TAKVİMİ — ay hafta hafta neyi açıyor",
        "baslangic": jd_to_iso(jd_bas),
        "ay_sayisi": ay_sayisi,
        "olay_sayisi": len(kayitlar),
        "olaylar": kayitlar,
        "haftalar": [{"hafta": h, "olaylar": v} for h, v in
                     sorted(haftalar.items())],
        "tutulma_sayisi": len([k for k in kayitlar if "tutulma" in k["tur"]]),
        "en_agir": sorted(kayitlar, key=lambda x: -x["agirlik"])[:5],
        "yontem": ("Yeni ay ve dolunay: Ay–Güneş farkının 0° ve 180°'yi "
                   "kestiği an, ikiye bölmeyle saniye hassasiyetinde. "
                   "Tutulmalar Swiss Ephemeris'in tutulma arayıcılarından — "
                   "yaklaşık hesap değil gerçek geometri."),
        "uyari": ("Lunasyon bir OLAY ÜRETMEZ. Zaten var olan bir konunun "
                  "görünürlük kazandığı aralığı gösterir. 'O gün şu olacak' "
                  "denmez."),
    }


def _agirlik(k: dict) -> float:
    """Bir lunasyonun bu kişi için ne kadar önemli olduğu (0–10)."""
    p = 2.0 if "tutulma" in k["tur"] else 1.0
    if k.get("cesit") == "tam":
        p += 1.5
    for t in k["temaslar"][:3]:
        pay = {"kavuşum": 3.0, "karşıt": 2.4, "kare": 2.0, "üçgen": 1.2}
        agir = 1.4 if t["nokta"] in ("Yükselen", "Tepe noktası",
                                     "Güneş", "Ay") else 1.0
        p += pay.get(t["aci"], 1.0) * agir * max(0.3, 1 - t["orb"] / 3.0)
    return round(min(10.0, p), 2)


def bu_hafta(takvim: dict, jd: Optional[float] = None) -> dict:
    """İçinde bulunulan haftanın olayları ve sonraki iki hafta."""
    if jd is None:
        u = dt.datetime.utcnow()
        jd = swe.julday(u.year, u.month, u.day, u.hour + u.minute / 60.0)
    hepsi = takvim.get("olaylar") or []
    yakin = [o for o in hepsi
             if 0 <= (swe.julday(*[int(x) for x in o["tarih"].split("-")], 12.0)
                      - jd) <= 21]
    return {"bugun": jd_to_iso(jd)[:10],
            "yaklasan": yakin[:4],
            "okuma": ("Önümüzdeki üç haftada belirgin bir gök olayı yok."
                      if not yakin else
                      f"{len(yakin)} olay yaklaşıyor; en yakını "
                      f"{yakin[0]['tarih']} {yakin[0]['tur']}.")}


# ============================================================================
# KATEGORİ BAĞI — lunasyon hangi analiz katmanını uyandırıyor
# ============================================================================
# Takvim tek başına "10 Ekim'de yeni ay var" der ve bu bir bilgi parçasıdır,
# tavsiye değil. Danışmanın ihtiyacı şu: BU olay, sistemdeki HANGİ analizi
# canlandırıyor?
#
# Bağ iki yoldan kurulur ve ikisi de hesaplanabilir:
#   1. Düştüğü EV → hangi hayat alanı → hangi kategoriler
#   2. Değdiği NOKTA → o noktanın baskın olduğu katman
#
# Böylece takvim, 22 kategorinin hangisinin o hafta öne çıktığını söyler.

# Kod adları ARAYÜZLE birebir aynı olmalı: 'gravitron' ve 'yer' yazılmıştı
# ama arayüzde bunlar 'chrono' ve 'kartografi'. Yanlış kod, o bölümü hiç
# uyandırmıyordu — sessiz bir kopukluk.
EV_KATEGORI: Dict[int, List[str]] = {
    1:  ["hukum", "kutleler", "hd", "halka"],
    2:  ["kabzbast", "kutleler", "kenarlar"],
    3:  ["deneme", "kadim", "dinamik"],
    4:  ["kadim", "alanbukmesi", "hamveri"],
    5:  ["kutleler", "deneme", "halka"],
    6:  ["kabzbast", "hd", "dinamik"],
    7:  ["hukum", "catal", "sinastri", "kompozit", "topoloji"],
    8:  ["hudud", "chrono", "kadim", "alanbukmesi"],
    9:  ["kartografi", "sira", "manevi"],
    10: ["hukum", "alanbukmesi", "kartografi", "topoloji"],
    11: ["deneme", "sira", "kenarlar"],
    12: ["hudud", "manevi", "kadim", "direnc"],
}

EV_ALAN: Dict[int, str] = {
    1: "kendini ortaya koyma", 2: "kaynak ve değer", 3: "yakın çevre ve dil",
    4: "kök ve ev", 5: "kendini gösterme ve yaratım", 6: "gündelik düzen ve iş",
    7: "birebir ilişki", 8: "ortak kaynak ve dönüşüm", 9: "uzak ve anlam",
    10: "görünürlük ve konum", 11: "çevre ve gelecek",
    12: "geri çekilme ve görünmeyen",
}

NOKTA_KATMAN: Dict[str, List[str]] = {
    "Güneş": ["hukum", "kutleler", "halka"],
    "Ay": ["kadim", "hd", "dinamik"],
    "Merkür": ["deneme", "sira", "dinamik"],
    "Venüs": ["kutleler", "catal", "sinastri"],
    "Mars": ["alanbukmesi", "kabzbast", "kenarlar", "topoloji"],
    "Jüpiter": ["kartografi", "sira", "halka"],
    "Satürn": ["alanbukmesi", "hudud", "direnc"],
    "Uranüs": ["hudud", "celiski", "kenarlar"],
    "Neptün": ["manevi", "hudud", "kadim"],
    "Plüton": ["chrono", "kadim", "alanbukmesi"],
    "Yükselen": ["hukum", "hd", "halka"],
    "Tepe noktası": ["kartografi", "alanbukmesi", "hukum"],
}

KATEGORI_AD: Dict[str, str] = {
    "hukum": "Hüküm", "halka": "Alan halkası", "catal": "Çatal",
    "kutleler": "Kütleler", "kenarlar": "Alanın kenarları",
    "alanbukmesi": "Alan bükmesi", "topoloji": "Alan topolojisi", "chrono": "Chrono-Gravitron",
    "hudud": "Hudûd-ı Felek", "sira": "Şi'râ çevrimi",
    "dinamik": "Yürüyen Berzah", "kabzbast": "Kabz/Bast",
    "deneme": "Deneme modülleri", "kadim": "Kadim katman",
    "hd": "Human Design", "hamveri": "Ham veri",
    "celiski": "Çelişkiler", "direnc": "Direnç",
    "kartografi": "Yer · astrokartografi", "manevi": "Spiritüel çalışma",
    "sinastri": "Sinastri", "kompozit": "Kompozit",
}


def kategori_bagi(olay: dict) -> dict:
    """
    Bu lunasyonun hangi analiz kategorilerini uyandırdığını hesaplar.

    Ev ve temas edilen noktalar üzerinden puanlanır; en yüksek üç kategori
    döner. Puan, temas orb'una ve olay ağırlığına göre ağırlıklandırılır.
    """
    puan: Dict[str, float] = {}

    def art(k: str, n: float):
        puan[k] = puan.get(k, 0.0) + n

    ev = olay.get("natal_ev")
    if ev:
        for k in EV_KATEGORI.get(int(ev), []):
            art(k, 2.0)
    sev = olay.get("solar_ev")
    if sev:
        for k in EV_KATEGORI.get(int(sev), []):
            art(k, 1.2)          # solar ev natalden hafif
    for t in (olay.get("temaslar") or [])[:4]:
        yakin = max(0.3, 1.0 - t.get("orb", 3) / 3.0)
        agir = {"kavuşum": 2.2, "karşıt": 1.8, "kare": 1.6, "üçgen": 1.0}
        pay = agir.get(t.get("aci"), 1.0) * yakin
        for k in NOKTA_KATMAN.get(t.get("nokta", ""), []):
            art(k, pay)
    if "tutulma" in str(olay.get("tur", "")):
        for k in list(puan):
            puan[k] *= 1.4

    sirali = sorted(puan.items(), key=lambda x: -x[1])[:3]
    return {
        "kategoriler": [{"kod": k, "ad": KATEGORI_AD.get(k, k),
                         "puan": round(v, 2)} for k, v in sirali],
        "alan_natal": EV_ALAN.get(int(ev), "") if ev else "",
        "alan_solar": EV_ALAN.get(int(sev), "") if sev else "",
    }


def oneri_uret(olay: dict, bag: dict) -> List[str]:
    """
    Veriden ÇIKAN somut öneriler. AI yok — hesaplanmış bağdan türer.
    AI okuması bunların üstüne gelir.
    """
    o: List[str] = []
    tur = str(olay.get("tur", ""))
    ev = olay.get("natal_ev")
    sev = olay.get("solar_ev")
    alan = bag.get("alan_natal") or ""
    salan = bag.get("alan_solar") or ""

    if "yeni ay" in tur and alan:
        o.append(f"Bu aralıkta {alan} konusu gündeme geliyor. Yeni bir şey "
                 f"başlatmak zorunda değilsin; bu konuya BAKMAN yeterli.")
    elif "dolunay" in tur and alan:
        o.append(f"{alan.capitalize()} konusunda saklanan şey görünür hâle "
                 f"geliyor. Yeni bilgi çıkarsa şaşırma; zaten oradaydı.")
    elif "güneş tutulması" in tur and alan:
        o.append(f"{alan.capitalize()} alanında aylara yayılan bir kapı "
                 f"aralanıyor. Acele karar verme; bu bir an değil bir dönem.")
    elif "ay tutulması" in tur and alan:
        o.append(f"{alan.capitalize()} konusunda bir şey kapanıyor ya da "
                 f"yerini bırakıyor. Zorlamadan bırakabildiğin varsa bırak.")

    if sev and salan and sev != ev:
        o.append(f"Bu yılın haritasında aynı olay {salan} alanına düşüyor. "
                 f"Yani konu iki yerden birden geliyor — dış görünüşü "
                 f"{alan}, bu yılki karşılığı {salan}.")

    for t in (olay.get("temaslar") or [])[:2]:
        if t.get("orb", 9) <= 1.5:
            o.append(f"{t['nokta']} ile {t['aci']} — orb {t['orb']}°. Bu "
                     f"kadar dar bir temas, o yanın bu aralıkta belirgin "
                     f"biçimde devrede olduğunu gösterir.")

    kats = bag.get("kategoriler") or []
    if kats:
        adlar = ", ".join(k["ad"] for k in kats)
        o.append(f"Bu olayı okurken şu bölümlere bak: {adlar}.")

    if (olay.get("agirlik") or 0) < 2.5:
        o.append("Ağırlık düşük — bu olay bu kişide belirgin bir şey "
                 "açmıyor. Takvimde durur ama seansta öne çıkarmaya gerek yok.")
    return o
