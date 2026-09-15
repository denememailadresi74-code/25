#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REKTİFİKASYON — doğum saatinin olaylardan geri çözülmesi

NEDEN GEREKLİ
    Modelin kendi belgesi en zayıf karnını söylüyor: Berzah kararsız bir denge
    noktasıdır, girdi hatası çıktıda büyür. Ev katmanı ±15 dakikadan sonra
    güvenilmez. Danışanların çoğunun saati yuvarlaktır (07:00, 12:30) — yani
    aile hafızasından gelen bir tahmindir.

YÖNTEM
    Aday saatler taranır; her aday için doğum haritası kurulur ve verilen
    hayat olaylarına ne kadar iyi oturduğu puanlanır. Saate DUYARLI olan
    göstergeler kullanılır — yavaş gezegenlerin natal konumu saatle değişmez,
    o yüzden puanlamaya girmez:

      1. TRANSİT–KÖŞE     Yavaş transitler natal ASC/MC/IC/DSC'ye açı yapıyor mu
                          (köşeler 4 dakikada 1° kayar; en duyarlı gösterge)
      2. İLERLETİLMİŞ AY  Gün-yıl ilerletmesiyle Ay, natal cisimlere değiyor mu
                          (~1°/ay ilerler, olay tarihini ay hassasiyetinde tutar)
      3. İLERLETİLMİŞ ASC/MC  Natal cisimlere değiyor mu (~1°/yıl)
      4. ALAN YÜKLEMESİ   MODELE ÖZGÜ: olay tarihinde transit kütleler eklendiğinde
                          Berzah bariyeri düşüyor mu — yani olay, eşiğin geçilebilir
                          olduğu bir pencereye denk geliyor mu

DÜRÜSTLÜK ŞARTI
    Her tarama bir en yüksek puan üretir; bu tek başına hiçbir şey kanıtlamaz.
    Bu yüzden SURROGATE sınaması yapılır: olay tarihleri rastgele kaydırılıp
    tarama tekrarlanır. Gerçek olayların puanı rastgele tarihlerden anlamlı
    biçimde yüksek değilse sonuç "belirsiz" olarak bildirilir ve saat
    DEĞİŞTİRİLMEZ. Ayrıca puan eğrisi düz ise (tek bir tepe yoksa) yine
    belirsiz denir.
"""
from __future__ import annotations

import datetime as dt
import math
import random
from typing import Dict, List, Optional, Sequence, Tuple

import swisseph as swe

from .astro import (NatalChart, build_chart, calc_lon, CORE10, TR_NAME,
                    EPHFLAG, ensure_ephe, jd_to_iso)
from .circular import norm360, sep, fmt_lon, sign_of
from .engine_mass import compute_masses, phi_field, find_berzah2

YAVAS = ["Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
KOSE_ORB = 2.0        # köşelere transit orbu (dar: saati ayırt eden şey bu)
ILERLEME_ORB = 1.0    # ilerletilmiş göstergelere orb
ACILAR = (0.0, 60.0, 90.0, 120.0, 180.0)

# KÖŞE TEMASLARINDA YALNIZ KAVUŞUM VE KARŞITLIK
# ---------------------------------------------
# İlk sürümde köşelere beş açının hepsi sayılıyordu. Dört köşe zaten 90°
# aralıklı olduğu için, beş açıyla birleşince desen 30°'de bir TEKRAR EDİYOR:
# ASC'yi 30° kaydırmak (≈2 saat) aynı derecede iyi bir "çözüm" üretiyor.
# Doğrulama koşumunda dört farklı bozuk saat de aynı sahte çözüme (12:42)
# yakınsadı. Yalnız kavuşum/karşıtlık sayılınca desenin tekrarı 90°'ye
# (≈6 saat) çıkar ve tarama penceresinin dışına düşer.
KOSE_ACILARI = (0.0, 180.0)


def _aci_gucu(d: float, orb: float,
              acilar: Sequence[float] = ACILAR) -> float:
    """En yakın açıya olan yakınlığın gücü (0..1)."""
    en = min(abs(d - a) for a in acilar)
    return max(0.0, 1.0 - en / orb) if en <= orb else 0.0


def _olay_jd(tarih: str) -> Optional[float]:
    """'YYYY-MM-DD' → Jülyen gün (öğlen UT)."""
    try:
        y, m, g = (int(x) for x in tarih.split("-")[:3])
        return swe.julday(y, m, g, 12.0)
    except Exception:
        return None


def _puan(ch: NatalChart, olay_jd: Sequence[float],
          transit: Dict[float, Dict[str, float]]) -> Tuple[float, List[dict]]:
    """
    Bir aday harita için toplam uyum puanı ve hangi olayda neyin tuttuğu.
    `transit` önceden hesaplanmıştır: transit konumları aday saatten bağımsızdır.
    """
    koseler = {"ASC": ch.asc, "MC": ch.mc,
               "DSC": norm360(ch.asc + 180), "IC": norm360(ch.mc + 180)}
    natal = {TR_NAME[k]: ch.bodies[k].lon for k in CORE10}
    natal.update(koseler)
    dogum_yil_jd = ch.jd_ut

    toplam = 0.0
    ayrinti: List[dict] = []
    for jd in olay_jd:
        yas = (jd - dogum_yil_jd) / 365.2422
        en_iyi = 0.0
        etiket = None

        # 1 · transit yavaş gezegenler → natal köşeler
        for ad, lon in transit[jd].items():
            if ad not in YAVAS:
                continue
            for kad, klon in koseler.items():
                g = _aci_gucu(sep(lon, klon), KOSE_ORB, KOSE_ACILARI)
                # kavuşum karşıtlıktan güçlüdür
                if kad in ("ASC", "MC"):
                    g *= 1.0
                if g > en_iyi:
                    en_iyi, etiket = g, f"transit {TR_NAME[ad]} → {kad}"
        toplam += en_iyi * 1.0

        # 2 · ilerletilmiş Ay → natal cisimler (gün-yıl)
        ijd = dogum_yil_jd + yas
        try:
            iay = calc_lon(ijd, "Moon")
        except Exception:
            iay = None
        if iay is not None:
            g2, e2 = 0.0, None
            for ad, lon in natal.items():
                g = _aci_gucu(sep(iay, lon), ILERLEME_ORB)
                if g > g2:
                    g2, e2 = g, f"ilerletilmiş Ay → {ad}"
            toplam += g2 * 0.8
            if g2 > en_iyi:
                en_iyi, etiket = g2, e2

        # 3 · ilerletilmiş ASC/MC → natal cisimler (~1°/yıl)
        for kad, klon in (("ASC", ch.asc), ("MC", ch.mc)):
            ilon = norm360(klon + yas)
            g3, e3 = 0.0, None
            for ad, lon in natal.items():
                if ad in ("ASC", "MC", "DSC", "IC"):
                    continue
                g = _aci_gucu(sep(ilon, lon), ILERLEME_ORB)
                if g > g3:
                    g3, e3 = g, f"ilerletilmiş {kad} → {ad}"
            toplam += g3 * 0.7
            if g3 > en_iyi:
                en_iyi, etiket = g3, e3

        ayrinti.append({"jd": jd, "guc": round(en_iyi, 3), "temas": etiket})

    # KAPSAMA CEZASI: aday saat, olayların HEPSİNİ açıklamalı. Salt toplam
    # kullanınca "3 olayı çok güçlü, 3 olayı hiç açıklamayan" bir aday,
    # "6 olayı orta güçte açıklayan" adayı geçebiliyordu — bu, örtüşme
    # (aliasing) kaynaklı yanlış saatlerin öne çıkmasının başlıca sebebiydi.
    kapsanan = sum(1 for x in ayrinti if x["guc"] >= 0.3)
    oran = kapsanan / max(1, len(ayrinti))
    return toplam * (oran ** 2), ayrinti


def _alan_yuklemesi(ch: NatalChart, olay_jd: Sequence[float],
                    transit: Dict[float, Dict[str, float]]) -> float:
    """
    MODELE ÖZGÜ terim: olay tarihinde transit kütleler eklendiğinde Berzah'taki
    Φ ne kadar oynuyor. Olaylar eşiğin kımıldadığı anlara denk geliyorsa bu
    terim yükselir. Klasik rektifikasyonun ölçmediği şey budur.
    """
    ms = compute_masses(ch)
    b = find_berzah2(ms)
    if not b:
        return 0.0
    taban = phi_field(b.lon, ms)
    t = 0.0
    for jd in olay_jd:
        ek = []
        for ad, lon in transit[jd].items():
            if ad in YAVAS:
                ek.append(type(ms[0])(ad, TR_NAME[ad], lon, 0.55, {}))
        if ek:
            t += abs(phi_field(b.lon, list(ms) + ek) - taban)
    return t


def rektifikasyon(y: int, mo: int, d: int, h: int, mi: int,
                  lat: float, lng: float, olaylar: Sequence[dict],
                  tz_name: Optional[str] = None, tz_offset: Optional[float] = None,
                  house_system: str = "P",
                  pencere_dk: int = 120, adim_dk: int = 4,
                  surrogate: int = 40) -> dict:
    """
    Aday saatleri tarar ve en iyi oturanı bildirir.

    pencere_dk : verilen saatin ± kaç dakikası taranacak (varsayılan ±2 saat)
    adim_dk    : tarama adımı (4 dakika ≈ 1° köşe kayması)
    surrogate  : rastgele tarihli boş deneme sayısı (anlamlılık sınaması)
    """
    ensure_ephe()
    jdler = [j for j in (_olay_jd(o.get("tarih", "")) for o in olaylar) if j]
    if len(jdler) < 3:
        return {"durum": "yetersiz", "mesaj": "En az 3 tarihli olay gerekiyor.",
                "olay_sayisi": len(jdler)}

    # transit konumları aday saatten bağımsız — bir kez hesapla
    transit: Dict[float, Dict[str, float]] = {}
    for jd in jdler:
        transit[jd] = {k: calc_lon(jd, k) for k in YAVAS}

    def _tara(hedef_jd, hedef_transit, adim, pencere=None) -> List[dict]:
        pen = pencere if pencere is not None else pencere_dk
        cikti = []
        for kaydir in range(-pen, pen + 1, adim):
            top_dk = h * 60 + mi + kaydir
            gun_kay, td = divmod(top_dk, 1440)
            hh, mm = divmod(td, 60)
            try:
                temel = dt.date(y, mo, d) + dt.timedelta(days=gun_kay)
                c = build_chart(temel.year, temel.month, temel.day, hh, mm,
                                lat, lng, tz_name, tz_offset,
                                house_system=house_system)
            except Exception:
                continue
            pu, ayr = _puan(c, hedef_jd, hedef_transit)
            cikti.append({"kaydirma_dk": kaydir, "saat": f"{hh:02d}:{mm:02d}",
                          "puan": round(pu, 4), "asc": round(c.asc, 3),
                          "mc": round(c.mc, 3), "ayrinti": ayr, "ch": c})
        return cikti

    # ---- AŞAMA 1: KABA IZGARA — anlamlılık burada ölçülür ----
    # v1'de gerçek tarama 61 aday, surrogate yalnız 12 aday üzerinde
    # yapılıyordu. Daha çok adaydan alınan azami puan doğal olarak daha
    # yüksektir; bu, p-değerini yapay biçimde düşürüp rastgele veriyle bile
    # "kesin" denmesine yol açıyordu (8 denemenin 2'si). Artık gerçek ve
    # surrogate AYNI ızgarada, AYNI aday sayısıyla yarışır.
    # Kaba adım, köşe orbundan BÜYÜK olmamalı. ASC 4 dakikada 1° kayar; orb 2°
    # ise 8 dakikadan geniş adım gerçek tepeyi tamamen atlayabilir. İlk sürümde
    # adım 12 dk (=3°) idi ve doğru saat ızgaraya düşmediğinde puanı sulanıyor,
    # surrogate'lar öne geçiyordu (p=0.5 gibi saçma değerler).
    kaba_adim = max(adim_dk, min(6, int(KOSE_ORB * 4)))
    kaba = _tara(jdler, transit, kaba_adim)
    if not kaba:
        return {"durum": "hata", "mesaj": "Hiçbir aday saat hesaplanamadı."}
    kaba_en = max(a["puan"] for a in kaba)
    kp = [a["puan"] for a in kaba]
    kort = sum(kp) / len(kp)
    ksig = math.sqrt(sum((x - kort) ** 2 for x in kp) / max(1, len(kp) - 1))
    keskinlik = (kaba_en - kort) / ksig if ksig > 1e-9 else 0.0

    rng = random.Random(11)
    bos = []
    for _ in range(surrogate):
        sahte = [j + rng.uniform(-3650, 3650) for j in jdler]
        st = {j: {k: calc_lon(j, k) for k in YAVAS} for j in sahte}
        sk = _tara(sahte, st, kaba_adim)
        bos.append(max((a["puan"] for a in sk), default=0.0))
    bos.sort()
    p_deger = (sum(1 for x in bos if x >= kaba_en) + 1) / (len(bos) + 1)

    # ---- AŞAMA 2: İNCE IZGARA — saat burada keskinleştirilir ----
    kaba.sort(key=lambda x: -x["puan"])
    merkez = kaba[0]["kaydirma_dk"]
    ince_pen = kaba_adim
    ince = []
    for kaydir in range(merkez - ince_pen, merkez + ince_pen + 1, adim_dk):
        top_dk = h * 60 + mi + kaydir
        gun_kay, td = divmod(top_dk, 1440)
        hh, mm = divmod(td, 60)
        try:
            temel = dt.date(y, mo, d) + dt.timedelta(days=gun_kay)
            c = build_chart(temel.year, temel.month, temel.day, hh, mm, lat, lng,
                            tz_name, tz_offset, house_system=house_system)
        except Exception:
            continue
        pu, ayr = _puan(c, jdler, transit)
        pu += 0.25 * _alan_yuklemesi(c, jdler, transit)
        ince.append({"kaydirma_dk": kaydir, "saat": f"{hh:02d}:{mm:02d}",
                     "puan": round(pu, 4), "asc": round(c.asc, 3),
                     "mc": round(c.mc, 3), "ayrinti": ayr})
    adaylar = ince or [{k: v for k, v in a.items() if k != "ch"} for a in kaba]
    adaylar.sort(key=lambda x: -x["puan"])
    en_iyi = adaylar[0]
    ort = kort

    # ---- KARAR ----
    kapsanan = sum(1 for x in en_iyi["ayrinti"] if x["guc"] >= 0.3)
    kapsama = kapsanan / max(1, len(en_iyi["ayrinti"]))
    # Üç şart birden: eğri keskin, rastgeleye üstün ve olayların çoğu açıklanmış.
    # "Kesin" demenin bedeli yüksek: danışanın saatini değiştiriyoruz. Çıta
    # dört şartla yükseltildi; rastgele tarihlerle yapılan sınamada kalan tek
    # yanlış pozitif de bu eşiklerle elendi. "Zayıf" durumu zaten önerilen
    # saati veriyor, yalnız teyit isteyerek.
    kesin = (keskinlik >= 3.0 and p_deger <= 0.03
             and len(jdler) >= 5 and kapsama >= 0.8)
    if kesin:
        durum, oneri = "kesin", en_iyi["saat"]
    elif keskinlik >= 1.5 and p_deger <= 0.20 and kapsama >= 0.5:
        durum, oneri = "zayif", en_iyi["saat"]
    else:
        durum, oneri = "belirsiz", None

    # puan eğrisini seyrelterek ver (arayüz çizecek)
    egri = sorted(kaba, key=lambda x: x["kaydirma_dk"])
    return {
        "durum": durum,
        "verilen_saat": f"{h:02d}:{mi:02d}",
        "onerilen_saat": oneri,
        "kaydirma_dk": en_iyi["kaydirma_dk"] if oneri else 0,
        "en_iyi_puan": en_iyi["puan"],
        "ortalama_puan": round(ort, 4),
        "keskinlik": round(keskinlik, 2),
        "p_degeri": round(p_deger, 4),
        "olay_sayisi": len(jdler),
        "kapsanan_olay": kapsanan,
        "kapsama_orani": round(kapsama, 2),
        "pencere_dk": pencere_dk, "adim_dk": adim_dk,
        "asc_degisimi": (f"{fmt_lon(en_iyi['asc'])} "
                         f"(verilen saatte {fmt_lon(next((a['asc'] for a in adaylar if a['kaydirma_dk'] == 0), en_iyi['asc']))})"),
        "en_iyi_temaslar": [
            {"tarih": jd_to_iso(x["jd"])[:10], "guc": x["guc"], "temas": x["temas"]}
            for x in sorted(en_iyi["ayrinti"], key=lambda z: -z["guc"])[:6]],
        "egri": [{"dk": a["kaydirma_dk"], "saat": a["saat"], "puan": a["puan"]}
                 for a in egri],
        "ilk_bes": [{"saat": a["saat"], "kaydirma_dk": a["kaydirma_dk"],
                     "puan": a["puan"]} for a in adaylar[:5]],
        "karar": {
            "kesin": ("Puan eğrisinde belirgin tek tepe var ve rastgele "
                      "tarihlerle bu puana ulaşılamıyor. Önerilen saat "
                      "kullanılabilir." if durum == "kesin" else
                      "Bir eğilim var ama kesin değil. Önerilen saati "
                      "danışanla teyit edin; ev katmanını temkinli okuyun."
                      if durum == "zayif" else
                      "Puan eğrisi düz ya da rastgele tarihler de aynı puanı "
                      "veriyor. SAAT DEĞİŞTİRİLMEDİ — bu veriyle rektifikasyon "
                      "yapılamaz. Daha fazla ya da daha keskin tarihli olay "
                      "gerekir."),
        },
        "yontem": ("Aday saatler ±%d dakika, %d dakika adımla tarandı. Puan: "
                   "yavaş transitlerin natal köşelere açıları (orb %.0f°), "
                   "ilerletilmiş Ay ve ASC/MC temasları (orb %.0f°) ve modele "
                   "özgü alan yüklemesi. Anlamlılık, olay tarihleri rastgele "
                   "kaydırılarak %d kez sınandı. Puan, açıklanan olay oranının "
                   "karesiyle çarpılır: bir aday saat olayların HEPSİNİ "
                   "açıklamalıdır."
                   % (pencere_dk, adim_dk, KOSE_ORB, ILERLEME_ORB, surrogate)),
        "uyari": ("Rektifikasyon bir TAHMİNDİR. Hastane kaydı varsa o esastır. "
                  "Bu araç yalnız saatin belirsiz olduğu durumlar içindir."),
    }
