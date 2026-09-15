#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HÜKÜM BAĞLAMI — Natal çekirdeği ve isteğe bağlı Solar Return aktivasyonu.

Bu modül AI üretmez. Hesaplanmış iki haritanın Hüküm için gerekli alanlarını
tek, kararlı bir veri sözleşmesinde toplar. Natal her zaman temel katmandır;
Solar Return yalnız yıllık aktivasyon olarak eklenir.
"""
from __future__ import annotations
from typing import Any, Dict, Optional


def _lon(n: Any) -> Optional[float]:
    try:
        if isinstance(n, dict) and n.get("lon") is not None:
            return float(n["lon"]) % 360.0
    except Exception:
        pass
    return None


def _fark(a: float, b: float) -> float:
    d = abs((a - b) % 360.0)
    return min(d, 360.0 - d)


def _aci_adi(fark: float, orb: float = 6.0) -> Optional[Dict[str, Any]]:
    acilar = ((0.0, "kavuşum"), (60.0, "sekstil"), (90.0, "kare"),
              (120.0, "üçgen"), (180.0, "karşıt"))
    hedef, ad = min(acilar, key=lambda x: abs(fark - x[0]))
    sapma = abs(fark - hedef)
    if sapma <= orb:
        return {"aci": ad, "hedef": hedef, "orb": round(sapma, 2),
                "fark": round(fark, 2)}
    return None


def _cekirdek(v2: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    v2 = v2 or {}
    b = v2.get("berzah") or {}
    kurt = (v2.get("kurtarici") or [{}])[0] or {}
    return {
        "sikayet": v2.get("AD") or {},
        "sebep": v2.get("KD") or {},
        "karar": b,
        "talimat": kurt,
    }


def hukum_baglam(natal_v2: Dict[str, Any],
                 solar_v2: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Natal Hüküm çekirdeğini ve varsa Solar Return tetiklerini birleştirir."""
    sonuc: Dict[str, Any] = {
        "mode": "natal",
        "natal": _cekirdek(natal_v2),
        "kural": "Natal temel örüntüdür; Solar Return varsa yalnız yıllık aktivasyondur.",
    }
    if not isinstance(solar_v2, dict) or solar_v2.get("hata"):
        return sonuc

    sv2 = solar_v2.get("berzah_v2") or solar_v2
    if not isinstance(sv2, dict) or not sv2:
        return sonuc

    sonuc["mode"] = "natal+solar"
    sonuc["solar"] = {
        "yil": solar_v2.get("yil"),
        "an": solar_v2.get("an"),
        **_cekirdek(sv2),
    }

    tetikler = []
    natal_noktalar = {
        "Natal Şikâyet": (natal_v2.get("AD") or {}),
        "Natal Sebep": (natal_v2.get("KD") or {}),
        "Natal Karar": (natal_v2.get("berzah") or {}),
    }
    solar_noktalar = {
        "SR Şikâyet": (sv2.get("AD") or {}),
        "SR Sebep": (sv2.get("KD") or {}),
        "SR Karar": (sv2.get("berzah") or {}),
    }
    for sad, sn in solar_noktalar.items():
        sl = _lon(sn)
        if sl is None:
            continue
        for nad, nn in natal_noktalar.items():
            nl = _lon(nn)
            if nl is None:
                continue
            f = _fark(sl, nl)
            a = _aci_adi(f)
            if a:
                tetikler.append({
                    "solar": sad, "natal": nad,
                    "solar_konum": sn.get("konum"),
                    "natal_konum": nn.get("konum"),
                    **a,
                })
    tetikler.sort(key=lambda x: x["orb"])
    sonuc["cross"] = {
        "tetiklenmeler": tetikler[:12],
        "adet": len(tetikler),
        "yorum": ("Solar Return, Natal Hükümün yerine geçmez; aşağıdaki açılar "
                  "bu yıl hangi natal eşiklerin daha görünür olduğunu gösterir."),
    }
    return sonuc
