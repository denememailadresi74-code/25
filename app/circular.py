#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ortak dairesel matematik + ebced altyapısı — BERZAH Servisi."""
from __future__ import annotations
import math
from typing import Iterable, List, Optional, Sequence, Tuple

SIGNS = ["Koç", "Boğa", "İkizler", "Yengeç", "Aslan", "Başak",
         "Terazi", "Akrep", "Yay", "Oğlak", "Kova", "Balık"]
SIGN_GLYPH = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]
ELEMENT = {"Koç": "Ateş", "Aslan": "Ateş", "Yay": "Ateş",
           "Boğa": "Toprak", "Başak": "Toprak", "Oğlak": "Toprak",
           "İkizler": "Hava", "Terazi": "Hava", "Kova": "Hava",
           "Yengeç": "Su", "Akrep": "Su", "Balık": "Su"}
RULER = {"Koç": "Mars", "Boğa": "Venüs", "İkizler": "Merkür", "Yengeç": "Ay",
         "Aslan": "Güneş", "Başak": "Merkür", "Terazi": "Venüs", "Akrep": "Mars",
         "Yay": "Jüpiter", "Oğlak": "Satürn", "Kova": "Satürn", "Balık": "Jüpiter"}

PHI = (1 + 5 ** 0.5) / 2
GOLDEN_ANGLE = 360.0 * (1 - 1 / PHI)          # 137.50776405°


def norm360(x: float) -> float:
    return float(x) % 360.0


def sep(a: float, b: float) -> float:
    """En kısa yay 0..180."""
    d = abs(norm360(a) - norm360(b)) % 360.0
    return 360.0 - d if d > 180.0 else d


def signed_sep(a: float, b: float) -> float:
    """b'den a'ya işaretli en kısa yay (−180..180]."""
    return (norm360(a) - norm360(b) + 180.0) % 360.0 - 180.0


def project(a: float, b: float, ratio: float) -> float:
    """a'dan b'ye kısa yay üzerinde oranla ilerle (KRN altın-oran izdüşümü)."""
    return norm360(a + ratio * signed_sep(b, a))


def sign_of(lon: float) -> str:
    return SIGNS[int(norm360(lon) // 30)]


def deg_in_sign(lon: float) -> float:
    return norm360(lon) % 30.0


def fmt_lon(lon: float) -> str:
    d = deg_in_sign(lon)
    dd = int(d); mm = int(round((d - dd) * 60))
    if mm == 60: dd, mm = dd + 1, 0
    return f"{dd:02d}°{mm:02d}' {sign_of(lon)}"


def antiscion(lon: float) -> float:
    """Yengeç0/Oğlak0 ekseninde ayna (klasik antisya)."""
    return norm360(180.0 - lon)


def contrantiscion(lon: float) -> float:
    return norm360(360.0 - lon)


def circular_mean_weighted(items: Iterable[Tuple[float, float]]) -> Tuple[Optional[float], float]:
    """[(lon, w)] → (ortalama_boylam, R∈[0,1]). R=toplanmışlık (Vahdet–Kesret)."""
    sx = sy = sw = 0.0
    for lon, w in items:
        r = math.radians(norm360(lon)); w = float(w)
        sx += w * math.cos(r); sy += w * math.sin(r); sw += w
    if sw <= 0: return None, 0.0
    R = math.hypot(sx, sy) / sw
    if R < 1e-12: return None, 0.0
    return norm360(math.degrees(math.atan2(sy, sx))), R


def circular_median(lons_w: Sequence[Tuple[float, float]], step: float = 0.25) -> Tuple[float, float]:
    """L1 dairesel medyan: argmin Σ w·d(φ,λ). Aykırılara dirençli (Süveyda)."""
    best_phi, best_cost = 0.0, math.inf
    n = int(360.0 / step)
    for i in range(n):
        phi = i * step
        c = sum(w * sep(phi, lon) for lon, w in lons_w)
        if c < best_cost: best_phi, best_cost = phi, c
    return best_phi, best_cost


def rayleigh_R(lons_w: Sequence[Tuple[float, float]], harmonic: float) -> float:
    """Katlanmış dağılımın kümelenmesi — H harmoniğinde çınlama."""
    sx = sy = sw = 0.0
    for lon, w in lons_w:
        th = math.radians(norm360(lon) * harmonic)
        sx += w * math.cos(th); sy += w * math.sin(th); sw += w
    return math.hypot(sx, sy) / sw if sw > 0 else 0.0


def house_of(lon: float, cusps: Optional[Sequence[float]]) -> Optional[int]:
    if not cusps or len(cusps) < 12: return None
    lon = norm360(lon)
    for i in range(12):
        a, b = norm360(cusps[i]), norm360(cusps[(i + 1) % 12])
        if (lon - a) % 360.0 < (b - a) % 360.0:
            return i + 1
    return None


# ============================================================================
# EBCED — klasik (kebîr) abjad + Türkçe→Arapça transliterasyon
# ============================================================================
_EBCED = {
    'ا': 1, 'ب': 2, 'ج': 3, 'د': 4, 'ه': 5, 'و': 6, 'ز': 7, 'ح': 8, 'ط': 9,
    'ي': 10, 'ك': 20, 'ل': 30, 'م': 40, 'ن': 50, 'س': 60, 'ع': 70, 'ف': 80,
    'ص': 90, 'ق': 100, 'ر': 200, 'ش': 300, 'ت': 400, 'ث': 500, 'خ': 600,
    'ذ': 700, 'ض': 800, 'ظ': 900, 'غ': 1000,
    'ء': 1, 'آ': 1, 'أ': 1, 'إ': 1, 'ؤ': 6, 'ئ': 10, 'ة': 5, 'ى': 10,
    'پ': 2, 'چ': 3, 'ژ': 7, 'گ': 20,   # Osmanlı ek harfler → yakın değer
}
# Türkçe hece/harf → Osmanlı imlâsı (yaklaşık, klasik havâs geleneği)
_TR2AR = [
    ('ş', 'ش'), ('ç', 'چ'), ('ğ', 'غ'), ('ö', 'و'), ('ü', 'و'), ('ı', 'ي'),
    ('İ', 'ي'), ('â', 'ا'), ('î', 'ي'), ('û', 'و'),
    ('a', 'ا'), ('b', 'ب'), ('c', 'ج'), ('d', 'د'), ('e', 'ه'), ('f', 'ف'),
    ('g', 'گ'), ('h', 'ه'), ('i', 'ي'), ('j', 'ژ'), ('k', 'ك'), ('l', 'ل'),
    ('m', 'م'), ('n', 'ن'), ('o', 'و'), ('p', 'پ'), ('r', 'ر'), ('s', 'س'),
    ('t', 'ت'), ('u', 'و'), ('v', 'و'), ('y', 'ي'), ('z', 'ز'), ('x', 'كس'),
    ('w', 'و'), ('q', 'ق'),
]


def to_arabic(text: str) -> str:
    """Latin/Türkçe metni yaklaşık Osmanlı imlâsına çevirir; Arapça girdi aynen geçer."""
    if any('\u0600' <= ch <= '\u06FF' for ch in text):
        return text
    out = text.lower()
    for tr, ar in _TR2AR:
        out = out.replace(tr.lower(), ar)
    return out


def ebced_value(text: str) -> int:
    return sum(_EBCED.get(ch, 0) for ch in to_arabic(text))


def ebced_detail(text: str) -> dict:
    ar = to_arabic(text)
    total = sum(_EBCED.get(ch, 0) for ch in ar)
    return {"girdi": text, "arapca": ar, "ebced": total,
            "isim_derecesi": norm360(total), "burc": sign_of(total),
            "burc_ici": round(deg_in_sign(total), 2)}
