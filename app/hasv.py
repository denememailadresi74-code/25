#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HAŞV — sessiz mercekte kurulmuş danışmanlık iddiasını ölçer.

ŞAHİT bir alanın sessiz olduğunu, İDDİA ise metnin hangi alanlarda iddia
kurduğunu biliyordu; iki bilgi v13.3'e kadar hiç çaprazlanmıyordu. HAŞV bu
boşluğu ölçer. Otomatik sansür ya da yeniden yazma yapmaz: yalnız "ölçülmedi"
denen yerde metnin yine de güvenli bir iddia kurup kurmadığını görünür kılar.
"""
from __future__ import annotations

from typing import Any, Dict, List, Set

from . import iddia
from .tanik import MERCEKLER, sahit_agi

# ŞAHİT alan kodları ile İDDİA hayat alanları birebir değildir. Bu eşleme yeni
# hüküm üretmez; yalnız iki mevcut ölçüm sözlüğünün ortak dilidir.
_ALAN_ESLEME = {
    "kimlik": "kimlik", "iceri": "iceri", "yaratim": "yaratim", "gorunurluk": "yaratim",
    "duzen": "duzen", "kok": "kok", "anlam": "anlam", "iliski": "iliski",
    "kaynak": "kaynak", "cevre": "cevre", "yer": "yer", "zaman": "zaman",
}


def _sessiz_alanlar(analiz: Dict[str, Any]) -> Dict[str, Set[str]]:
    ag = analiz.get("sahit_7")
    if not isinstance(ag, dict) or not isinstance(ag.get("mercekler"), list):
        ag = sahit_agi(analiz)
    out: Dict[str, Set[str]] = {}
    for m in ag.get("mercekler") or []:
        if m.get("durum") != "sessiz":
            continue
        kod = str(m.get("kod") or "")
        meta = MERCEKLER.get(kod) or {}
        alanlar = {_ALAN_ESLEME.get(str(x), str(x)) for x in meta.get("alan", ())}
        out[kod] = {x for x in alanlar if x}
    return out


def _paragraf_iddialari(metin: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for davranis, alan, yon, zaman in iddia.iddialar(metin):
        if davranis == "genel" and alan == "genel":
            continue
        out.append({"davranis": davranis, "alan": alan, "yon": yon, "zaman": zaman})
    return out


def olc(metin: str, analiz: Dict[str, Any], paragraflar: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    sessiz = _sessiz_alanlar(analiz)
    sessiz_tumu = set().union(*sessiz.values()) if sessiz else set()
    iddialar = _paragraf_iddialari(metin)
    aday = [x for x in iddialar if x.get("alan") in sessiz_tumu]
    oran = len(aday) / len(iddialar) if iddialar else 0.0

    ps: List[Dict[str, Any]] = []
    for p in paragraflar or []:
        q = dict(p)
        pidd = _paragraf_iddialari(str(q.get("metin") or ""))
        sessiz_iddia = [x for x in pidd if x.get("alan") in sessiz_tumu]
        # En güçlü doldurma sinyali: paragrafın dayanağı mekanik olarak doğrulanmamış
        # ve aynı paragraf ŞAHİT'in sessiz dediği alanda iddia kuruyor.
        q["hasv"] = bool(q.get("dayanaksiz") and sessiz_iddia)
        q["hasv_iddialari"] = sessiz_iddia
        ps.append(q)
    return {
        "hasv_orani": round(oran, 3), "hasv_adet": len(aday), "iddia_adet": len(iddialar),
        "adaylar": aday, "sessiz_mercekler": sorted(sessiz), "sessiz_alanlar": sorted(sessiz_tumu),
        "paragraflar": ps,
        "olculemedi": not bool(iddialar),
    }
