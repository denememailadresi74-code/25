#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUMAN DESIGN ANALİZİ — Astro Pro v9.2.4'ten ayrıştırıldı ve kanal-tabanlı
tanım düzeltmesiyle (v9.2 hotfix) korundu: Type/Authority/Definition zinciri
TEKİL KAPIDAN değil TAMAMLANMIŞ KANALLARDAN türetilir.
Design haritası: doğumdan ~88 güneş derecesi önce (Güneş 88° geridayken).
"""
from __future__ import annotations
import math
from typing import Dict, List, Optional, Set, Tuple

import swisseph as swe

from .astro import (NatalChart, BODY_IDS, EPHFLAG, TR_NAME, chart_at_jd,
                    jd_to_iso, calc_lon)
from .circular import norm360, sep

HD_GATE_OFFSET = 302.0                 # Kapı 41 = 02°00' Kova
HD_GATE_SIZE = 360.0 / 64.0
HD_GATES_WHEEL = [41, 19, 13, 49, 30, 55, 37, 63, 22, 36, 25, 17, 21, 51, 42, 3,
                  27, 24, 2, 23, 8, 20, 16, 35, 45, 12, 15, 52, 39, 53, 62, 56,
                  31, 33, 7, 4, 29, 59, 40, 64, 47, 6, 46, 18, 48, 57, 32, 50,
                  28, 44, 1, 43, 14, 34, 9, 5, 26, 11, 10, 58, 38, 54, 61, 60]

HD_CENTER_GATES: Dict[str, Set[int]] = {
    "Head": {64, 61, 63},
    "Ajna": {47, 24, 4, 17, 43, 11},
    "Throat": {62, 23, 56, 35, 12, 45, 33, 8, 31, 20, 16},
    "G": {1, 13, 25, 46, 2, 15, 10, 7},
    "Heart": {26, 51, 21, 40},
    "Sacral": {5, 14, 29, 59, 9, 3, 42, 27, 34},
    "SolarPlexus": {6, 37, 22, 36, 30, 55, 49},
    "Spleen": {48, 57, 44, 50, 32, 28, 18},
    "Root": {53, 60, 52, 19, 39, 41, 58, 38, 54},
}
CENTER_TR = {"Head": "Baş", "Ajna": "Ajna", "Throat": "Boğaz", "G": "G (Kimlik)",
             "Heart": "Kalp/Ego", "Sacral": "Sakral", "SolarPlexus": "Duygusal",
             "Spleen": "Dalak", "Root": "Kök"}
MOTORS = {"Sacral", "SolarPlexus", "Heart", "Root"}

HD_CHANNELS: List[Tuple[int, int]] = [
    (1, 8), (2, 14), (3, 60), (4, 63), (5, 15), (6, 59), (7, 31), (9, 52),
    (10, 20), (10, 34), (10, 57), (11, 56), (12, 22), (13, 33), (16, 48),
    (17, 62), (18, 58), (19, 49), (20, 34), (20, 57), (21, 45), (23, 43),
    (24, 61), (25, 51), (26, 44), (27, 50), (28, 38), (29, 46), (30, 41),
    (32, 54), (34, 57), (35, 36), (37, 40), (39, 55), (42, 53), (47, 64)]

_HD_BODIES = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
              "Uranus", "Neptune", "Pluto", "TrueNode"]

NOT_SELF = {
    "Generator": [("Başlatma tuzağı", "Yanıtlamadan adım atarsan hayal kırıklığı yükselir.")],
    "Manifesting Generator": [("Adım atlama", "Hız nedeniyle önemli detayları kaçırırsın."),
                              ("Bilgilendirmeden hareket", "Çevreyi haberdar etmeden başlarsın, direnç doğar.")],
    "Manifestor": [("Kontrol isteği", "Bilgilendirmemek çevreyle çatışma yaratır."),
                   ("Öfke birikimi", "Durdurulduğunda öfke; inisiyasyon alanını korumalısın.")],
    "Projector": [("Davetsiz rehberlik", "Çağrılmadan yönlendirmek acı/görünmezlik getirir."),
                  ("Aşırı çalışma", "Sakral motorun yok; dinlenme stratejinin parçası.")],
    "Reflector": [("Aceleci karar", "Ay döngüsünü (28 gün) beklemeden karar sürüklenme yaratır.")],
}
TYPE_TR = {"Generator": "Üretici", "Manifesting Generator": "Manifest Üretici",
           "Manifestor": "Manifestör", "Projector": "Projektör",
           "Reflector": "Yansıtıcı"}
STRATEGY = {"Generator": "Yanıt vermek", "Manifesting Generator": "Yanıtla, sonra bilgilendir",
            "Manifestor": "Bilgilendirmek", "Projector": "Daveti beklemek",
            "Reflector": "Bir Ay döngüsü beklemek"}
AUTH_TR = {"Emotional": "Duygusal otorite — netlik dalgada, anda karar yok",
           "Sacral": "Sakral otorite — bedensel evet/hayır sesi",
           "Splenic": "Dalak otoritesi — anlık sezgisel fısıltı",
           "Ego": "Ego otoritesi — irade/söz: 'bunu gerçekten istiyor muyum'",
           "Self": "Öz (G) otoritesi — sesli düşünürken yön belirir",
           "Mental": "Zihinsel projektör — güvenli ortamda konuşarak süzme",
           "Lunar": "Ay otoritesi — 28 günlük tam döngü"}


def gate_line(lon: float) -> Tuple[int, int]:
    off = (norm360(lon) - HD_GATE_OFFSET) % 360.0
    idx = int(off // HD_GATE_SIZE)
    line = int((off - idx * HD_GATE_SIZE) // (HD_GATE_SIZE / 6)) + 1
    return HD_GATES_WHEEL[idx], max(1, min(6, line))


def _design_jd(natal_jd: float) -> float:
    """Güneş'in natal konumundan 88° geride olduğu an (≈88 gün önce)."""
    target = norm360(calc_lon(natal_jd, "Sun") - 88.0)
    jd = natal_jd - 95.0
    for _ in range(60):
        s = calc_lon(jd, "Sun")
        diff = ((target - s + 180) % 360) - 180
        if abs(diff) < 1e-6: break
        jd += diff / 0.9856
    return jd


def _activations(jd: float) -> Dict[str, Tuple[int, int]]:
    out = {}
    for k in _HD_BODIES:
        out[k] = gate_line(calc_lon(jd, k))
    # Güney düğüm = kuzeyin karşısı
    nn = calc_lon(jd, "TrueNode")
    out["SouthNode"] = gate_line(norm360(nn + 180))
    # Dünya = Güneş karşısı
    su = calc_lon(jd, "Sun")
    out["Earth"] = gate_line(norm360(su + 180))
    return out


def _center_of(gate: int) -> str:
    for c, gs in HD_CENTER_GATES.items():
        if gate in gs: return c
    return "?"


def human_design(ch: NatalChart) -> dict:
    pers = _activations(ch.jd_ut)
    djd = _design_jd(ch.jd_ut)
    des = _activations(djd)

    gates: Set[int] = {g for g, _l in pers.values()} | {g for g, _l in des.values()}
    channels = [(a, b) for a, b in HD_CHANNELS if a in gates and b in gates]
    defined: Set[str] = set()
    for a, b in channels:
        defined.add(_center_of(a)); defined.add(_center_of(b))

    sacral = "Sacral" in defined
    motor_throat = any(
        ("Throat" in (_center_of(a), _center_of(b)))
        and ({_center_of(a), _center_of(b)} & MOTORS)
        for a, b in channels)

    if not defined: hd_type = "Reflector"
    elif sacral and motor_throat: hd_type = "Manifesting Generator"
    elif sacral: hd_type = "Generator"
    elif motor_throat: hd_type = "Manifestor"
    else: hd_type = "Projector"

    if hd_type == "Reflector": auth = "Lunar"
    elif "SolarPlexus" in defined: auth = "Emotional"
    elif sacral: auth = "Sacral"
    elif "Spleen" in defined: auth = "Splenic"
    elif "Heart" in defined: auth = "Ego"
    elif "G" in defined: auth = "Self"
    else: auth = "Mental"

    profile = f"{pers['Sun'][1]}/{des['Sun'][1]}"

    # Tanım (definition): bağlı bileşen sayısı
    if defined:
        adj = {c: set() for c in defined}
        for a, b in channels:
            ca, cb = _center_of(a), _center_of(b)
            if ca in adj and cb in adj:
                adj[ca].add(cb); adj[cb].add(ca)
        seen, comps = set(), 0
        for c in defined:
            if c in seen: continue
            comps += 1
            stack = [c]
            while stack:
                x = stack.pop()
                if x in seen: continue
                seen.add(x); stack.extend(adj[x] - seen)
        definition = {1: "Tek tanım", 2: "İkili ayrım", 3: "Üçlü ayrım",
                      4: "Dörtlü ayrım"}.get(comps, f"{comps} parça")
    else:
        definition = "Tanımsız (Yansıtıcı)"

    return {"modul": "Human Design Analizi",
            "tip": {"en": hd_type, "tr": TYPE_TR[hd_type]},
            "strateji": STRATEGY[hd_type],
            "otorite": {"en": auth, "tr": AUTH_TR[auth]},
            "profil": profile,
            "tanim": definition,
            "tanimli_merkezler": sorted(CENTER_TR[c] for c in defined),
            "acik_merkezler": sorted(CENTER_TR[c] for c in HD_CENTER_GATES
                                     if c not in defined),
            "kanallar": [f"{a}-{b}" for a, b in sorted(channels)],
            "kisilik_kapilari": {TR_NAME.get(k, k): f"{g}.{l}"
                                 for k, (g, l) in pers.items()},
            "dizayn_kapilari": {TR_NAME.get(k, k): f"{g}.{l}"
                                for k, (g, l) in des.items()},
            "dizayn_ani": jd_to_iso(djd),
            "not_self_tuzaklari": [{"tuzak": t, "aciklama": a}
                                   for t, a in NOT_SELF[hd_type]],
            "yontem": ("Design = Güneş natalden 88° gerideyken; tanım zinciri "
                       "tekil kapıdan değil TAMAMLANMIŞ kanaldan (v9.2 düzeltmesi).")}
