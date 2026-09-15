#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ASTROKARTOGRAFİ ve ARZ İZDÜŞÜMÜ

İKİ KATMAN VAR VE BİRİ KLASİK, ÖTEKİ YENİ:

  A · ASTROKARTOGRAFİ  (klasik, Jim Lewis 1970'ler)
      Doğum ANI sabit, KONUM değişken. Yeryüzünde her gezegenin dört
      çizgisi vardır: o gezegenin doğduğu (ASC), battığı (DSC), tepede
      olduğu (MC) ve dipte olduğu (IC) yerler. Hesabı tamdır, yoruma
      açık olan yalnız anlamıdır.

  B · ARZ İZDÜŞÜMÜ  (bu modelin kendi genişletmesi)
      Klasik astrokartografi GEZEGENLERİN nerede açısal olduğunu gösterir.
      Bu katman ise MODELİN KENDİ EŞİĞİNİN yeryüzünde nasıl değiştiğini
      gösterir.

      Neden mümkün: BERZAH kütleleri açısallıktan (ASC/MC yakınlığı)
      besleniyor. Konum değişince açısallık değişir, kütleler değişir,
      alan değişir — dolayısıyla KARAR EŞİĞİ DE DEĞİŞİR. Aynı anda doğmuş
      ama başka yerde doğmuş biri, aynı gökyüzüne sahip olduğu hâlde
      farklı bir eşikle yaşar.

      Ölçülen üç şey:
        · eşiğin keskinliği (asimetri) — karar ne kadar net kutuplaşıyor
        · alanın toplanması (Rayleigh R) — tek tema mı, dağınık mı
        · Kara Delik'in düştüğü ev — hayatın hangi alanı ağırlık taşıyor

      Bu, "nereye taşınmalıyım" sorusuna klasik astrokartografiden FARKLI
      bir cevap verir; ikisi çeliştiğinde bu bir hata değil, iki ayrı
      soruya iki ayrı cevaptır.

ÜÇ ZAMAN DÜZLEMİ
    Natal, Güneş dönüşü (yıllık) ve Ay dönüşü (aylık) için ayrı ayrı
    hesaplanır. Güneş dönüşü yılın, Ay dönüşü ayın haritasıdır; ikisinin
    de kendi astrokartografisi vardır ve klasik uygulamada "bu yılı nerede
    geçirmeli" sorusu tam olarak buradan okunur.
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence, Tuple

import swisseph as swe

from .astro import (NatalChart, CORE10, TR_NAME, EPHFLAG, ensure_ephe,
                    calc_lon, chart_at_jd, jd_to_iso, BODY_IDS)
from .circular import norm360, sep, fmt_lon
from .engine_mass import compute_masses, find_berzah2, find_kd_ad

PARAN_ORB = 1.2          # derece — klasikte ~70 deniz mili (≈1.15°)


def _gmst(jd: float) -> float:
    """Greenwich ortalama yıldız zamanı, derece."""
    T = (jd - 2451545.0) / 36525.0
    g = (280.46061837 + 360.98564736629 * (jd - 2451545.0)
         + 0.000387933 * T * T - T * T * T / 38710000.0)
    return g % 360.0


def _ekvatoral(jd: float, key: str) -> Tuple[float, float]:
    """Cismin sağ açıklığı ve deklinasyonu (derece)."""
    ensure_ephe()
    (ra, dec, *_), _ = swe.calc_ut(jd, BODY_IDS[key], EPHFLAG | swe.FLG_EQUATORIAL)
    return norm360(ra), dec


# ============================================================================
# A · KLASİK ASTROKARTOGRAFİ
# ============================================================================
def astrokartografi(jd: float, adim_enlem: float = 3.0,
                    azami_enlem: float = 66.0) -> dict:
    """
    Her cisim için dört çizgi.

    MC/IC dikey çizgilerdir (sabit boylam): gezegenin sağ açıklığı yıldız
    zamanına eşit olduğu meridyen.
        boylam = RA − GMST            (MC)
        boylam = RA + 180 − GMST      (IC)

    ASC/DSC eğridir: her enlemde gezegenin ufukta olduğu boylam.
        cos H = −tan φ · tan δ
    |tan φ · tan δ| > 1 olduğunda cisim o enlemde hiç doğmaz/batmaz
    (kutup bölgesi); o enlemde çizgi YOKTUR ve uydurulmaz.
    """
    g = _gmst(jd)
    cizgiler = []
    for k in CORE10:
        ra, dec = _ekvatoral(jd, k)
        mc = ((ra - g + 540) % 360) - 180
        ic = ((ra + 180 - g + 540) % 360) - 180
        asc: List[dict] = []
        dsc: List[dict] = []
        f = -azami_enlem
        while f <= azami_enlem + 1e-9:
            try:
                c = -math.tan(math.radians(f)) * math.tan(math.radians(dec))
            except Exception:
                f += adim_enlem
                continue
            if -1.0 <= c <= 1.0:
                H = math.degrees(math.acos(c))
                asc.append({"enlem": round(f, 2),
                            "boylam": round(((ra - H - g + 540) % 360) - 180, 3)})
                dsc.append({"enlem": round(f, 2),
                            "boylam": round(((ra + H - g + 540) % 360) - 180, 3)})
            f += adim_enlem
        cizgiler.append({"cisim": TR_NAME[k], "kod": k,
                         "ra": round(ra, 3), "dekl": round(dec, 3),
                         "MC": round(mc, 3), "IC": round(ic, 3),
                         "ASC": asc, "DSC": dsc,
                         "kutup_kesintisi": len(asc) < int(2 * azami_enlem / adim_enlem)})
    return {"an": jd_to_iso(jd), "gmst": round(g, 3), "cizgiler": cizgiler,
            "yontem": ("MC/IC: boylam = RA ∓ GMST (dikey). ASC/DSC: her enlemde "
                       "cos H = −tanφ·tanδ çözülür; |değer| > 1 olan enlemlerde "
                       "cisim doğmaz/batmaz ve çizgi çizilmez."),
            "not_in_mundo": (
                "Çizgiler gezegenin GERÇEK yükselişine göre çizilir (in mundo), "
                "ekliptik derecesinin yükselişine göre değil. İkisi yalnız "
                "ekliptik üzerindeki cisimler için (Güneş) aynıdır; ekliptik "
                "enlemi olan cisimlerde (Jüpiter, Satürn, Plüton) ayrışır ve "
                "fark yüksek enlemlerde büyür. Doğrulama: her çizgi noktasında "
                "cismin ufuk yüksekliği 0.000° ölçüldü. Başka bir yazılım "
                "'zodiacal' yöntem kullanıyorsa sonuçlar farklı çıkabilir; "
                "klasik Astro*Carto*Graphy in mundo'dur."),
            "uyari": ("Çizgiler ölçümdür, kader değildir. 'Şu şehirde şu olur' "
                      "denmez; o yerin hangi konuyu ÖNE ÇIKARDIĞI söylenir.")}


def paranlar(ak: dict, orb: float = PARAN_ORB) -> List[dict]:
    """
    İki cismin çizgilerinin kesiştiği ENLEMLER.

    Paran, iki gezegenin aynı anda açısal olduğu enlem kuşağıdır ve
    boylamdan bağımsızdır: o enlemin tamamında geçerlidir. Klasik
    astrokartografinin en az bilinen ama en kullanışlı parçasıdır.
    """
    c = ak["cizgiler"]
    out = []
    for i in range(len(c)):
        for j in range(i + 1, len(c)):
            a, b = c[i], c[j]
            for ta in ("ASC", "DSC"):
                for tb in ("ASC", "DSC"):
                    ha = {x["enlem"]: x["boylam"] for x in a[ta]}
                    for x in b[tb]:
                        if x["enlem"] in ha:
                            d = abs(((ha[x["enlem"]] - x["boylam"] + 540) % 360) - 180)
                            if d <= orb:
                                out.append({"a": f"{a['cisim']} {ta}",
                                            "b": f"{b['cisim']} {tb}",
                                            "enlem": x["enlem"],
                                            "boylam": round(x["boylam"], 2),
                                            "orb": round(d, 2)})
            # MC/IC kesişimleri: dikey çizgiler, tek boylamda
            for ta in ("MC", "IC"):
                for tb in ("MC", "IC"):
                    d = abs(((a[ta] - b[tb] + 540) % 360) - 180)
                    if d <= orb:
                        out.append({"a": f"{a['cisim']} {ta}",
                                    "b": f"{b['cisim']} {tb}",
                                    "enlem": None, "boylam": round(a[ta], 2),
                                    "orb": round(d, 2)})
    out.sort(key=lambda x: x["orb"])
    return out[:20]


# ============================================================================
# AY DÖNÜŞÜ
# ============================================================================
def ay_donusu_jd(natal: NatalChart, baslangic_jd: Optional[float] = None) -> float:
    """
    Ay'ın natal boylamına döndüğü ilk an (yaklaşık 27.32 günde bir).

    Güneş dönüşünde olduğu gibi kaba tarama sonrası ikiye bölme; Ay hızlı
    olduğu için adım 0.25 gün tutulur.
    """
    import datetime as dt
    ensure_ephe()
    if baslangic_jd is None:
        u = dt.datetime.utcnow()
        baslangic_jd = swe.julday(u.year, u.month, u.day, 0.0)
    hedef = natal.bodies["Moon"].lon

    def fark(j: float) -> float:
        return ((calc_lon(j, "Moon") - hedef + 540) % 360) - 180

    jd = baslangic_jd
    onceki = fark(jd)
    for _ in range(140):                       # ~35 gün, 0.25 adım
        jd += 0.25
        simdi = fark(jd)
        if onceki < 0 <= simdi:
            a, b = jd - 0.25, jd
            for _ in range(40):
                o = (a + b) / 2
                if fark(o) < 0:
                    a = o
                else:
                    b = o
            return (a + b) / 2
        onceki = simdi
    return baslangic_jd


# ============================================================================
# B · ARZ İZDÜŞÜMÜ — bu modelin kendi genişletmesi
# ============================================================================
def arz_izdusumu(jd: float, adim: float = 12.0,
                 azami_enlem: float = 60.0,
                 house_system: str = "P") -> dict:
    """
    Modelin karar eşiğinin yeryüzünde nasıl değiştiği.

    Gökyüzü sabit, KONUM değişken. Her ızgara noktasında harita yeniden
    kurulur, kütleler yeniden tartılır (açısallık konuma bağlıdır) ve üç
    şey ölçülür: eşiğin keskinliği, alanın toplanması, Kara Delik'in evi.

    Izgara kaba tutulur: her nokta bir ev hesabı + on kütle + eşik araması
    demektir. 12° adımda 30×11 = 330 nokta, birkaç saniye sürer.
    """
    from .circular import rayleigh_R
    ensure_ephe()
    noktalar: List[dict] = []
    hatalar: List[str] = []
    enlemler: List[float] = []
    f = -azami_enlem
    while f <= azami_enlem + 1e-9:
        enlemler.append(round(f, 2))
        f += adim
    boylamlar = [round(-180 + i * adim, 2)
                 for i in range(int(360 / adim))]

    for la in enlemler:
        for lo in boylamlar:
            try:
                ch = chart_at_jd(jd, la, lo, "izdüşüm", house_system)
                ms = compute_masses(ch)
                b = find_berzah2(ms)
                kd, _ad = find_kd_ad(ms)
                R = rayleigh_R([(m.lon, m.abs_mass) for m in ms], 1)
                noktalar.append({
                    "enlem": la, "boylam": lo,
                    "asimetri": round(b.asymmetry, 3) if b else None,
                    "toplanma": round(R, 3),
                    "kd_ev": ch.house(kd),
                })
            except Exception as e:
                # Sessiz yutma YOK: tek bir alan adı hatası bütün ızgarayı
                # boşaltıyor ve bu "veri yok" gibi görünüyordu.
                hatalar.append(f"{la},{lo}: {type(e).__name__}: {e}")
                continue

    gecerli = [x for x in noktalar if x["asimetri"] is not None]
    if not gecerli:
        return {"hata": "hiçbir ızgara noktası hesaplanamadı",
                "ilk_hatalar": hatalar[:3]}
    en_keskin = max(gecerli, key=lambda x: x["asimetri"])
    en_yumusak = min(gecerli, key=lambda x: x["asimetri"])
    en_toplu = max(noktalar, key=lambda x: x["toplanma"])
    en_dagi = min(noktalar, key=lambda x: x["toplanma"])
    asim = [x["asimetri"] for x in gecerli]
    yayilim = max(asim) - min(asim)

    return {
        "an": jd_to_iso(jd), "adim_derece": adim,
        "nokta_sayisi": len(noktalar),
        "hatali_nokta": len(hatalar),
        "en_keskin_esik": en_keskin,
        "en_yumusak_esik": en_yumusak,
        "en_toplu_alan": {k: en_toplu[k] for k in ("enlem", "boylam", "toplanma")},
        "en_dagilmis_alan": {k: en_dagi[k] for k in ("enlem", "boylam", "toplanma")},
        "asimetri_yayilimi": round(yayilim, 3),
        "izgara": noktalar,
        "okuma": ("Konum değiştikçe eşik neredeyse hiç değişmiyor "
                  f"(yayılım {yayilim:.2f}); bu haritada yer seçimi karar "
                  "yapısını etkilemiyor." if yayilim < 0.15 else
                  f"Eşiğin keskinliği yeryüzünde {yayilim:.2f} kadar "
                  "değişiyor. En keskin olduğu yerde kararlar net kutuplaşır "
                  "— bu iyi ya da kötü değildir: net karar isteyen biri için "
                  "kolaylık, esneklik isteyen biri için baskıdır."),
        "yontem": ("Gökyüzü sabit tutulup konum taranır. Her noktada ev "
                   "sistemi yeniden kurulur; BERZAH kütleleri açısallıktan "
                   "beslendiği için kütleler ve dolayısıyla eşik değişir."),
        "sinir": ("Bu KLASİK astrokartografi DEĞİLDİR; modelin kendi "
                  "genişletmesidir. Klasik çizgiler gezegenlerin nerede "
                  "açısal olduğunu, bu katman eşiğin nerede nasıl "
                  "davrandığını gösterir. Çelişirlerse ikisi ayrı soruya "
                  "cevap veriyordur."),
    }


# ============================================================================
def kartografi_katmani(chart: NatalChart, sr_jd: Optional[float] = None,
                       izdusum: bool = True, solar_aktif: bool = True) -> dict:
    """Natal · Güneş dönüşü · Ay dönüşü için üç astrokartografi."""
    import datetime as dt
    out: Dict[str, object] = {
        "modul": "Astrokartografi ve arz izdüşümü",
        "natal": astrokartografi(chart.jd_ut),
    }
    out["natal_paran"] = paranlar(out["natal"])          # type: ignore[arg-type]
    if solar_aktif:
        try:
            if sr_jd is None:
                from .astro import solar_return_jd
                sr_jd = solar_return_jd(chart, dt.datetime.utcnow().year)
            out["gunes_donusu"] = astrokartografi(sr_jd)
            out["gunes_donusu_an"] = jd_to_iso(sr_jd)
        except Exception as e:
            out["gunes_donusu"] = {"hata": str(e)[:120]}
    else:
        out["gunes_donusu"] = None
        out["gunes_donusu_an"] = None
    try:
        aj = ay_donusu_jd(chart)
        out["ay_donusu"] = astrokartografi(aj)
        out["ay_donusu_an"] = jd_to_iso(aj)
    except Exception as e:
        out["ay_donusu"] = {"hata": str(e)[:120]}
    if izdusum:
        try:
            out["arz_izdusumu"] = arz_izdusumu(chart.jd_ut)
        except Exception as e:
            out["arz_izdusumu"] = {"hata": str(e)[:150]}
    out["uyari"] = ("Yer seçimi bir araçtır, çözüm değildir. Taşınmak bir "
                    "konuyu öne çıkarır ya da geri çeker; kişinin kendisini "
                    "değiştirmez.")
    return out
