#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AYÂR — yaşayan popülasyon ile kalibrasyon referansı arasındaki sapmayı izler.

v13.3 yüzdelikleri mutlak ``50 / %20 / %20`` hedefine göre denetliyordu. Bir
referansın kendi ayrık yapısı 53.6 ortalama üretiyorsa AYÂR bunu popülasyon
kayması sanabiliyordu. v13.4 referans örnekleminin gözlenen tabanını saklar ve
yeni popülasyonu bu tabana göre kıyaslar; KS eşiği de iki örneklemlidir.

Uniform olmayan dağılım "endeks yanlış" demek değildir. Yalnız kullanılan
referansın mevcut danışan havuzuna uymuyor olabileceğini söyler.
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from . import depo

AZAMI = 500
ASGARI = 60


def _sayi(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _aktif_ref(ad: str) -> Dict[str, Any]:
    kok = Path(__file__).resolve().parent
    kalici = depo.referans_yolu(ad)
    gercek = kok / f"{ad}_quantiles_gercek.json"
    sentetik = kok / f"{ad}_quantiles.json"
    yol = kalici if kalici.exists() else (gercek if gercek.exists() else sentetik)
    try:
        d = json.loads(yol.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _uniform_ornek(n: int = 101) -> List[float]:
    return [i * 100.0 / max(1, n - 1) for i in range(n)]


def _tabanlar() -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for aile, ref, alan in (("mizan", _aktif_ref("mizan"), "eksenler"),
                            ("sahit", _aktif_ref("sahit"), "mercekler")):
        for kod, meta in (ref.get(alan) or {}).items():
            tab = dict(meta.get("ayar_taban") or {}) if isinstance(meta, dict) else {}
            ornek = list(meta.get("ayar_ornek") or []) if isinstance(meta, dict) else []
            n = int(tab.get("n") or ref.get("ornek_sayisi") or ref.get("n") or len(ornek) or 101)
            if not ornek:
                ornek = _uniform_ornek(max(60, min(n, 401)))
            ort = _sayi(tab.get("ortalama"), sum(ornek) / max(1, len(ornek)))
            le20 = _sayi(tab.get("le20"), sum(1 for x in ornek if x <= 20) / max(1, len(ornek)) * 100)
            ge80 = _sayi(tab.get("ge80"), sum(1 for x in ornek if x >= 80) / max(1, len(ornek)) * 100)
            out[f"{aile}.{kod}"] = {
                "ortalama": ort, "le20": le20, "ge80": ge80, "n": max(1, n),
                "ornek": [max(0.0, min(100.0, _sayi(x))) for x in ornek],
                "kaynak": ref.get("kaynak") or "bilinmiyor",
            }
    return out


def sifirla() -> None:
    """Referans değiştiğinde eski yüzdelikler yeni cetvelle kıyaslanamaz."""
    depo.tablo_sil("ayar")


def analizden_kayit(analiz: Dict[str, Any]) -> Dict[str, Any]:
    from .oruntu_omurgasi import oruntu_omurgasi
    from .tanik import sahit_agi

    om = analiz.get("oruntu_omurgasi")
    if not isinstance(om, dict) or not isinstance(om.get("eksenler"), list):
        om = oruntu_omurgasi(analiz)
    sh = analiz.get("sahit_7")
    if not isinstance(sh, dict) or not isinstance(sh.get("mercekler"), list):
        sh = sahit_agi(analiz)
    return {
        "ts": round(time.time(), 3),
        "mizan": {str(x.get("kod")): _sayi(x.get("puan")) for x in om.get("eksenler", []) if x.get("kod")},
        "sahit": {str(x.get("kod")): _sayi(x.get("belirginlik")) for x in sh.get("mercekler", []) if x.get("kod")},
    }


def kaydet(analiz: Dict[str, Any]) -> Dict[str, Any]:
    kayit = analizden_kayit(analiz)
    depo.json_kayit_ekle("ayar", kayit, AZAMI)
    # AYÂR zaten her gerçek analizin sonunda çağrılan ölçüm kancasıdır. SİCİL
    # aynı noktada ham değerleri toplar; main.py'ye ikinci bir paralel kanca
    # eklemek yerine tek atomik analiz sonu kullanılır.
    try:
        from . import sicil
        sicil.kaydet(analiz)
    except Exception:
        pass
    return kayit


def _ks_iki(a: Iterable[float], b: Iterable[float]) -> float:
    A = sorted(max(0.0, min(100.0, float(x))) for x in a)
    B = sorted(max(0.0, min(100.0, float(x))) for x in b)
    if not A or not B:
        return 0.0
    noktalar = sorted(set(A + B))
    ia = ib = 0
    d = 0.0
    for x in noktalar:
        while ia < len(A) and A[ia] <= x:
            ia += 1
        while ib < len(B) and B[ib] <= x:
            ib += 1
        d = max(d, abs(ia / len(A) - ib / len(B)))
    return d


def _yon(ort: float, alt: float, ust: float, tab: Dict[str, Any]) -> str:
    d_ort = ort - _sayi(tab.get("ortalama"), 50.0)
    d_alt = alt - _sayi(tab.get("le20"), 20.0)
    d_ust = ust - _sayi(tab.get("ge80"), 20.0)
    if d_ort >= 4.0 or d_ust >= 8.0 or d_alt <= -8.0:
        return "yukari"
    if d_ort <= -4.0 or d_alt >= 8.0 or d_ust <= -8.0:
        return "asagi"
    return "dagilim"


def _gosterge(kod: str, degerler: List[float], tab: Dict[str, Any]) -> Dict[str, Any]:
    n1 = len(degerler)
    if n1 < ASGARI:
        return {"kod": kod, "n": n1, "durum": "yetersiz_ornek", "kritik": None}
    ref_ornek = list(tab.get("ornek") or _uniform_ornek())
    n2 = max(1, len(ref_ornek))
    ort = sum(degerler) / n1
    alt = sum(1 for x in degerler if x <= 20) / n1 * 100
    ust = sum(1 for x in degerler if x >= 80) / n1 * 100
    ks = _ks_iki(degerler, ref_ornek)
    kritik = 1.36 * math.sqrt((n1 + n2) / (n1 * n2))
    d_ort = abs(ort - _sayi(tab.get("ortalama"), 50.0))
    d_alt = abs(alt - _sayi(tab.get("le20"), 20.0))
    d_ust = abs(ust - _sayi(tab.get("ge80"), 20.0))
    # İki örneklem KS, referansın kendi ayrık/plato yapısını hesaba katar. Yalnız
    # KS geçişi de küçük örneklemde gereksiz alarm üretebildiği için yönlü etki
    # büyüklüğünden en az biri görünür olmalıdır.
    yonlu = d_ort >= 8.0 or d_alt >= 15.0 or d_ust >= 15.0
    kaymis = ks > kritik and yonlu
    return {
        "kod": kod, "n": n1, "referans_n": int(tab.get("n") or n2),
        "durum": "kaymis" if kaymis else "uyumlu", "ks": round(ks, 4),
        "kritik": round(kritik, 4), "ks_asildi": ks > kritik,
        "ortalama": round(ort, 2), "le20": round(alt, 2), "ge80": round(ust, 2),
        "taban": {"ortalama": round(_sayi(tab.get("ortalama"), 50.0), 2),
                  "le20": round(_sayi(tab.get("le20"), 20.0), 2),
                  "ge80": round(_sayi(tab.get("ge80"), 20.0), 2)},
        "fark": {"ortalama": round(ort - _sayi(tab.get("ortalama"), 50.0), 2),
                 "le20": round(alt - _sayi(tab.get("le20"), 20.0), 2),
                 "ge80": round(ust - _sayi(tab.get("ge80"), 20.0), 2)},
        "yon": _yon(ort, alt, ust, tab) if kaymis else "—",
    }


def rapor(kayitlar: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    ks = list(kayitlar) if kayitlar is not None else depo.json_kayit_liste("ayar", AZAMI)
    n = len(ks)
    taban = _tabanlar()
    bias = {k: round(_sayi(v.get("ortalama"), 50.0) - 50.0, 2) for k, v in taban.items()}
    if n < ASGARI:
        return {
            "modul": "AYÂR · Kalibrasyon Sapma Denetçisi", "durum": "yetersiz_ornek",
            "n": n, "asgari": ASGARI, "kaymis": [], "gostergeler": [],
            "referans_biasi": bias,
            "sinir": "Uniform olmayan dağılım endeksin yanlış olduğunu değil, referansın bu popülasyona uymayabileceğini gösterir.",
            "depo_uyari": "defter sıfırlanmış olabilir" if depo.sifirlanmis_olabilir() else None,
        }
    gruplar: Dict[str, List[float]] = {}
    for kayit in ks:
        for aile in ("mizan", "sahit"):
            for kod, v in (kayit.get(aile) or {}).items():
                gruplar.setdefault(f"{aile}.{kod}", []).append(_sayi(v))
    gostergeler = [_gosterge(k, v, taban.get(k, {"ornek": _uniform_ornek(), "n": 101}))
                   for k, v in sorted(gruplar.items())]
    kaymis = [x for x in gostergeler if x.get("durum") == "kaymis"]
    return {
        "modul": "AYÂR · Kalibrasyon Sapma Denetçisi", "durum": "kaymis" if kaymis else "uyumlu",
        "n": n, "asgari": ASGARI, "kaymis": kaymis, "gostergeler": gostergeler,
        "referans_biasi": bias,
        "ozet": f"AYÂR: {len(kaymis)}/{len(gostergeler)} gösterge kaymış" + (" — referans yenilenmeli" if kaymis else " — referans popülasyonla uyumlu"),
        "sinir": "Uniform olmayan dağılım endeksin yanlış olduğunu değil, referansın bu popülasyona uymayabileceğini gösterir.",
        "gizlilik": "Tampon yalnız yüzdelik sayıları ve zaman damgası tutar; kişi kimliği ve doğum verisi saklanmaz.",
        "depo_uyari": "defter sıfırlanmış olabilir" if depo.sifirlanmis_olabilir() else None,
    }


def ozet() -> Dict[str, Any]:
    r = rapor()
    if r["durum"] == "yetersiz_ornek":
        metin = f"AYÂR: {r['n']}/{ASGARI} örnek — sapma ölçmek için erken"
    else:
        metin = r.get("ozet") or "AYÂR: ölçüm yok"
    if r.get("depo_uyari"):
        metin += " · defter sıfırlanmış olabilir"
    return {"durum": r["durum"], "n": r["n"], "metin": metin,
            "kaymis": len(r.get("kaymis") or []), "depo_uyari": r.get("depo_uyari")}
