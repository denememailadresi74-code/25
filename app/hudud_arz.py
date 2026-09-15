#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUDÛD-I ARZ — astrokartografi ile deklinasyon katmanının birleşimi

BİRLEŞTİREN BAĞ
    İki katman ayrı ayrı duruyordu. Aralarındaki bağ ise matematikseldir ve
    tek bir denklemde saklı:

        φ_kritik = 90° − |δ|

    Bir cisim, |enlem| > φ_kritik olan bölgelerde HİÇ DOĞMAZ VE BATMAZ
    (kutupsal olur). Yani o cismin ASC/DSC çizgisi yeryüzünün o kısmında
    YOKTUR — çizilmez, çünkü yoktur.

    Buradan çıkan şey şu: deklinasyon ne kadar büyükse, cismin çizgisi
    yeryüzünün o kadar büyük bir kısmından SİLİNİR.

    Hudûd dışı cisim (|δ| > eğiklik) tanım gereği en büyük deklinasyona
    sahip olandır. Dolayısıyla:

        Gökyüzünde "kendi kuralının dışına taşmış" olan kapasite,
        YERYÜZÜNDE de en geniş alanda ulaşılamaz olandır.

    Bu bir benzetme değil, aynı sayının iki yüzüdür: |δ| hem hudûd dışılığı
    hem kritik enlemi belirler. İki katman zaten aynı büyüklüğe bakıyordu;
    bu modül bunu görünür kılar.

ÜÇ ÇIKTI
    1. KRİTİK ENLEM — her cisim için çizginin kaybolduğu enlem
    2. SESSİZ KUŞAK — hudûd dışı cisimlerin hiç kapısı olmayan enlem bandı
    3. ŞEHİR ÇÖZÜMLEMESİ — belirli bir şehir için hangi çizgiler yakın,
       o şehir bir sessiz kuşağın içinde mi

SINIR
    Çizgiler ölçümdür; anlamları yorumdur. "Şu şehirde şu olur" denmez.
    Bir yer bir konuyu öne çıkarır ya da geri çeker; kişiyi değiştirmez.
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence, Tuple

from .astro import NatalChart, CORE10, TR_NAME, jd_to_iso
from .circular import fmt_lon
from .hudud import egiklik
from .kartografi import astrokartografi, _ekvatoral, _gmst

KM_DERECE = 111.32          # ekvatorda bir boylam derecesi
YAKIN_KM = 700.0            # klasik astrokartografide ~600-800 km etki mesafesi


def _boylam_km(d_boylam: float, enlem: float) -> float:
    """Boylam farkını o enlemde kilometreye çevirir."""
    d = abs(((d_boylam + 540) % 360) - 180)
    return d * KM_DERECE * math.cos(math.radians(enlem))


# ============================================================================
# 1 · KRİTİK ENLEM
# ============================================================================
def kritik_enlemler(chart: NatalChart) -> dict:
    """
    Her cismin çizgisinin kaybolduğu enlem: φ = 90° − |δ|.

    Bu tek denklem astrokartografiyi deklinasyon katmanına bağlar.
    """
    eps = egiklik(chart.jd_ut)
    satir = []
    for k in CORE10:
        _ra, dec = _ekvatoral(chart.jd_ut, k)
        fk = 90.0 - abs(dec)
        disarida = (k != "Sun") and (abs(dec) > eps)
        # Yeryüzünün ne kadarı çizgisiz kalıyor (küre yüzey oranı)
        pay = 1.0 - math.sin(math.radians(fk)) if fk < 90 else 0.0
        satir.append({
            "cisim": TR_NAME[k], "kod": k,
            "dekl": round(dec, 3),
            "kritik_enlem": round(fk, 2),
            "hudud_disi": disarida,
            "cizgisiz_yuzey_orani": round(max(0.0, pay), 4),
        })
    satir.sort(key=lambda x: x["kritik_enlem"])
    oob = [x for x in satir if x["hudud_disi"]]
    return {
        "egiklik": round(eps, 3),
        "cisimler": satir,
        "en_dar_kapi": satir[0],
        "hudud_disi_sayisi": len(oob),
        "okuma": (
            f"{satir[0]['cisim']} ±{satir[0]['kritik_enlem']:.0f}° enleminin "
            f"ötesinde hiç doğmuyor; o bölgelerde bu kapasiteye kapı yok."
            + (f" {', '.join(x['cisim'] for x in oob)} hudûd dışında: "
               "gökyüzünde kendi kuralının dışında olan kapasite, yeryüzünde "
               "de en geniş alanda ulaşılamaz olandır — aynı sayının iki yüzü."
               if oob else "")),
        "yontem": ("φ_kritik = 90° − |δ|. Bu enlemin ötesinde cisim kutupsal "
                   "olur: ne doğar ne batar, dolayısıyla ASC/DSC çizgisi "
                   "orada YOKTUR. Deklinasyon büyüdükçe çizgisiz alan büyür."),
    }


# ============================================================================
# 2 · SESSİZ KUŞAK
# ============================================================================
def sessiz_kusaklar(chart: NatalChart) -> dict:
    """Hudûd dışı cisimlerin hiç kapısı olmadığı enlem bantları."""
    ke = kritik_enlemler(chart)
    kusak = []
    for x in ke["cisimler"]:
        if not x["hudud_disi"]:
            continue
        fk = x["kritik_enlem"]
        kusak.append({
            "cisim": x["cisim"],
            "kuzey_bandi": [round(fk, 1), 90.0],
            "guney_bandi": [-90.0, round(-fk, 1)],
            "yuzey_orani": x["cizgisiz_yuzey_orani"],
            "anlam": (f"{x['cisim']} ±{fk:.0f}° enleminin ötesinde hiç "
                      "doğmuyor. O kapasite orada devreye girmez — ne iyi "
                      "ne kötü: sadece o konu orada gündeme gelmez."),
        })
    return {
        "kusaklar": kusak,
        "okuma": ("Hudûd dışı cisim yok; bütün kapasitelerin yeryüzünün "
                  "büyük kısmında kapısı var." if not kusak else
                  f"{len(kusak)} kapasitenin sessiz kaldığı enlem bandı var."),
    }


# ============================================================================
# 3 · PARALEL ÇİZGİ ÇİFTLERİ
# ============================================================================
def paralel_cizgiler(chart: NatalChart, orb: float = 1.0) -> dict:
    """
    Deklinasyonu eşit olan cisimlerin çizgileri AYNI BİÇİMDEDİR.

    Paralel iki cismin kritik enlemi de aynıdır; ASC eğrileri birbirinin
    boylamda kaydırılmış kopyasıdır. Yani birlikte görünür, birlikte
    kaybolurlar — deklinasyondaki bağın yeryüzündeki karşılığı budur.
    """
    veri = []
    for k in CORE10:
        _ra, dec = _ekvatoral(chart.jd_ut, k)
        veri.append((k, dec))
    ciftler = []
    for i in range(len(veri)):
        for j in range(i + 1, len(veri)):
            k1, d1 = veri[i]
            k2, d2 = veri[j]
            fp, fk = abs(d1 - d2), abs(d1 + d2)
            tur, o = (None, None)
            if fp <= orb:
                tur, o = "paralel", fp
            elif fk <= orb:
                tur, o = "karşıt-paralel", fk
            if not tur:
                continue
            ciftler.append({
                "a": TR_NAME[k1], "b": TR_NAME[k2], "tur": tur,
                "orb": round(o, 2),
                "kritik_enlem_a": round(90 - abs(d1), 1),
                "kritik_enlem_b": round(90 - abs(d2), 1),
                "anlam": ("Çizgileri aynı biçimde; birlikte görünür, birlikte "
                          "kaybolurlar." if tur == "paralel" else
                          "Çizgileri birbirinin aynadaki hâli: biri kuzeyde "
                          "güçlüyken öteki güneyde."),
            })
    ciftler.sort(key=lambda x: x["orb"])
    return {"ciftler": ciftler[:10],
            "okuma": ("Aynı deklinasyon kuşağında cisim yok."
                      if not ciftler else
                      f"{len(ciftler)} çift aynı kuşakta: bu cisimlerin "
                      "çizgileri yeryüzünde birlikte hareket eder.")}


# ============================================================================
# 4 · ŞEHİR ÇÖZÜMLEMESİ
# ============================================================================
def sehir_cozumle(chart: NatalChart, enlem: float, boylam: float,
                  ad: str = "", jd: Optional[float] = None,
                  yakin_km: float = YAKIN_KM) -> dict:
    """
    Belirli bir konum için: hangi çizgiler yakın, hangi kapasiteler orada
    sessiz, hangi paralel çiftler devrede.
    """
    j = jd if jd is not None else chart.jd_ut
    ak = astrokartografi(j)
    ke = kritik_enlemler(chart)
    kritik = {x["kod"]: x for x in ke["cisimler"]}

    yakin: List[dict] = []
    for c in ak["cizgiler"]:
        # MC / IC — dikey çizgiler
        for tur in ("MC", "IC"):
            km = _boylam_km(c[tur] - boylam, enlem)
            if km <= yakin_km:
                yakin.append({"cisim": c["cisim"], "kod": c["kod"],
                              "cizgi": tur, "uzaklik_km": round(km),
                              "guc": round(max(0.0, 1 - km / yakin_km), 3)})
        # ASC / DSC — bu enlemdeki boylam
        for tur in ("ASC", "DSC"):
            en_yakin = None
            for nk in c[tur]:
                if abs(nk["enlem"] - enlem) <= 3.5:
                    km = _boylam_km(nk["boylam"] - boylam, enlem)
                    if en_yakin is None or km < en_yakin:
                        en_yakin = km
            if en_yakin is not None and en_yakin <= yakin_km:
                yakin.append({"cisim": c["cisim"], "kod": c["kod"],
                              "cizgi": tur, "uzaklik_km": round(en_yakin),
                              "guc": round(max(0.0, 1 - en_yakin / yakin_km), 3)})
    yakin.sort(key=lambda x: x["uzaklik_km"])

    # bu enlemde hangi cisimlerin çizgisi hiç yok
    sessiz = [{"cisim": kritik[k]["cisim"], "kritik_enlem": kritik[k]["kritik_enlem"],
               "hudud_disi": kritik[k]["hudud_disi"]}
              for k in CORE10 if abs(enlem) > kritik[k]["kritik_enlem"]]

    # hudûd dışı bir cismin çizgisi yakınsa: özel durum
    oob_yakin = [x for x in yakin if kritik.get(x["kod"], {}).get("hudud_disi")]

    return {
        "yer": {"ad": ad or f"{enlem:.2f}, {boylam:.2f}",
                "enlem": round(enlem, 4), "boylam": round(boylam, 4)},
        "an": jd_to_iso(j),
        "yakin_cizgiler": yakin[:10],
        "sessiz_kapasiteler": sessiz,
        "hudud_disi_etkin": [{"cisim": x["cisim"], "cizgi": x["cizgi"],
                              "uzaklik_km": x["uzaklik_km"]} for x in oob_yakin],
        "okuma": _sehir_okuma(yakin, sessiz, oob_yakin, ad),
        "yontem": (f"Etki mesafesi {yakin_km:.0f} km. Boylam farkı o enlemde "
                   "kilometreye çevrilir (111.32 × cos φ). ASC/DSC için "
                   "enlemde en yakın çizgi noktası alınır."),
    }


def _sehir_okuma(yakin: List[dict], sessiz: List[dict],
                 oob: List[dict], ad: str) -> str:
    yer = ad or "burası"
    if not yakin and not sessiz:
        return (f"{yer} için belirgin bir çizgi yok; bu yer haritada "
                "nötr sayılır. Nötr olması kötü değildir — hiçbir konu "
                "zorla öne çıkmaz.")
    p = []
    if yakin:
        ilk = yakin[0]
        p.append(f"{yer} en çok {ilk['cisim']} {ilk['cizgi']} çizgisine yakın "
                 f"({ilk['uzaklik_km']} km).")
    if oob:
        p.append(f"Dikkat: {oob[0]['cisim']} hudûd dışı bir kapasite ve burada "
                 "çizgisi geçiyor. Kendi kurallarına uymayan yan, bu yerde "
                 "doğrudan devreye giriyor.")
    if sessiz:
        p.append(f"{', '.join(x['cisim'] for x in sessiz[:3])} bu enlemde hiç "
                 "doğmuyor; o konular burada kendiliğinden gündeme gelmez.")
    return " ".join(p)


# ============================================================================
def hudud_arz(chart: NatalChart, jd: Optional[float] = None) -> dict:
    """İki katmanın birleşimi."""
    return {
        "modul": "HUDÛD-I ARZ — astrokartografi ve deklinasyonun birleşimi",
        "kritik_enlem": kritik_enlemler(chart),
        "sessiz_kusaklar": sessiz_kusaklar(chart),
        "paralel_cizgiler": paralel_cizgiler(chart),
        "bag": ("Bu iki katmanı birleştiren şey tek bir denklemdir: "
                "φ_kritik = 90° − |δ|. Deklinasyon hem hudûd dışılığı hem "
                "çizginin kaybolduğu enlemi belirler. Gökyüzünde kendi "
                "kuralının dışına taşmış kapasite, yeryüzünde de en geniş "
                "alanda ulaşılamaz olandır."),
        "uyari": ("Çizgiler ölçümdür, anlamları yorumdur. Bir yer bir konuyu "
                  "öne çıkarır ya da geri çeker; kişiyi değiştirmez."),
    }
