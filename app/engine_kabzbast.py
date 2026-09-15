#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modül 66–74 — BERZAH v1 (Kabz/Bast Uzay-Zaman Modeli) JSON adaptörü.
Motor, Astro Pro v9.2.4'ten AYNEN taşınan app/kabzbast_v1.py'dir (icat korunur):
  66 Kabz/Bast alanı · 67 Kabz/Bast ekseni (Σκ·m) · 68 Einstein–Rosen köprüleri
  69 Olay Ufku/Boğaz · 70 Kuramoto C · 71 528 Hz imza · 72 LQC ρ/ρc
  73 Kuantum Sıçrama takvimi · 74 Tayy-i Mekân geçit pencereleri
Geçit skoru (v9.2 ile aynı): S = 0.45·bounce + 0.30·C + 0.25·(ρ/ρc)
"""
from __future__ import annotations
import datetime as dt
from typing import Optional

import swisseph as swe

from . import kabzbast_v1 as kb
from .astro import NatalChart, jd_to_iso
from .circular import sep


def _chart_v1(nc: NatalChart) -> "kb.Chart":
    return kb.build_chart(nc.jd_ut, nc.lat, nc.lng, nc.label)


def run_kabzbast(nc: NatalChart, days: int = 365,
                 from_jd: Optional[float] = None,
                 sr_year: Optional[int] = None) -> dict:
    natal = _chart_v1(nc)
    j0 = from_jd if from_jd is not None else swe.julday(
        *dt.datetime.utcnow().timetuple()[:3], 0.0)

    # 66-67 — eğrilik alanı + net eksen
    bodies = []
    for b in sorted(natal.bodies.values(), key=lambda x: x.kappa):
        bodies.append({"cisim": b.name, "konum": kb.dms(b.lon), "ev": b.house,
                       "kappa": round(b.kappa, 3), "kutle": round(b.mass, 2),
                       "durum": list(b.state)})
    net = sum(b.kappa * b.mass for b in natal.bodies.values())
    eksen = {"net_egrilik": round(net, 3),
             "kutup": "KABZ (kara delik yönlü — içe çöken)" if net < 0
                      else "BAST (ak delik yönlü — dışa yayan)"}

    # 68 — Einstein–Rosen köprüleri
    bridges = []
    for i, br in enumerate(kb.find_berzah(natal), 1):
        bridges.append({"sira": i, "kabz": br.kabz, "bast": br.bast,
                        "aci": round(br.angle, 2), "guc": round(br.strength, 3),
                        "tip": br.kind,
                        "cumle": f"'{br.kabz}' alanında sıkışan yük, "
                                 f"'{br.bast}' kapısından tahliye olur."})

    # 69 — ufuk/boğaz olayları
    horizon = [{"cisim": b.name, "konum": kb.dms(b.lon), "isaret": list(b.state)}
               for b in natal.bodies.values() if b.state]

    # 70+72 — anlık C, ρ/ρc
    ph = kb.cycle_phases(natal, j0)
    C, psi = kb.coherence(ph)
    rc = kb.critical_density(natal)
    x, H = kb.hubble(kb.density(natal, j0), rc)
    bounce_now = kb.bounce_index(ph)
    passage_now = 0.45 * bounce_now + 0.30 * C + 0.25 * x

    # 71 — 528 Hz harmonik imza
    hs = kb.harmonic_signature(natal)
    imza = {"kok_ton": hs["root"], "kok_hz": round(hs["root_hz"], 2),
            "puruzluluk": round(hs["dissonance"], 4),
            "frekanslar": {n: round(f, 2) for n, f in hs["freqs"].items()},
            "en_puruzlu": [{"cift": f"{a}–{b}", "sent": round(c, 1),
                            "puruz": round(r, 4)}
                           for a, b, c, r in hs["intervals"][:3]]}

    # 73-74 — sıçrama takvimi + geçit pencereleri
    _rows, peaks = kb.bounce_calendar(natal, j0, days)
    windows = []
    for r in peaks:
        S = 0.45 * r["bounce"] + 0.30 * r["C"] + 0.25 * r["x"]
        tag = ("★ TAM SIÇRAMA — döngüler hizalı"
               if r["bounce"] > .82 and r["C"] > .70 else
               "GEÇİT (Tayy-i Mekân) penceresi"
               if r["C"] > .50 or r["bounce"] > .70 else "kısmi hizalanma")
        if r["x"] > 0.92: tag += " ⚠ ρ→ρc geri sekme"
        windows.append({"tarih": jd_to_iso(r["jd"])[:10],
                        "gecit_skoru": round(S, 4), "C": round(r["C"], 3),
                        "sicrama": round(r["bounce"], 3),
                        "rho_orani": round(r["x"], 3), "not": tag})

    # Lunasyon üst katmanı (boğazda sıçrama = tutulma)
    lun = []
    for j, nm, lo, ec in kb.lunations(j0, min(days, 200)):
        hit = None
        for b in natal.bodies.values():
            if kb.sep(lo, b.lon) < 3.0 and abs(b.kappa) > .25:
                hit = f"natal {b.name} (κ={b.kappa:+.2f})"; break
        if hit or ec:
            lun.append({"tarih": jd_to_iso(j)[:10], "faz": nm,
                        "konum": kb.dms(lo), "tutulma": bool(ec),
                        "temas": hit})

    out = {
        "motor": "BERZAH MODELİ v1.0 (Astro Pro v9.2.4'ten aynen)",
        "not": ("'Kara delik', 'Einstein–Rosen', 'LQC', '528 Hz' ifadeleri "
                "modelin sembolik/biçimsel terminolojisidir; fiziksel "
                "nedensellik iddiası değildir."),
        "m66_67_kabz_bast": {"alan": bodies, "eksen": eksen},
        "m68_einstein_rosen": bridges,
        "m69_ufuk_bogaz": horizon,
        "m70_kuramoto": {"C": round(C, 3), "psi": round(psi, 3)},
        "m71_528hz": imza,
        "m72_lqc": {"rho_orani": round(x, 3), "H": round(H, 3),
                    "durum": "⚠ SIÇRAMA EŞİĞİ" if x > 0.9
                             else "sıkışma" if x > 0.5 else "genişleme"},
        "m73_anlik_sicrama": round(bounce_now, 3),
        "m74_gecit": {"anlik_gecit_skoru": round(passage_now, 4),
                      "pencereler": windows},
        "lunasyon_katmani": lun,
    }

    # Solar Return delta-eğrilik (köprü yılı testi)
    if sr_year:
        sr = kb.solar_return(natal, sr_year, nc.lat, nc.lng)
        dk = (sum(b.kappa * b.mass for b in sr.bodies.values())
              - sum(b.kappa * b.mass for b in natal.bodies.values()))
        bridge_year = any(
            sep(sr.asc, natal.bodies[br.bast].lon) < 5
            or sep(sr.asc, natal.bodies[br.kabz].lon) < 5
            for br in kb.find_berzah(natal, top=3))
        out["solar_return"] = {
            "yil": sr_year, "an": jd_to_iso(sr.jd),
            "delta_egrilik": round(dk, 3),
            "yon": "KABZ yönünde (inşa/sıkıştırma)" if dk < 0
                   else "BAST yönünde (tahliye/yayılma)",
            "kopru_yili": bridge_year}
    return out
