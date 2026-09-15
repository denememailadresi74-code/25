#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SÜKÛT HARİTASI — gökyüzünün sustuğu aralıklar

İCADIN FİKRİ
    Astrolojinin tamamı NEYİN AKTİF OLDUĞU üzerine kuruludur. Her kitap,
    her yazılım, her danışman "şu transit geliyor, şu tetikleniyor" der.

    Kimse SUSKUNLUĞU ölçmez.

    Oysa bir yılın her günü aynı yoğunlukta değildir. Bazı aralıklarda
    gökyüzünde kişinin haritasına değen hiçbir şey yoktur — hiçbir gezegen
    hiçbir natal noktaya yaklaşmaz. O aralıklar boşluk değildir; ÖLÇÜLEBİLİR
    BİR OLGUDUR ve şunu söyler:

        Bu aralıkta dışarıdan bir baskı yok.

    Bunun neden önemli olduğu şurada: danışan "her şey üst üste geldi"
    dediğinde, astrolog otomatik olarak transitlere bakar ve bir şey bulur —
    çünkü herhangi bir günde bakılırsa hep bir şey bulunur. Sükût haritası
    bunun tersini yapar: eğer şikâyet edilen dönem SESSİZ bir aralığa
    düşüyorsa, sebep gökyüzü değildir.

    Yani bu bir YANLIŞLAMA ARACIDIR. Astrolojide böyle bir şey yok.

NASIL ÖLÇÜLÜR
    Yılın her günü için, gökteki cisimlerin natal noktalara yaptığı
    temaslar puanlanır (gezegen ağırlığı × açı ağırlığı × orb yakınlığı).
    Ortaya bir BASINÇ EĞRİSİ çıkar.

    · Basınç eşiğin altında ve N gün üst üste kalırsa → SÜKÛT ARALIĞI
    · Basınç tepe yaparsa → SIKIŞMA ARALIĞI
    · İkisinin oranı kişinin yılının "dokusunu" verir

DÜRÜSTLÜK
    Sükût "iyi", sıkışma "kötü" DEĞİLDİR. Sükût aralığında kişi kendi
    başınadır — bu bazıları için rahatlama, bazıları için boşluktur.
    Modül bunu yorumlamaz, ölçer.
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Optional, Tuple

import swisseph as swe

from .astro import NatalChart, CORE10, TR_NAME, EPHFLAG, ensure_ephe, jd_to_iso
from .circular import sep

# Gezegen ağırlığı: yavaş olan daha uzun ve derin basınç yapar
GEZEGEN_AGIRLIK = {
    "Sun": 1.0, "Moon": 0.35, "Mercury": 0.7, "Venus": 0.8, "Mars": 1.2,
    "Jupiter": 1.6, "Saturn": 2.2, "Uranus": 2.0, "Neptune": 1.8,
    "Pluto": 2.0,
}
ACI = ((0, "kavuşum", 1.0), (180, "karşıt", 0.9), (90, "kare", 0.85),
       (120, "üçgen", 0.55), (60, "altmışlık", 0.35))
ORB = 3.0                     # derece
ESIK = 2.0                    # bu değerin altı "sessiz"
ASGARI_GUN = 6                # sükût sayılması için en az bu kadar gün


def _gunluk_basinc(jd: float, hedefler: List[Tuple[str, float]]) -> Tuple[float, List[dict]]:
    """O gün gökteki cisimlerin natal noktalara yaptığı toplam basınç."""
    toplam = 0.0
    temas: List[dict] = []
    for k in CORE10:
        # AY HARİÇ: 27 günde bir tur atıyor ve her natal noktaya ayda bir
        # değiyor. Bu sinyal değil taban gürültüsü; eğriyi düzleştirip
        # sessiz aralıkları görünmez yapıyordu.
        if k == "Moon":
            continue
        kod = getattr(swe, {"Sun": "SUN", "Moon": "MOON", "Mercury": "MERCURY",
                            "Venus": "VENUS", "Mars": "MARS", "Jupiter": "JUPITER",
                            "Saturn": "SATURN", "Uranus": "URANUS",
                            "Neptune": "NEPTUNE", "Pluto": "PLUTO"}[k])
        try:
            lon = swe.calc_ut(jd, kod, EPHFLAG)[0][0]
        except Exception:
            continue
        ag = GEZEGEN_AGIRLIK.get(k, 1.0)
        for ad, nlon in hedefler:
            d = sep(lon, nlon)
            for hedef, tur, pay in ACI:
                fark = abs(d - hedef)
                if fark <= ORB:
                    yakin = 1.0 - fark / ORB
                    p = ag * pay * yakin
                    toplam += p
                    if p >= 0.6:
                        temas.append({"gok": TR_NAME[k], "natal": ad,
                                      "aci": tur, "orb": round(fark, 2),
                                      "puan": round(p, 2)})
                    break
    temas.sort(key=lambda x: -x["puan"])
    return toplam, temas[:4]


def sukut_haritasi(chart: NatalChart, jd_bas: Optional[float] = None,
                   gun: int = 365, adim: int = 2) -> dict:
    """
    Bir yılın basınç eğrisini çıkarır; sessiz ve sıkışık aralıkları bulur.

    adim: kaç günde bir örnekleme (2 gün yeterli; yavaş gezegenler günde
    en fazla ~1° gider, hızlılar zaten eşiği tek başına aşmaz).
    """
    ensure_ephe()
    if jd_bas is None:
        u = dt.datetime.utcnow()
        jd_bas = swe.julday(u.year, u.month, u.day, 12.0)

    hedefler: List[Tuple[str, float]] = [
        (TR_NAME[k], chart.bodies[k].lon) for k in CORE10 if k in chart.bodies]
    hedefler += [("Yükselen", chart.asc), ("Tepe noktası", chart.mc)]

    egri: List[dict] = []
    j = jd_bas
    while j < jd_bas + gun:
        p, t = _gunluk_basinc(j, hedefler)
        egri.append({"jd": j, "tarih": jd_to_iso(j)[:10],
                     "basinc": round(p, 2), "temas": t})
        j += adim

    if not egri:
        return {"hata": "eğri hesaplanamadı"}

    puanlar = [x["basinc"] for x in egri]
    ort = sum(puanlar) / len(puanlar)
    enb, ens = max(puanlar), min(puanlar)

    # EŞİK YÜZDELİK DİLİMDEN ALINIR.
    # İlk deneme "ortalamanın %45'i" diyordu ve HİÇ aralık bulamadı:
    # eşik (4.11) eğrinin minimumunun (4.72) altında kalıyordu. Ortalamaya
    # oranlamak yanlış — taban gürültüsü yüksek olduğu için ortalama da
    # yüksek çıkıyor. Kişinin KENDİ dağılımının alt ve üst dilimi alınır;
    # bu her haritada anlamlı sonuç verir.
    sirali = sorted(puanlar)

    def dilim(o):
        return sirali[max(0, min(len(sirali) - 1, int(len(sirali) * o)))]

    esik = dilim(0.22)             # alt beşte bir → sükût
    esik_ust = dilim(0.80)         # üst beşte bir → sıkışma

    sukut = _aralik_bul(egri, lambda p: p <= esik, ASGARI_GUN // adim + 1)
    sikisma = _aralik_bul(egri, lambda p: p >= esik_ust, 2)

    return {
        "modul": "SÜKÛT HARİTASI — gökyüzünün sustuğu aralıklar",
        "baslangic": jd_to_iso(jd_bas)[:10],
        "gun": gun,
        "ortalama_basinc": round(ort, 2),
        "en_yuksek": round(enb, 2),
        "en_dusuk": round(ens, 2),
        "esik": round(esik, 2),
        "esik_sikisma": round(esik_ust, 2),
        "sukut_araliklari": sukut,
        "sikisma_araliklari": sikisma,
        "sukut_gun": sum(a["gun"] for a in sukut),
        "sukut_orani": round(sum(a["gun"] for a in sukut) / gun, 3),
        "egri": [{"tarih": x["tarih"], "basinc": x["basinc"]} for x in egri],
        "doku": _doku(sukut, sikisma, gun, ort),
        "yanlislama": (
            "BU MODÜLÜN ASIL İŞİ: danışan bir dönemden şikâyet ediyorsa, o "
            "dönem sükût aralığına düşüyor mu diye bak. Düşüyorsa sebep "
            "gökyüzü DEĞİLDİR — başka yere bakmak gerekir. Astrolojide "
            "herhangi bir güne bakılırsa hep bir şey bulunur; bu modül "
            "bulunmayacağı zamanları söyler."),
        "uyari": ("Sükût 'iyi', sıkışma 'kötü' değildir. Sükût aralığında "
                  "kişi kendi başınadır: kimine rahatlama, kimine boşluk. "
                  "Modül yorumlamaz, ölçer."),
        "yontem": (f"Her {adim} günde bir, gökteki on cismin on iki natal "
                   f"noktaya yaptığı temaslar puanlanır (gezegen ağırlığı × "
                   f"açı ağırlığı × orb yakınlığı, orb {ORB}°). Ay hariç "
                   f"tutulur: 27 günde bir tur attığı için taban gürültüsü "
                   f"üretir. Eşik, kişinin KENDİ dağılımının alt %22 ve üst "
                   f"%20 dilimidir — sabit ya da ortalamaya oranlı eşik "
                   f"hiç aralık bulamıyordu."),
    }


def _aralik_bul(egri: List[dict], kosul, asgari: int) -> List[dict]:
    """Koşulu sağlayan ardışık aralıkları bulur."""
    out: List[dict] = []
    bas = None
    for i, x in enumerate(egri):
        if kosul(x["basinc"]):
            if bas is None:
                bas = i
        else:
            if bas is not None and i - bas >= asgari:
                out.append(_aralik(egri, bas, i - 1))
            bas = None
    if bas is not None and len(egri) - bas >= asgari:
        out.append(_aralik(egri, bas, len(egri) - 1))
    return out


def _aralik(egri: List[dict], i: int, j: int) -> dict:
    dilim = egri[i:j + 1]
    p = [x["basinc"] for x in dilim]
    gun = int(round(dilim[-1]["jd"] - dilim[0]["jd"])) + 1
    en = max(dilim, key=lambda x: x["basinc"])
    return {"basla": dilim[0]["tarih"], "bitis": dilim[-1]["tarih"],
            "gun": gun, "ortalama": round(sum(p) / len(p), 2),
            "tepe": round(max(p), 2),
            "tepe_tarih": en["tarih"],
            "tepe_temas": en["temas"]}


def _doku(sukut: List[dict], sikisma: List[dict], gun: int,
          ort: float) -> str:
    o = sum(a["gun"] for a in sukut) / gun
    if o >= 0.30:
        d = ("Bu yılın önemli bir kısmı sessiz. Dışarıdan az itiliyorsun; "
             "olan biten çoğunlukla senin kendi hareketin.")
    elif o >= 0.12:
        d = ("Dengeli bir yıl: baskı dönemleri var ama arada gerçekten "
             "boş aralıklar da var.")
    else:
        d = ("Yıl yoğun. Sessiz aralık neredeyse yok; sürekli bir şey "
             "temas hâlinde. Dinlenme aralığını sen kurmak zorundasın, "
             "gökyüzü vermiyor.")
    if sikisma:
        en = max(sikisma, key=lambda x: x["tepe"])
        d += (f" En sıkışık aralık {en['basla']} – {en['bitis']}; "
              f"tepe {en['tepe_tarih']}.")
    return d


def sukut_sorgusu(harita: dict, tarih: str) -> dict:
    """
    YANLIŞLAMA SORGUSU: verilen tarih sessiz bir aralığa mı düşüyor?

    Danışan "şu dönemde her şey üst üste geldi" dediğinde bu sorgu
    çalıştırılır. Cevap "evet, sessizdi" ise sebep gökyüzü değildir.
    """
    for a in harita.get("sukut_araliklari") or []:
        if a["basla"] <= tarih <= a["bitis"]:
            return {"tarih": tarih, "durum": "sükût",
                    "aralik": f"{a['basla']} – {a['bitis']}",
                    "gun": a["gun"], "ortalama": a["ortalama"],
                    "okuma": ("Bu tarih SESSİZ bir aralığa düşüyor. "
                              "Gökyüzünde bu kişinin haritasına değen "
                              "belirgin bir şey yok. O dönemde yaşananların "
                              "kaynağı başka yerde — kişinin kendi hamlesi, "
                              "çevresi ya da birikmiş bir şeyin patlaması.")}
    for a in harita.get("sikisma_araliklari") or []:
        if a["basla"] <= tarih <= a["bitis"]:
            return {"tarih": tarih, "durum": "sıkışma",
                    "aralik": f"{a['basla']} – {a['bitis']}",
                    "gun": a["gun"], "tepe": a["tepe"],
                    "temas": a["tepe_temas"],
                    "okuma": ("Bu tarih yoğun bir aralığa düşüyor. "
                              "Dışarıdan gerçekten baskı var; kişinin "
                              "'zorlandım' demesi yerinde.")}
    return {"tarih": tarih, "durum": "olağan",
            "okuma": ("Bu tarih ne özellikle sessiz ne özellikle yoğun. "
                      "Sıradan bir aralık.")}
