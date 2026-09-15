#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SARSMA TESTİ — hangi bulgu doğum saati hatasına dayanır

TÜM SİSTEMİN DAYANDIĞI TEK VARSAYIM
    Yirmi beş kategori, dokuz icat, on beş katman — hepsi tek bir sayıya
    dayanıyor: doğum saati.

    Astroloji bunu bilir ve "saatiniz kesin mi" diye sorar. Sonra cevap
    ne olursa olsun BÜTÜN bulguları aynı güvenle anlatır.

    Oysa bulgular eşit değildir:

      · Burç konumları saat hatasına neredeyse duyarsızdır. Güneş bir
        derece için bir gün ister; on beş dakika hiçbir şeyi değiştirmez.
      · EV konumları çok duyarlıdır. Yükselen dört dakikada bir derece
        yürür; on beş dakika bir evi tamamen değiştirebilir.
      · Ay hızlıdır — on beş dakikada 8 dakika-yay yürür.

    Yani bir okumanın yarısı sağlam, yarısı kumun üstünde olabilir ve
    danışan ikisini ayırt edemez.

İCAT
    Haritayı SARS: doğum saatini ±5, ±15, ±30 dakika kaydır, her seferinde
    yeniden hesapla, ve bulguların hangisinin DEĞİŞTİĞİNİ say.

      · Hiç değişmeyen bulgu → SAĞLAM. Açıkça söylenebilir.
      · ±30'da değişen        → DAYANIKLI. Saat kabaca doğruysa geçerli.
      · ±15'te değişen        → KIRILGAN. Çekinceyle söylenmeli.
      · ±5'te değişen         → KUM. Söylenmemeli.

    Sonuç bir güven listesi değil, bir AYIRIM: neyin arkasında
    durulabileceği.

NEDEN YENİ
    Astroloji belirsizliği bir UYARI olarak ele alır ("saatiniz kesin
    değilse ev katmanı güvenilmez"). Bu modül onu ÖLÇÜME çevirir: hangi
    bulgu, tam olarak ne kadar hataya dayanır.

    Kimse bunu hesaplamıyor.

SINIR
    Kırılgan bulgu YANLIŞ demek değildir; saat doğruysa doğrudur. Ölçülen
    şey doğruluk değil, HATAYA DAYANIKLILIK.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .astro import NatalChart, build_chart, CORE10, TR_NAME

# Sarsma adımları (dakika). Simetrik uygulanır: ±5, ±15, ±30.
ADIMLAR = (5, 15, 30)

# Bulgunun hangi sınıfa girdiği, en küçük kaç dakikada değiştiğine bağlı
SINIF = {
    5:  ("kum", "Söylenmemeli. Beş dakikalık hata bunu değiştiriyor."),
    15: ("kırılgan", "Çekinceyle söyle. On beş dakikalık hata değiştiriyor."),
    30: ("dayanıklı", "Saat kabaca doğruysa geçerli."),
    0:  ("sağlam", "Açıkça söylenebilir; saat hatası bunu bozmuyor."),
}


def _bulgular(ch: NatalChart, v2: dict) -> Dict[str, Any]:
    """
    Bir haritadan karşılaştırılabilir bulgu kümesi çıkarır.

    Karşılaştırma için SAYISAL değil KATEGORİK değer alınır: burç, ev,
    tür. Derece farkı zaten olacak; önemli olan YORUMUN değişip
    değişmediği.
    """
    b = v2.get("berzah") or {}
    ad, kd = v2.get("AD") or {}, v2.get("KD") or {}

    def burc(lon: float) -> int:
        return int(lon // 30)

    out: Dict[str, Any] = {
        "Şikâyet burcu": burc(ad.get("lon", 0)) if ad.get("lon") is not None else None,
        "Şikâyet evi": ad.get("ev"),
        "Sebep burcu": burc(kd.get("lon", 0)) if kd.get("lon") is not None else None,
        "Sebep evi": kd.get("ev"),
        "Karar eşiği burcu": burc(b.get("lon", 0)) if b.get("lon") is not None else None,
        "Karar eşiği evi": b.get("ev"),
        "Eşik türü": b.get("tur"),
        "Çatal": b.get("catalin_adi") or b.get("catalin_cumlesi"),
        "Yanlış refleks": b.get("yanlis_refleks"),
        "Yükselen burcu": burc(ch.asc),
        "Tepe noktası burcu": burc(ch.mc),
    }
    for k in CORE10:
        if k in ch.bodies:
            out[f"{TR_NAME[k]} burcu"] = burc(ch.bodies[k].lon)
    # Cisimlerin evleri — en duyarlı katman
    cusps = list(getattr(ch, "cusps", []) or [])
    if len(cusps) >= 12:
        for k in CORE10:
            if k not in ch.bodies:
                continue
            lon = ch.bodies[k].lon
            for i in range(12):
                a, c = cusps[i] % 360, cusps[(i + 1) % 12] % 360
                if (a <= c and a <= lon < c) or (a > c and (lon >= a or lon < c)):
                    out[f"{TR_NAME[k]} evi"] = i + 1
                    break
    return out


def sarsma_testi(y: int, mo: int, d: int, h: int, mi: int,
                 lat: float, lng: float, tz_name: Optional[str] = None,
                 tz_offset: Optional[float] = None,
                 house_system: str = "P") -> dict:
    """
    Doğum saatini kaydırıp hangi bulguların değiştiğini ölçer.

    Her adımda hem geri hem ileri kaydırılır; bir bulgu iki yönden
    birinde bile değişiyorsa o adımda kırılmış sayılır.
    """
    from .engine_mass import full_v2

    def kur(dakika: int) -> Tuple[NatalChart, dict]:
        tm = h * 60 + mi + dakika
        gun_kaymasi, tm = divmod(tm, 1440)
        dd = d + gun_kaymasi
        c = build_chart(y, mo, dd, tm // 60, tm % 60, lat, lng,
                        tz_name=tz_name, tz_offset=tz_offset,
                        house_system=house_system)
        return c, full_v2(c, topoloji=False)

    ch0, v0 = kur(0)
    temel = _bulgular(ch0, v0)

    # Her bulgu için: en küçük kaç dakikada değişti
    kirilma: Dict[str, int] = {k: 0 for k in temel}
    for adim in ADIMLAR:
        for yon in (-adim, adim):
            try:
                c, v = kur(yon)
            except Exception:
                continue
            b = _bulgular(c, v)
            for k, t in temel.items():
                if kirilma[k]:            # zaten daha küçük adımda kırılmış
                    continue
                if b.get(k) != t:
                    kirilma[k] = adim

    gruplar: Dict[str, List[str]] = {"sağlam": [], "dayanıklı": [],
                                     "kırılgan": [], "kum": []}
    for k, adim in kirilma.items():
        if temel.get(k) is None:
            continue
        ad_sinif = SINIF[adim][0]
        gruplar[ad_sinif].append(k)

    toplam = sum(len(v) for v in gruplar.values()) or 1
    saglamlik = round(
        (len(gruplar["sağlam"]) * 1.0 + len(gruplar["dayanıklı"]) * 0.7
         + len(gruplar["kırılgan"]) * 0.3) / toplam, 3)

    return {
        "modul": "SARSMA TESTİ — hangi bulgu saat hatasına dayanır",
        "adimlar": list(ADIMLAR),
        "bulgu_sayisi": toplam,
        "gruplar": gruplar,
        "saglamlik": saglamlik,
        "seviye": _seviye(saglamlik, gruplar),
        "okuma": _okuma(gruplar, saglamlik),
        "talimat": _talimat(gruplar),
        "yontem": ("Doğum saati ±5, ±15 ve ±30 dakika kaydırılıp harita "
                   "yeniden kuruluyor. Bir bulgu iki yönden birinde bile "
                   "değişiyorsa o adımda kırılmış sayılır. Karşılaştırma "
                   "SAYISAL değil KATEGORİK: burç, ev, tür — çünkü derece "
                   "farkı zaten olacak, önemli olan yorumun değişmesi."),
        "sinir": ("Kırılgan bulgu YANLIŞ demek değildir; saat doğruysa "
                  "doğrudur. Ölçülen şey doğruluk değil, HATAYA "
                  "DAYANIKLILIK."),
    }


def _seviye(s: float, g: Dict[str, List[str]]) -> str:
    if g["kum"]:
        return "kum var"
    if s >= 0.85:
        return "sağlam"
    if s >= 0.65:
        return "dayanıklı"
    return "kırılgan"


def _okuma(g: Dict[str, List[str]], s: float) -> str:
    p = [f"Bulguların %{round(s*100)}'i saat hatasına dayanıklı."]
    if g["sağlam"]:
        p.append(f"{len(g['sağlam'])} bulgu hiç değişmiyor — bunlar "
                 "haritanın omurgası.")
    if g["kum"]:
        p.append(f"DİKKAT: {len(g['kum'])} bulgu beş dakikalık hatayla "
                 f"değişiyor ({', '.join(g['kum'][:3])}). Saat kesin "
                 "değilse bunları söyleme.")
    elif g["kırılgan"]:
        p.append(f"{len(g['kırılgan'])} bulgu on beş dakikalık hataya "
                 f"dayanmıyor ({', '.join(g['kırılgan'][:3])}). "
                 "Çekinceyle söyle.")
    return " ".join(p)


def _talimat(g: Dict[str, List[str]]) -> List[str]:
    """Prompta girecek somut talimatlar."""
    t: List[str] = []
    if g["sağlam"]:
        t.append("AÇIKÇA SÖYLENEBİLİR (saat hatası bozmuyor): "
                 + ", ".join(g["sağlam"][:8]) + ".")
    if g["kırılgan"]:
        t.append("ÇEKİNCEYLE SÖYLE (on beş dakikalık hata değiştiriyor): "
                 + ", ".join(g["kırılgan"][:6])
                 + ". Bunları anlatırken 'saatiniz kesinse' kaydını düş.")
    if g["kum"]:
        t.append("SÖYLEME (beş dakikalık hata değiştiriyor): "
                 + ", ".join(g["kum"][:6])
                 + ". Saat doğrulanmadan bu bulgular üzerine yorum kurma.")
    return t
