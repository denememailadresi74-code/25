#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KADİM KATMAN — İsim Tecellîsi · Kadim Arap–Osmanlı Teknikleri Laboratuvarı ·
Hüviyet Mührü (sentez). Astro Pro v9.2.4 CELL 2.13 / 2.28 / 2.18'den ayrıştırıldı.
Etik ilke (kaynak hücreyle aynı): ömür/ölüm tarihi, tıbbî teşhis, kesin kader
veya büyü garantisi ÜRETİLMEZ. Hyleg yalnız aday tespiti yapar.
"""
from __future__ import annotations
import math
import datetime as dt
from typing import Dict, List, Optional

import swisseph as swe

from .astro import (NatalChart, BODY_IDS, CORE10, EPHFLAG, TR_NAME,
                    jd_to_iso, calc_lon, calc_lonspeed)
from .circular import (norm360, sep, sign_of, deg_in_sign, fmt_lon, SIGNS,
                       ELEMENT, RULER, ebced_detail,
                       circular_mean_weighted)
from .modules_deneme import NURANI_W, mizan, vahdet, _aspects_to


# ============================================================================
# İSİM TECELLÎSİ — ebced × astroloji köprüsü  (CELL 2.13)
# ============================================================================
def isim_tecellisi(ch: NatalChart, isim: str, anne: Optional[str] = None,
                   mz: Optional[dict] = None, vh: Optional[dict] = None) -> dict:
    full = isim + ((" " + anne) if anne else "")
    eb = ebced_detail(full)
    th = eb["isim_derecesi"]
    # Mizan alanındaki konum — hazır verilmişse yeniden hesaplanmaz
    mz = mz or mizan(ch)
    # NOT: key vermeden min() kullanılırsa mesafeler eşitlendiğinde Python
    # ikinci öğeyi (dict) karşılaştırmaya çalışır ve TypeError atar.
    near_sekine = min(((sep(th, s["lon"]), s) for s in mz["sekineler"]),
                      key=lambda x: x[0], default=(999.0, None))
    near_berzah = min(((sep(th, b["lon"]), b) for b in mz["berzahlar"]),
                      key=lambda x: x[0], default=(999.0, None))
    if near_sekine[0] < 8:
        konum_mizan = f"Sekîne'ye yaslı ({near_sekine[1]['konum']}) — isim, makamla hizalı"
    elif near_berzah[0] < 8:
        konum_mizan = f"Berzah eşiğinde ({near_berzah[1]['konum']}) — isim, geçit görevlisi"
    else:
        konum_mizan = "alan boşluğunda — isim bir ÇAĞRIDIR, sahibini o dereceye çeker"
    # Vahdet hizası — hazır verilmişse yeniden hesaplanmaz
    vh = vh or vahdet(ch)
    v_lon = (vh["vahdet_noktasi"] or {}).get("lon")
    hiza = round(sep(th, v_lon), 1) if v_lon is not None else None
    # İsim progresyonu: θ_E + 1°/yıl → natal gezegen temasları
    prog = []
    birth_year = swe.revjul(ch.jd_ut)[0]
    for k in CORE10:
        d = (ch.bodies[k].lon - th) % 360.0
        yil = birth_year + d
        if yil <= birth_year + 96:
            prog.append({"yas": round(d, 1), "yil": int(yil),
                         "temas": TR_NAME[k],
                         "konum": fmt_lon(ch.bodies[k].lon)})
    prog.sort(key=lambda p: p["yas"])
    return {"modul": "İsim Tecellîsi (ebced köprüsü)",
            "ebced": eb,
            "isim_derecesi": {"lon": round(th, 2), "konum": fmt_lon(th),
                              "ev": ch.house(th)},
            "mizan_konumu": konum_mizan,
            "vahdet_hizasi_derece": hiza,
            "acilar": _aspects_to(th, ch, limit=6),
            "isim_progresyonu": prog[:10],
            "yontem": "θ_E = ebced(isim[+anne]) mod 360; 1°/yıl progresyon."}


# ============================================================================
# KADİM ARAP–OSMANLI LABORATUVARI  (CELL 2.28)
# ============================================================================
_TERMS_EGYPT = {  # Mısır hudûdu: (üst sınır derece, yönetici)
    "Koç": [(6, "Jupiter"), (12, "Venus"), (20, "Mercury"), (25, "Mars"), (30, "Saturn")],
    "Boğa": [(8, "Venus"), (14, "Mercury"), (22, "Jupiter"), (27, "Saturn"), (30, "Mars")],
    "İkizler": [(6, "Mercury"), (12, "Jupiter"), (17, "Venus"), (24, "Mars"), (30, "Saturn")],
    "Yengeç": [(7, "Mars"), (13, "Venus"), (19, "Mercury"), (26, "Jupiter"), (30, "Saturn")],
    "Aslan": [(6, "Jupiter"), (11, "Venus"), (18, "Saturn"), (24, "Mercury"), (30, "Mars")],
    "Başak": [(7, "Mercury"), (17, "Venus"), (21, "Jupiter"), (28, "Mars"), (30, "Saturn")],
    "Terazi": [(6, "Saturn"), (14, "Mercury"), (21, "Jupiter"), (28, "Venus"), (30, "Mars")],
    "Akrep": [(7, "Mars"), (11, "Venus"), (19, "Mercury"), (24, "Jupiter"), (30, "Saturn")],
    "Yay": [(12, "Jupiter"), (17, "Venus"), (21, "Mercury"), (26, "Saturn"), (30, "Mars")],
    "Oğlak": [(7, "Mercury"), (14, "Jupiter"), (22, "Venus"), (26, "Saturn"), (30, "Mars")],
    "Kova": [(7, "Mercury"), (13, "Venus"), (20, "Jupiter"), (25, "Mars"), (30, "Saturn")],
    "Balık": [(12, "Venus"), (16, "Jupiter"), (19, "Mercury"), (28, "Mars"), (30, "Saturn")],
}
_TRIPL_DOROTHEUS = {  # unsur: (gündüz, gece, ortak)
    "Ateş": ("Sun", "Jupiter", "Saturn"), "Toprak": ("Venus", "Moon", "Mars"),
    "Hava": ("Saturn", "Mercury", "Jupiter"), "Su": ("Venus", "Mars", "Moon")}


def _term_lord(lon: float) -> str:
    s = sign_of(lon); d = deg_in_sign(lon)
    for ub, lord in _TERMS_EGYPT[s]:
        if d < ub: return lord
    return _TERMS_EGYPT[s][-1][1]


def _is_day_chart(ch: NatalChart) -> bool:
    # Güneş ufkun üstünde mi: ev 7-12 arası gündüz
    h = ch.house(ch.bodies["Sun"].lon) or 1
    return h in (7, 8, 9, 10, 11, 12)


def kadim_lab(ch: NatalChart, tasyir_years: int = 90) -> dict:
    day = _is_day_chart(ch)

    # --- Hyleg (etik: yalnız aday; alcocoden/ömür HESAPLANMAZ) ---
    hyleg_order = (["Sun", "Moon"] if day else ["Moon", "Sun"]) + ["Asc"]
    hyleg = None
    for cand in hyleg_order:
        lon = ch.asc if cand == "Asc" else ch.bodies[cand].lon
        h = ch.house(lon) or 0
        if h in (1, 7, 9, 10, 11):
            hyleg = {"aday": TR_NAME.get(cand, "Yükselen"),
                     "konum": fmt_lon(lon), "ev": h}
            break
    if hyleg is None:
        hyleg = {"aday": "Yükselen", "konum": fmt_lon(ch.asc), "ev": 1}
    kadkhudah = {"hudud_sahibi": TR_NAME.get(_term_lord(
        ch.asc if hyleg["aday"] == "Yükselen"
        else ch.bodies["Sun" if hyleg["aday"] == "Güneş" else "Moon"].lon))}

    # --- Tasyîr (sembolik 1°/yıl yönlendirme: ASC ve MC → vaad ediciler) ---
    birth_year = swe.revjul(ch.jd_ut)[0]
    tasyir = []
    for anchor_name, anchor in (("ASC", ch.asc), ("MC", ch.mc)):
        for k in CORE10:
            d = (ch.bodies[k].lon - anchor) % 360.0
            if d <= tasyir_years:
                tasyir.append({"yonlendirilen": anchor_name,
                               "vaad_edici": TR_NAME[k],
                               "yas": round(d, 1), "yil": int(birth_year + d)})
    tasyir.sort(key=lambda t: t["yas"])

    # --- Kırân-ı Ekber (Jüpiter–Satürn büyük kavuşumu — GERÇEK efemeris taraması) ---
    jd_now = swe.julday(*dt.datetime.utcnow().timetuple()[:3], 0.0)

    def _js_phase(jd: float) -> float:
        return ((calc_lon(jd, "Jupiter") - calc_lon(jd, "Saturn") + 180.0) % 360.0) - 180.0

    phase0 = _js_phase(jd_now)
    prev_jd, prev_ph = jd_now, phase0
    conj_jd = None
    for k in range(1, 900):                     # 10 günlük adımlarla ~24 yıl
        jd = jd_now + k * 10.0
        ph = _js_phase(jd)
        if prev_ph < 0 <= ph and abs(ph - prev_ph) < 90:   # yalnız 0-geçişi = kavuşum (±180 sarımı değil)
            lo, hi = prev_jd, jd
            for _ in range(60):                 # ikiye bölme rafine
                mid = (lo + hi) / 2
                if _js_phase(mid) < 0: lo = mid
                else: hi = mid
            conj_jd = (lo + hi) / 2
            break
        prev_jd, prev_ph = jd, ph
    if conj_jd is not None:
        conj_lon = calc_lon(conj_jd, "Jupiter")
        kiran_ekber = {"anlik_faz": round(norm360(phase0), 1),
                       "cevrim": "~20 yıl (mülk devri) · ~200 yıl unsur devri · ~800 yıl büyük devir",
                       "siradaki_kavusum": jd_to_iso(conj_jd)[:10],
                       "siradaki_kavusum_burcu": sign_of(conj_lon),
                       "siradaki_kavusum_konum": fmt_lon(conj_lon),
                       "unsur_devri": ELEMENT[sign_of(conj_lon)],
                       "sahsi_ev": ch.house(conj_lon),
                       "not": "Sıradaki kırân senin bu evinde vuruyor — devrin sana değdiği kapı."}
    else:
        kiran_ekber = {"anlik_faz": round(norm360(phase0), 1), "hata": "kavuşum ufukta bulunamadı"}

    # --- Mütellet (triplicity) + Hudûd sahipleri (ışıklar ve ASC) ---
    hudud = []
    for label, lon in (("Güneş", ch.bodies["Sun"].lon),
                       ("Ay", ch.bodies["Moon"].lon), ("ASC", ch.asc)):
        el = ELEMENT[sign_of(lon)]
        d_, n_, p_ = _TRIPL_DOROTHEUS[el]
        hudud.append({"nokta": label, "konum": fmt_lon(lon),
                      "hudud_sahibi": TR_NAME.get(_term_lord(lon)),
                      "mutellet": {"gunduz": TR_NAME[d_], "gece": TR_NAME[n_],
                                   "ortak": TR_NAME[p_],
                                   "aktif": TR_NAME[d_ if day else n_]}})

    # --- İhtiyârât (önümüzdeki 30 gün seçim kalitesi — Ay durumu) ---
    iht = []
    for d in range(30):
        jd = jd_now + d
        ml, msp = calc_lonspeed(jd, "Moon")
        su = calc_lon(jd, "Sun")
        score = 0.0; tags = []
        s = sign_of(ml)
        if s in ("Boğa", "Yengeç"): score += 2; tags.append("Ay güçlü burçta")
        if s in ("Akrep", "Oğlak"): score -= 2; tags.append("Ay zararda/düşükte")
        elong = sep(ml, norm360(su))
        if elong < 12: score -= 2; tags.append("muhâk — Ay yanık")
        if 90 < norm360(ml - su) < 180 or 270 < norm360(ml - su) < 360:
            pass
        if msp > 13.5: score += 1; tags.append("Ay hızlı")
        if score >= 2:
            iht.append({"tarih": jd_to_iso(jd)[:10], "kalite": "SA'D (uğurlu)",
                        "sebep": tags})
        elif score <= -2:
            iht.append({"tarih": jd_to_iso(jd)[:10], "kalite": "NAHS (kaçın)",
                        "sebep": tags})
    return {"modul": "Kadim Arap–Osmanlı Teknikleri Laboratuvarı",
            "etik_ilke": ("Bu katman ömür/ölüm tarihi, tıbbî teşhis, kesin kader "
                          "veya büyü garantisi üretmez; Hyleg yalnız adaydır."),
            "hyleg": hyleg, "kadkhudah_hudud": kadkhudah,
            "tasyir": tasyir[:12],
            "kiran_i_ekber": kiran_ekber,
            "hudud_ve_mutellet": hudud,
            "ihtiyarat_30gun": iht}


# ============================================================================
# HÜVİYET MÜHRÜ — sentez  (CELL 2.18)
#   Bütünlük = f(R, λ₂, ayna simetrisi, kalp-küll, KRN uyumu)
#   Gerilim  = f(kalp-küll açığı, düşey eğim, asimetri)
# ============================================================================
def huviyet_muhru(ch: NatalChart, deneme: dict, v2: dict) -> dict:
    R = deneme["vahdet"]["R_indeksi"]
    lam2 = deneme["asabiyye"]["asabiyye_lambda2"]
    sym = deneme["ayna_ekseni"]["simetri_skoru"]
    gap = deneme["suveyda"]["kalp_kull_farki"] or 0.0
    krn_s = deneme["krn"]["skor"] / 100.0
    tilt = abs(deneme["ars_ekseni"]["egim_derece"])
    asym = (v2.get("berzah") or {}).get("asimetri", 1.0)

    butunluk = round(100 * (0.25 * R + 0.20 * min(lam2 / 1.5, 1)
                            + 0.20 * sym + 0.20 * max(0, 1 - gap / 60)
                            + 0.15 * krn_s), 0)
    gerilim = round(100 * (0.35 * min(gap / 60, 1) + 0.25 * min(tilt / 3, 1)
                           + 0.40 * min(max(asym - 1, 0) / 4, 1)), 0)

    # Mühür pencereleri: takvim çakışmaları (Sahib-Kırân zaten hesapladı)
    muhur_pencereleri = deneme["sahib_kiran"]["pencereler"][:4]

    kimlik = ("MÜTTEHİD (bütünleşik) mühür" if butunluk >= 70 and gerilim < 40 else
              "MÜCÂHİD (gerilimle bilenen) mühür" if gerilim >= 55 else
              "MÜTEREDDİD (eşikte duran) mühür")
    return {"modul": "Hüviyet Mührü (sentez)",
            "butunluk_endeksi": butunluk, "gerilim_endeksi": gerilim,
            "muhur_kimligi": kimlik,
            "bilesenler": {"R": R, "lambda2": lam2, "ayna_simetri": sym,
                           "kalp_kull": gap, "KRN": deneme["krn"]["skor"],
                           "dusey_egim": tilt, "berzah_asimetri": asym},
            "muhur_pencereleri": muhur_pencereleri,
            "yontem": "On tekniğin ortak imzası: toparlanma + dayanışma + simetri "
                      "+ kalp-küll yakınlığı + KRN uyumu ↔ açık + eğim + asimetri."}
