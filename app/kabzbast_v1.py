#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BERZAH MODELİ v1.0  —  Kabz / Bast Dinamiği
============================================
Kara delik–ak delik ikiliğini, Einstein–Rosen köprüsünü, Kuantum Sıçramasını (LQC),
altın oranı ve 528 Hz akordunu tek bir HESAPLANABİLİR natal harita motoruna bağlar.

Fizik burada TÜREV değil, İSKELETtir: denklemler gerçek (LQC efektif Friedmann,
Kuramoto düzen parametresi, Cousto kozmik oktav, Plomp–Levelt pürüzlülüğü),
astrolojiye eşlemesi ise sembolik ve tanımsaldır. Bkz. BERZAH_MODELI.md §9.

Bağımlılık: pyswisseph, numpy
Yazar: Astro Pro / astromizacakademi  —  motor tasarımı
"""

from __future__ import annotations
import math, cmath, datetime as dt
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional

import swisseph as swe

# ============================================================================
# 0. SABİTLER
# ============================================================================

PHI      = (1 + 5 ** 0.5) / 2          # 1.6180339887
INV_PHI  = 1 / PHI                      # 0.6180339887
INV_PHI2 = 1 / PHI ** 2                 # 0.3819660113
INV_PHI3 = 1 / PHI ** 3                 # 0.2360679775  -> a_min (sıçrama tabanı)

GOLDEN_ANGLE  = 360 * INV_PHI2          # 137.50776405°
GOLDEN_ANGLE2 = 360 * INV_PHI           # 222.49223595°

ANCHOR_HZ = 528.0                       # 0° Koç'un frekansı (akort referansı)
OBLIQUITY = 23.4392911                  # OOB eşiği

EPH = swe.FLG_MOSEPH | swe.FLG_SPEED    # veri dosyası gerektirmez

BODIES = {
    'Güneş':   swe.SUN,    'Ay':      swe.MOON,   'Merkür': swe.MERCURY,
    'Venüs':   swe.VENUS,  'Mars':    swe.MARS,   'Jüpiter': swe.JUPITER,
    'Satürn':  swe.SATURN, 'Uranüs':  swe.URANUS, 'Neptün': swe.NEPTUNE,
    'Plüton':  swe.PLUTO,  'AyDüğümü': swe.MEAN_NODE,
}

# ortalama günlük hız (derece/gün) — hız normalizasyonu için
MEAN_SPEED = {
    'Güneş': 0.9856, 'Ay': 13.1764, 'Merkür': 1.383, 'Venüs': 1.174,
    'Mars': 0.524, 'Jüpiter': 0.0831, 'Satürn': 0.0335, 'Uranüs': 0.01176,
    'Neptün': 0.00600, 'Plüton': 0.00397, 'AyDüğümü': 0.0529, 'GüneyDüğüm': 0.0529,
}

# temel kütle (etki ağırlığı)
BASE_MASS = {
    'Güneş': 1.00, 'Ay': 1.00, 'Merkür': 0.75, 'Venüs': 0.75, 'Mars': 0.75,
    'Jüpiter': 0.60, 'Satürn': 0.70, 'Uranüs': 0.50, 'Neptün': 0.50,
    'Plüton': 0.50, 'AyDüğümü': 0.55, 'GüneyDüğüm': 0.55, 'ASC': 0.90, 'MC': 0.85,
}

SIGNS = ['Koç','Boğa','İkizler','Yengeç','Aslan','Başak',
         'Terazi','Akrep','Yay','Oğlak','Kova','Balık']

# yönetici / yücelme / düşüş / zarar tabloları (klasik)
RULER   = {'Koç':'Mars','Boğa':'Venüs','İkizler':'Merkür','Yengeç':'Ay','Aslan':'Güneş',
           'Başak':'Merkür','Terazi':'Venüs','Akrep':'Mars','Yay':'Jüpiter',
           'Oğlak':'Satürn','Kova':'Satürn','Balık':'Jüpiter'}
EXALT   = {'Güneş':'Koç','Ay':'Boğa','Merkür':'Başak','Venüs':'Balık','Mars':'Oğlak',
           'Jüpiter':'Yengeç','Satürn':'Terazi'}
FALL    = {'Güneş':'Terazi','Ay':'Akrep','Merkür':'Balık','Venüs':'Başak','Mars':'Yengeç',
           'Jüpiter':'Oğlak','Satürn':'Koç'}
DETRI   = {'Güneş':['Kova'],'Ay':['Oğlak'],'Merkür':['Yay','Balık'],
           'Venüs':['Koç','Akrep'],'Mars':['Boğa','Terazi'],
           'Jüpiter':['İkizler','Başak'],'Satürn':['Yengeç','Aslan']}

# klasik Ptolemaik + altın açılar:  (ad, açı, orb, tip)
ASPECTS = [
    ('Kavuşum',      0.0,  8.0, 'ptol'), ('Karşıt',     180.0, 8.0, 'ptol'),
    ('Üçgen',      120.0,  7.0, 'ptol'), ('Kare',        90.0, 7.0, 'ptol'),
    ('Sekstil',     60.0,  5.0, 'ptol'), ('Kincunks',   150.0, 3.0, 'minor'),
    ('YarımSekstil',30.0,  2.0, 'minor'),('YarımKare',   45.0, 2.5, 'minor'),
    ('SeskiKare',  135.0,  2.5, 'minor'),
    ('AltınAçı',   GOLDEN_ANGLE,  2.5, 'phi'),
    ('AltınTümler',GOLDEN_ANGLE2, 2.5, 'phi'),
    ('YarımAltın',  GOLDEN_ANGLE/2, 1.8, 'phi'),
    ('ÇeyrekAltın', GOLDEN_ANGLE/4, 1.2, 'phi'),
]

# ============================================================================
# 1. YARDIMCILAR
# ============================================================================

def norm360(x: float) -> float:
    return x % 360.0

def sep(a: float, b: float) -> float:
    """0..180 arası açısal ayrım."""
    d = abs(norm360(a - b))
    return 360 - d if d > 180 else d

def sign_of(lon: float) -> str:
    return SIGNS[int(norm360(lon) // 30)]

def dms(lon: float) -> str:
    l = norm360(lon); s = int(l // 30); r = l - 30 * s
    return f"{int(r):02d}°{int((r%1)*60):02d}' {SIGNS[s]}"

def phi_orb(delta: float, orb: float) -> float:
    """Altın oranlı orb sönümü: tam açıda 1, orb sınırında φ⁻¹≈0.618'in karesi."""
    if orb <= 0: return 0.0
    return PHI ** (-((delta / orb) ** 2)) if abs(delta) <= orb else 0.0

def jd_of(y, mo, d, h=0.0, tz=0.0) -> float:
    return swe.julday(y, mo, d, h - tz)

def dt_of(jd: float) -> dt.datetime:
    y, mo, d, h = swe.revjul(jd)
    return dt.datetime(y, mo, d) + dt.timedelta(hours=h)

def calc(jd: float, ipl: int) -> Tuple[float, float, float]:
    """(boylam, hız, deklinasyon)"""
    ecl, _ = swe.calc_ut(jd, ipl, EPH)
    equ, _ = swe.calc_ut(jd, ipl, EPH | swe.FLG_EQUATORIAL)
    return ecl[0], ecl[3], equ[1]

# ============================================================================
# 2. GÖK CİSMİ DURUMU
# ============================================================================

@dataclass
class Body:
    name: str
    lon: float
    speed: float
    decl: float
    house: int = 0
    # türetilenler
    kappa: float = 0.0            # eğrilik yükü  [-1..+1]  (- = Kabz, + = Bast)
    mass: float = 0.0             # etki kütlesi
    state: List[str] = field(default_factory=list)   # 'ufuk', 'boğaz', 'donmuş', 'OOB', 'R'
    dignity: float = 0.0

    @property
    def retro(self) -> bool: return self.speed < 0
    @property
    def sign(self) -> str:   return sign_of(self.lon)
    @property
    def oob(self) -> bool:   return abs(self.decl) > OBLIQUITY
    @property
    def antiscion(self) -> float:      return norm360(180 - self.lon)   # Yengeç/Oğlak ekseninde ayna
    @property
    def contra_antiscion(self) -> float: return norm360(360 - self.lon) # Koç/Terazi ekseninde ayna


@dataclass
class Chart:
    jd: float
    lat: float
    lon: float
    label: str = ""
    bodies: Dict[str, Body] = field(default_factory=dict)
    cusps: Tuple[float, ...] = ()
    asc: float = 0.0
    mc: float = 0.0

    def house_of(self, lon: float) -> int:
        lon = norm360(lon)
        for i in range(12):
            a, b = self.cusps[i], self.cusps[(i + 1) % 12]
            span = norm360(b - a)
            if norm360(lon - a) < span:
                return i + 1
        return 12


def build_chart(jd: float, lat: float, lon: float, label: str = "") -> Chart:
    # v2.2 yaması: Placidus kutup dairesi ötesinde tanımsızdır ve swisseph
    # hata verir. Astro Pro v9.2.4 ile aynı davranış: Whole Sign'a düş.
    # (Motorun geri kalanı v1.0'dan aynen korunmuştur.)
    try:
        cusps, ascmc = swe.houses(jd, lat, lon, b'P')
    except Exception:
        cusps, ascmc = swe.houses(jd, lat, lon, b'W')
    ch = Chart(jd=jd, lat=lat, lon=lon, label=label,
               cusps=tuple(cusps), asc=ascmc[0], mc=ascmc[1])
    for name, ipl in BODIES.items():
        l, v, dec = calc(jd, ipl)
        ch.bodies[name] = Body(name, l, v, dec)
    # Güney Düğüm
    nn = ch.bodies['AyDüğümü']
    ch.bodies['GüneyDüğüm'] = Body('GüneyDüğüm', norm360(nn.lon + 180), nn.speed, -nn.decl)
    # açılar
    ch.bodies['ASC'] = Body('ASC', ch.asc, 0.0, 0.0)
    ch.bodies['MC']  = Body('MC',  ch.mc,  0.0, 0.0)
    for b in ch.bodies.values():
        b.house = ch.house_of(b.lon)
    _curvature_field(ch)
    return ch

# ============================================================================
# 3. EĞRİLİK ALANI  κ   (Kabz / Bast)
# ============================================================================

def _dignity_score(b: Body) -> float:
    if b.name in ('ASC', 'MC', 'AyDüğümü', 'GüneyDüğüm'): return 0.0
    s = b.sign
    if RULER.get(s) == b.name:      return  1.00
    if EXALT.get(b.name) == s:      return  0.75
    if s in DETRI.get(b.name, []):  return -0.75
    if FALL.get(b.name) == s:       return -1.00
    return 0.0

def _house_score(h: int) -> float:
    if h in (1, 10):      return  0.90
    if h in (4, 7):       return  0.65
    if h in (5, 11):      return  0.35
    if h in (2, 9):       return  0.15
    if h in (3,):         return -0.20
    if h in (6,):         return -0.65
    if h in (8,):         return -0.80
    if h in (12,):        return -0.95
    return 0.0

def _solar_phase(b: Body, sun_lon: float) -> Tuple[float, List[str]]:
    """Yanma koridoru = olay ufku.  Cazimi = solucan deliği boğazı (işaret çevrilir)."""
    if b.name in ('Güneş', 'ASC', 'MC'): return 0.0, []
    d = sep(b.lon, sun_lon)
    if d <= 17 / 60:   return  +1.30, ['BOĞAZ (cazimi)']      # < 17'  -> ak delik ağzı
    if d <= 8.5:       return  -1.20, ['UFUK (yanık)']        # < 8.5° -> olay ufku içi
    if d <= 15.0:      return  -0.45, ['ışın altı']           # 8.5–15°
    return 0.0, []

def _curvature_field(ch: Chart) -> None:
    sun = ch.bodies['Güneş'].lon
    for b in ch.bodies.values():
        st: List[str] = []

        # 1) hareket bileşeni — duraksama = olay ufkunda donma
        vm = MEAN_SPEED.get(b.name, 1.0)
        c_mot = max(-1.0, min(1.0, b.speed / vm)) if vm else 0.0
        if b.name in ('ASC', 'MC'): c_mot = 0.0
        if b.retro: st.append('R (içe akış)')
        if (vm and abs(b.speed) < 0.06 * vm and
                b.name not in ('ASC','MC','Güneş','Ay','AyDüğümü','GüneyDüğüm')):
            st.append('DONMUŞ (duraksama = ufukta)')

        # 2) güneş fazı
        c_sol, st2 = _solar_phase(b, sun); st += st2

        # 3) ev
        c_hou = _house_score(b.house)

        # 4) onur
        c_dig = _dignity_score(b); b.dignity = c_dig

        # 5) düğümler sabit kutuplu
        if b.name == 'AyDüğümü':   c_hou, c_dig, c_mot, c_sol = 0.6, 0.6, 0.6, 0.0
        if b.name == 'GüneyDüğüm': c_hou, c_dig, c_mot, c_sol = -0.9, -0.9, -0.9, 0.0

        raw = 0.30 * c_mot + 0.30 * c_sol + 0.22 * c_hou + 0.18 * c_dig
        k = math.tanh(2.2 * raw)

        # 6) sınır dışı (OOB) = manifold dışı — genliği büyütür
        if b.oob and b.name not in ('ASC', 'MC'):
            st.append('OOB (manifold dışı)'); k *= 1.25

        b.kappa = max(-1.0, min(1.0, k))
        b.state = st

        m = BASE_MASS.get(b.name, 0.5)
        m *= 1 + 0.35 * max(0.0, _house_score(b.house))
        m *= 1 + 0.20 * abs(c_dig)
        if 'BOĞAZ (cazimi)' in st: m *= 1.6
        b.mass = m

# ============================================================================
# 4. BERZAH — Einstein–Rosen köprüleri
# ============================================================================

@dataclass
class Berzah:
    kabz: str
    bast: str
    kind: str          # açı adı / 'Antiscia' / 'KontraAntiscia'
    angle: float
    delta: float
    omega: float       # orb sönümü
    strength: float    # köprü şiddeti
    throat: float      # geçilebilirlik (boğaz yarıçapı)
    mediator: Optional[str] = None   # orta noktada duran üçüncü cisim

    def __str__(self):
        med = f"  ⟨aracı: {self.mediator}⟩" if self.mediator else ""
        return (f"{self.kabz:>11s} ⟶⟵ {self.bast:<11s} | {self.kind:<13s} "
                f"Δ={self.delta:4.2f}°  şiddet={self.strength:5.3f}  boğaz={self.throat:5.3f}{med}")


def find_berzah(ch: Chart, tau: float = 0.12, top: int = 12) -> List[Berzah]:
    """κ<-τ (Kabz) ile κ>+τ (Bast) düğümleri arasında açısal/aynalı bağ arar."""
    kabz = [b for b in ch.bodies.values() if b.kappa < -tau]
    bast = [b for b in ch.bodies.values() if b.kappa > +tau]
    out: List[Berzah] = []

    for A in kabz:
        for B in bast:
            if A.name == B.name: continue
            cands: List[Tuple[str, float, float, float]] = []
            d = sep(A.lon, B.lon)
            for nm, ang, orb, typ in ASPECTS:
                a = ang if ang <= 180 else 360 - ang
                dd = abs(d - a)
                if dd <= orb:
                    boost = 1.15 if typ == 'phi' else (1.0 if typ == 'ptol' else 0.8)
                    cands.append((nm, a, dd, phi_orb(dd, orb) * boost))
            # ayna simetrileri (solucan deliği ağzı eşleşmesi)
            da = sep(A.antiscion, B.lon)
            if da <= 1.5: cands.append(('Antiscia', 0.0, da, phi_orb(da, 1.5) * 1.10))
            dc = sep(A.contra_antiscion, B.lon)
            if dc <= 1.5: cands.append(('KontraAntiscia', 0.0, dc, phi_orb(dc, 1.5) * 1.10))
            if not cands: continue
            nm, ang, dd, om = max(cands, key=lambda t: t[3])

            # orta nokta aracısı
            mid = norm360(A.lon + norm360(B.lon - A.lon) / 2)
            mediator, mbonus = None, 0.0
            for C in ch.bodies.values():
                if C.name in (A.name, B.name): continue
                md = min(sep(C.lon, mid), sep(C.lon, norm360(mid + 180)))
                if md <= 1.8:
                    mediator, mbonus = C.name, 0.45 * phi_orb(md, 1.8) * C.mass
                    break

            grad = (B.kappa - A.kappa) / 2.0
            s = math.sqrt(A.mass * B.mass) * om * grad * (1 + mbonus)
            throat = om * grad * (1.35 if 'BOĞAZ (cazimi)' in B.state else 1.0)
            out.append(Berzah(A.name, B.name, nm, ang, dd, om, s, throat, mediator))

    out.sort(key=lambda x: -x.strength)
    seen: Dict[str, int] = {}
    keep: List[Berzah] = []
    for b in out:
        if seen.get(b.kabz, 0) >= 2: continue
        seen[b.kabz] = seen.get(b.kabz, 0) + 1
        keep.append(b)
    return keep[:top]

# ============================================================================
# 5. SIÇRAMA — iç içe döngülerin faz uyumu (Kuramoto)
# ============================================================================

CYCLE_W = {'Ay Fazı': 1.00, 'Ay Dönüşü': 0.85, 'Solar Return': 1.00,
           'İlerletilmiş Ay Fazı': 0.80, 'Düğüm': 0.55, 'Jüpiter': 0.45, 'Satürn': 0.90}

def cycle_phases(natal: Chart, jd: float) -> Dict[str, float]:
    """Her döngü için Θ ∈ [0,2π). Θ=0 → SIÇRAMA (yeni döngü), Θ=π → azami genişleme."""
    ph: Dict[str, float] = {}
    su, _, _ = calc(jd, swe.SUN); mo, _, _ = calc(jd, swe.MOON)
    ph['Ay Fazı']      = math.radians(norm360(mo - su))
    ph['Ay Dönüşü']    = math.radians(norm360(mo - natal.bodies['Ay'].lon))
    ph['Solar Return'] = math.radians(norm360(su - natal.bodies['Güneş'].lon))
    nd, _, _ = calc(jd, swe.MEAN_NODE)
    ph['Düğüm']   = math.radians(norm360(natal.bodies['AyDüğümü'].lon - nd))
    ju, _, _ = calc(jd, swe.JUPITER); sa, _, _ = calc(jd, swe.SATURN)
    ph['Jüpiter'] = math.radians(norm360(ju - natal.bodies['Jüpiter'].lon))
    ph['Satürn']  = math.radians(norm360(sa - natal.bodies['Satürn'].lon))
    # ikincil ilerletme: 1 gün = 1 yıl
    pjd = natal.jd + (jd - natal.jd) / 365.242190
    psu, _, _ = calc(pjd, swe.SUN); pmo, _, _ = calc(pjd, swe.MOON)
    ph['İlerletilmiş Ay Fazı'] = math.radians(norm360(pmo - psu))
    return ph

def scale_factor(theta: float, a_min: float = INV_PHI3) -> float:
    """a(Θ) = a_min + (1-a_min)(1-cosΘ)/2 — sıfıra asla inmez (kuantum tabanı φ⁻³)."""
    return a_min + (1 - a_min) * (1 - math.cos(theta)) / 2

def coherence(ph: Dict[str, float]) -> Tuple[float, float]:
    """Kuramoto düzen parametresi: (C, Ψ). C→1 tüm döngüler hizalı."""
    num = sum(CYCLE_W[k] * cmath.exp(1j * v) for k, v in ph.items() if k in CYCLE_W)
    den = sum(CYCLE_W[k] for k in ph if k in CYCLE_W)
    z = num / den
    return abs(z), math.degrees(cmath.phase(z)) % 360

def bounce_index(ph: Dict[str, float]) -> float:
    """Sıçrama yakınlığı: tüm Θ'lar 0'a yaklaştıkça 1'e gider."""
    tot = w = 0.0
    for k, v in ph.items():
        if k not in CYCLE_W: continue
        tot += CYCLE_W[k] * (1 + math.cos(v)) / 2
        w   += CYCLE_W[k]
    return tot / w

# ============================================================================
# 6. LQC YOĞUNLUK / GERİ SEKME
# ============================================================================

HARD = [0.0, 90.0, 180.0, 45.0, 135.0]
STRESSORS = {'Satürn': swe.SATURN, 'Uranüs': swe.URANUS, 'Neptün': swe.NEPTUNE,
             'Plüton': swe.PLUTO, 'Mars': swe.MARS}

def density(natal: Chart, jd: float) -> float:
    """ρ(t): Kabz düğümlerine gelen sert transitlerin birikmiş basıncı."""
    rho = 0.0
    for tn, ipl in STRESSORS.items():
        tl, _, _ = calc(jd, ipl)
        wt = {'Satürn': 1.0, 'Plüton': 1.1, 'Uranüs': 0.9, 'Neptün': 0.7, 'Mars': 0.35}[tn]
        for b in natal.bodies.values():
            if b.kappa >= 0: continue
            d = sep(tl, b.lon)
            for a in HARD:
                aa = a if a <= 180 else 360 - a
                dd = abs(d - aa)
                orb = 6.0 if aa in (0, 90, 180) else 2.0
                if dd <= orb:
                    rho += wt * b.mass * abs(b.kappa) * phi_orb(dd, orb)
    return rho

def critical_density(natal: Chart) -> float:
    """ρ_c: haritanın taşıma kapasitesi (Satürn durumu + toplam kütle)."""
    sat = natal.bodies['Satürn']
    cap = 1.6 + 0.5 * sat.dignity + 0.35 * max(0.0, _house_score(sat.house))
    cap *= 1 + 0.10 * sum(b.mass for b in natal.bodies.values()) / 8
    return max(0.8, cap)

def hubble(rho: float, rho_c: float) -> Tuple[float, float]:
    """LQC efektif Friedmann:  H ∝ √(ρ(1-ρ/ρ_c)).  x=1'de H=0 → SIÇRAMA."""
    x = min(rho / rho_c, 1.4)
    H = 2 * math.sqrt(max(0.0, x * (1 - x))) if x <= 1 else 0.0
    return x, H

# ============================================================================
# 7. 528 Hz HARMONİK İMZA
# ============================================================================

def to_hz(lon: float) -> float:
    """Tüm zodyağı TEK oktava eşler: 0° Koç = 528 Hz, 360° = 1056 Hz."""
    return ANCHOR_HZ * 2 ** (norm360(lon) / 360)

def cents(a: float, b: float) -> float:
    return 1200 * math.log2(a / b)

def dissonance(f1: float, f2: float, a1: float = 1.0, a2: float = 1.0) -> float:
    """Plomp–Levelt / Sethares pürüzlülük çekirdeği."""
    fmin, fmax = (f1, f2) if f1 < f2 else (f2, f1)
    s = 0.24 / (0.0207 * fmin + 18.96)
    d = fmax - fmin
    return a1 * a2 * (math.exp(-3.5 * s * d) - math.exp(-5.75 * s * d))

def harmonic_signature(ch: Chart, names: Optional[List[str]] = None) -> dict:
    names = names or ['Güneş','Ay','Merkür','Venüs','Mars','Jüpiter','Satürn','ASC','MC']
    bs = [ch.bodies[n] for n in names if n in ch.bodies]
    freqs = {b.name: to_hz(b.lon) for b in bs}
    ivals, D = [], 0.0
    for i in range(len(bs)):
        for j in range(i + 1, len(bs)):
            c = abs(cents(freqs[bs[i].name], freqs[bs[j].name]))
            c = min(c, 1200 - c)
            w = math.sqrt(bs[i].mass * bs[j].mass)
            r = dissonance(freqs[bs[i].name], freqs[bs[j].name], w, w)
            D += r
            ivals.append((bs[i].name, bs[j].name, c, r))
    ivals.sort(key=lambda t: -t[3])
    # temel ton: en ağır cismin frekansı
    root = max(bs, key=lambda b: b.mass)
    return {'freqs': freqs, 'intervals': ivals,
            'dissonance': D / max(1, len(ivals)),
            'root': root.name, 'root_hz': freqs[root.name]}

# ============================================================================
# 8. DÖNÜŞ HARİTALARI & SIÇRAMA TAKVİMİ
# ============================================================================

def _find_return(jd0: float, ipl: int, target: float, step: float, span: float) -> float:
    """target boylamına dönüş anını ikili aramayla bulur."""
    def f(j):
        l, _, _ = calc(j, ipl)
        d = norm360(l - target)
        return d - 360 if d > 180 else d
    a = jd0; fa = f(a); j = a
    n = int(span / step)
    for _ in range(n):
        b = j + step; fb = f(b)
        if fa <= 0 <= fb and abs(fb - fa) < 180:
            for _ in range(60):
                m = (j + b) / 2; fm = f(m)
                if fa * fm <= 0: b, fb = m, fm
                else: j, fa = m, fm
            return (j + b) / 2
        j, fa = b, fb
    return jd0

def solar_return(natal: Chart, year: int, lat: float, lon: float) -> Chart:
    start = swe.julday(year, 1, 1, 0)
    jd = _find_return(start, swe.SUN, natal.bodies['Güneş'].lon, 2.0, 380)
    return build_chart(jd, lat, lon, f"Solar Return {year}")

def lunar_return(natal: Chart, after_jd: float, lat: float, lon: float) -> Chart:
    jd = _find_return(after_jd, swe.MOON, natal.bodies['Ay'].lon, 0.25, 30)
    return build_chart(jd, lat, lon, "Ay Dönüşü")

def lunations(jd0: float, days: int) -> List[Tuple[float, str, float, bool]]:
    """(jd, 'Yeni Ay'/'Dolunay', boylam, tutulma_mı)"""
    out = []
    prev = None; j = jd0
    while j < jd0 + days:
        su, _, _ = calc(j, swe.SUN); mo, _, _ = calc(j, swe.MOON)
        el = norm360(mo - su)
        if prev is not None:
            for tgt, nm in ((0.0, 'Yeni Ay'), (180.0, 'Dolunay')):
                a = norm360(prev - tgt); b = norm360(el - tgt)
                if a > 300 and b < 60:
                    lo, hi = j - 0.5, j
                    for _ in range(50):
                        m = (lo + hi) / 2
                        s2, _, _ = calc(m, swe.SUN); m2, _, _ = calc(m, swe.MOON)
                        e = norm360(norm360(m2 - s2) - tgt)
                        if e > 180: e -= 360
                        if e < 0: lo = m
                        else: hi = m
                    t = (lo + hi) / 2
                    s3, _, _ = calc(t, swe.SUN); m3, _, _ = calc(t, swe.MOON)
                    nd, _, _ = calc(t, swe.MEAN_NODE)
                    dn = min(sep(m3, nd), sep(m3, norm360(nd + 180)))
                    ecl = dn < (18.0 if nm == 'Yeni Ay' else 12.0)
                    out.append((t, nm, m3, ecl))
        prev = el; j += 0.5
    return out

def bounce_calendar(natal: Chart, jd0: float, days: int = 365, top: int = 10):
    """Günlük C(t), sıçrama endeksi ve ρ/ρ_c taraması; en yüksek geçiş pencereleri."""
    rho_c = critical_density(natal)
    rows = []
    for k in range(days):
        j = jd0 + k
        ph = cycle_phases(natal, j)
        C, Psi = coherence(ph)
        Bi = bounce_index(ph)
        x, H = hubble(density(natal, j), rho_c)
        rows.append({'jd': j, 'C': C, 'psi': Psi, 'bounce': Bi, 'x': x, 'H': H,
                     'score': 0.45 * Bi + 0.30 * C + 0.25 * x})
    peaks = []
    for i in range(1, len(rows) - 1):
        if rows[i]['score'] >= rows[i-1]['score'] and rows[i]['score'] > rows[i+1]['score']:
            peaks.append(rows[i])
    peaks.sort(key=lambda r: -r['score'])
    return rows, peaks[:top]

# ============================================================================
# 9. RAPOR
# ============================================================================

def report(natal: Chart, days: int = 365, calendar: bool = True,
           from_jd: Optional[float] = None) -> str:
    L = []
    P = L.append
    P("=" * 78)
    P(f"  BERZAH MODELİ v1.0 — {natal.label}")
    P(f"  {dt_of(natal.jd):%Y-%m-%d %H:%M} UT   φ={natal.lat:.3f}  λ={natal.lon:.3f}")
    P("=" * 78)

    P("\n▸ 1. EĞRİLİK ALANI  (κ<0 Kabz/kara delik · κ>0 Bast/ak delik)")
    P(f"  {'cisim':<12}{'konum':<16}{'ev':>3}  {'κ':>7} {'kütle':>6}  durum")
    for b in sorted(natal.bodies.values(), key=lambda x: x.kappa):
        bar = ('█' * int(abs(b.kappa) * 10)).rjust(10) if b.kappa < 0 else ' ' * 10
        bar2 = '█' * int(abs(b.kappa) * 10) if b.kappa > 0 else ''
        P(f"  {b.name:<12}{dms(b.lon):<16}{b.house:>3}  {b.kappa:+7.3f} {b.mass:6.2f}  "
          f"{bar}|{bar2:<10} {', '.join(b.state)}")

    tot = sum(b.kappa * b.mass for b in natal.bodies.values())
    P(f"\n  ⟹ Net eğrilik Σκ·m = {tot:+.3f}  "
      f"({'KABZ baskın — içe çöken harita' if tot < 0 else 'BAST baskın — dışa yayan harita'})")

    P("\n▸ 2. BERZAH KÖPRÜLERİ  (Kabz ⟶⟵ Bast · Einstein–Rosen ekseni)")
    brs = find_berzah(natal)
    if not brs: P("  (eşiği aşan köprü yok)")
    for i, b in enumerate(brs, 1):
        P(f"  {i:>2}. {b}")
    if brs:
        b = brs[0]
        P(f"\n  ⟹ BİRİNCİL DÖNÜŞÜM EKSENİ: {b.kabz} → {b.bast}")
        P(f"     '{b.kabz}' alanında sıkışan yük, '{b.bast}' kapısından tahliye olur.")

    P("\n▸ 3. UFUK & BOĞAZ OLAYLARI")
    any_ = False
    for b in natal.bodies.values():
        if b.state:
            P(f"  · {b.name:<12} {dms(b.lon):<16} → {', '.join(b.state)}"); any_ = True
    if not any_: P("  (kayda değer ufuk olayı yok)")

    P("\n▸ 4. HARMONİK İMZA  (0° Koç = 528 Hz, zodyak = 1 oktav)")
    hs = harmonic_signature(natal)
    P(f"  Temel ton: {hs['root']} = {hs['root_hz']:.2f} Hz   "
      f"ortalama pürüzlülük D = {hs['dissonance']:.4f}")
    for n, f in sorted(hs['freqs'].items(), key=lambda kv: kv[1]):
        P(f"    {n:<10} {f:7.2f} Hz")
    P("  En pürüzlü üç aralık:")
    for a, b2, c, r in hs['intervals'][:3]:
        P(f"    {a}–{b2}: {c:6.1f} sent  (pürüzlülük {r:.4f})")

    P("\n▸ 5. LQC BASINÇ DURUMU (bugün)")
    rc = critical_density(natal)
    x, H = hubble(density(natal, natal.jd), rc)
    P(f"  ρ/ρ_c = {x:.3f}   H = {H:.3f}   "
      f"{'⚠ SIÇRAMA EŞİĞİ' if x > 0.9 else ('sıkışma' if x > 0.5 else 'genişleme')}")

    if calendar:
        j0 = from_jd if from_jd is not None else swe.julday(*dt.datetime.utcnow().timetuple()[:3], 0)
        P(f"\n▸ 6. SIÇRAMA TAKVİMİ  ({dt_of(j0):%Y-%m-%d} + {days} gün)")
        rows, peaks = bounce_calendar(natal, j0, days)
        P(f"  {'tarih':<12}{'C':>6}{'sıçrama':>9}{'ρ/ρc':>7}{'H':>7}  yorum")
        for r in peaks:
            note = ('★ TAM SIÇRAMA — döngüler hizalı' if r['bounce'] > .82 and r['C'] > .70
                    else 'GEÇİT (Tayy-i Mekân) penceresi' if r['C'] > .50 or r['bounce'] > .70
                    else 'kısmi hizalanma')
            if r['x'] > 0.92: note += '  ⚠ρ→ρc: geri sekme'
            P(f"  {dt_of(r['jd']):%Y-%m-%d}  {r['C']:5.3f} {r['bounce']:8.3f}"
              f" {r['x']:6.3f} {r['H']:6.3f}  {note}")

        P("\n▸ 7. AY DÖNGÜSÜ ÜST KATMANI")
        for j, nm, lo, ec in lunations(j0, min(days, 200)):
            hit = None
            for b in natal.bodies.values():
                if sep(lo, b.lon) < 3.0 and abs(b.kappa) > .25:
                    hit = f"→ natal {b.name} (κ={b.kappa:+.2f})"; break
            tag = ' ★TUTULMA (boğazda sıçrama)' if ec else ''
            if hit or ec:
                P(f"  {dt_of(j):%Y-%m-%d}  {nm:<8} {dms(lo):<16}{tag} {hit or ''}")

    P("\n" + "=" * 78)
    return "\n".join(L)


# ============================================================================
# 10. DEMO
# ============================================================================
if __name__ == '__main__':
    swe.set_ephe_path(None)
    # ——— BURAYI KENDİ VERİNİZLE DEĞİŞTİRİN ———
    Y, MO, D, H, TZ = 1990, 6, 21, 14.5, 3.0      # yerel saat, UTC ofseti
    LAT, LON = 40.8000, 29.4333                    # Gebze
    natal = build_chart(jd_of(Y, MO, D, H, TZ), LAT, LON, "Örnek Natal")
    today = swe.julday(*dt.datetime.utcnow().timetuple()[:3], 0.0)
    print(report(natal, days=365, from_jd=today))

    print("\n\n### SOLAR RETURN 2026 — delta eğrilik ###")
    sr = solar_return(natal, 2026, LAT, LON)
    print(f"SR anı: {dt_of(sr.jd):%Y-%m-%d %H:%M} UT   ASC {dms(sr.asc)}")
    dk = sum(b.kappa * b.mass for b in sr.bodies.values()) - \
         sum(b.kappa * b.mass for b in natal.bodies.values())
    print(f"Δ(Σκ·m) = {dk:+.3f}  →  "
          f"{'yıl KABZ yönünde (inşa/sıkıştırma)' if dk < 0 else 'yıl BAST yönünde (tahliye/yayılma)'}")
    for br in find_berzah(natal, top=3):
        if sep(sr.asc, natal.bodies[br.bast].lon) < 5 or sep(sr.asc, natal.bodies[br.kabz].lon) < 5:
            print(f"★ SR ASC natal berzah ucunda: {br.kabz}→{br.bast} — KÖPRÜ YILI")
