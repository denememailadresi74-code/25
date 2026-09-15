#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Efemeris köprüsü — tek harita üretici. MOSEPH (dosyasız) varsayılan; ephe/ varsa SWIEPH."""
from __future__ import annotations
import datetime as dt
import math
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import swisseph as swe

from .circular import norm360, sep, sign_of, house_of

# Efemeris dosyaları repo içinde ephe/ altında varsa yüksek hassasiyet kullan
_EPHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ephe")
if os.path.isdir(_EPHE_DIR) and any(f.endswith(".se1") for f in os.listdir(_EPHE_DIR)):
    swe.set_ephe_path(_EPHE_DIR)
    EPHFLAG = swe.FLG_SWIEPH | swe.FLG_SPEED
else:
    EPHFLAG = swe.FLG_MOSEPH | swe.FLG_SPEED

BODY_IDS: Dict[str, int] = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY, "Venus": swe.VENUS,
    "Mars": swe.MARS, "Jupiter": swe.JUPITER, "Saturn": swe.SATURN,
    "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE, "Pluto": swe.PLUTO,
    "TrueNode": swe.TRUE_NODE, "Chiron": swe.CHIRON,
}
TR_NAME = {"Sun": "Güneş", "Moon": "Ay", "Mercury": "Merkür", "Venus": "Venüs",
           "Mars": "Mars", "Jupiter": "Jüpiter", "Saturn": "Satürn",
           "Uranus": "Uranüs", "Neptune": "Neptün", "Pluto": "Plüton",
           "TrueNode": "Kuzey Ay Düğümü", "Chiron": "Chiron"}
MEAN_SPEED = {"Sun": 0.9856, "Moon": 13.1764, "Mercury": 1.383, "Venus": 1.2,
              "Mars": 0.524, "Jupiter": 0.0831, "Saturn": 0.0335,
              "Uranus": 0.0117, "Neptune": 0.006, "Pluto": 0.004,
              "TrueNode": 0.0529, "Chiron": 0.05}
CORE10 = ["Sun", "Moon", "Mercury", "Venus", "Mars",
          "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]


_EPHE_AYARLI = False


def ensure_ephe() -> None:
    """
    SWIEPH yolunu bir kez ayarlar.
    v3.0'da bu fonksiyon her calc_ut öncesi set_ephe_path çağırıyordu: tek
    analizde 21.476 çağrı, 0.5 saniye boşa gidiyordu. Yol süreç ömrü boyunca
    kalıcıdır; bir kez ayarlamak yeterli.
    """
    global _EPHE_AYARLI
    if _EPHE_AYARLI:
        return
    if EPHFLAG & swe.FLG_SWIEPH:
        swe.set_ephe_path(_EPHE_DIR)
    _EPHE_AYARLI = True


def _yeniden_dene(fn):
    """
    Efemeris yolu herhangi bir sebeple kaybolursa (süreç yeniden başlatma,
    kütüphane içi sıfırlama, iş parçacığı havuzu) swisseph 'seas_18.se1 not
    found' hatası verir ve kullanıcı ekranda ham hata görür. v3.1'de yol tek
    seferlik bayrakla ayarlanıyordu; bayrak True kalıp yol gitmişse kurtuluş
    yoktu. Artık ilk hatada yol zorla yeniden kurulur ve işlem bir kez
    tekrarlanır.
    """
    def sarmal(*a, **kw):
        try:
            return fn(*a, **kw)
        except Exception:
            global _EPHE_AYARLI
            _EPHE_AYARLI = False
            ensure_ephe()
            return fn(*a, **kw)
    return sarmal


@_yeniden_dene
def calc_lon(jd: float, key: str) -> float:
    ensure_ephe()
    (lo, *_), _ = swe.calc_ut(jd, BODY_IDS[key], EPHFLAG)
    return norm360(lo)


@_yeniden_dene
def calc_lonspeed(jd: float, key: str) -> Tuple[float, float]:
    ensure_ephe()
    (lo, _la, _r, sp, *_), _ = swe.calc_ut(jd, BODY_IDS[key], EPHFLAG)
    return norm360(lo), sp


@dataclass
class BodyPos:
    key: str
    name_tr: str
    lon: float
    lat: float
    speed: float
    decl: float
    retro: bool
    # Sağ açıklık: küresel alan (Φ üzerinde iki boyut) için gerekli.
    # Ekvatoral çağrı zaten yapılıyordu ama RA atılıyordu.
    ra: float = 0.0


@dataclass
class NatalChart:
    label: str
    jd_ut: float
    lat: float
    lng: float
    tz_offset: float
    bodies: Dict[str, BodyPos]
    asc: float
    mc: float
    vertex: float
    cusps: List[float]
    house_system: str = "P"
    tz_source: str = "?"

    def lon(self, key: str) -> float:
        return self.bodies[key].lon

    def lons_w(self, weights: Dict[str, float], keys: Optional[List[str]] = None):
        ks = keys or CORE10
        return [(self.bodies[k].lon, weights.get(k, 1.0)) for k in ks if k in self.bodies]

    def house(self, lon: float) -> Optional[int]:
        return house_of(lon, self.cusps)


def _zone_tanisi(when: dt.datetime, zone) -> Tuple[float, str]:
    """
    Bir yerel duvar saatinin UTC ofsetini çöz ve yaz saati geçiş tuzaklarını bildir.

    İki tuzak vardır ve ikisi de sessizce 1 saat hata üretir:
      • VAR OLMAYAN saat — saat ileri alınırken atlanan aralık (o an hiç yaşanmadı)
      • BELİRSİZ saat    — saat geri alınırken iki kez yaşanan aralık
    Astro Pro v9.2.4 bunları pytz ile açıkça yakalıyordu; burada da yakalanır.
    """
    a0 = when.replace(tzinfo=zone, fold=0)
    a1 = when.replace(tzinfo=zone, fold=1)
    off0 = a0.utcoffset().total_seconds() / 3600.0
    off1 = a1.utcoffset().total_seconds() / 3600.0

    # Var olmayan saat: gidip dönünce duvar saati değişiyorsa boşluktayız
    geri = a0.astimezone(dt.timezone.utc).astimezone(zone).replace(tzinfo=None)
    if geri != when:
        return off0, ("⚠ VAR OLMAYAN SAAT — bu an yaz saati ileri alınırken atlandı. "
                      f"UTC{off0:+.1f} varsayıldı; doğum saatini teyit edin.")
    if off0 != off1:
        return off0, ("⚠ BELİRSİZ SAAT — saat geri alınırken bu an iki kez yaşandı. "
                      f"Yaz saati dalı (UTC{off0:+.1f}) seçildi; kış dalı UTC{off1:+.1f}.")

    yaz = a0.dst().total_seconds() / 3600.0 if a0.dst() else 0.0
    ad = a0.tzname() or ""
    return off0, (f"{ad} · UTC{off0:+.1f}" + (f" (yaz saati +{yaz:.0f}sa)" if yaz else ""))


def resolve_tz(lat: float, lng: float, when: dt.datetime,
               tz_name: Optional[str] = None,
               tz_offset: Optional[float] = None) -> Tuple[float, str]:
    """
    UTC ofsetini çöz ve KAYNAĞINI bildir.
    Öncelik: tz_offset > tz_name(IANA) > timezonefinder(varsa) > boylamdan tahmin.
    Sessiz yanlış saat dilimi natal haritada en pahalı hatadır; kaynak her zaman
    yanıtta görünür.
    """
    if tz_offset is not None:
        return float(tz_offset), f"elle verilen ofset UTC{float(tz_offset):+.1f}"
    if tz_name:
        from zoneinfo import ZoneInfo
        try:
            return _zone_tanisi(when, ZoneInfo(tz_name))
        except Exception as e:
            raise ValueError(f"Saat dilimi tanınmadı: {tz_name} ({e})")
    try:
        from timezonefinder import TimezoneFinder   # opsiyonel
        from zoneinfo import ZoneInfo
        name = TimezoneFinder().timezone_at(lat=lat, lng=lng)
        if name:
            off, notu = _zone_tanisi(when, ZoneInfo(name))
            return off, f"timezonefinder {name} · {notu}"
    except Exception:
        pass
    return round(lng / 15.0), ("⚠ BOYLAMDAN TAHMİN — yaz saati tarihçesi hesaba "
                               "katılmadı. tz_name veya tz_offset gönderin.")


def julday_local(y: int, mo: int, d: int, h: int, mi: int, tz_off: float) -> float:
    return swe.julday(y, mo, d, h + mi / 60.0 - tz_off)


@_yeniden_dene
def calc_body(jd: float, key: str) -> BodyPos:
    ensure_ephe()
    (lo, la, _r, slo, _sla, _sr), _ = swe.calc_ut(jd, BODY_IDS[key], EPHFLAG)
    try:
        (ra, dec, *_), _ = swe.calc_ut(jd, BODY_IDS[key],
                                       EPHFLAG | swe.FLG_EQUATORIAL)
    except Exception:
        ra, dec = 0.0, 0.0
    return BodyPos(key, TR_NAME.get(key, key), norm360(lo), la, slo, dec,
                   slo < 0, norm360(ra))


def _evler(jd: float, lat: float, lng: float, hsys: str):
    """
    Ev uçlarını hesapla.
      • pyswisseph sürümüne göre cusps 12 ya da 13 (idx 0 boş) elemanlı olabilir.
      • Placidus/Koch kutup dairelerinde (|enlem| > 66.5°) matematiksel olarak
        tanımsızdır ve swisseph hata verir → Whole Sign'a düşülür (Astro Pro ile aynı).
    """
    hb = hsys.encode() if isinstance(hsys, str) else hsys
    kullanilan = hsys if isinstance(hsys, str) else hsys.decode()
    try:
        cusps, ascmc = swe.houses_ex(jd, lat, lng, hb)
    except Exception:
        cusps, ascmc = swe.houses_ex(jd, lat, lng, b"W")
        kullanilan = "W (kutup bölgesi — Placidus tanımsız)"
    cl = list(cusps)
    c12 = [norm360(cl[i]) for i in range(1, 13)] if len(cl) >= 13 \
        else [norm360(cl[i]) for i in range(12)]
    return c12, ascmc, kullanilan


def build_chart(y: int, mo: int, d: int, h: int, mi: int,
                lat: float, lng: float,
                tz_name: Optional[str] = None, tz_offset: Optional[float] = None,
                label: str = "Natal", house_system: str = "P",
                jd_ut_override: Optional[float] = None) -> NatalChart:
    # Swiss Ephemeris yolu süreç-globaldir. Uzun yaşayan web worker'ında başka
    # bir katman yolu değiştirirse bayrak True kaldığı için `ensure_ephe()` bunu
    # fark etmeyebilir ve sonraki istek sessizce MOSEPH'e düşebilir. Harita
    # başına bir kez yolu yeniden ilan etmek, A-sınıfı natal çıktının SR aç/kapa
    # sırasından bağımsız ve hash düzeyinde kararlı kalmasını sağlar.
    if EPHFLAG & swe.FLG_SWIEPH:
        swe.set_ephe_path(_EPHE_DIR)
    when = dt.datetime(y, mo, d, h, mi)
    tz, tz_src = resolve_tz(lat, lng, when, tz_name, tz_offset)
    jd = jd_ut_override if jd_ut_override is not None else julday_local(y, mo, d, h, mi, tz)
    bodies = {k: calc_body(jd, k) for k in BODY_IDS}
    cusps, ascmc, house_system = _evler(jd, lat, lng, house_system)
    return NatalChart(label=label, jd_ut=jd, lat=lat, lng=lng, tz_offset=tz,
                      bodies=bodies, asc=norm360(ascmc[0]), mc=norm360(ascmc[1]),
                      vertex=norm360(ascmc[3]), cusps=cusps,
                      house_system=house_system, tz_source=tz_src)


def chart_at_jd(jd: float, lat: float, lng: float, label: str,
                house_system: str = "P") -> NatalChart:
    if EPHFLAG & swe.FLG_SWIEPH:
        swe.set_ephe_path(_EPHE_DIR)
    bodies = {k: calc_body(jd, k) for k in BODY_IDS}
    cusps, ascmc, hs_used = _evler(jd, lat, lng, house_system)
    return NatalChart(label=label, jd_ut=jd, lat=lat, lng=lng, tz_offset=0.0,
                      bodies=bodies, asc=norm360(ascmc[0]), mc=norm360(ascmc[1]),
                      vertex=norm360(ascmc[3]), cusps=cusps, house_system=hs_used)


def solar_return_jd(natal: NatalChart, year: int) -> float:
    """Güneş natal boylamına döndüğü an (ikiye bölme)."""
    ensure_ephe()
    target = natal.bodies["Sun"].lon
    jd = swe.julday(year, 1, 1, 0.0)
    # kaba tarama (gün adımı) sonra rafine
    prev = norm360(swe.calc_ut(jd, swe.SUN, EPHFLAG)[0][0] - target)
    for i in range(1, 400):
        j2 = jd + i
        cur = norm360(swe.calc_ut(j2, swe.SUN, EPHFLAG)[0][0] - target)
        if prev > 300 and cur < 60:  # 360 sarımı
            lo, hi = j2 - 1, j2
            for _ in range(50):
                mid = (lo + hi) / 2
                v = norm360(swe.calc_ut(mid, swe.SUN, EPHFLAG)[0][0] - target)
                if v > 300: lo = mid
                else: hi = mid
            return (lo + hi) / 2
        prev = cur
    return jd


def jd_to_iso(jd: float) -> str:
    y, mo, d, h = swe.revjul(jd)
    hh = int(h); mm = int(round((h - hh) * 60))
    if mm == 60: hh, mm = hh + 1, 0
    return f"{y:04d}-{mo:02d}-{d:02d} {hh:02d}:{mm:02d} UT"
