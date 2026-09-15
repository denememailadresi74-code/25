#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KAYIP ZAMAN ve DÖNÜŞ NOKTASI — ömür ölçeğinde iki soru

İKİ İCAT, TEK MODÜL
    İkisi de aynı hesaptan besleniyor (gökteki cisimlerin natal noktalara
    zaman içindeki teması), o yüzden birlikte duruyorlar.


1. KAYIP ZAMAN — hangi yıllar boş geçti
    Sükût haritası BİR YILI ölçüyor. Aynı hesap doğumdan bugüne
    yayıldığında başka bir soru cevaplanır:

        Bu kişinin hayatında hangi yıllar sessizdi?

    Danışan "şu yıllarım kayıp" dediğinde astrolojinin söyleyecek bir
    şeyi yoktur — genelde o dönemin transitlerine bakılır ve bir şey
    bulunur, çünkü herhangi bir döneme bakılırsa hep bir şey bulunur.

    Bu modül tersini yapar: o yıllarda gökyüzünde gerçekten az şey
    olduğunu ÖLÇER. "Kayıp" hissi bir kere ölçülünce kişisel bir kusur
    olmaktan çıkar.

    Not: sessiz yıl "kötü yıl" DEĞİLDİR. Dışarıdan az itilmek kimi için
    huzur, kimi için boşluktur.


2. DÖNÜŞ NOKTASI — bir daha gelmeyecek kapılar
    Yavaş gezegenler bir natal noktaya ömürde bir ya da iki kez gelir.
    Plüton bir turu 248 yılda tamamlar: bir insanın natal Plütonuna
    karşıt gelmesi ömürde BİR kez olur, sonra bir daha olmaz.

    Astroloji "transit geçti" der. "Bu bir daha olmayacak" demez.

    Bu modül her yavaş gezegen–natal nokta çifti için son geçişi ve
    varsa bir sonrakini hesaplar. Bir daha gelmeyecek olanları işaretler.

    Bu, zamanlama bilgisi değil AĞIRLIK bilgisidir: danışman hangi
    aralığın tekrar etmeyeceğini bilir.
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Optional, Tuple

import swisseph as swe

from .astro import NatalChart, CORE10, TR_NAME, EPHFLAG, ensure_ephe, jd_to_iso
from .circular import sep

# Kayıp zaman: hızlı cisimler taban gürültüsü yapar (Ay/Merkür/Venüs hariç)
AGIR = [("Mars", swe.MARS, 1.2), ("Jupiter", swe.JUPITER, 1.6),
        ("Saturn", swe.SATURN, 2.2), ("Uranus", swe.URANUS, 2.0),
        ("Neptune", swe.NEPTUNE, 1.8), ("Pluto", swe.PLUTO, 2.0)]

# Dönüş noktası: yalnız gerçekten yavaş olanlar
COK_YAVAS = [("Saturn", swe.SATURN, 29.46), ("Uranus", swe.URANUS, 84.0),
             ("Neptune", swe.NEPTUNE, 164.8), ("Pluto", swe.PLUTO, 248.0)]

ACILAR = ((0, "kavuşum"), (180, "karşıt"), (90, "kare"), (120, "üçgen"))
ORB = 2.0


def _hedefler(ch: NatalChart) -> List[Tuple[str, float]]:
    h = [(TR_NAME[k], ch.bodies[k].lon) for k in CORE10 if k in ch.bodies]
    h += [("Yükselen", ch.asc), ("Tepe noktası", ch.mc)]
    return h


# ============================================================================
# 1 · KAYIP ZAMAN
# ============================================================================
def kayip_zaman(ch: NatalChart, bugun_jd: Optional[float] = None,
                adim_gun: int = 30) -> dict:
    """
    Doğumdan bugüne basınç eğrisi, yıl yıl. Sessiz yılları bulur.

    Aylık örnekleme yeterli: bu cisimler ayda en fazla birkaç derece
    gider ve aradığımız şey tek bir gün değil, YILLIK doku.
    """
    ensure_ephe()
    if bugun_jd is None:
        u = dt.datetime.utcnow()
        bugun_jd = swe.julday(u.year, u.month, u.day, 12.0)

    hedefler = _hedefler(ch)
    yillik: Dict[int, List[float]] = {}

    j = ch.jd_ut
    while j < bugun_jd:
        toplam = 0.0
        for _ad, kod, ag in AGIR:
            try:
                lon = swe.calc_ut(j, kod, EPHFLAG)[0][0]
            except Exception:
                continue
            for _n, nlon in hedefler:
                d = sep(lon, nlon)
                for hedef, _t in ACILAR:
                    f = abs(d - hedef)
                    if f <= ORB:
                        toplam += ag * (1 - f / ORB)
                        break
        yas = int((j - ch.jd_ut) / 365.2422)
        yillik.setdefault(yas, []).append(toplam)
        j += adim_gun

    if not yillik:
        return {"hata": "eğri hesaplanamadı"}

    ort_yil = {y: sum(v) / len(v) for y, v in sorted(yillik.items())}
    degerler = sorted(ort_yil.values())
    esik = degerler[max(0, int(len(degerler) * 0.25))]      # alt çeyrek

    sessiz = [y for y, v in ort_yil.items() if v <= esik]
    yogun = [y for y, v in ort_yil.items()
             if v >= degerler[min(len(degerler) - 1, int(len(degerler) * 0.85))]]

    return {
        "modul": "KAYIP ZAMAN — hangi yıllar sessiz geçti",
        "yas_araligi": [min(ort_yil), max(ort_yil)],
        "yillik": [{"yas": y, "basinc": round(v, 2),
                    "sessiz": v <= esik} for y, v in ort_yil.items()],
        "sessiz_yaslar": _aralik_yaz(sessiz),
        "yogun_yaslar": _aralik_yaz(yogun),
        "esik": round(esik, 2),
        "okuma": _kayip_okuma(sessiz, yogun, ort_yil),
        "yontem": ("Doğumdan bugüne, ayda bir, altı ağır cismin on iki "
                   "natal noktaya teması puanlanır. Yıllık ortalama alınır; "
                   "alt çeyrek 'sessiz' sayılır. Ay, Merkür ve Venüs hariç "
                   "tutulur — taban gürültüsü üretirler."),
        "sinir": ("Sessiz yıl 'kötü yıl' DEĞİLDİR. Dışarıdan az itilmek "
                  "kimi için huzur, kimi için boşluktur. Modül yükü ölçer, "
                  "işareti değil."),
    }


def _aralik_yaz(yaslar: List[int]) -> List[str]:
    """Ardışık yaşları aralık olarak yazar: [3,4,5,9] → ['3–5','9']."""
    if not yaslar:
        return []
    yaslar = sorted(yaslar)
    out, bas, onc = [], yaslar[0], yaslar[0]
    for y in yaslar[1:]:
        if y == onc + 1:
            onc = y
            continue
        out.append(f"{bas}–{onc}" if onc > bas else str(bas))
        bas = onc = y
    out.append(f"{bas}–{onc}" if onc > bas else str(bas))
    return out


def _kayip_okuma(sessiz, yogun, ort) -> str:
    p = []
    if sessiz:
        p.append("Sessiz geçen yaşlar: " + ", ".join(_aralik_yaz(sessiz))
                 + ". O aralıklarda gökyüzünde bu kişinin haritasına değen "
                   "az şey vardı — 'kayıp yıllar' hissi varsa ölçülebilir "
                   "bir karşılığı var, kişisel bir kusur değil.")
    if yogun:
        p.append("En yoğun yaşlar: " + ", ".join(_aralik_yaz(yogun)) + ".")
    return " ".join(p) or "Yıllar arasında belirgin fark yok."


# ============================================================================
# 2 · DÖNÜŞ NOKTASI
# ============================================================================
def donus_noktasi(ch: NatalChart, bugun_jd: Optional[float] = None,
                  ileri_yil: float = 40.0) -> dict:
    """
    Yavaş gezegenlerin natal noktalara son ve sonraki geçişi.
    Bir daha gelmeyecek olanları işaretler.
    """
    ensure_ephe()
    if bugun_jd is None:
        u = dt.datetime.utcnow()
        bugun_jd = swe.julday(u.year, u.month, u.day, 12.0)

    hedefler = _hedefler(ch)
    kayitlar: List[dict] = []

    for ad, kod, periyot in COK_YAVAS:
        tr = TR_NAME.get(ad, ad)
        for nokta, nlon in hedefler:
            for hedef, tur in ACILAR:
                gecmis = _gecis_bul(kod, nlon, hedef, ch.jd_ut, bugun_jd)
                gelecek = _gecis_bul(kod, nlon, hedef, bugun_jd,
                                     bugun_jd + ileri_yil * 365.2422)
                if not gecmis and not gelecek:
                    continue
                # Ömürde bir kez mi? Periyot, kalan ömürden uzunsa evet.
                yas = (bugun_jd - ch.jd_ut) / 365.2422
                tek_sefer = periyot > (90 - yas) and not gelecek
                kayitlar.append({
                    "gok": tr, "nokta": nokta, "aci": tur,
                    "son": jd_to_iso(gecmis[-1])[:7] if gecmis else None,
                    "son_yas": (round((gecmis[-1] - ch.jd_ut) / 365.2422, 1)
                                if gecmis else None),
                    "sonraki": jd_to_iso(gelecek[0])[:7] if gelecek else None,
                    "sonraki_yas": (round((gelecek[0] - ch.jd_ut) / 365.2422, 1)
                                    if gelecek else None),
                    "bir_daha_yok": tek_sefer,
                    "periyot": periyot,
                })

    kayitlar.sort(key=lambda x: (x["sonraki"] or "9999"))
    yaklasan = [k for k in kayitlar if k["sonraki"]][:6]
    kapanmis = [k for k in kayitlar if k["bir_daha_yok"]][:6]

    return {
        "modul": "DÖNÜŞ NOKTASI — bir daha gelmeyecek kapılar",
        "toplam": len(kayitlar),
        "yaklasan": yaklasan,
        "kapanmis": kapanmis,
        "okuma": _donus_okuma(yaklasan, kapanmis),
        "yontem": (f"Dört yavaş gezegenin (Satürn, Uranüs, Neptün, Plüton) "
                   f"on iki natal noktaya {ORB}° orbla geçişleri, doğumdan "
                   f"bugüne ve {int(ileri_yil)} yıl ileriye taranır. "
                   f"Gezegenin periyodu kalan ömürden uzunsa ve ileride "
                   f"geçiş yoksa 'bir daha yok' işaretlenir."),
        "sinir": ("Bir kapının kapanması kayıp DEĞİLDİR. Kimi kapı "
                  "açıldığında zorlar, kapandığında rahatlatır. Modül "
                  "tekrarlanabilirliği ölçer, iyiliği değil."),
    }


def _gecis_bul(kod: int, nlon: float, aci: float, jd_bas: float,
               jd_son: float, adim: float = 20.0) -> List[float]:
    """Verilen aralıkta cismin natal noktaya `aci` yaptığı anlar."""
    out: List[float] = []
    j = jd_bas
    onceki = None
    while j < jd_son:
        try:
            lon = swe.calc_ut(j, kod, EPHFLAG)[0][0]
        except Exception:
            break
        f = ((sep(lon, nlon) - aci + 180) % 360) - 180
        if onceki is not None and onceki * f < 0 and abs(f - onceki) < 90:
            a, b = j - adim, j
            for _ in range(24):
                o = (a + b) / 2
                try:
                    lo = swe.calc_ut(o, kod, EPHFLAG)[0][0]
                except Exception:
                    break
                fo = ((sep(lo, nlon) - aci + 180) % 360) - 180
                if onceki * fo < 0:
                    b = o
                else:
                    a, onceki = o, fo
            out.append((a + b) / 2)
        onceki = f
        j += adim
    return out


def _donus_okuma(yaklasan, kapanmis) -> str:
    p = []
    if yaklasan:
        y = yaklasan[0]
        p.append(f"En yakın kapı: {y['gok']} {y['nokta']} {y['aci']}ı "
                 f"{y['sonraki']} ({y['sonraki_yas']} yaş).")
    if kapanmis:
        k = kapanmis[0]
        p.append(f"BİR DAHA GELMEYECEK: {k['gok']} {k['nokta']} {k['aci']}ı "
                 + (f"son {k['son']} ({k['son_yas']} yaş) yaşandı."
                    if k["son"] else "bu ömürde gerçekleşmiyor.")
                 + " Bu aralık tekrar etmez; okumada ağırlığı ona göre ver.")
    return " ".join(p) or "Yavaş gezegen kapısı bulunamadı."
