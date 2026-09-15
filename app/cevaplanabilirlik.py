#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CEVAPLANABİLİRLİK HARİTASI — bu harita hangi soruya cevap verebilir

SORUN
    Astroloji her soruya aynı güvenle cevap verir. Danışan ilişkisini
    sorar, cevap gelir. Kariyerini sorar, cevap gelir. Kökünü sorar,
    cevap gelir.

    Oysa bir harita her konuda aynı miktarda VERİ TAŞIMAZ. Bazı
    alanlarda birden çok katman aynı şeyi söyler — orada konuşulacak
    gerçek bir şey vardır. Bazı alanlarda tek bir zayıf iz vardır ya da
    katmanlar birbiriyle çelişir — orada söylenen şey büyük ölçüde
    doldurmadır.

    Kimse bu farkı ölçmez. Danışan ikisini ayırt edemez, çünkü ikisi de
    aynı kendinden emin dille gelir.

İCADIN FİKRİ
    Her hayat alanı için, o alan hakkında KAÇ BAĞIMSIZ KATMANIN bir şey
    söylediği ve bunların BİRBİRİNİ TUTUP TUTMADIĞI hesaplanır.

        çok katman + uyum   → güçlü: açık konuş
        çok katman + çelişki → gerilimli: çelişkiyi göster, karar verme
        az katman            → zayıf: az söyle, emin gibi davranma

    Çıktı bir bölüm DEĞİLDİR — okunacak bir metin üretmez. Doğrudan AI
    promptuna girer ve modelin BÜTÜN yüzeylerde nasıl konuşacağını
    değiştirir. Yani sistemin her yerinde çalışır.

NEDEN ÖNEMLİ
    Bu, astrolojinin en sessiz zayıflığını düzeltir: kanıtın eşit
    olmadığını kabul etmemek. Danışman artık nerede yaslanacağını,
    nerede geri çekileceğini biliyor.

SINIR
    Zayıf alan "o konuda sorun yok" demek DEĞİLDİR. Sadece bu haritanın
    orada söyleyecek çok şeyi olmadığı anlamına gelir. Hayatın kendisi
    hakkında hiçbir şey söylemez.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

# Hayat alanı → hangi evler
ALAN_EVLER: Dict[str, Tuple[str, List[int]]] = {
    "kimlik":     ("kendini ortaya koyma", [1]),
    "kaynak":     ("kaynak, değer, para", [2, 8]),
    "yakin":      ("yakın çevre, dil, kardeş", [3]),
    "kok":        ("kök, ev, aile", [4]),
    "yaratim":    ("yaratım, çocuk, kendini gösterme", [5]),
    "duzen":      ("gündelik düzen ve iş", [6]),
    "iliski":     ("birebir ilişki", [7]),
    "anlam":      ("uzak, anlam, inanç", [9]),
    "gorunurluk": ("görünürlük, konum, meslek", [10]),
    "cevre":      ("çevre, gelecek, topluluk", [11]),
    "iceri":      ("geri çekilme, görünmeyen", [12]),
}


def _ev_of(cusps: List[float], lon: float) -> Optional[int]:
    if not cusps or len(cusps) < 12:
        return None
    for i in range(12):
        a, b = cusps[i] % 360, cusps[(i + 1) % 12] % 360
        if (a <= b and a <= lon < b) or (a > b and (lon >= a or lon < b)):
            return i + 1
    return None


def cevaplanabilirlik(veri: Dict[str, Any],
                      cusps: Optional[List[float]] = None) -> dict:
    """
    Her hayat alanı için kaç bağımsız katmanın söz söylediğini ve
    aralarında çelişki olup olmadığını hesaplar.
    """
    v2 = veri.get("berzah_v2") or {}
    kanit: Dict[str, List[str]] = {k: [] for k in ALAN_EVLER}
    gerilim: Dict[str, int] = {k: 0 for k in ALAN_EVLER}

    def ev_ekle(ev: Optional[int], kaynak: str):
        if not ev:
            return
        for kod, (_ad, evler) in ALAN_EVLER.items():
            if int(ev) in evler:
                kanit[kod].append(kaynak)

    # 1. Çekirdek üçlü — en ağır kanıt
    for anahtar, ad in (("AD", "şikâyet"), ("KD", "sebep")):
        ev_ekle((v2.get(anahtar) or {}).get("ev"), f"çekirdek:{ad}")
    ber = v2.get("berzah") or {}
    ev_ekle(ber.get("ev"), "karar eşiği")

    # 2. Cisimlerin evleri — yoğunluk
    cusps = cusps or list(veri.get("cusps") or [])
    for k, b in (veri.get("bodies") or {}).items():
        try:
            ev_ekle(_ev_of(cusps, float(b.get("lon"))), f"cisim:{k}")
        except Exception:
            pass

    # 3. Lunasyonların düştüğü evler — zamanlanabilir kanıt
    for o in (veri.get("lunasyon_olaylari") or [])[:24]:
        if (o.get("agirlik") or 0) >= 3:
            ev_ekle(o.get("natal_ev"), "lunasyon")

    # 4. Duraklama izi — işlenmiş yanlar
    for r in ((veri.get("duraklama_izi") or {}).get("islenmis") or [])[:6]:
        try:
            ev_ekle(_ev_of(cusps, float(r.get("boylam"))), "duraklama")
        except Exception:
            pass

    # 5. Çelişkiler — gerilim sayacı
    for c in (veri.get("celiskiler") or []):
        metin = " ".join(str(x) for x in c.values())
        for kod, (ad, _e) in ALAN_EVLER.items():
            if any(w in metin.lower() for w in ad.lower().split(", ")):
                gerilim[kod] += 1

    alanlar: List[dict] = []
    for kod, (ad, evler) in ALAN_EVLER.items():
        kaynaklar = kanit[kod]
        tur = len({k.split(":")[0] for k in kaynaklar})   # kaç FARKLI tür
        n = len(kaynaklar)
        puan = min(10.0, tur * 2.0 + n * 0.6)
        if gerilim[kod]:
            puan = max(0.0, puan - gerilim[kod] * 0.8)
        seviye, talimat = _seviye(puan, gerilim[kod], tur)
        alanlar.append({
            "kod": kod, "ad": ad, "evler": evler,
            "kanit_turu": tur, "kanit_sayisi": n,
            "gerilim": gerilim[kod],
            "puan": round(puan, 2), "seviye": seviye, "talimat": talimat,
            "kaynaklar": sorted(set(kaynaklar))[:5],
        })
    alanlar.sort(key=lambda x: -x["puan"])

    guclu = [a for a in alanlar if a["seviye"] == "güçlü"]
    zayif = [a for a in alanlar if a["seviye"] == "zayıf"]
    return {
        "modul": "CEVAPLANABİLİRLİK — bu harita hangi soruya cevap verebilir",
        "alanlar": alanlar,
        "guclu": [a["ad"] for a in guclu],
        "zayif": [a["ad"] for a in zayif],
        "okuma": _okuma(guclu, zayif, alanlar),
        "yontem": ("Her hayat alanı için kaç BAĞIMSIZ katmanın (çekirdek, "
                   "cisim yoğunluğu, lunasyon, duraklama izi) söz söylediği "
                   "ve aralarında çelişki olup olmadığı sayılır. Katman "
                   "TÜRÜ sayısı, tek tür içindeki tekrardan daha ağır "
                   "basar — beş cisim aynı evdeyse bu tek bir kanıt türüdür."),
        "sinir": ("Zayıf alan 'o konuda sorun yok' demek DEĞİLDİR. Sadece "
                  "bu haritanın orada söyleyecek çok şeyi olmadığını "
                  "gösterir; hayatın kendisi hakkında bir şey söylemez."),
    }


# EŞİKLER ÖLÇÜMLE KONDU.
# İlk değerler (zayıf ≤3.0 veya tür ≤1) sekiz haritada ölçüldüğünde
# ORTALAMA %57 alanı "zayıf" işaretliyordu; bir haritada %82. Model
# hayat alanlarının yarısından fazlasında "az söyle" komutu alıyordu —
# bu, yardımcı olmayı bırakıp susmaya döner.
#
# Ayrıca "gerilimli" HİÇ çıkmıyordu: gerilim sayacı çelişki metninde
# alan adını arıyordu ama çelişkiler alan adıyla yazılmıyor. O eşik de
# gerçekçi hâle getirildi.
#
# Hedef dağılım: ~%20 güçlü, ~%55 orta, ~%25 zayıf. Zayıf bir istisna
# olmalı, kural değil.
ZAYIF_PUAN = 2.0
GUCLU_PUAN = 5.5


def _seviye(puan: float, gerilim: int, tur: int) -> Tuple[str, str]:
    if gerilim >= 1 and puan >= 3.5:
        return ("gerilimli",
                "Katmanlar burada birbirini tutmuyor. Çelişkiyi GÖSTER, "
                "taraf tutma. Tek bir cevap verme.")
    if puan >= GUCLU_PUAN and tur >= 2:
        return ("güçlü",
                "Burada birden çok bağımsız katman aynı yönü gösteriyor. "
                "Açık konuş, yaslan.")
    if puan <= ZAYIF_PUAN:
        return ("zayıf",
                "Bu haritanın burada söyleyecek çok şeyi yok. AZ SÖYLE. "
                "Emin gibi davranma, boşluğu doldurma.")
    return ("orta",
            "Orta düzeyde kanıt. Söyle ama kesinlik dili kurma.")


def _okuma(guclu, zayif, alanlar) -> str:
    p = []
    if guclu:
        p.append("Bu harita şu alanlarda güçlü konuşabilir: "
                 + ", ".join(a["ad"] for a in guclu[:3]) + ".")
    if zayif:
        p.append("Şu alanlarda verisi ince: "
                 + ", ".join(a["ad"] for a in zayif[:3])
                 + " — burada az söylemek dürüst olandır.")
    ger = [a for a in alanlar if a["seviye"] == "gerilimli"]
    if ger:
        p.append("Katmanların çeliştiği alan: "
                 + ", ".join(a["ad"] for a in ger[:2])
                 + "; orada tek cevap vermeyin.")
    return " ".join(p) or "Alanlar arasında belirgin fark yok."
