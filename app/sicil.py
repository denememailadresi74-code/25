#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SİCİL — ZÎC'in kendi anonim danışan havuzundan ham referans biriktirir.

Sentetik referans geliştirme için gereklidir ama gerçek danışan havuzunun dağılımı
farklı olabilir. SİCİL her gerçek analizde yalnız MİZAN/ŞAHİT ham ölçülerini ve
zaman damgasını saklar. Kişi adı, doğum tarihi, koordinat ve yorum metni tutulmaz.

Yeterli kayıt birikince yönetici açıkça ``referans-kur`` çağrısı yapabilir.
Otomatik devreye alma yoktur; referansı sessizce değiştirmek, ölçümdeki en
tehlikeli sessiz hatalardan biridir.
"""
from __future__ import annotations

import json
import math
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from . import depo

ASGARI = 60
AZAMI = 5000


def _sayi(v: Any, d: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def kayit_cikar(analiz: Dict[str, Any]) -> Dict[str, Any]:
    from .oruntu_omurgasi import oruntu_omurgasi
    from .tanik import ham_mercekler
    om = oruntu_omurgasi(analiz, kalibre=False)
    sh = ham_mercekler(analiz)
    return {
        "ts": round(time.time(), 3),
        "mizan": {str(x.get("kod")): _sayi(x.get("ham_puan")) for x in om.get("eksenler", []) if x.get("kod")},
        "sahit": {k: {"belirginlik": _sayi(v.get("ham_belirginlik")), "gerilim": _sayi(v.get("ham_gerilim"))}
                  for k, v in sh.items()},
    }


def kaydet(analiz: Dict[str, Any]) -> Dict[str, Any]:
    kayit = kayit_cikar(analiz)
    depo.json_kayit_ekle("sicil", kayit, AZAMI)
    return kayit


def _quantile(xs: List[float], q: float) -> float:
    s = sorted(xs)
    if not s:
        return 0.0
    if len(s) == 1:
        return float(s[0])
    p = q * (len(s) - 1)
    a, b = int(math.floor(p)), int(math.ceil(p))
    if a == b:
        return float(s[a])
    return float(s[a] + (s[b] - s[a]) * (p - a))


def _qtablo(xs: List[float]) -> List[Dict[str, float]]:
    return [{"q": i / 100, "v": round(_quantile(xs, i / 100), 6)} for i in range(0, 101, 2)]


def _yuzdelik(ham: float, noktalar: List[Dict[str, float]]) -> float:
    pts = sorted((float(x["q"]), float(x["v"])) for x in noktalar if "q" in x and "v" in x)
    if not pts:
        return max(0.0, min(100.0, ham))
    es = [q for q, v in pts if abs(v - ham) < 1e-9]
    if es:
        return sum(es) / len(es) * 100
    if ham < pts[0][1]:
        return pts[0][0] * 100
    if ham > pts[-1][1]:
        return pts[-1][0] * 100
    for (q0, v0), (q1, v1) in zip(pts, pts[1:]):
        if v0 <= ham <= v1:
            q = (q0 + q1) / 2 if abs(v1 - v0) < 1e-12 else q0 + (ham - v0) / (v1 - v0) * (q1 - q0)
            return q * 100
    return 50.0


def _ayar_taban(raw: List[float], qtab: List[Dict[str, float]]) -> Tuple[Dict[str, Any], List[float]]:
    ys = [round(_yuzdelik(x, qtab), 2) for x in raw]
    n = max(1, len(ys))
    return ({
        "n": len(ys), "ortalama": round(statistics.mean(ys), 4),
        "le20": round(sum(1 for x in ys if x <= 20) / n * 100, 4),
        "ge80": round(sum(1 for x in ys if x >= 80) / n * 100, 4),
    }, ys)


def _hamlar(kayitlar: List[Dict[str, Any]]) -> Tuple[Dict[str, List[float]], Dict[str, Dict[str, List[float]]]]:
    m: Dict[str, List[float]] = {}
    s: Dict[str, Dict[str, List[float]]] = {}
    for k in kayitlar:
        for kod, v in (k.get("mizan") or {}).items():
            m.setdefault(str(kod), []).append(_sayi(v))
        for kod, v in (k.get("sahit") or {}).items():
            s.setdefault(str(kod), {"belirginlik": [], "gerilim": []})["belirginlik"].append(_sayi((v or {}).get("belirginlik")))
            s.setdefault(str(kod), {"belirginlik": [], "gerilim": []})["gerilim"].append(_sayi((v or {}).get("gerilim")))
    return m, s


def referans_verisi(kayitlar: List[Dict[str, Any]] | None = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    ks = list(kayitlar) if kayitlar is not None else depo.json_kayit_liste("sicil", AZAMI)
    if len(ks) < ASGARI:
        raise ValueError(f"SİCİL referansı için en az {ASGARI} kayıt gerekir; bulunan={len(ks)}")
    mham, sham = _hamlar(ks)
    tarih = datetime.now(timezone.utc).isoformat()
    mref: Dict[str, Any] = {"surum": 4, "n": len(ks), "ornek_sayisi": len(ks), "kaynak": "sicil", "uretim_tarihi": tarih, "eksenler": {}}
    for kod, raw in mham.items():
        qt = _qtablo(raw)
        tab, y = _ayar_taban(raw, qt)
        mref["eksenler"][kod] = {"quantiles": qt, "min": min(raw), "max": max(raw), "ortalama": statistics.mean(raw),
                                   "ayar_taban": tab, "ayar_ornek": y}
    sref: Dict[str, Any] = {"surum": 3, "n": len(ks), "ornek_sayisi": len(ks), "kaynak": "sicil", "uretim_tarihi": tarih, "mercekler": {}}
    for kod, raw in sham.items():
        bel = raw["belirginlik"]
        qt = _qtablo(bel)
        tab, y = _ayar_taban(bel, qt)
        sref["mercekler"][kod] = {"quantiles": qt, "gerilim_q75": round(_quantile(raw["gerilim"], .75), 6),
                                    "ortalama_ham": round(statistics.mean(bel), 6),
                                    "gerilim_ortalama": round(statistics.mean(raw["gerilim"]), 6),
                                    "ayar_taban": tab, "ayar_ornek": y}
    return mref, sref


def referans_kur() -> Dict[str, Any]:
    ks = depo.json_kayit_liste("sicil", AZAMI)
    mref, sref = referans_verisi(ks)
    depo.referans_yolu("mizan").write_text(json.dumps(mref, ensure_ascii=False, indent=2), encoding="utf-8")
    depo.referans_yolu("sahit").write_text(json.dumps(sref, ensure_ascii=False, indent=2), encoding="utf-8")
    from . import ayar
    from .oruntu_omurgasi import referans_sifirla as m_sifirla
    from .tanik import referans_sifirla as s_sifirla
    m_sifirla(); s_sifirla(); ayar.sifirla()
    depo.meta_yaz("sicil_son_referans", {"ts": time.time(), "ornek_sayisi": len(ks), "kaynak": "sicil"})
    return {"ok": True, "kaynak": "sicil", "ornek_sayisi": len(ks), "uretim_tarihi": mref["uretim_tarihi"],
            "uyari": "Sicil danışman havuzudur; genel nüfus değildir. Havuz taraflıysa referans da taraflıdır."}


def ozet() -> Dict[str, Any]:
    ks = depo.json_kayit_liste("sicil", AZAMI)
    n = len(ks)
    tarihler = [float(x.get("ts") or 0) for x in ks if x.get("ts")]
    def iso(t: float | None) -> str | None:
        return datetime.fromtimestamp(t, timezone.utc).isoformat() if t else None
    return {
        "n": n, "asgari": ASGARI, "kalan": max(0, ASGARI - n), "hazir": n >= ASGARI,
        "ilk": iso(min(tarihler)) if tarihler else None, "son": iso(max(tarihler)) if tarihler else None,
        "son_referans": depo.meta_oku("sicil_son_referans"),
        "sinir": "Sicil danışmanın kendi havuzudur; genel nüfus değildir. Havuz taraflıysa referans da taraflı olur.",
        "gizlilik": "Yalnız ham MİZAN/ŞAHİT endeksleri ve zaman damgası tutulur; kişi verisi tutulmaz.",
    }


def konum(analiz: Dict[str, Any]) -> Dict[str, Any]:
    ks = depo.json_kayit_liste("sicil", AZAMI)
    if len(ks) < ASGARI:
        return {"durum": "ornek_yetersiz", "n": len(ks), "asgari": ASGARI, "eksenler": []}
    cur = kayit_cikar(analiz)
    mham, _ = _hamlar(ks)
    eksenler = []
    for kod, ham in (cur.get("mizan") or {}).items():
        ref = sorted(mham.get(kod) or [])
        if not ref:
            continue
        # Eşit değerler için mid-rank; kendi havuzunda yapay sıçrama üretmez.
        alt = sum(1 for x in ref if x < ham)
        esit = sum(1 for x in ref if abs(x - ham) < 1e-9)
        yuz = (alt + esit * .5) / len(ref) * 100
        eksenler.append({"kod": kod, "ham": round(float(ham), 3), "yuzdelik": round(yuz, 1),
                         "cumle": f"Bu haritanın {kod.capitalize()} değeri, okunan {len(ref)} haritanın %{round(yuz)}'inden yüksek."})
    return {"durum": "olculdu", "n": len(ks), "eksenler": eksenler,
            "sinir": "Bu karşılaştırma yalnız ZÎC danışan havuzuna aittir; genel nüfus normu değildir."}
