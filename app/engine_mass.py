#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BERZAH v2 — KÜTLE MOTORU (Mercü'l-Bahreyn)
Bu oturumun icadı: gezegenlere KÜTLE atar; orta nokta yerine BARİSENTR,
Φ potansiyel alanı, KD (Kara Delik) / AD (Ak Delik=antisya) / B (Berzah =
kararsız denge F=0, dF/dλ>0), mercekleme, 137.508° kurtarıcı, heksagram
Hamming ikizleri, öz-modül spektrumu (surrogate p + BH-FDR) ve yorum matrisi.
"""
from __future__ import annotations
import math
import random
from bisect import bisect_left
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from .astro import NatalChart, MEAN_SPEED, CORE10, TR_NAME
from .circular import (norm360, sep, signed_sep, sign_of, deg_in_sign, fmt_lon,
                       antiscion, GOLDEN_ANGLE, SIGNS, RULER)

EPS = 0.30
EXALT = {"Sun": ("Koç", 19), "Moon": ("Boğa", 3), "Mercury": ("Başak", 15),
         "Venus": ("Balık", 27), "Mars": ("Oğlak", 28),
         "Jupiter": ("Yengeç", 15), "Saturn": ("Terazi", 21)}
RULER_EN = {"Koç": "Mars", "Boğa": "Venus", "İkizler": "Mercury", "Yengeç": "Moon",
            "Aslan": "Sun", "Başak": "Mercury", "Terazi": "Venus", "Akrep": "Mars",
            "Yay": "Jupiter", "Oğlak": "Saturn", "Kova": "Saturn", "Balık": "Jupiter"}
PRIMES = [11, 13, 17, 19, 23, 29, 31, 37, 41, 43]

# İnsan Dizaynı çark sırası (Kapı 41 = 02° Kova'dan zodyak yönünde)
GATE_WHEEL = [41, 19, 13, 49, 30, 55, 37, 63, 22, 36, 25, 17, 21, 51, 42, 3,
              27, 24, 2, 23, 8, 20, 16, 35, 45, 12, 15, 52, 39, 53, 62, 56,
              31, 33, 7, 4, 29, 59, 40, 64, 47, 6, 46, 18, 48, 57, 32, 50,
              28, 44, 1, 43, 14, 34, 9, 5, 26, 11, 10, 58, 38, 54, 61, 60]
GATE_START = 302.0
GATE_SIZE = 360.0 / 64.0
KING_WEN_BITS = {
    1: 0b111111, 2: 0b000000, 3: 0b010001, 4: 0b100010, 5: 0b010111,
    6: 0b111010, 7: 0b000010, 8: 0b010000, 9: 0b110111, 10: 0b111011,
    11: 0b000111, 12: 0b111000, 13: 0b111101, 14: 0b101111, 15: 0b000100,
    16: 0b001000, 17: 0b011001, 18: 0b100110, 19: 0b000011, 20: 0b110000,
    21: 0b101001, 22: 0b100101, 23: 0b100000, 24: 0b000001, 25: 0b111001,
    26: 0b100111, 27: 0b100001, 28: 0b011110, 29: 0b010010, 30: 0b101101,
    31: 0b011100, 32: 0b001110, 33: 0b111100, 34: 0b001111, 35: 0b101000,
    36: 0b000101, 37: 0b110101, 38: 0b101011, 39: 0b010100, 40: 0b001010,
    41: 0b100011, 42: 0b110001, 43: 0b011111, 44: 0b111110, 45: 0b011000,
    46: 0b000110, 47: 0b011010, 48: 0b010110, 49: 0b011101, 50: 0b101110,
    51: 0b001001, 52: 0b100100, 53: 0b110100, 54: 0b001011, 55: 0b001101,
    56: 0b101100, 57: 0b110110, 58: 0b011011, 59: 0b110010, 60: 0b010011,
    61: 0b110011, 62: 0b001100, 63: 0b010101, 64: 0b101010}


def mundane_positions(chart: NatalChart) -> Dict[str, Optional[float]]:
    """swisseph house_pos ile sürekli mundan konum (1.0 = ASC). Enlemi hesaba katar."""
    import swisseph as swe
    from .astro import ensure_ephe
    ensure_ephe()
    out: Dict[str, Optional[float]] = {}
    try:
        hb = (chart.house_system or "P")[0].encode()
        armc = swe.houses_ex(chart.jd_ut, chart.lat, chart.lng, hb)[1][2]
        eps = swe.calc_ut(chart.jd_ut, swe.ECL_NUT, 0)[0][0]
        for k, b in chart.bodies.items():
            try:
                out[k] = float(swe.house_pos(armc, chart.lat, eps, (b.lon, b.lat), hb))
            except Exception:
                out[k] = None
    except Exception:
        for k in chart.bodies:
            out[k] = None
    return out


# ---------------------------------------------------------------- kütle m(P)
@dataclass
class MassBody:
    key: str
    name: str
    lon: float
    mass: float          # işaretli: retro → negatif (İTİCİ kütle)
    parts: Dict[str, float]

    @property
    def abs_mass(self) -> float:
        return abs(self.mass)


def _dignity(key: str, lon: float) -> float:
    s = sign_of(lon); d = deg_in_sign(lon); score = 0.0
    if RULER_EN.get(s) == key: score += 5.0
    if key in EXALT:
        ex_s, ex_d = EXALT[key]
        if s == ex_s:
            score += 4.0 + math.exp(-((d - ex_d) ** 2) / 32.0)
        if s == SIGNS[(SIGNS.index(ex_s) + 6) % 12]:
            score -= 4.0
    for sg, rl in RULER_EN.items():
        if rl == key and s == SIGNS[(SIGNS.index(sg) + 6) % 12]:
            score -= 5.0
    return score


def _gauquelin(hp: Optional[float], lon: float, asc: float, mc: float,
               peak: float = 0.30, sigma: float = 0.55, gain: float = 1.6) -> float:
    """
    Açısallık ağırlığı — GERÇEK MUNDAN (günlük hareket) konumdan.

    Gauquelin 'artı bölgeleri' köşenin üstünde değil, köşeyi günlük hareket
    yönünde biraz GEÇMİŞ yerdedir: 12. ev (doğuşun hemen ardı) ve 9. ev
    (külminasyonun hemen ardı). Bunlar ekliptik boylamda değil, mundan
    konumda tanımlıdır — enlemi yüksek cisimlerde ikisi ciddi biçimde ayrışır.

    hp : swisseph house_pos çıktısı (1.0 = ASC, sürekli 1..13).
         Hesaplanamazsa ekliptik boylam yaklaşımına düşülür.
    """
    if hp is None:
        best = 0.0
        for a in (asc, norm360(asc + 180), mc, norm360(mc + 180)):
            d = signed_sep(lon, a)
            best = max(best, math.exp(-((d + 8.0) ** 2) / (2 * 14.0 ** 2)))
        return 1.0 + gain * best
    hpm = (hp - 1.0) % 12.0 + 1.0          # 1..13 → 1..12 sarımlı
    best = 0.0
    for kose in (1.0, 4.0, 7.0, 10.0):      # ASC, IC, DSC, MC
        d = ((hpm - kose + 6.0) % 12.0) - 6.0
        best = max(best, math.exp(-((d + peak) ** 2) / (2 * sigma ** 2)))
    return 1.0 + gain * best


def _visibility(key: str, lon: float, sun_lon: float) -> float:
    if key in ("Sun", "Moon", "TrueNode"): return 1.0
    d = sep(lon, sun_lon)
    if d < 17 / 60: return 2.00            # kazimi — kalbe alınmış
    if d < 8.5: return 0.35 + 0.05 * d / 8.5   # yanık
    if d < 15.0: return 0.70 + 0.30 * (d - 8.5) / 6.5
    return 1.0


def compute_masses(chart: NatalChart, keys: Optional[List[str]] = None) -> List[MassBody]:
    ks = keys or CORE10
    sun = chart.bodies["Sun"].lon
    hpos = mundane_positions(chart)
    out: List[MassBody] = []
    for k in ks:
        b = chart.bodies[k]
        w_dig = max(0.25, 1.0 + 0.09 * _dignity(k, b.lon))
        ms = MEAN_SPEED.get(k, 1.0)
        ratio = abs(b.speed) / ms if ms > 0 else 1.0
        w_spd = max(0.30, min(2.0, 0.30 + 0.70 * math.sqrt(max(ratio, 0.0))))
        w_ang = _gauquelin(hpos.get(k), b.lon, chart.asc, chart.mc)
        w_vis = _visibility(k, b.lon, sun)
        w_dec = 1.0 + abs(b.decl) / 23.44
        m = w_dig * w_spd * w_ang * w_vis * w_dec
        out.append(MassBody(k, b.name_tr, b.lon, -m if b.retro else m,
                            {"asalet": round(w_dig, 3), "hız": round(w_spd, 3),
                             "açısal": round(w_ang, 3), "görünür": round(w_vis, 3),
                             "dekl": round(w_dec, 3)}))
    return out


# ---------------------------------------------------- barisentr & Φ & kuvvet
def barycenter(a: MassBody, b: MassBody) -> float:
    ma, mb = a.abs_mass, b.abs_mass
    if ma + mb == 0: return norm360((a.lon + b.lon) / 2)
    return norm360(a.lon + (mb / (ma + mb)) * signed_sep(b.lon, a.lon))


def phi_field(lon: float, ms: Sequence[MassBody]) -> float:
    return sum(m.mass / (sep(lon, m.lon) + EPS) for m in ms)


def force(lon: float, ms: Sequence[MassBody]) -> float:
    f = 0.0
    for m in ms:
        d = (m.lon - lon + 180.0) % 360.0 - 180.0
        r = abs(d) + EPS
        f += m.mass * (1.0 if d >= 0 else -1.0) / (r * r)
    return f


def find_kd_ad(ms: Sequence[MassBody], step: float = 0.1) -> Tuple[float, float]:
    best, bv = 0.0, -math.inf
    n = int(360 / step)
    for i in range(n):
        v = phi_field(i * step, ms)
        if v > bv: best, bv = i * step, v
    return best, antiscion(best)


@dataclass
class Berzah2:
    lon: float
    sea_a: str; sea_b: str
    mass_a: float; mass_b: float
    kind: str; asymmetry: float; stability: float
    saf_lon: float = 0.0          # iki-deniz analitik denge noktası
    sapma: float = 0.0            # tam alanın saf noktadan kaydırdığı miktar
    guven: str = ""               # bulgunun güvenilirliği
    en_yakin_gezegen: float = 0.0


def _iki_deniz_dengesi(a: MassBody, b: MassBody) -> float:
    """
    Yalnız iki denizin analitik denge noktası — üçüncü cisimler yok.

        m_A/(x+ε)² = m_B/(L−x+ε)²
      → x = [√m_A·L + ε(√m_A − √m_B)] / (√m_A + √m_B)

    x, A'dan B'ye kısa yay üzerinde alınan mesafedir. Ağır olan denizden
    UZAKTA, hafif olana yakın çıkar — fiziksel olarak doğrudur.
    """
    L = signed_sep(b.lon, a.lon)
    yon = 1.0 if L >= 0 else -1.0
    L = abs(L)
    ra, rb = math.sqrt(a.abs_mass), math.sqrt(b.abs_mass)
    if ra + rb == 0:
        return norm360(a.lon + yon * L / 2)
    x = (ra * L + EPS * (ra - rb)) / (ra + rb)
    x = max(0.0, min(L, x))
    return norm360(a.lon + yon * x)


def find_berzah2(ms: Sequence[MassBody], step: float = 0.05,
                 tekillik_yasagi: float = 2.5) -> Optional[Berzah2]:
    """
    BERZAH = iki denizin eşiği.

    v2.0'daki hata: tam alanın kuvvet fonksiyonunda, iki baskın kütle
    arasındaki bütün yay taranıyordu. Kuvvet her gezegenin üzerinde
    1/r² tekilliğine sahip olduğu için işaret her cismin yanında değişir;
    tarama bu SAHTE kökleri gerçek denge sanıp Berzah'ı bir gezegenin
    tam üstüne oturtabiliyordu (dF/dλ patlar, anlam kaybolur).

    v2.1 yöntemi:
      1. İki denizin analitik denge noktasını çöz (üçüncü cisim yok) → saf eşik.
      2. Tam alanda bu noktanın yakınındaki gerçek kökü ara.
      3. Herhangi bir gezegene `tekillik_yasagi` dereceden yakın kökleri REDDET.
      4. Geçerli kök yoksa saf eşiği bildir ve "alan bozucu" olarak işaretle.
    """
    ranked = sorted(ms, key=lambda m: m.abs_mass, reverse=True)
    if len(ranked) < 2:
        return None
    a, b = ranked[0], ranked[1]
    saf = _iki_deniz_dengesi(a, b)

    f = lambda x: force(x, ms)
    yakinlik = lambda x: min(sep(x, m.lon) for m in ms)

    # Saf eşiğin çevresinde (±25°) tam alanın gerçek köklerini tara
    kokler: List[Tuple[float, float]] = []
    PENCERE = 35.0
    onceki_lon = norm360(saf - PENCERE)
    onceki_f = f(onceki_lon)
    adim = 0.25
    for i in range(1, int(2 * PENCERE / adim) + 1):
        cur = norm360(saf - PENCERE + i * adim)
        cf = f(cur)
        if onceki_f * cf < 0:
            lo, hi, flo = onceki_lon, cur, onceki_f
            for _ in range(50):
                mid = norm360(lo + signed_sep(hi, lo) / 2)
                fm = f(mid)
                if flo * fm <= 0:
                    hi = mid
                else:
                    lo, flo = mid, fm
            kok = norm360(lo + signed_sep(hi, lo) / 2)
            if yakinlik(kok) >= tekillik_yasagi:       # tekillik yasağı
                h = 0.05
                dfdl = (f(norm360(kok + h)) - f(norm360(kok - h))) / (2 * h)
                kokler.append((kok, dfdl))
        onceki_lon, onceki_f = cur, cf

    if kokler:
        lon, stab = min(kokler, key=lambda k: sep(k[0], saf))
        guven = "tam alanda doğrulanmış denge"
    else:
        lon, stab = saf, 0.0
        guven = ("alan bozucu — üçüncü cisimler gerçek dengeyi siliyor; "
                 "saf iki-deniz eşiği bildiriliyor")

    asym = max(a.abs_mass, b.abs_mass) / max(1e-9, min(a.abs_mass, b.abs_mass))
    if a.mass < 0 or b.mass < 0:
        kind = "itici sırt"
    elif asym > 3.0:
        kind = "sahte simetri"
    else:
        kind = "gerçek çatal"

    return Berzah2(lon=lon, sea_a=a.name, sea_b=b.name, mass_a=a.mass,
                   mass_b=b.mass, kind=kind, asymmetry=asym, stability=stab,
                   saf_lon=saf, sapma=sep(lon, saf), guven=guven,
                   en_yakin_gezegen=yakinlik(lon))


def barycentric_tree(ms: Sequence[MassBody], target: float, orb: float = 1.5):
    hits = []
    H = [0, 22.5, 45, 67.5, 90, 112.5, 135, 157.5, 180]
    for i in range(len(ms)):
        for j in range(i + 1, len(ms)):
            bc = barycenter(ms[i], ms[j])
            best = min(min(sep(bc, norm360(target + h)),
                           sep(bc, norm360(target - h))) for h in H)
            if best <= orb:
                hits.append({"cift": f"{ms[i].name}/{ms[j].name}",
                             "barisentr": fmt_lon(bc), "lon": round(bc, 3),
                             "sapma": round(best, 2)})
    hits.sort(key=lambda x: x["sapma"])
    return hits[:12]


def lensing(ms: Sequence[MassBody], kd: float, k: float = 1.4,
            window: float = 12.0, ring: float = 2.5):
    kd_mass = max((m.abs_mass for m in ms if sep(m.lon, kd) < 5), default=1.0)
    out = []
    for m in ms:
        d = signed_sep(m.lon, kd)
        if 0.3 < abs(d) <= window:
            defl = k * kd_mass / abs(d)
            out.append({"gezegen": m.name, "gercek": fmt_lon(m.lon),
                        "gorunen": fmt_lon(norm360(m.lon + math.copysign(defl, d))),
                        "sapma": round(defl, 2), "cift_goruntu": defl >= ring})
    out.sort(key=lambda r: -r["sapma"])
    return out


def liberator(ms: Sequence[MassBody], kd: float, orb: float = 3.0):
    """
    KURTARICI — KD'ye altın açı (137.508°) yapan gezegen.

    v2.1'de orb 1.5° idi ve yalnız listeye giren gezegenler bildiriliyordu:
    40 haritanın 37'sinde liste BOŞ çıkıyor, modelin "tek somut talimat"
    vaadi neredeyse hiç karşılanmıyordu. Artık orb 3°'ye açıldı ve orbun
    dışında kalsa bile EN YAKIN aday, sapmasıyla birlikte her zaman bildirilir;
    danışman kapının ne kadar aralık olduğunu kendisi görür.
    """
    adaylar = [{"gezegen": m.name, "aci": round(sep(m.lon, kd), 2),
                "sapma": round(abs(sep(m.lon, kd) - GOLDEN_ANGLE), 2)}
               for m in ms]
    adaylar.sort(key=lambda x: x["sapma"])
    for a in adaylar:
        a["kapi_acik"] = a["sapma"] <= orb
        a["durum"] = ("kapı açık — talimat bu gezegenden yazılır"
                      if a["sapma"] <= orb else
                      "kapı aralık — zayıf kanal" if a["sapma"] <= 8.0 else
                      "kapı kapalı")
    return adaylar[:3]


def gate_of(lon: float) -> Tuple[int, int]:
    off = (norm360(lon) - GATE_START) % 360.0
    idx = int(off // GATE_SIZE)
    line = int((off - idx * GATE_SIZE) // (GATE_SIZE / 6)) + 1
    return GATE_WHEEL[idx], min(6, line)


def structural_twins(ms: Sequence[MassBody], max_h: int = 1):
    out = []
    for i in range(len(ms)):
        for j in range(i + 1, len(ms)):
            ga, _ = gate_of(ms[i].lon); gb, _ = gate_of(ms[j].lon)
            if ga == gb: continue
            h = bin(KING_WEN_BITS[ga] ^ KING_WEN_BITS[gb]).count("1")
            if h <= max_h:
                out.append({"a": ms[i].name, "b": ms[j].name, "kapi_a": ga,
                            "kapi_b": gb, "hamming": h,
                            "acisal": round(sep(ms[i].lon, ms[j].lon), 1)})
    out.sort(key=lambda x: (x["hamming"], -x["acisal"]))
    return out


def prime_angles(ms: Sequence[MassBody], orb: float = 0.75):
    out = []
    for i in range(len(ms)):
        for j in range(i + 1, len(ms)):
            d = sep(ms[i].lon, ms[j].lon)
            for p in PRIMES:
                unit = 360.0 / p; k = round(d / unit)
                if k == 0 or k * unit > 180: continue
                dev = abs(d - k * unit)
                if dev <= orb:
                    out.append({"a": ms[i].name, "b": ms[j].name, "asal": p,
                                "kat": k, "aci": round(k * unit, 2),
                                "sapma": round(dev, 2)})
                    break
    out.sort(key=lambda x: x["sapma"])
    return out[:10]


def spectrum(ms: Sequence[MassBody], step: float = 0.25,
             n_surrogate: int = 250, alpha: float = 0.10):
    lw = [(m.lon, m.abs_mass) for m in ms]

    def R(mod: float) -> float:
        sx = sy = sw = 0.0
        for lon, w in lw:
            th = ((lon % mod) / mod) * 2 * math.pi
            sx += w * math.cos(th); sy += w * math.sin(th); sw += w
        return math.hypot(sx, sy) / sw if sw > 0 else 0.0

    spec = []
    m = 1.0
    while m <= 180.0 + 1e-9:
        spec.append((round(m, 3), R(m))); m += step
    peaks = []
    for i in range(1, len(spec) - 1):
        if spec[i][1] > spec[i - 1][1] and spec[i][1] >= spec[i + 1][1]:
            peaks.append(spec[i])
    peaks.sort(key=lambda x: -x[1])
    kept = []
    for mm, rr in peaks:
        if all(abs(mm - k[0]) >= 2.0 for k in kept): kept.append((mm, rr))
        if len(kept) >= 8: break
    rng = random.Random(7)
    weights = [w for _, w in lw]
    pvals = []
    for mm, rr in kept:
        dist = []
        for _ in range(n_surrogate):
            fake = [(rng.uniform(0, 360), w) for w in weights]
            sx = sy = sw = 0.0
            for lon, w in fake:
                th = ((lon % mm) / mm) * 2 * math.pi
                sx += w * math.cos(th); sy += w * math.sin(th); sw += w
            dist.append(math.hypot(sx, sy) / sw)
        dist.sort()
        p = (len(dist) - bisect_left(dist, rr) + 1) / (len(dist) + 1)
        pvals.append(p)
    n = len(pvals)
    order = sorted(range(n), key=lambda i: pvals[i])
    kmax = -1
    for rank, i in enumerate(order, 1):
        if pvals[i] <= alpha * rank / n: kmax = rank
    keep = [False] * n
    for rank, i in enumerate(order, 1):
        if rank <= kmax: keep[i] = True
    return [{"M": kept[i][0], "R": round(kept[i][1], 3),
             "p": round(pvals[i], 4), "fdr": keep[i]} for i in range(n)]


# ------------------------------------------------------------- yorum matrisi
SIGN_MATRIX = {
    "Koç": ("Şimdi mi, hiç mi?", "Gerilimden kurtulmak için seçimi erken kapatmak", "İlk dürtüyü değil, ikincisini izlemek"),
    "Boğa": ("Tutmak mı, bırakmak mı?", "Hareketsizlikle seçmiş olmak — atalet gizli karardır", "Bedelin fiyatını rakamla yazmak"),
    "İkizler": ("İki doğru aynı anda doğru", "İkisini de savunup üçüncü bir dile kaçmak", "Birini tanık önünde, yüksek sesle söylemek"),
    "Yengeç": ("Aidiyet mi, ayrılık mı?", "Tanıdık olana geri çekilmek", "Ayrılığı ihanet saymamayı öğrenmek"),
    "Aslan": ("Görülmek mi, gerçek olmak mı?", "Kararı performansa çevirip seyirci toplamak", "Kararı kimseye anlatmadan uygulamak"),
    "Başak": ("Düzeltmek mi, kabul etmek mi?", "Veri toplayarak erteleme", "%70 bilgiyle kesmek"),
    "Terazi": ("En saf berzah — burcun kendisi denge noktasıdır", "Kararı karşı tarafa devretmek", "Tek taraflı ilan"),
    "Akrep": ("Yüzleşmek mi, gömmek mi?", "Belirsizliği kontrol aracı olarak elde tutmak", "Kaybı önceden kabullenip girmek"),
    "Yay": ("Genişlemek mi, kök salmak mı?", "Yeni bir ufuk icat ederek kaçmak", "Ya kal ve derinleş, ya git ve dönme"),
    "Oğlak": ("Sorumluluk mu, özgürlük mü?", "Yükü alıp buna 'görev' demek", "Bir kez, gerekçesiz 'hayır'"),
    "Kova": ("Ait olmak mı, ayrışmak mı?", "İlkeye sığınıp insanı feda etmek", "İstisnayı tanımak"),
    "Balık": ("Sınır mı, erime mi?", "Seçim anını hiç fark etmemek", "Karara saat ve takvim koymak")}
HOUSE_MATRIX = {
    1: ("Tavırda, bedende — 'kim olarak gireyim'", "Dış olay, ani"),
    2: ("Fiyatta — neyi ödemeye razısın", "Birikim, yavaş"),
    3: ("Tek bir cümlede — hangisini kurarsan o olur", "İç fark ediş, sinsi"),
    4: ("Kalmak/ayrılmak; hangi soyağacını sürdürmek", "Dış olay, ani"),
    5: ("Bahis — yaratmak mı, korumak mı", "Birikim, yavaş"),
    6: ("Günlük düzenin hangi yarısı feda edilecek", "İç fark ediş, sinsi"),
    7: ("Ötekinin çatalı — ilişki, ortaklık, dava", "Dış olay, ani"),
    8: ("Kimin gücüne bağlanacaksın; borç ve teslim", "Birikim, yavaş"),
    9: ("Hangi hikâyeye inanacaksın", "İç fark ediş, sinsi"),
    10: ("Hangi unvan, kimin gözü önünde", "Dış olay, ani"),
    11: ("Hangi kabile, hangi gelecek", "Birikim, yavaş"),
    12: ("Çatal görünmez — sabotaj veya feragat olarak yaşanır", "İç fark ediş, sinsi")}
SEA_PAIRS = {
    frozenset({"Ay", "Satürn"}): ("Bakım ile disiplin", "Sevilmek mi, sağlam olmak mı"),
    frozenset({"Venüs", "Plüton"}): ("Uyum ile arzu", "Barış mı, gerçek mi"),
    frozenset({"Güneş", "Neptün"}): ("Kimlik ile çözülme", "Ben mi, biz mi"),
    frozenset({"Merkür", "Jüpiter"}): ("Kesinlik ile genişlik", "Doğru mu, geniş mi"),
    frozenset({"Mars", "Satürn"}): ("İtki ile yapı", "Hız mı, sağlamlık mı"),
    frozenset({"Ay", "Uranüs"}): ("Güvenlik ile özgürlük", "Kal mı, git mi"),
    frozenset({"Güneş", "Satürn"}): ("Otorite alma ile otorite olma", "İzin mi, sorumluluk mu"),
    frozenset({"Venüs", "Satürn"}): ("Değer ile yeterlilik", "Hak ediyor muyum"),
    frozenset({"Merkür", "Neptün"}): ("Ayırt etme ile sezgi", "Bildiğim mi, hissettiğim mi"),
    frozenset({"Mars", "Plüton"}): ("Eylem ile dönüşüm", "Savaş mı, yıkım mı")}


def full_v2(chart: NatalChart, topoloji: bool = True) -> dict:
    ms = compute_masses(chart)
    kd, ad = find_kd_ad(ms)
    b = find_berzah2(ms)
    # Φ alanının 360 örneklik profili — arayüzdeki alan halkasını bu çizer
    raw = [phi_field(i * 1.0, ms) for i in range(360)]
    lo, hi = min(raw), max(raw)
    rng = (hi - lo) or 1.0
    res = {
        "kutleler": [{"gezegen": m.name, "m": round(m.mass, 3),
                      "lon": round(m.lon, 3), "konum": fmt_lon(m.lon),
                      "retro": m.mass < 0, "bilesenler": m.parts}
                     for m in sorted(ms, key=lambda x: -x.abs_mass)],
        "ev_uclari": [round(c, 3) for c in (chart.cusps or [])],
        "asc": round(chart.asc, 3), "mc": round(chart.mc, 3),
        "phi_alani": {"ornek": [round((v - lo) / rng, 4) for v in raw],
                      "min": round(lo, 3), "max": round(hi, 3),
                      "aciklama": "Φ(λ) 1° adımlarla, 0..1 normalize"},
        "KD": {"lon": round(kd, 3), "konum": fmt_lon(kd), "ev": chart.house(kd)},
        "AD": {"lon": round(ad, 3), "konum": fmt_lon(ad), "ev": chart.house(ad)},
        "mercekleme": lensing(ms, kd),
        "kurtarici": liberator(ms, kd),
        "yapisal_ikizler": structural_twins(ms),
        "asal_acilar": prime_angles(ms),
        "oz_modul_spektrumu": spectrum(ms),
    }
    if b:
        sm = SIGN_MATRIX[sign_of(b.lon)]
        ev = chart.house(b.lon)
        hm = HOUSE_MATRIX.get(ev or 0, ("", ""))
        key = frozenset({b.sea_a, b.sea_b})
        deniz, ad_c = SEA_PAIRS.get(key, (f"{b.sea_a} ile {b.sea_b}", "kataloglanmamış çatal"))
        lights = {"Güneş", "Ay"} & {b.sea_a, b.sea_b}
        outer = {b.sea_a, b.sea_b} <= {"Uranüs", "Neptün", "Plüton"}
        kapsam = ("Işık dahil → çatal kimliğe dokunur, ömür boyu tekrarlar" if lights
                  else "İkisi de dış gezegen → çatal kuşağa aittir" if outer
                  else "Kişisel ölçekli çatal")
        duz = []
        if b.asymmetry > 3: duz.append("SAHTE SİMETRİ — kişi seçim sanır, biri baskındır; iş baskını görmektir")
        elif b.asymmetry < 1.35: duz.append("GERÇEK ÇATAL — iki yol da yaşanabilir; sonuç geri alınamaz")
        if b.mass_a < 0 or b.mass_b < 0: duz.append("İTİCİ SIRT — nokta çekmez, iter; karar verilmez, terk edilir")
        near = [m for m in ms if sep(m.lon, b.lon) <= 2.0]
        if near: duz.append(f"BERZAH BEKÇİSİ: {near[0].name} — karar organı budur, bu dilde yanılır")
        elif all(sep(m.lon, b.lon) > 30 for m in ms):
            duz.append("SESSİZ BERZAH — doğuştan sezilmez, transitle açılır")
        if abs(sep(b.lon, kd) - GOLDEN_ANGLE) <= 1.0:
            duz.append("NADİR: Berzah = kaçış kapısı (KD'ye 137.5°); çatal çözülünce döngü biter")
        res["berzah"] = {
            "lon": round(b.lon, 3), "konum": fmt_lon(b.lon), "ev": ev,
            "iki_deniz": {"a": b.sea_a, "m_a": round(b.mass_a, 3),
                          "b": b.sea_b, "m_b": round(b.mass_b, 3)},
            "tur": b.kind, "asimetri": round(b.asymmetry, 2),
            "kararsizlik_dF": float(f"{b.stability:.3g}"),
            "denge_tipi": ("KARARSIZ denge — gerçek berzah (itilirse geri dönmez)"
                           if b.stability > 0 else
                           "kararlı çukur — eşik değil, tuzak (geri çeker)"
                           if b.stability < 0 else "denge doğrulanamadı"),
            "saf_esik": fmt_lon(b.saf_lon),
            "alan_sapmasi": round(b.sapma, 2),
            "en_yakin_gezegen": round(b.en_yakin_gezegen, 2),
            "guven": b.guven,
            "catalin_adi": f"{deniz} — \"{ad_c}\"", "kapsam": kapsam,
            "catalin_cumlesi": sm[0], "yanlis_refleks": sm[1],
            "berzah_hamlesi": sm[2], "sahne": hm[0], "tetikleyici": hm[1],
            "duzelticiler": duz,
            "barisentr_agaci": barycentric_tree(ms, b.lon)}
    # v3.0 icatları: alan topolojisi (kalıcılık), havza tayini ve eşik
    # yüksekliği. Hepsi ucuz; yürüyen Berzah ayrı uçta (/api/v1/dinamik).
    if topoloji:
        try:
            from .field_dynamics import alan_topolojisi
            res["alan_topolojisi"] = alan_topolojisi(chart, ms)
        except Exception as e:
            res["alan_topolojisi"] = {"hata": str(e)[:200]}
    # Hesaplanan noktalar halkada gezegen gibi konumlanır ve açı yapar.
    # (KRN, Vahdet, Süveyda, İcâbet, Noksan gibi noktalar deneme modüllerinde
    # üretilir; burada yalnız v2'ye ait olanlar toplanır, gerisi main'de eklenir.)
    nk = [{"ad": "Kara Delik", "kod": "KD", "lon": round(kd, 3), "glif": "●"},
          {"ad": "Ak Delik", "kod": "AD", "lon": round(ad, 3), "glif": "◎"}]
    if b:
        nk.append({"ad": "Berzah", "kod": "BZ", "lon": round(b.lon, 3), "glif": "◆"})
    res["noktalar"] = nk
    res["protokol"] = ("Danışan Ak Delik'le gelir, sebep Kara Delik'tedir, "
                       "çözüm Berzah'tadır — talimat altın açı gezegeninden yazılır.")
    return res


def nokta_acilari(chart, noktalar, orb_carpani: float = 0.6) -> List[dict]:
    """
    Hesaplanmış noktaların gezegenlerle ve birbirleriyle açıları.

    Orb, gezegen–gezegen açılarının %60'ı kadar tutulur: bu noktalar
    matematiksel olarak türetilmiş, cisim olmayan yerlerdir; klasik gelenekte
    türetilmiş noktalara (Şans Noktası gibi) dar orb verilir.
    """
    from .modules_deneme import _ASPECTS, _orb_gucu
    hedefler = [(chart.bodies[k].name_tr, chart.bodies[k].lon) for k in CORE10]
    hedefler += [("Yükselen", chart.asc), ("MC", chart.mc)]
    out: List[dict] = []
    # Noktaların BİRBİRİYLE açıları da hesaplanır: türetilmiş noktalar arası
    # temas (ör. Kader Rezonansı ile Süveyda'nın kavuşması) klasik gelenekte
    # de anlamlıdır ve v3.2'de eksikti.
    # Tanım gereği sabit açıda olan çiftler atlanır: bunlar bulgu değil
    # tautolojidir (Anti-KRN zaten KRN+180'dir; ikisinin "karşıtlığı" bilgi
    # taşımaz ve listede ilk sıraya oturup gerçek bulguları aşağı itiyordu).
    TANIMLI = {frozenset({"KRN", "aKRN"})}
    for i in range(len(noktalar)):
        for j in range(i + 1, len(noktalar)):
            n1, n2 = noktalar[i], noktalar[j]
            if frozenset({n1["kod"], n2["kod"]}) in TANIMLI:
                continue
            d = sep(n1["lon"], n2["lon"])
            from .modules_deneme import _ASPECTS as _A, _orb_gucu as _og
            for nm, glif, ang, orb, w, majör in _A:
                if not majör:
                    continue
                o = abs(d - ang)
                if o <= orb * orb_carpani * 0.8:      # nokta–nokta daha da dar
                    out.append({"nokta": n1["ad"], "kod": n1["kod"],
                                "hedef": n2["ad"], "hedef_kod": n2["kod"],
                                "aci": nm, "glif": glif, "orb": round(o, 2),
                                "guc": round(w * _og(o, orb * orb_carpani * 0.8), 3),
                                "n_lon": n1["lon"], "h_lon": n2["lon"],
                                "tur": "nokta-nokta"})
                    break
    for n in noktalar:
        for ad, lon in hedefler:
            d = sep(n["lon"], lon)
            for nm, glif, ang, orb, w, majör in _ASPECTS:
                if not majör:
                    continue
                o = abs(d - ang)
                if o <= orb * orb_carpani:
                    out.append({"nokta": n["ad"], "kod": n["kod"], "hedef": ad,
                                "aci": nm, "glif": glif, "orb": round(o, 2),
                                "guc": round(w * _orb_gucu(o, orb * orb_carpani), 3),
                                "n_lon": n["lon"], "h_lon": round(lon, 3),
                                "tur": "nokta-gezegen"})
                    break
    out.sort(key=lambda x: -x["guc"])
    return out[:26]


def transit_konumlari(chart, jd: Optional[float] = None) -> dict:
    """
    Çift çark (bi-wheel) için o anki gök konumları.

    Tam bir v2 analizi gerekmez: dış halkada yalnız cisimlerin boylamı, geri
    hareket durumu ve natal cisimlerle açıları gösterilir. Bu yüzden hafif
    tutuldu — ana analize kayda değer bir maliyet eklemez.
    """
    import datetime as dt
    import swisseph as swe
    from .astro import calc_lonspeed, jd_to_iso
    if jd is None:
        u = dt.datetime.utcnow()
        jd = swe.julday(u.year, u.month, u.day, u.hour + u.minute / 60.0)
    cisimler = []
    for k in CORE10:
        lon, hiz = calc_lonspeed(jd, k)
        cisimler.append({"gezegen": TR_NAME[k], "lon": round(lon, 4),
                         "konum": fmt_lon(lon), "retro": hiz < 0,
                         "ev": chart.house(lon)})
    return {"an": jd_to_iso(jd), "cisimler": cisimler}


def capraz_acilar_basit(natal_lonlar, dis_cisimler, orb_carpani: float = 0.7):
    """Dış halka cisimleriyle natal cisimler arasındaki majör açılar."""
    from .modules_deneme import _ASPECTS
    out = []
    for d in dis_cisimler:
        for ad, nlon in natal_lonlar:
            fark = sep(d["lon"], nlon)
            for nm, glif, ang, orb, w, majör in _ASPECTS:
                if not majör:
                    continue
                o = abs(fark - ang)
                if o <= orb * orb_carpani:
                    out.append({"dis": d["gezegen"], "natal": ad, "aci": nm,
                                "glif": glif, "orb": round(o, 2),
                                "d_lon": d["lon"], "n_lon": round(nlon, 4)})
                    break
    out.sort(key=lambda x: x["orb"])
    return out[:24]
