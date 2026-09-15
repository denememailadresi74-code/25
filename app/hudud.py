#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUDÛD-I FELEK — DEKLİNASYON KATMANI VE KÜRESEL ALAN  (ZÎC v3.9 icadı)

Modelin bugüne kadarki kör noktası: Φ alanı YALNIZ BOYLAMDA hesaplanıyordu.
Oysa gökyüzü iki boyutludur. Bu iki sonuç doğuruyordu:

  · Boylamda 3° yakın ama deklinasyonda 45° uzak iki cisim "kavuşum" sayılıyor,
    oysa gökküre üzerinde 45° ayrıdırlar — hiç de yakın değiller.
  · Boylamda hiç açı yapmayan ama aynı deklinasyonda duran iki cisim
    "ilişkisiz" sayılıyor, oysa klasik gelenekte bu bir KAVUŞUM kadar güçlüdür.

Üç katman:

  A · PARALEL / KARŞIT-PARALEL
      Aynı deklinasyon (paralel) veya eşit büyüklükte zıt işaret
      (karşıt-paralel). Ptolemy'den beri kullanılır. Asıl değeri GİZLİ
      olanlardadır: boylamda hiçbir açı yapmayan ama deklinasyonda bağlı
      çiftler — bu model şimdiye kadar onları hiç görmüyordu.

  B · HUDÛD DIŞI (out-of-bounds)
      Deklinasyonu ekliptik eğikliğini (≈23.44°, tarihe göre hesaplanır)
      aşan cisim, Güneş'in hiç ulaşamadığı bir enlemdedir. BERZAH diliyle:
      iki denizin de dışına taşmış bir kapasite. Kendi kurallarına uymaz.

  C · KÜRESEL ALAN  Φ(α, δ)
      Gerçek açısal ayrım kullanılarak alan gökküre üzerinde kurulur:
          cos d = sin δ₁·sin δ₂ + cos δ₁·cos δ₂·cos(α₁ − α₂)
      Küresel Kara Delik, boylam-KD'sinden sapıyorsa boylam okuması
      YANILTICIDIR ve sapma miktarı bunu ölçer.
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence, Tuple

import swisseph as swe

from .astro import NatalChart, CORE10, TR_NAME, EPHFLAG, ensure_ephe, jd_to_iso
from .circular import norm360, sep, fmt_lon, sign_of
from .engine_mass import compute_masses, MassBody, EPS

PARALEL_ORB = 1.0       # derece — klasikte dar tutulur
# Hudûd dışı sayılmak için eğikliği en az bu kadar aşmak gerekir. Sıfır pay
# bırakılırsa gündönümünde doğanların GÜNEŞ'i kayan nokta hatasıyla "hudûd
# dışı" çıkıyordu; Güneş tanımı gereği eğikliği aşamaz.
OOB_PAY = 0.05
# Güneş hiçbir zaman hudûd dışı olamaz: eğiklik zaten Güneş'in azami
# deklinasyonudur. Listeden yapısal olarak çıkarılır.
OOB_HARIC = {"Sun"}


# ============================================================================
# yardımcılar
# ============================================================================
def egiklik(jd: float) -> float:
    """Tarihe ait GERÇEK ekliptik eğikliği. Sabit 23.44 kullanmak yanlış olur:
    değer yüzyılda ~0.013° azalır ve hudûd dışı sınırını doğrudan belirler."""
    ensure_ephe()
    try:
        (eps, *_), _ = swe.calc_ut(jd, swe.ECL_NUT, EPHFLAG)
        return float(eps)
    except Exception:
        T = (jd - 2451545.0) / 36525.0
        return 23.439291 - 0.0130042 * T


def acisal_ayrim(a1: float, d1: float, a2: float, d2: float) -> float:
    """Gökküre üzerinde iki nokta arasındaki gerçek açısal uzaklık (derece)."""
    r = math.radians
    c = (math.sin(r(d1)) * math.sin(r(d2))
         + math.cos(r(d1)) * math.cos(r(d2)) * math.cos(r(a1 - a2)))
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


def ekliptikten_ekvatora(lon: float, eps: float,
                         lat: float = 0.0) -> Tuple[float, float]:
    """Ekliptik (λ, β) → ekvatoral (α, δ)."""
    r = math.radians
    sl, cl = math.sin(r(lon)), math.cos(r(lon))
    sb, cb = math.sin(r(lat)), math.cos(r(lat))
    se, ce = math.sin(r(eps)), math.cos(r(eps))
    a = math.degrees(math.atan2(sl * ce - (sb / max(cb, 1e-12)) * se, cl))
    d = math.degrees(math.asin(sb * ce + cb * se * sl))
    return norm360(a), d


# ============================================================================
# A · PARALEL / KARŞIT-PARALEL
# ============================================================================
def paraleller(chart: NatalChart, ms: Sequence[MassBody],
               orb: float = PARALEL_ORB) -> dict:
    """
    Deklinasyon temasları. Boylamdaki açı durumu da işaretlenir: asıl bulgu,
    boylamda HİÇBİR açı olmadığı hâlde deklinasyonda bağlı olan çiftlerdir.
    """
    from .modules_deneme import _ASPECTS

    def boylam_acisi(l1: float, l2: float) -> Optional[str]:
        d = sep(l1, l2)
        for nm, glif, ang, ob, w, majör in _ASPECTS:
            if abs(d - ang) <= ob:
                return f"{nm} ({abs(d - ang):.1f}°)"
        return None

    cisimler = [(k, chart.bodies[k]) for k in CORE10]
    kutle = {m.name: m.abs_mass for m in ms}
    out: List[dict] = []
    for i in range(len(cisimler)):
        for j in range(i + 1, len(cisimler)):
            k1, b1 = cisimler[i]
            k2, b2 = cisimler[j]
            fark_p = abs(b1.decl - b2.decl)                 # paralel
            fark_k = abs(b1.decl + b2.decl)                 # karşıt-paralel
            tur, o = (None, None)
            if fark_p <= orb:
                tur, o = "paralel", fark_p
            elif fark_k <= orb:
                tur, o = "karşıt-paralel", fark_k
            if not tur:
                continue
            bo = boylam_acisi(b1.lon, b2.lon)
            out.append({
                "a": b1.name_tr, "b": b2.name_tr, "tur": tur,
                "orb": round(o, 2),
                "dekl_a": round(b1.decl, 2), "dekl_b": round(b2.decl, 2),
                "guc": round((1 - o / orb) * min(kutle.get(b1.name_tr, 1),
                                                 kutle.get(b2.name_tr, 1)), 3),
                "boylam_acisi": bo,
                "gizli": bo is None,
                "anlam": ("aynı yönde çalışırlar; biri hareket edince öteki de eder"
                          if tur == "paralel" else
                          "birbirini dengeler; biri artınca öteki azalır"),
            })
    out.sort(key=lambda x: (-int(x["gizli"]), -x["guc"]))
    gizli = [x for x in out if x["gizli"]]
    return {
        "temaslar": out,
        "gizli_baglar": gizli,
        "orb": orb,
        "okuma": ("Gizli bağ yok — deklinasyon katmanı boylamla aynı şeyi söylüyor."
                  if not gizli else
                  f"{len(gizli)} GİZLİ bağ var: bu çiftler boylamda hiç açı "
                  "yapmıyor, dolayısıyla klasik okumada görünmezler; ama aynı "
                  "deklinasyon kuşağında oldukları için birlikte hareket ederler."),
        "yontem": ("Paralel: iki cismin deklinasyonu aynı işaretli ve eşit. "
                   "Karşıt-paralel: eşit büyüklükte zıt işaretli. Orb 1°, "
                   "klasik gelenekteki gibi dar."),
    }


# ============================================================================
# B · HUDÛD DIŞI
# ============================================================================
def hudud_disi(chart: NatalChart) -> dict:
    eps = egiklik(chart.jd_ut)
    disari = []
    sinirda = []
    for k in CORE10:
        if k in OOB_HARIC:
            continue
        b = chart.bodies[k]
        asim = abs(b.decl) - eps
        if asim <= OOB_PAY:
            continue
        kayit = {
            "cisim": b.name_tr, "dekl": round(b.decl, 3),
            "asim": round(asim, 3),
            "yon": "kuzey" if b.decl > 0 else "güney",
            "konum": fmt_lon(b.lon),
            "ev": chart.house(b.lon),
            # 0.5°'den az aşım ölçüm gürültüsü mesafesindedir; ayrı işaretlenir
            "sinirda": asim < 0.5,
        }
        (sinirda if kayit["sinirda"] else disari).append(kayit)
    disari.sort(key=lambda x: -x["asim"])
    sinirda.sort(key=lambda x: -x["asim"])
    return {
        "egiklik": round(eps, 4),
        "hudud_disi": disari,
        "sinirdakiler": sinirda,
        "sayi": len(disari),
        "okuma": ("Hiçbir cisim hudûdun dışına taşmıyor — kapasiteler kişinin "
                  "kendi düzeni içinde çalışıyor." if not disari else
                  f"{', '.join(x['cisim'] for x in disari)} hudûdun dışında: "
                  "Güneş'in hiç ulaşamadığı bir enlemde duruyor. Bu kapasite "
                  "kişinin kendi kurallarına uymaz; ne bastırılabilir ne "
                  "evcilleştirilebilir, ancak kendine ayrı bir alan açılarak "
                  "yönetilir."),
        "yontem": (f"Deklinasyonu tarihe ait gerçek eğikliği ({eps:.3f}°) "
                   f"{OOB_PAY}° payla aşan cisimler. Sabit 23.44 kullanılmaz: "
                   "eğiklik yüzyılda ~0.013° azalır ve sınırı doğrudan belirler. "
                   "Güneş yapısal olarak hariçtir — eğiklik zaten onun azami "
                   "deklinasyonudur. 0.5°'den az aşımlar 'sınırda' sayılır."),
    }


# ============================================================================
# C · KÜRESEL ALAN Φ(α, δ)
# ============================================================================
def _kuresel_kutleler(chart: NatalChart,
                      ms: Sequence[MassBody]) -> List[Tuple[float, float, float, str]]:
    """(RA, dekl, kütle, ad) listesi."""
    m_ad = {m.name: m.mass for m in ms}
    out = []
    for k in CORE10:
        b = chart.bodies[k]
        out.append((b.ra, b.decl, m_ad.get(b.name_tr, 1.0), b.name_tr))
    return out


def _phi_kuresel(a: float, d: float,
                 kutleler: Sequence[Tuple[float, float, float, str]]) -> float:
    r = math.radians
    sd, cd = math.sin(r(d)), math.cos(r(d))
    t = 0.0
    for (a2, d2, m, _ad) in kutleler:
        c = sd * math.sin(r(d2)) + cd * math.cos(r(d2)) * math.cos(r(a - a2))
        ayrim = math.degrees(math.acos(max(-1.0, min(1.0, c))))
        t += m / (ayrim + EPS)
    return t


def kuresel_alan(chart: NatalChart, ms: Optional[Sequence[MassBody]] = None,
                 adim: float = 2.0) -> dict:
    """
    Alanı gökküre üzerinde kurar ve boylam-yalnız okumayla karşılaştırır.

    Sapma büyükse boylam okuması yanıltıcıdır: iki cisim aynı derecede
    görünürken deklinasyonda uzak olabilir ve gerçekte hiç yakın değildirler.
    """
    ms = ms or compute_masses(chart)
    eps = egiklik(chart.jd_ut)
    kut = _kuresel_kutleler(chart, ms)

    # kaba ızgara taraması
    en_iyi = (-1e18, 0.0, 0.0)
    a = 0.0
    while a < 360.0:
        d = -88.0
        while d <= 88.0:
            v = _phi_kuresel(a, d, kut)
            if v > en_iyi[0]:
                en_iyi = (v, a, d)
            d += adim
        a += adim
    # yerel rafine
    v, ba, bd = en_iyi
    ad_ = adim
    for _ in range(28):
        ad_ *= 0.6
        for da in (-ad_, 0.0, ad_):
            for dd in (-ad_, 0.0, ad_):
                nd = max(-89.9, min(89.9, bd + dd))
                nv = _phi_kuresel(norm360(ba + da), nd, kut)
                if nv > v:
                    v, ba, bd = nv, norm360(ba + da), nd

    # boylam-yalnız KD'nin küre üzerindeki karşılığı (ekliptik üzerinde, β=0)
    from .engine_mass import find_kd_ad
    kd_lon, _ad_lon = find_kd_ad(ms)
    kd_a, kd_d = ekliptikten_ekvatora(kd_lon, eps, 0.0)
    sapma = acisal_ayrim(ba, bd, kd_a, kd_d)

    # küresel KD'nin ekliptik boylam karşılığı (yorum için)
    r = math.radians
    lam = math.degrees(math.atan2(
        math.sin(r(ba)) * math.cos(r(eps)) + math.tan(r(bd)) * math.sin(r(eps)),
        math.cos(r(ba))))
    bet = math.degrees(math.asin(
        math.sin(r(bd)) * math.cos(r(eps))
        - math.cos(r(bd)) * math.sin(r(eps)) * math.sin(r(ba))))

    # en yakın cisim
    yakin = min(kut, key=lambda x: acisal_ayrim(ba, bd, x[0], x[1]))

    # iki baskın kütle arasındaki büyük çember üzerinde eşik (küresel Berzah)
    agir = sorted(kut, key=lambda x: -abs(x[2]))[:2]
    berzah = None
    if len(agir) == 2:
        (a1, d1, _m1, n1), (a2, d2, _m2, n2) = agir
        toplam = acisal_ayrim(a1, d1, a2, d2)
        # 179°'yi aşarsa iki nokta neredeyse zıt kutuptadır ve aralarından
        # SONSUZ büyük çember geçer; eşik tanımsızdır, bildirilmez.
        if 1.0 < toplam < 179.0:
            # büyük çember üzerinde eşit adımlarla en düşük Φ (su bölümü)
            best = (1e18, None)
            N = 400
            for i in range(1, N):
                f = i / N
                # küresel doğrusal interpolasyon (slerp)
                w = math.radians(toplam)
                s1 = math.sin((1 - f) * w) / math.sin(w)
                s2 = math.sin(f * w) / math.sin(w)
                x = (s1 * math.cos(r(d1)) * math.cos(r(a1))
                     + s2 * math.cos(r(d2)) * math.cos(r(a2)))
                yv = (s1 * math.cos(r(d1)) * math.sin(r(a1))
                      + s2 * math.cos(r(d2)) * math.sin(r(a2)))
                z = s1 * math.sin(r(d1)) + s2 * math.sin(r(d2))
                aa = norm360(math.degrees(math.atan2(yv, x)))
                dd2 = math.degrees(math.asin(max(-1.0, min(1.0, z))))
                val = _phi_kuresel(aa, dd2, kut)
                if val < best[0]:
                    best = (val, (aa, dd2, f))
            if best[1]:
                aa, dd2, f = best[1]
                blam = math.degrees(math.atan2(
                    math.sin(r(aa)) * math.cos(r(eps)) + math.tan(r(dd2)) * math.sin(r(eps)),
                    math.cos(r(aa))))
                berzah = {
                    "iki_deniz": f"{n1} ↔ {n2}",
                    "yay_uzunlugu": round(toplam, 2),
                    "ra": round(aa, 3), "dekl": round(dd2, 3),
                    "ekliptik_boylam": fmt_lon(norm360(blam)),
                    "ev": chart.house(norm360(blam)),
                    "konum_orani": round(f, 3),
                    "phi": round(best[0], 3),
                }

    if berzah is None and len(agir) == 2:
        berzah = {"hata": "iki baskın kütle neredeyse zıt kutupta — "
                          "aralarından sonsuz büyük çember geçer, eşik tanımsız"}
    return {
        "kuresel_KD": {"ra": round(ba, 3), "dekl": round(bd, 3),
                       "phi": round(v, 3),
                       "ekliptik_boylam": fmt_lon(norm360(lam)),
                       "ekliptik_enlem": round(bet, 3),
                       "ev": chart.house(norm360(lam)),
                       "en_yakin_cisim": yakin[3],
                       "en_yakin_ayrim": round(acisal_ayrim(ba, bd, yakin[0], yakin[1]), 2)},
        "boylam_KD": {"konum": fmt_lon(kd_lon), "ra": round(kd_a, 3),
                      "dekl": round(kd_d, 3)},
        "sapma_derece": round(sapma, 2),
        "kuresel_berzah": berzah,
        "egiklik": round(eps, 4),
        "yorum": ("Küresel alan boylam okumasıyla örtüşüyor; iki boyutlu "
                  "düzeltme bu haritada bir şey değiştirmiyor." if sapma < 5 else
                  f"Küresel Kara Delik, boylam okumasından {sapma:.1f}° sapıyor. "
                  "Boylamda yakın görünen cisimler deklinasyonda ayrık; "
                  "tek boyutlu okuma bu haritada YANILTICI." if sapma > 15 else
                  f"{sapma:.1f}° sapma var — boylam okuması kabaca doğru ama "
                  "deklinasyon katmanı dikkate alınmalı."),
        "yontem": ("Φ(α,δ) = Σ mᵢ/(d+ε); d gerçek açısal ayrımdır "
                   "(cos d = sinδ₁sinδ₂ + cosδ₁cosδ₂cos Δα). Küresel Berzah, "
                   "iki baskın kütleyi birleştiren büyük çember üzerindeki "
                   "en düşük Φ noktasıdır."),
    }


# ============================================================================
def hudud_katmani(chart: NatalChart,
                  ms: Optional[Sequence[MassBody]] = None) -> dict:
    ms = ms or compute_masses(chart)
    return {
        "modul": "HUDÛD-I FELEK — deklinasyon ve küresel alan",
        "paralel": paraleller(chart, ms),
        "hudud_disi": hudud_disi(chart),
        "kuresel_alan": kuresel_alan(chart, ms),
        "takvim": hudud_takvimi(chart),
        "transit_paralel": transit_paralelleri(chart),
        "uyari": ("Deklinasyon temasları klasik gelenekte de kullanılır; "
                  "küresel alan bu modelin kendi genişletmesidir."),
    }


# ============================================================================
# EK KATMANLAR (v5.4)
# ============================================================================
def hudud_takvimi(chart: NatalChart, yil: int = 3) -> dict:
    """
    Hudûd dışı cisimlerin GİRİŞ ve ÇIKIŞ tarihleri.

    "Ay hudûd dışında" demek yeterli değil: ne zaman girdi, ne zaman çıkacak?
    Ay için bu ayda birkaç gün sürer ve tekrarlar; Mars için yıllarca sürebilir.
    Süre, o kapasitenin ne kadar süreyle "kendi kuralı dışında" çalıştığını
    söyler.
    """
    ensure_ephe()
    eps = egiklik(chart.jd_ut)
    jd0 = chart.jd_ut
    olay: List[dict] = []
    for k in CORE10:
        if k == "Sun":
            continue
        # PERFORMANS: Ay'ın deklinasyon çevrimi 27.3 gündür; üç yıl taramak
        # aynı örüntüyü 40 kez tekrar etmek demekti (11.157 efemeris çağrısı,
        # 193 ms) ve çıktı zaten 24 kayda kırpılıyordu. Ay için 8 ay yeterli:
        # o pencerede tüm geçiş türleri en az bir kez görünür.
        adim = 0.25 if k == "Moon" else 3.0
        pencere = min(yil, 0.7) if k == "Moon" else yil
        onceki = None
        n = int(pencere * 365.25 / adim)
        for i in range(n):
            jd = jd0 + i * adim
            try:
                (_ra, dec, *_), _ = swe.calc_ut(
                    jd, getattr(swe, k.upper(), 0), EPHFLAG | swe.FLG_EQUATORIAL)
            except Exception:
                continue
            disarida = abs(dec) > eps
            if onceki is not None and disarida != onceki:
                # kaba adımda bulunan geçişi ikiye bölerek keskinleştir
                a, b = jd - adim, jd
                for _ in range(24):
                    o = (a + b) / 2
                    try:
                        (_r, d2, *_), _ = swe.calc_ut(
                            o, getattr(swe, k.upper(), 0),
                            EPHFLAG | swe.FLG_EQUATORIAL)
                    except Exception:
                        break
                    if (abs(d2) > eps) == onceki:
                        a = o
                    else:
                        b = o
                olay.append({"cisim": TR_NAME[k],
                             "tarih": jd_to_iso((a + b) / 2)[:10],
                             "yon": "çıkış" if disarida else "dönüş"})
            onceki = disarida
    olay.sort(key=lambda x: x["tarih"])
    return {"pencere_yil": yil, "gecisler": olay[:24],
            "okuma": ("Bu dönemde hudûd geçişi yok."
                      if not olay else
                      f"{len(olay)} geçiş var. 'Çıkış' o kapasitenin kendi "
                      "kurallarının dışına taştığı, 'dönüş' geri girdiği "
                      "tarihtir."),
            "yontem": (f"Deklinasyonun ±{eps:.3f}° sınırını kestiği anlar; "
                       "kaba tarama sonrası ikiye bölerek keskinleştirilir. "
                       "Ay hızlı olduğu için 6 saatlik, ötekiler 3 günlük "
                       "adımla taranır.")}


def transit_paralelleri(chart: NatalChart, jd: Optional[float] = None,
                        orb: float = 1.0) -> dict:
    """
    BUGÜNKÜ gökyüzünün natal cisimlerle deklinasyon temasları.

    Klasik transit yalnız boylama bakar. Bugün bir gezegen natal bir cisimle
    aynı deklinasyon kuşağındaysa, boylamda hiç açı olmasa bile temas vardır
    ve bu temas klasik okumada GÖRÜNMEZ.
    """
    import datetime as dt
    ensure_ephe()
    if jd is None:
        u = dt.datetime.utcnow()
        jd = swe.julday(u.year, u.month, u.day, u.hour + u.minute / 60.0)
    out = []
    for kt in CORE10:
        try:
            (_ra, dt_, *_), _ = swe.calc_ut(
                jd, getattr(swe, kt.upper(), 0), EPHFLAG | swe.FLG_EQUATORIAL)
        except Exception:
            continue
        for kn in CORE10:
            b = chart.bodies[kn]
            fp, fk = abs(dt_ - b.decl), abs(dt_ + b.decl)
            tur, o = (None, None)
            if fp <= orb:
                tur, o = "paralel", fp
            elif fk <= orb:
                tur, o = "karşıt-paralel", fk
            if tur:
                out.append({"transit": TR_NAME[kt], "natal": b.name_tr,
                            "tur": tur, "orb": round(o, 2),
                            "transit_dekl": round(dt_, 2),
                            "natal_dekl": round(b.decl, 2)})
    out.sort(key=lambda x: x["orb"])
    return {"an": jd_to_iso(jd), "temaslar": out[:12], "orb": orb,
            "okuma": ("Bugün deklinasyon teması yok."
                      if not out else
                      f"{len(out)} temas var; en yakını {out[0]['transit']} "
                      f"{out[0]['tur']} {out[0]['natal']} ({out[0]['orb']}°). "
                      "Bunlar boylamda görünmez."),
            "yontem": "Bugünkü deklinasyonlar ile natal deklinasyonlar, orb 1°."}
