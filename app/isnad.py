#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""İSNÂD — üretilen paragraf ile gerçekten verilen kanıt arasındaki zincir.

Bölüm düzeyindeki rozet yalnız "hangi katmanlar vardı" der. İSNÂD ise modelin
her paragrafın sonunda bildirdiği dayanak kodunu, süzülmüş bağlamda mekanik
olarak doğrular. Bağlamda olmayan kod metni sansürlemez; yalnız ``dayanaksiz``
işareti üretir. Böylece ölçülmeyen boşluk görünür kalır.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Set

_BASLIK = re.compile(r"(?m)^\[([^\]\n]+)\]\s*$")
_MARKER = re.compile(r"\s*\[dayanak\s*:\s*([^\]]+)\]\s*", re.IGNORECASE)

_ESLEME = {
    "GÜVEN NOTU": ("guven", "cevaplanabilirlik"), "SARSMA TESTİ": ("sarsma", "sarsma"),
    "NEREDE KONUŞ, NEREDE SUS": ("cevap", "cevaplanabilirlik"), "TEMAS AÇISI": ("temas", "temas_acisi"),
    "HAMLE PENCERESİ": ("hamle", "hamle_penceresi"), "ÇEKİRDEK YAKINSAMA": ("yakinsama", "yakinsama"),
    "KATMANLAR ARASI BAĞ": ("bag", "yakinsama"), "DİRENÇ": ("direnc", "direnc"), "ÇELİŞKİLER": ("celiski", "celiskiler"),
    "ALAN TOPOLOJİSİ": ("topoloji", "alan_topolojisi"), "YÜRÜYEN BERZAH": ("dinamik", "dinamik"),
    "DENEME MODÜLLERİ": ("deneme", "deneme_modulleri"), "KABZ/BAST": ("kb", "kabzbast_v1_m66_74"),
    "KADİM KATMAN": ("kadim", "kadim_katman"), "DURAKLAMA İZİ": ("duraklama", "duraklama_izi"),
    "HUDÛD-I FELEK": ("felek", "hudud_felek"), "BUGÜNKÜ GÖK": ("bugun", "transit"), "KAYIP ZAMAN": ("kayip", "kayip_zaman"),
    "YAŞ KATMANI": ("yas", "yas_katmani"), "YILIN HARİTASI": ("yil", "solar_v2"), "KAPILAR": ("kapilar", "maneviyat"),
    "YER": ("yer", "kartografi"), "ŞİRÂ ÇEVRİMİ": ("sira", "sira_cevrimi"), "HUMAN DESIGN": ("hd", "human_design"),
    "SİNASTRİ": ("iliski_a", "sinastri"), "DAVISON": ("iliski_b", "davison"), "DEKLİNASYON SİNASTRİSİ": ("iliski_c", "deklinasyon"),
    "KOMPOZİT": ("iliski_d", "kompozit"), "ÇEKİRDEK": ("cekirdek", "berzah_v2"),
    "SÜKÛT": ("sukut", "sukut"), "ALGI EŞİĞİ": ("esik", "esik"), "DÖNÜŞ NOKTASI": ("donus", "donus"),
}
_ALIAS_TO_IC = {alias: ic for alias, ic in _ESLEME.values()}


def _ana(baslik: str) -> str:
    b = (baslik or "").strip().upper()
    for x in (" —", " -", ":"):
        if x in b:
            b = b.split(x, 1)[0]
    return b.strip()


def mevcut_kodlar(baglam: str) -> Set[str]:
    out: Set[str] = set()
    for m in _BASLIK.finditer(baglam or ""):
        a = _ana(m.group(1))
        if a in _ESLEME:
            out.add(_ESLEME[a][0])
    return out


def talimat(baglam: str) -> str:
    kodlar = sorted(mevcut_kodlar(baglam))
    if not kodlar:
        return "\nHer paragrafın sonuna [dayanak: olculmedi] yaz; bağlamda dayanak kodu görünmüyor."
    return (
        "\nHer paragrafın veya tek parça madde kümesinin sonuna [dayanak: kod] ekle. "
        "Kod yalnız şu listeden olabilir: " + ", ".join(kodlar) + ". Bir paragraf birden fazla katmana "
        "dayanıyorsa kodları virgülle ayır; listede olmayan kod uydurma."
    )


def dogrula(metin: str, baglam: str) -> Dict[str, Any]:
    izin = mevcut_kodlar(baglam)
    # Paragraf sınırı marker temizlenmeden önce korunur; önceki regex yeni satırları
    # yuttuğunda ayrı iddialar tek paragrafmış gibi görünüyordu.
    parcalar = [x.strip() for x in re.split(r"\n\s*\n", metin or "") if x.strip()]
    out: List[Dict[str, Any]] = []
    temiz_parcalar: List[str] = []
    for p in parcalar:
        bulunan = [m.group(1) for m in _MARKER.finditer(p)]
        kodlar: List[str] = []
        for ham in bulunan:
            kodlar.extend([x.strip() for x in re.split(r"[,;/]", ham) if x.strip()])
        temiz = _MARKER.sub("", p).strip()
        gecerli_alias = [x for x in kodlar if x in izin]
        gecerli = [_ALIAS_TO_IC[x] for x in gecerli_alias]
        dayanaksiz = not bool(kodlar) or len(gecerli_alias) != len(kodlar)
        out.append({"metin": temiz, "dayanak": gecerli, "bildirilen": kodlar, "dayanaksiz": dayanaksiz})
        if temiz:
            temiz_parcalar.append(temiz)
    # Model boş satır kullanmadıysa yine tek paragraf olarak ölçülür.
    if not out and (metin or "").strip():
        temiz = _MARKER.sub("", metin).strip()
        out = [{"metin": temiz, "dayanak": [], "bildirilen": [], "dayanaksiz": True}]
        temiz_parcalar = [temiz]
    dogru = sum(1 for x in out if not x["dayanaksiz"])
    oran = dogru / len(out) if out else 0.0
    temiz_metin = "\n\n".join(temiz_parcalar)
    # Her koşulda marker kalıntısı sıfırlanır; kodlar yalnız yapılandırılmış yanıtta yaşar.
    temiz_metin = _MARKER.sub("", temiz_metin).strip()
    return {
        "metin": temiz_metin, "paragraflar": out, "isnad_orani": round(oran, 3),
        "dayanaksiz_adet": sum(1 for x in out if x["dayanaksiz"]),
        "uyari": "dayanak_zayif" if out and oran < 0.5 else None,
        "izinli": sorted(izin),
    }
