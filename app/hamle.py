#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HAMLE PENCERESİ — bu kişi için hangi hafta hangi hamleye uygun

CEVAPLANMAYAN SORU
    Sistem kişiyi on dokuz katmanda tarif ediyor, zamanı yedi katmanda
    ölçüyor. Ama danışanın ASIL sorduğu şeyi cevaplamıyor:

        "Bunu yapmalı mıyım, ne zaman?"

    Astrolojide seçim (elektional) dalı vardır: uğurlu an seçme. Ama o
    GENELDİR — "sözleşme için iyi gün", "Merkür geri değilken imzala".
    Herkes için aynı.

    Kimse seçimi KİŞİNİN KENDİ YAPISINA göre hesaplamıyor.

İCADIN FİKRİ
    "İyi gün" diye bir şey yok. Bir hafta, YAPILACAK İŞİN TÜRÜNE göre
    uygundur ya da değildir — ve bu, kişinin kendi alan yapısına bağlıdır.

    Beş hamle türü ayrıştırıldı:

      BAŞLATMAK   yeni bir şeye girmek
      BİTİRMEK    kapatmak, bırakmak
      BAĞLANMAK   derinleştirmek, söz vermek
      ÇEKİLMEK    geri durmak, dinlenmek
      SÖYLEMEK    açmak, yüzleşmek, görünür kılmak

    Her hafta, her tür için ayrı puanlanır. Puan kişinin kendi
    katmanlarından gelir:

      · Lunasyon türü ve düştüğü ev  → hangi konu açılıyor
      · Sükût basıncı               → dışarıdan itiliyor mu, kendi mi
      · Kabz/Bast evresi            → toparlanma mı yayılma mı
      · Yaş eşiği yığılması         → kaç kapı açık
      · Karar eşiği türü            → doğal eğilim hangi yöne

    Sonuç: "önümüzdeki 12 haftada BAŞLATMAK için en uygun aralık şu,
    BİTİRMEK için şu" — kişiye özel, iş türüne göre.

NEDEN DAHA GÜÇLÜ
    Silinen Yürüyen Berzah çatalın ne zaman tetiklendiğini söylüyordu —
    tarif. Bu modül ne yapılabileceğini söylüyor — karar.

SINIR
    Pencere GARANTİ DEĞİLDİR. "Bu hafta başlat" denmez; "bu hafta
    başlatmak daha az sürtünmeyle olur" denir. Kötü hafta da yoktur:
    her hafta bir şeye uygun, başka şeye değildir.
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Optional, Tuple

import swisseph as swe

from .astro import NatalChart, ensure_ephe, jd_to_iso

HAMLELER: Dict[str, Tuple[str, str]] = {
    "baslatmak": ("Başlatmak", "yeni bir şeye girmek"),
    "bitirmek": ("Bitirmek", "kapatmak, bırakmak"),
    "baglanmak": ("Bağlanmak", "derinleştirmek, söz vermek"),
    "cekilmek": ("Çekilmek", "geri durmak, dinlenmek"),
    "soylemek": ("Söylemek", "açmak, yüzleşmek, görünür kılmak"),
}

# Lunasyon türü → hangi hamleyi destekler / köstekler
LUNASYON_ETKI: Dict[str, Dict[str, float]] = {
    "yeni ay":        {"baslatmak": 2.0, "baglanmak": 0.8, "soylemek": 0.5,
                       "bitirmek": -0.8, "cekilmek": -0.3},
    "dolunay":        {"soylemek": 2.0, "bitirmek": 1.4, "baglanmak": 0.4,
                       "baslatmak": -1.0, "cekilmek": -0.5},
    "güneş tutulması": {"baslatmak": 1.2, "bitirmek": 0.6, "cekilmek": 1.0,
                        "baglanmak": -1.2, "soylemek": -0.6},
    "ay tutulması":   {"bitirmek": 1.8, "cekilmek": 1.2, "soylemek": 0.3,
                       "baslatmak": -1.4, "baglanmak": -1.0},
}

# Evler → hangi hamle o alanda anlamlı
EV_HAMLE: Dict[int, List[str]] = {
    1: ["baslatmak", "soylemek"], 2: ["baglanmak", "baslatmak"],
    3: ["soylemek"], 4: ["cekilmek", "baglanmak"],
    5: ["baslatmak", "soylemek"], 6: ["baslatmak", "bitirmek"],
    7: ["baglanmak", "soylemek"], 8: ["bitirmek", "baglanmak"],
    9: ["baslatmak", "cekilmek"], 10: ["soylemek", "baslatmak"],
    11: ["baglanmak", "baslatmak"], 12: ["cekilmek", "bitirmek"],
}


def hamle_penceresi(veri: Dict[str, Any], hafta: int = 12,
                    jd_bas: Optional[float] = None) -> dict:
    """
    Önümüzdeki `hafta` hafta için, beş hamle türünün her birine
    uygunluk puanı hesaplar.
    """
    ensure_ephe()
    if jd_bas is None:
        u = dt.datetime.utcnow()
        jd_bas = swe.julday(u.year, u.month, u.day, 12.0)

    olaylar = (veri.get("lunasyon_olaylari")
               or (veri.get("lunasyon") or {}).get("olaylar") or [])
    sukut = veri.get("sukut") or {}
    v2 = veri.get("berzah_v2") or {}
    ber = v2.get("berzah") or {}
    yk = veri.get("yas_katmani") or {}
    kb = veri.get("kabzbast_v1_m66_74") or {}

    # --- SABİT EĞİLİMLER: kişinin yapısından gelen taban ---
    taban: Dict[str, float] = {k: 0.0 for k in HAMLELER}
    notlar: List[str] = []

    tur = str(ber.get("tur") or "")
    if "itici" in tur:
        taban["bitirmek"] += 1.0
        taban["cekilmek"] += 0.6
        taban["baglanmak"] -= 0.8
        notlar.append("Karar eşiği itici: bu kişide bitirmek doğal, "
                      "bağlanmak zorlu. Bağlanma penceresi geldiğinde "
                      "fazladan destek gerekir.")
    durum = str(kb.get("durum") or kb.get("yon") or "").lower()
    if "kabz" in durum or "toparlan" in durum:
        taban["cekilmek"] += 0.8
        taban["bitirmek"] += 0.5
        taban["baslatmak"] -= 0.7
        notlar.append("Dönem toparlanma yönünde: başlatmak akıntıya karşı.")
    elif "bast" in durum or "yayıl" in durum:
        taban["baslatmak"] += 0.8
        taban["soylemek"] += 0.5
        taban["cekilmek"] -= 0.6
        notlar.append("Dönem yayılma yönünde: başlatmak akıntıyla.")

    esik_n = yk.get("esik_sayisi") or 0
    if esik_n >= 3:
        taban["baslatmak"] -= 0.8
        taban["cekilmek"] += 0.7
        notlar.append(f"{esik_n} gelişim eşiği aynı anda açık: yeni yük "
                      "almak yerine var olanı taşımak daha gerçekçi.")

    # --- HAFTALIK PUANLAMA ---
    haftalar: List[dict] = []
    for h in range(hafta):
        h_bas = jd_bas + h * 7
        h_son = h_bas + 7
        puan = dict(taban)
        sebep: List[str] = []

        for o in olaylar:
            try:
                y, m, d = [int(x) for x in str(o.get("tarih", ""))[:10].split("-")]
                ojd = swe.julday(y, m, d, 12.0)
            except Exception:
                continue
            if not (h_bas <= ojd < h_son):
                continue
            etki = LUNASYON_ETKI.get(str(o.get("tur")), {})
            agir = min(1.5, (o.get("agirlik") or 2) / 4.0)
            for k, v in etki.items():
                puan[k] = puan.get(k, 0) + v * agir
            ev = o.get("natal_ev")
            if ev:
                for k in EV_HAMLE.get(int(ev), []):
                    puan[k] = puan.get(k, 0) + 0.7
            sebep.append(f"{o.get('tarih')} {o.get('tur')}"
                         + (f" ({ev}. ev)" if ev else ""))

        # Sükût: sessizse kişi kendi hareketini yapar → başlatmak/söylemek
        for a in (sukut.get("sukut_araliklari") or []):
            if a.get("basla", "9") <= jd_to_iso(h_bas)[:10] <= a.get("bitis", "0"):
                puan["baslatmak"] += 0.6
                puan["cekilmek"] += 0.4
                sebep.append("sessiz aralık — dışarıdan itiş yok")
        for a in (sukut.get("sikisma_araliklari") or []):
            if a.get("basla", "9") <= jd_to_iso(h_bas)[:10] <= a.get("bitis", "0"):
                puan["cekilmek"] += 0.8
                puan["baslatmak"] -= 0.6
                sebep.append("sıkışık aralık — dışarıdan baskı var")

        en = max(puan.items(), key=lambda x: x[1])
        haftalar.append({
            "hafta": h + 1,
            "basla": jd_to_iso(h_bas)[:10],
            "bitis": jd_to_iso(h_son - 1)[:10],
            "puanlar": {k: round(v, 2) for k, v in puan.items()},
            "en_uygun": en[0], "en_uygun_ad": HAMLELER[en[0]][0],
            "en_uygun_puan": round(en[1], 2),
            "sebep": sebep,
        })

    # Her hamle türü için en iyi hafta
    en_iyi: Dict[str, dict] = {}
    for k, (ad, acik) in HAMLELER.items():
        best = max(haftalar, key=lambda w: w["puanlar"].get(k, -9))
        en_iyi[k] = {
            "ad": ad, "aciklama": acik,
            "hafta": best["hafta"], "basla": best["basla"],
            "bitis": best["bitis"], "puan": best["puanlar"].get(k, 0),
            "sebep": best["sebep"][:2],
        }

    return {
        "modul": "HAMLE PENCERESİ — hangi hafta hangi hamleye uygun",
        "hafta_sayisi": hafta,
        "taban_egilim": {HAMLELER[k][0]: round(v, 2)
                         for k, v in sorted(taban.items(), key=lambda x: -x[1])},
        "yapisal_notlar": notlar,
        "haftalar": haftalar,
        "en_iyi": en_iyi,
        "okuma": _okuma(en_iyi, taban, notlar),
        "talimat": _talimat(en_iyi, taban),
        "yontem": ("Beş hamle türü haftalık puanlanır. Puan iki kaynaktan: "
                   "(1) kişinin yapısal tabanı — karar eşiği türü, "
                   "Kabz/Bast evresi, yaş eşiği yığılması; (2) o haftaya "
                   "düşen lunasyon türü, düştüğü ev, ve sükût basıncı. "
                   "Seçim astrolojisi genel 'uğurlu gün' verir; bu, KİŞİNİN "
                   "kendi alan yapısına göre hesaplanır."),
        "sinir": ("Pencere GARANTİ DEĞİLDİR. 'Bu hafta başlat' denmez; "
                  "'bu hafta başlatmak daha az sürtünmeyle olur' denir. "
                  "Kötü hafta yoktur: her hafta bir şeye uygun, başka "
                  "şeye değildir."),
    }


def _okuma(en_iyi: Dict[str, dict], taban: Dict[str, float],
           notlar: List[str]) -> str:
    p = []
    guclu = max(taban.items(), key=lambda x: x[1])
    zayif = min(taban.items(), key=lambda x: x[1])
    if guclu[1] > 0.3:
        p.append(f"Bu kişinin yapısal eğilimi {HAMLELER[guclu[0]][0].lower()}"
                 f" yönünde; {HAMLELER[zayif[0]][0].lower()} ise ona karşı.")
    for k in ("baslatmak", "bitirmek", "soylemek"):
        e = en_iyi.get(k)
        if e:
            p.append(f"{e['ad']} için en uygun aralık {e['basla']} – "
                     f"{e['bitis']}.")
    if notlar:
        p.append(notlar[0])
    return " ".join(p)


def _talimat(en_iyi: Dict[str, dict], taban: Dict[str, float]) -> List[str]:
    t: List[str] = []
    zayif = min(taban.items(), key=lambda x: x[1])
    for k, e in en_iyi.items():
        t.append(f"{e['ad'].upper()} ({e['aciklama']}): {e['basla']} – "
                 f"{e['bitis']}"
                 + (f" · {', '.join(e['sebep'])}" if e["sebep"] else ""))
    t.append(f"YAPISAL ZORLUK: {HAMLELER[zayif[0]][0].lower()} bu kişide "
             "akıntıya karşı. O pencere geldiğinde bile fazladan destek "
             "gerekir; 'uygun zaman' demek 'kolay' demek değildir.")
    t.append("Pencere garanti değildir. 'Bu hafta yap' deme; 'bu hafta "
             "daha az sürtünmeyle olur' de.")
    return t
