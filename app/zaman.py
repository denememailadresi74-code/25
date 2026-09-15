#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ZAMAN OMURGASI — natal + Solar Return + sessizlik tek şeritte.

v12.x'te lunasyon, sükût, algı eşiği ve dönüş noktası ayrı kartlardı. Hepsi
başka kelimelerle "hangi ay ne olur" diye konuştuğu için hem arayüzü hem AI
metnini şişiriyordu. Bu katman hesapları silmez; tek zaman ekseninde birleştirir
ve her olayın natal ile yıllık haritadaki karşılığını ayrı tutar.
"""
from __future__ import annotations

import calendar
import datetime as dt
from typing import Any, Dict, List, Optional, Tuple

import swisseph as swe

from .astro import NatalChart, jd_to_iso, chart_at_jd, solar_return_jd
from .lunasyon import (lunasyon_takvimi, solar_donus, _temaslar, _agirlik,
                       kategori_bagi, oneri_uret)
from .sukut import sukut_haritasi
from .esik import algi_esigi
from .omur import donus_noktasi


# Referans sınıfı tek yerde tutulur. v13.4.1 bazı yıllık katmanları seçili
# Solar Return yılına, bazılarını bugüne bağlayınca aynı analiz iki farklı
# zamana konuşmaya başladı. Bu sözlük hem API sözleşmesinin hem Rasathane
# rozetlerinin tek kaynağıdır.
KATMAN_SINIFLARI: Dict[str, str] = {
    "berzah_v2": "natal_sabit",
    "kutleler": "natal_sabit",
    "hudud_felek": "natal_sabit",
    "kadim_katman": "natal_sabit",
    "human_design": "natal_sabit",
    "deneme_modulleri": "natal_sabit",
    "kartografi.natal": "natal_sabit",
    "sarsma": "natal_sabit",
    "cevaplanabilirlik": "natal_sabit",
    "yas_katmani": "referansa_bagli",
    "duraklama_izi": "referansa_bagli",
    "kayip_zaman": "referansa_bagli",
    "donus_noktasi": "referansa_bagli",
    "sira_cevrimi": "referansa_bagli",
    "lunasyon": "referansa_bagli",
    "sukut": "referansa_bagli",
    "hamle_penceresi": "referansa_bagli",
    "solar_v2": "referansa_bagli",
    "kartografi.gunes_donusu": "referansa_bagli",
    "kartografi.ay_donusu": "referansa_bagli",
    "algi_esigi": "referansa_bagli",
    "transit": "daima_bugun",
    "maneviyat": "daima_bugun",
}


def referans_ani(natal: NatalChart, sr_year: Optional[int] = None,
                  bugun: Optional[dt.datetime] = None) -> Dict[str, Any]:
    """Yıllık katmanların tek zaman çapası.

    Solar Return seçilirse bütün ``referansa_bagli`` katmanlar aynı dönüşün
    Julian gününü kullanır. Seçilmezse aynı sözleşme bugünü döndürür; böylece
    çağıranların her birinin ayrı ``utcnow()`` üretip birkaç saniyelik bile olsa
    farklı referanslara düşmesi engellenir.
    """
    simdi = bugun or dt.datetime.utcnow()
    bugun_jd = swe.julday(simdi.year, simdi.month, simdi.day,
                          simdi.hour + simdi.minute / 60.0 + simdi.second / 3600.0)
    bugun_iso = jd_to_iso(bugun_jd)
    if sr_year is None:
        return {
            "yil": None, "jd": float(bugun_jd), "an": bugun_iso,
            "kaynak": "bugun", "chart": None, "aktif": False,
            "bugun": bugun_iso, "fark_yil": 0,
        }

    yil = int(sr_year)
    sjd = float(solar_return_jd(natal, yil))
    sch = chart_at_jd(sjd, natal.lat, natal.lng, f"SR {yil}", natal.house_system)
    try:
        ry = int(jd_to_iso(sjd)[:4])
        by = int(bugun_iso[:4])
        fark = abs(by - ry)
    except Exception:
        fark = abs(simdi.year - yil)
    return {
        "yil": yil, "jd": sjd, "an": jd_to_iso(sjd),
        "kaynak": "solar_return", "chart": sch, "aktif": True,
        "bugun": bugun_iso, "fark_yil": int(fark),
    }


def solar_yil(natal: NatalChart, bugun: Optional[dt.date] = None) -> int:
    """Şu anda YÜRÜRLÜKTE olan Solar Return yılını döndürür.

    Solar Return doğum gününde yenilenir. Doğum günü henüz gelmediyse içinde
    bulunulan takvim yılının dönüşü gelecektedir; yürürlükteki harita geçen
yılın dönüşüdür. v12.9 `utcnow().year` ile gelecekteki dönüşü sessizce
    kullanabiliyordu.
    """
    bugun = bugun or dt.datetime.utcnow().date()
    # jd_ut UTC'dir; doğumdaki yerel takvim gününü geri kazanmak için kayıtlı
    # ofset eklenir. Saatin gün sınırına yakın olduğu doğumlarda yalnız revjul
    # kullanmak bir gün kaydırabiliyordu.
    y, m, d, _ = swe.revjul(natal.jd_ut + float(getattr(natal, "tz_offset", 0.0)) / 24.0)
    dogum_gunu = (int(m), int(d))
    bu_yil = bugun.year
    return bu_yil if (bugun.month, bugun.day) >= dogum_gunu else bu_yil - 1


def _olay_agirligi(olay: dict, temaslar: List[dict]) -> float:
    k = dict(olay)
    k["temaslar"] = temaslar
    return float(_agirlik(k))


def cift_oturt(natal: NatalChart, solar: Optional[NatalChart],
                ay_sayisi: int = 12, jd_bas: Optional[float] = None) -> dict:
    """Lunasyonları natal ve yıllık haritaya birbirini ezmeden iki kez oturtur."""
    temel = lunasyon_takvimi(natal, solar, jd_bas=jd_bas, ay_sayisi=ay_sayisi)
    s_cusps = list(getattr(solar, "cusps", []) or []) if solar else []
    sonuc = []
    for o in temel.get("olaylar") or []:
        natal_temas = list(o.get("temaslar") or [])
        solar_temas = _temaslar(solar, float(o.get("boylam", 0))) if solar else []
        n = _olay_agirligi(o, natal_temas)
        s = _olay_agirligi(o, solar_temas) if solar else 0.0
        toplam = max(n, s) + min(n, s) * 0.5 if solar else n
        k = dict(o)
        k["natal_temaslar"] = natal_temas
        k["solar_temaslar"] = solar_temas
        k["temaslar"] = natal_temas  # v1 tüketicileri kırılmasın
        k["agirliklar"] = {"natal": round(n, 2), "solar": round(s, 2),
                            "toplam": round(toplam, 2)}
        k["agirlik"] = round(toplam, 2)
        k["iki_harita"] = bool(solar and n >= 2.5 and s >= 2.5)
        # Kategori bağı artık iki temas setini de görsün; solar temasın kaybolması
        # yıllık haritayı yalnız ev yerleşimine indirgiyordu.
        bag_girdi = dict(k)
        bag_girdi["temaslar"] = natal_temas + [dict(t, kaynak="solar") for t in solar_temas]
        k["bag"] = kategori_bagi(bag_girdi)
        k["oneriler"] = oneri_uret(k, k["bag"])
        sonuc.append(k)
    sonuc.sort(key=lambda x: x.get("an", ""))
    return {
        "modul": "ÇİFT OTURTMA — natal + Solar Return",
        "solar_var": solar is not None,
        "olaylar": sonuc,
        "iki_harita_olaylari": [x for x in sonuc if x.get("iki_harita")],
        "en_agir": sorted(sonuc, key=lambda x: -float((x.get("agirliklar") or {}).get("toplam", 0)))[:6],
        "yontem": ("Her olay natal ve Solar Return haritasında ayrı ev/temaslarla tartılır. "
                   "Ağırlıklar birbiriyle ortalanmaz: toplam=max(a,b)+min(a,b)*0.5. "
                   "Her iki haritada da ≥2.5 olan olay iki_harita olarak işaretlenir."),
    }


def _ay_anahtari(tarih: str) -> str:
    return str(tarih or "")[:7]


def _aylar(bas: dt.date, adet: int = 12) -> List[Tuple[int, int]]:
    out = []
    y, m = bas.year, bas.month
    for _ in range(adet):
        out.append((y, m))
        m += 1
        if m == 13:
            y += 1; m = 1
    return out


def _aralik_ayda(aralik: dict, y: int, m: int) -> int:
    bas = str(aralik.get("basla") or aralik.get("baslangic") or "")[:10]
    bit = str(aralik.get("bitis") or "")[:10]
    if not bas or not bit:
        return 0
    try:
        a = dt.date.fromisoformat(bas); b = dt.date.fromisoformat(bit)
    except Exception:
        return 0
    ay_a = dt.date(y, m, 1)
    ay_b = dt.date(y, m, calendar.monthrange(y, m)[1])
    lo, hi = max(a, ay_a), min(b, ay_b)
    return max(0, (hi - lo).days + 1)


def serit(natal: NatalChart, solar: Optional[NatalChart] = None,
          ay_sayisi: int = 12, jd_bas: Optional[float] = None,
          solar_year: Optional[int] = None) -> dict:
    """Lunasyon + sükût + algı eşiği + dönüş noktası → tek 12 aylık şerit."""
    if jd_bas is None:
        u = dt.datetime.utcnow()
        jd_bas = swe.julday(u.year, u.month, u.day, u.hour + u.minute / 60.0)
    bas_tarih = dt.date.fromisoformat(jd_to_iso(jd_bas)[:10])
    cift = cift_oturt(natal, solar, ay_sayisi=max(ay_sayisi, 12), jd_bas=jd_bas)
    suk = sukut_haritasi(natal, jd_bas=jd_bas, gun=max(365, int(ay_sayisi * 30.5)))
    es = algi_esigi(natal, suk if "hata" not in suk else None)
    try:
        dn = donus_noktasi(natal, bugun_jd=jd_bas, ileri_yil=4.0)
    except Exception as exc:
        dn = {"hata": str(exc)[:180], "yaklasan": []}

    kat = float(es.get("esik_kat", 1.0) or 1.0) if "hata" not in es else 1.0
    gorunurluk = round(max(2.0, min(5.5, 2.5 * kat)), 2)
    gorunen = [o for o in cift["olaylar"]
               if float((o.get("agirliklar") or {}).get("toplam", 0)) >= gorunurluk]

    ay_kayit = []
    for y, m in _aylar(bas_tarih, ay_sayisi):
        anahtar = f"{y:04d}-{m:02d}"
        olay = [o for o in gorunen if _ay_anahtari(o.get("tarih", "")) == anahtar]
        ham = sum(float((o.get("agirliklar") or {}).get("toplam", 0)) for o in olay)
        iki = [o for o in olay if o.get("iki_harita")]
        yogunluk = min(100, round(ham * 9 + len(iki) * 12))

        gun = calendar.monthrange(y, m)[1]
        sessiz_gun = sum(_aralik_ayda(a, y, m) for a in (suk.get("sukut_araliklari") or []))
        sikisik_gun = sum(_aralik_ayda(a, y, m) for a in (suk.get("sikisma_araliklari") or []))
        sessizlik = min(100, round(sessiz_gun / max(1, gun) * 100))
        sikisma = min(100, round(sikisik_gun / max(1, gun) * 100))
        donus = [x for x in (dn.get("yaklasan") or []) if str(x.get("sonraki") or "")[:7] == anahtar]

        if donus:
            doku = "dönüş"
        elif yogunluk >= 70:
            doku = "yüklü"
        elif sikisma >= 35:
            doku = "sıkışık"
        elif sessizlik >= 40:
            doku = "sessiz"
        elif iki or yogunluk >= 40:
            doku = "hareketli"
        else:
            doku = "olağan"

        en = max(olay, key=lambda x: float((x.get("agirliklar") or {}).get("toplam", 0))) if olay else None
        if doku == "sessiz":
            cumle = "Dış gök baskısı seyrek; şikâyet varsa sebebi otomatik olarak zamana yükleme."
        elif doku == "dönüş":
            cumle = "Yavaş bir kapı bu aya denk geliyor; olaydan çok tekrar etmeyecek ağırlığına bak."
        elif en:
            alan = ((en.get("bag") or {}).get("alan_natal") or "bir yaşam alanı")
            ek = " ve yıllık haritada da aynı anda güçlü" if en.get("iki_harita") else ""
            cumle = f"{alan.capitalize()} konusu görünürleşiyor{ek}; zorlamadan neyin kendiliğinden açıldığına bak."
        else:
            cumle = "Eşiği aşan belirgin olay az; sıradan hareketi büyük bir işaret gibi büyütme."

        ay_kayit.append({
            "ay": anahtar, "ad": dt.date(y, m, 1).strftime("%B"),
            "yogunluk": yogunluk, "sessizlik": sessizlik, "sikisma": sikisma,
            "doku": doku, "cumle": cumle, "olaylar": olay,
            "iki_harita": len(iki), "donus": donus,
        })

    return {
        "modul": "ZAMAN ŞERİDİ · on iki aylık tek omurga",
        # Solar yılı artık takvimden yeniden türetilmez. Kullanıcı formda hangi
        # yılı seçtiyse o yıl taşınır; Solar Return kapalıysa None kalır.
        "solar_yil": int(solar_year) if (solar is not None and solar_year is not None) else None,
        "solar_var": solar is not None,
        "gorunurluk_esigi": gorunurluk, "esik": es,
        "aylar": ay_kayit, "iki_harita_olaylari": cift.get("iki_harita_olaylari") or [],
        "gizlenen_olay": max(0, len(cift.get("olaylar") or []) - len(gorunen)),
        "sukut": {k: suk.get(k) for k in ("sukut_orani", "ortalama_basinc", "doku", "yanlislama") if k in suk},
        "donus": {"yaklasan": (dn.get("yaklasan") or [])[:5], "kapanmis": (dn.get("kapanmis") or [])[:3]},
        "yontem": (("Lunasyon/tutulma natal ve seçilen Solar Return'de ayrı tartılır. "
                    "Algı eşiğinin altında kalan olaylar şeride alınmaz. Yoğunluk olay yükünü, "
                    "sessizlik dış baskının yokluğunu ölçer; biri diğerinin tersi değildir.")
                   if solar is not None else
                   ("Solar Return bağlanmadığı için şerit yalnız natal haritaya göre kuruldu. "
                    "Algı eşiğinin altında kalan olaylar alınmaz; yoğunluk ile sessizlik ayrı eksenlerdir.")),
        "sinir": ("Şerit olay kehaneti değildir. 'Kolaylaşıyor' daha az sürtünme veya daha çok görünürlük "
                  "demektir; sonucun garanti olduğu anlamına gelmez."),
    }
