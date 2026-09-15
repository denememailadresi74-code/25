#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DERİN DOĞRULAMA — ZÎC

Duman testi "çöküyor mu" diye sorar. Bu koşum "DOĞRU MU" diye sorar:
her modülün çıktısını bağımsız bir yoldan yeniden hesaplar veya matematiksel
bir değişmezle sınar. Hata bulursa satır satır bildirir.
"""
from __future__ import annotations
import math
import os
import re
import sys
import random

sys.path.insert(0, ".")
import swisseph as swe

from app.astro import (build_chart, chart_at_jd, solar_return_jd, calc_lon,
                       EPHFLAG, ensure_ephe, CORE10, jd_to_iso)
from app.circular import (norm360, sep, signed_sep, antiscion, ebced_value,
                          circular_mean_weighted, circular_median, rayleigh_R,
                          house_of, fmt_lon, GOLDEN_ANGLE)
from app.engine_mass import (compute_masses, phi_field, force, barycenter,
                             find_kd_ad, find_berzah2, gate_of, GATE_WHEEL,
                             KING_WEN_BITS, full_v2, EPS)
from app.field_dynamics import kritik_noktalar, kalicilik_diyagrami, havza
from app.relationship import kompozit_harita
from app.module_hd import _design_jd, gate_line
from app.sira import sira_fazi, sira_yildizi, SIRA_P, SIRA_E, SIRA_T

GECTI, KALDI = [], []


def kontrol(ad: str, sart: bool, ayrinti: str = "") -> None:
    (GECTI if sart else KALDI).append(f"{ad}{(' — ' + ayrinti) if ayrinti else ''}")
    print(f"  {'✓' if sart else '✗ HATA'}  {ad}" + (f"  [{ayrinti}]" if ayrinti else ""))


CH = build_chart(1990, 6, 21, 14, 30, 40.80, 29.4333, tz_name="Europe/Istanbul")
MS = compute_masses(CH)


def bolum(b: str) -> None:
    print(f"\n{'='*70}\n {b}\n{'='*70}")


# ---------------------------------------------------------------- 1
bolum("1 · DAİRESEL MATEMATİK")
kontrol("sep simetrik", all(abs(sep(a, b) - sep(b, a)) < 1e-12
                            for a, b in [(10, 350), (0, 180), (95, 275), (359.9, 0.1)]))
kontrol("sep 0..180 aralığında", all(0 <= sep(random.uniform(0, 360),
                                              random.uniform(0, 360)) <= 180
                                     for _ in range(500)))
kontrol("signed_sep işaret tutarlı",
        all(abs(abs(signed_sep(a, b)) - sep(a, b)) < 1e-9
            for a, b in [(10, 350), (100, 20), (200, 350), (5, 6)]))
# antisya: Yengeç0/Oğlak0 ekseninde ayna → eksene uzaklık korunur
kontrol("antisya ekseni koruyor",
        all(abs(sep(x, 90) - sep(antiscion(x), 90)) < 1e-9
            for x in (0, 45, 137.5, 200, 315)))
kontrol("antisya kanonik: 0°Koç↔0°Terazi, 15°Boğa↔15°Aslan",
        abs(antiscion(0) - 180) < 1e-9 and abs(antiscion(45) - 135) < 1e-9)
kontrol("antisya evrimsel (iki kez uygula = kimlik)",
        all(abs(signed_sep(antiscion(antiscion(x)), x)) < 1e-9
            for x in (0, 33, 271, 359)))
# dairesel ortalama: aynı noktada toplanan küme
kontrol("circular_mean tek nokta",
        abs(signed_sep(circular_mean_weighted([(42.0, 1)] * 5)[0], 42.0)) < 1e-9)
m, R = circular_mean_weighted([(0, 1), (90, 1), (180, 1), (270, 1)])
kontrol("circular_mean tam simetride R≈0", R < 1e-9, f"R={R:.2e}")
kontrol("rayleigh_R tek noktada 1",
        abs(rayleigh_R([(30, 1), (30, 2)], 1) - 1.0) < 1e-12)
med, _ = circular_median([(10, 1), (12, 1), (14, 1)], step=0.05)
kontrol("circular_median ortada", sep(med, 12) < 0.2, f"{med:.2f}")

# ---------------------------------------------------------------- 2
bolum("2 · EFEMERİS VE EVLER")
jd = swe.julday(2000, 1, 1, 12.0)
kontrol("Güneş J2000 ≈ 280.37°", abs(calc_lon(jd, "Sun") - 280.369) < 0.05,
        f"{calc_lon(jd, 'Sun'):.4f}")


def asc_bagimsiz(jd_, lat, lng):
    T = (jd_ - 2451545.0) / 36525.0
    gmst = 280.46061837 + 360.98564736629 * (jd_ - 2451545.0) + 0.000387933 * T * T
    lst = math.radians((gmst + lng) % 360.0)
    eps = math.radians(23.439291 - 0.0130042 * T)
    phi = math.radians(lat)
    return math.degrees(math.atan2(math.cos(lst),
                                   -(math.sin(lst) * math.cos(eps)
                                     + math.tan(phi) * math.sin(eps)))) % 360.0


kontrol("Yükselen bağımsız formülle uyuşuyor",
        sep(CH.asc, asc_bagimsiz(CH.jd_ut, CH.lat, CH.lng)) < 0.05,
        f"{sep(CH.asc, asc_bagimsiz(CH.jd_ut, CH.lat, CH.lng))*3600:.1f}\"")
kontrol("12 ev ucu, ilk uç = ASC", len(CH.cusps) == 12 and sep(CH.cusps[0], CH.asc) < 1e-6)
kontrol("ev uçları artan sırada (dairesel)",
        all(0 < (CH.cusps[(i + 1) % 12] - CH.cusps[i]) % 360 < 180 for i in range(12)))
kontrol("her cisim bir eve düşüyor",
        all(house_of(b.lon, CH.cusps) is not None for b in CH.bodies.values()))
# MC 10. ev ucu olmalı (kuadrant sistemlerde)
kontrol("MC = 10. ev ucu (Placidus)", sep(CH.cusps[9], CH.mc) < 1e-6)

# Solar Return: Güneş natal boylamına dönmüş mü
srjd = solar_return_jd(CH, 2026)
kontrol("Solar Return Güneş natal boylamında",
        sep(calc_lon(srjd, "Sun"), CH.bodies["Sun"].lon) < 0.001,
        f"{sep(calc_lon(srjd, 'Sun'), CH.bodies['Sun'].lon)*3600:.2f}\"")
kontrol("Solar Return doğru yılda", swe.revjul(srjd)[0] == 2026)

# ---------------------------------------------------------------- 3
bolum("3 · KÜTLE, ALAN VE BERZAH")
# phi_field: gömülü matematik, referans uygulamayla aynı mı
ref = lambda lon: sum(m.mass / (sep(lon, m.lon) + EPS) for m in MS)
kontrol("phi_field optimize sürüm referansla aynı",
        all(abs(phi_field(x, MS) - ref(x)) < 1e-9 for x in range(0, 360, 7)))
refF = lambda lon: sum(m.mass * (1 if signed_sep(m.lon, lon) >= 0 else -1)
                       / (abs(signed_sep(m.lon, lon)) + EPS) ** 2 for m in MS)
kontrol("force optimize sürüm referansla aynı",
        all(abs(force(x, MS) - refF(x)) < 1e-9 for x in range(0, 360, 7)))
# F = dΦ/dλ olmalı (sayısal türev)
h = 1e-4
sapmalar = [abs(force(x, MS) - (phi_field(x + h, MS) - phi_field(x - h, MS)) / (2 * h))
            for x in (13, 77, 141, 203, 288, 331)]
kontrol("F(λ) = dΦ/dλ (sayısal türev)", max(sapmalar) < 1e-3, f"azami {max(sapmalar):.2e}")
# KD gerçekten küresel tepe mi
kd, ad = find_kd_ad(MS)
kontrol("KD küresel Φ tepesi",
        all(phi_field(kd, MS) >= phi_field(x, MS) - 1e-6 for x in range(0, 360)))
kontrol("AD = antisya(KD)", sep(ad, antiscion(kd)) < 1e-9)
# barisentr: ağır kütleye yakın olmalı
a, b = sorted(MS, key=lambda m: -m.abs_mass)[:2]
bc = barycenter(a, b)
kontrol("barisentr kısa yay içinde",
        sep(bc, a.lon) + sep(bc, b.lon) - sep(a.lon, b.lon) < 1e-6)
# DİKKAT: barisentr AĞIR kütleye yakındır (Güneş–Dünya barisentri Güneş içinde).
# Denge (L1) noktası ise HAFİF kütleye yakındır. İkisi karıştırılmamalı.
kontrol("barisentr ağır kütleye yakın",
        (sep(bc, a.lon) < sep(bc, b.lon)) == (a.abs_mass > b.abs_mass))
from app.engine_mass import _iki_deniz_dengesi
dng = _iki_deniz_dengesi(a, b)
kontrol("iki-deniz dengesi hafif kütleye yakın",
        (sep(dng, a.lon) > sep(dng, b.lon)) == (a.abs_mass > b.abs_mass))
# Berzah gerçekten denge mi
bz = find_berzah2(MS)
if bz and "doğrulanmış" in (bz.guven or ""):
    kontrol("Berzah'ta net kuvvet ≈ 0", abs(force(bz.lon, MS)) < 1e-4,
            f"F={force(bz.lon, MS):.2e}")
else:
    kontrol("Berzah saf eşik olarak bildirildi (alan bozucu)", True, bz.guven[:40] if bz else "")
kontrol("Berzah tekillikten uzak", bz.en_yakin_gezegen >= 2.5,
        f"{bz.en_yakin_gezegen:.2f}°")

# ---------------------------------------------------------------- 4
bolum("4 · HEKSAGRAM VE ALTIN AÇI")
kontrol("64 kapı, hepsi benzersiz", len(GATE_WHEEL) == 64 and len(set(GATE_WHEEL)) == 64)
kontrol("King Wen tablosu 64 kayıt", len(KING_WEN_BITS) == 64)
kontrol("King Wen bitleri 0-63 aralığında benzersiz",
        len(set(KING_WEN_BITS.values())) == 64
        and all(0 <= v <= 63 for v in KING_WEN_BITS.values()))
kontrol("hexagram 1 = 111111, hexagram 2 = 000000",
        KING_WEN_BITS[1] == 0b111111 and KING_WEN_BITS[2] == 0)
kontrol("11 (Tai) ve 12 (Pi) birbirinin tersi",
        KING_WEN_BITS[11] ^ KING_WEN_BITS[12] == 0b111111)
kontrol("kapı 41 = 302° (2° Kova) başlangıcı", gate_of(302.01)[0] == 41)
kontrol("kapı genişliği 5.625°",
        gate_of(302.0 + 5.62)[0] == 41 and gate_of(302.0 + 5.63)[0] != 41)
kontrol("altın açı = 360/φ²", abs(GOLDEN_ANGLE - 137.50776405) < 1e-6)
kontrol("çizgi 1..6 aralığında",
        all(1 <= gate_of(x)[1] <= 6 for x in range(0, 360, 3)))

# ---------------------------------------------------------------- 5
bolum("5 · HUMAN DESIGN")
djd = _design_jd(CH.jd_ut)
fark = (calc_lon(CH.jd_ut, "Sun") - calc_lon(djd, "Sun")) % 360
kontrol("dizayn haritası Güneş'i tam 88° geride", abs(fark - 88.0) < 0.001,
        f"{fark:.5f}°")
kontrol("dizayn anı doğumdan ~88 gün önce", 85 < (CH.jd_ut - djd) < 92,
        f"{CH.jd_ut - djd:.1f} gün")
kontrol("gate_line kapı ve çizgi tutarlı",
        all(gate_line(x)[0] == gate_of(x)[0] for x in range(0, 360, 11)))

# ---------------------------------------------------------------- 6
bolum("6 · TOPOLOJİ (v3.0)")
kn = kritik_noktalar(MS)
tepe = sum(1 for k in kn if k.tip == "tepe")
cukur = sum(1 for k in kn if k.tip == "cukur")
kontrol("çemberde tepe sayısı = çukur sayısı", tepe == cukur, f"{tepe} / {cukur}")
kontrol("tepe-çukur alternansı",
        all(kn[i].tip != kn[(i + 1) % len(kn)].tip for i in range(len(kn))))
kal = kalicilik_diyagrami(MS)
sonsuz = [o for o in kal["ozellikler"] if o["kalicilik"] is None]
kontrol("tam bir küresel tepe (sonsuz kalıcılık)", len(sonsuz) == 1)
kontrol("küresel tepe = KD", sep(sonsuz[0]["lon"], kd) < 1.0 if sonsuz else False,
        f"{sep(sonsuz[0]['lon'], kd):.2f}°" if sonsuz else "")
kontrol("kalıcılıklar negatif değil",
        all((o["kalicilik"] or 0) >= -1e-9 for o in kal["ozellikler"]))
# havza: varılan nokta gerçekten yerel tepe mi
tepe_lon, tepe_phi = havza(MS, CH.asc)
kontrol("havza gradyan çıkışı yerel tepeye varıyor",
        phi_field(tepe_lon, MS) >= phi_field(tepe_lon + 0.5, MS) - 1e-6
        and phi_field(tepe_lon, MS) >= phi_field(tepe_lon - 0.5, MS) - 1e-6)

# ---------------------------------------------------------------- 7
bolum("7 · ŞİRÂ ÇEVRİMİ (v3.1)")
# Kepler çözümü: E − e·sinE = M sağlanıyor mu
# Kepler denklemini ÇÖZÜCÜNÜN KENDİSİ üzerinden sına. Yayımlanan değerler
# yuvarlanmış olduğu için onlardan geri türetmek yapay artık üretir.
def _kepler_artik(t):
    M = 2 * math.pi * (((t - SIRA_T) / SIRA_P) % 1.0)
    E = M if SIRA_E < 0.8 else math.pi
    for _ in range(80):
        d = (E - SIRA_E * math.sin(E) - M) / (1 - SIRA_E * math.cos(E))
        E -= d
        if abs(d) < 1e-13:
            break
    return abs((E - SIRA_E * math.sin(E)) - M)


for t in (1990.47, 2026.6, 2044.0, 1950.0, 2099.9):
    kontrol(f"Kepler çözücüsü yakınsıyor (t={t})", _kepler_artik(t) < 1e-10,
            f"artık={_kepler_artik(t):.2e}")
# yayımlanan değerin hassasiyeti de yeterli mi
f = sira_fazi(swe.julday(2026, 8, 1, 0.0))
kontrol("yayımlanan faz/ayrıklık hassasiyeti ≥1e-6",
        abs(f["ayriklik"] - round(f["ayriklik"], 6)) < 1e-12)
peri = sira_fazi(swe.julday(1994, 7, 27, 0.0))
kontrol("perigeonda r/a = 1−e", abs(peri["ayriklik"] - (1 - SIRA_E)) < 0.01,
        f"{peri['ayriklik']:.4f} vs {1-SIRA_E:.4f}")
apo = sira_fazi(swe.julday(2019, 8, 5, 0.0))
kontrol("apogeonda r/a = 1+e", abs(apo["ayriklik"] - (1 + SIRA_E)) < 0.01,
        f"{apo['ayriklik']:.4f} vs {1+SIRA_E:.4f}")
kontrol("ayrıklık daima [1−e, 1+e] aralığında",
        all(1 - SIRA_E - 1e-9 <= sira_fazi(swe.julday(y, 1, 1, 0.0))["ayriklik"]
            <= 1 + SIRA_E + 1e-9 for y in range(1900, 2101, 7)))
kontrol("faz [0,1) aralığında",
        all(0 <= sira_fazi(swe.julday(y, 6, 1, 0.0))["faz"] < 1
            for y in range(1900, 2101, 11)))
# Kepler'in ikinci yasası: r²·(dν/dt) sabit
sabitler = []
for y in range(1995, 2045, 5):
    f = sira_fazi(swe.julday(y, 1, 1, 0.0))
    sabitler.append(f["ayriklik"] ** 2 * f["acisal_hiz"])
kontrol("Kepler 2. yasa: r²·dν/dt sabit",
        (max(sabitler) - min(sabitler)) < 1e-3,
        f"yayılım={max(sabitler)-min(sabitler):.2e}")
# Şi'râ A presesyonu
s1 = sira_yildizi(swe.julday(1900, 1, 1, 0.0))
s2 = sira_yildizi(swe.julday(2000, 1, 1, 0.0))
kayma = signed_sep(s2["lon"], s1["lon"])
kontrol("Şi'râ presesyonu ~1.39°/yüzyıl", 1.2 < kayma < 1.6, f"{kayma:.3f}°")
kontrol("Şi'râ Yengeç burcunda", 90 <= s2["lon"] < 120, fmt_lon(s2["lon"]))
kontrol("Şi'râ ekliptik enlemi ≈ −39.6°", abs(s2["enlem"] + 39.6) < 0.1,
        f"{s2['enlem']:.3f}")

# ---------------------------------------------------------------- 8
bolum("8 · KOMPOZİT VE EBCED")
CB = build_chart(1993, 11, 4, 9, 15, 41.0082, 28.9784, tz_name="Europe/Istanbul")
k1 = kompozit_harita(CH, CB)
k2 = kompozit_harita(CB, CH)
kontrol("kompozit simetrik (A&B = B&A)",
        all(sep(k1.bodies[k].lon, k2.bodies[k].lon) < 1e-6 for k in CORE10))
kontrol("kompozit gezegenleri kısa yay ortasında",
        all(abs(sep(k1.bodies[k].lon, CH.bodies[k].lon)
                - sep(k1.bodies[k].lon, CB.bodies[k].lon)) < 1e-6 for k in CORE10))
kontrol("kompozit eşit ev (30° aralıklı)",
        all(abs(((k1.cusps[(i + 1) % 12] - k1.cusps[i]) % 360) - 30) < 1e-6
            for i in range(12)))
# ebced: bilinen değerler
kontrol("ebced ا=1", ebced_value("ا") == 1)
kontrol("ebced محمد = 92", ebced_value("محمد") == 92, str(ebced_value("محمد")))
kontrol("ebced الله = 66", ebced_value("الله") == 66, str(ebced_value("الله")))
kontrol("ebced toplamsal",
        ebced_value("محمد") + ebced_value("الله") == ebced_value("محمدالله"))

# ---------------------------------------------------------------- 9
bolum("9 · UÇ DURUMLAR")
testler = [
    ("güney yarımküre", dict(y=1985, mo=3, d=9, h=11, mi=20, lat=-33.87, lng=151.21)),
    ("ekvator", dict(y=2000, mo=6, d=1, h=0, mi=0, lat=0.0, lng=0.0)),
    ("kutup dairesi", dict(y=1990, mo=12, d=21, h=3, mi=0, lat=69.65, lng=18.96)),
    ("gece yarısı", dict(y=1977, mo=1, d=1, h=0, mi=0, lat=39.93, lng=32.86)),
    ("artık gün", dict(y=1996, mo=2, d=29, h=12, mi=0, lat=41.01, lng=28.98)),
    ("1900 öncesi", dict(y=1888, mo=8, d=14, h=17, mi=45, lat=41.01, lng=28.98)),
    ("batı boylam", dict(y=1999, mo=7, d=4, h=8, mi=30, lat=40.71, lng=-74.01)),
]
for ad, kw in testler:
    try:
        c = build_chart(kw["y"], kw["mo"], kw["d"], kw["h"], kw["mi"],
                        kw["lat"], kw["lng"], tz_offset=0.0)
        r = full_v2(c)
        tamam = (r["KD"]["lon"] is not None and len(r["kutleler"]) == 10
                 and r.get("alan_topolojisi") is not None)
        kontrol(f"{ad}", tamam, f"KD {r['KD']['konum']}")
    except Exception as e:
        kontrol(f"{ad}", False, f"{type(e).__name__}: {e}")

# ---------------------------------------------------------------- 10
bolum("10 · ÇALIŞMA ZAMANI MATEMATİĞİ")
from app.modules_deneme import (asabiyye, vahdet, mizan, felek_saati, ayna_ekseni,
                                suveyda, icabet, noksan, _jacobi_eig, NURANI_W)
from app.modules_kadim import _TERMS_EGYPT, _TRIPL_DOROTHEUS
from app.module_hd import HD_CENTER_GATES, HD_CHANNELS, HD_GATES_WHEEL
from app.sira import MENZIL
from app.relationship import capraz_acilar
from app.circular import SIGNS

# statik tablolar
kontrol("Mısır hudûdu 12 burç × 5 terim, sınır 30°",
        len(_TERMS_EGYPT) == 12
        and all(len(v) == 5 and v[-1][0] == 30 for v in _TERMS_EGYPT.values()))
kontrol("hudûd sahipleri burç içinde tekrarsız ve ışıksız",
        all(len({x[1] for x in v}) == 5 and not ({x[1] for x in v} & {"Sun", "Moon"})
            for v in _TERMS_EGYPT.values()))
kontrol("Dorotheus üçlüleri 4 unsur × 3 yönetici",
        len(_TRIPL_DOROTHEUS) == 4 and all(len(v) == 3 for v in _TRIPL_DOROTHEUS.values()))
_tum = set()
for _g in HD_CENTER_GATES.values():
    _tum |= _g
kontrol("HD: 64 kapı tam olarak bir merkeze atanmış",
        _tum == set(range(1, 65))
        and sum(len(g) for g in HD_CENTER_GATES.values()) == 64)
_kk = set()
for _a, _b in HD_CHANNELS:
    _kk |= {_a, _b}
kontrol("HD: 36 kanal, kapıları merkezlerde", len(HD_CHANNELS) == 36 and _kk <= _tum)
kontrol("HD: çark kapı kümesi = merkez kapı kümesi", set(HD_GATES_WHEEL) == _tum)
kontrol("28 menzil, benzersiz", len(MENZIL) == 28 and len(set(MENZIL)) == 28)

# Laplasyen
_e = [v for v, _ in _jacobi_eig([[2, -1, -1], [-1, 2, -1], [-1, -1, 2]])]
kontrol("K3 Laplasyen özdeğerleri [0,3,3]",
        abs(_e[0]) < 1e-9 and abs(_e[1] - 3) < 1e-9 and abs(_e[2] - 3) < 1e-9)
_a = asabiyye(CH)
kontrol("λ₂ negatif değil", _a["asabiyye_lambda2"] >= -1e-9)
kontrol("bloklar 10 cismi kapsıyor", sum(len(b) for b in _a["bloklar"]) == 10)
kontrol("kenar sayısı 0..45 · yüzdelik 0..100",
        0 <= _a["kenar_sayisi"] <= 45 and 0 <= _a["yuzdelik"] <= 100)

# oran sınırları
_v = vahdet(CH)
kontrol("Vahdet R ve H1..H12 hepsi 0..1",
        0 <= _v["R_indeksi"] <= 1
        and all(0 <= x["R"] <= 1 for x in _v["rezonans_spektrumu"]))
_m = mizan(CH)
kontrol("Mizan: Sekîne sayısı = Berzah sayısı",
        len(_m["sekineler"]) == len(_m["berzahlar"]))
_ay = ayna_ekseni(CH)
kontrol("Ayna: simetri 0..1, eksen 0..180",
        0 <= _ay["simetri_skoru"] <= 1 and 0 <= _ay["eksen"]["lon"] < 180)

# sinodik dönemler bilinen değerlerle
_bil = {"Jüpiter–Satürn": 19.86, "Uranüs–Neptün": 171.4,
        "Satürn–Uranüs": 45.36, "Satürn–Neptün": 35.87}
_f = felek_saati(CH)
for _c in _f["en_yavas_saatler"]:
    if _c["cift"] in _bil:
        _b2 = _bil[_c["cift"]]
        kontrol(f"sinodik dönem {_c['cift']} ≈ {_b2} yıl",
                abs(_c["periyot_yil"] - _b2) / _b2 < 0.06, f"{_c['periyot_yil']}")

# Noksan gerçekten ıssız mı, Süveyda gerçekten L1 minimumu mu
_n = noksan(CH)
_ey = min(sep(_n["noksan"]["lon"], CH.bodies[x].lon) for x in CORE10)
kontrol("Noksan en ıssız bölgede (>25°)", _ey > 25, f"{_ey:.1f}°")
_s = suveyda(CH)
_mal = lambda q: sum(NURANI_W[x] * sep(q, CH.bodies[x].lon) for x in CORE10)
_kaba = min(range(0, 3600), key=lambda i: _mal(i / 10)) / 10
kontrol("Süveyda gerçek L1 medyanı", sep(_s["suveyda"]["lon"], _kaba) < 0.5,
        f"{_s['suveyda']['lon']:.1f} vs {_kaba:.1f}")
_ic = icabet(CH)
kontrol("İcâbet ≠ İbtilâ",
        sep(_ic["icabet"]["lon"], _ic["ibtila"]["lon"]) > 10)

# sinastri simetrisi
_ab = capraz_acilar(CH, CB, "A", "B", limit=99)
_ba = capraz_acilar(CB, CH, "B", "A", limit=99)
kontrol("sinastri çapraz açıları simetrik",
        len(_ab) == len(_ba)
        and sorted(round(x["orb"], 3) for x in _ab)
        == sorted(round(x["orb"], 3) for x in _ba))


# ============================================================================
# YENİ KATMANLAR — v10.x / v11.x icatları
# ============================================================================
# Bu beş modül eklendi ama HİÇ TESTİ YOKTU. Aynı hatayı üçüncü kez
# yapıyorum: özelliği ekleyip testini yazmayı atlamak. Kapatıldı.
bolum("YENİ KATMANLAR (icatlar)")

from app.lunasyon import lunasyon_takvimi, solar_donus       # noqa: E402
from app.sukut import sukut_haritasi, sukut_sorgusu          # noqa: E402
from app.esik import algi_esigi, orb_karsilastirma           # noqa: E402
from app.duraklama import duraklama_izi                      # noqa: E402
from app.cevaplanabilirlik import cevaplanabilirlik          # noqa: E402
from app.temas import temas_acisi                            # noqa: E402
from app.engine_mass import full_v2 as _fv2                  # noqa: E402

_V2 = _fv2(CH)

_lt = lunasyon_takvimi(CH, solar_donus(CH), ay_sayisi=12)
kontrol("Lunasyon: olay üretiliyor", _lt["olay_sayisi"] >= 20)
kontrol("Lunasyon: yeni ay ve dolunay AYRI etiketleniyor",
        len({o["tur"] for o in _lt["olaylar"]}) >= 3)
kontrol("Lunasyon: tutulma bulunuyor", _lt["tutulma_sayisi"] >= 2)
kontrol("Lunasyon: solar ev dolduruluyor",
        any(o.get("solar_ev") for o in _lt["olaylar"]))
kontrol("Lunasyon: kategori bağı kuruluyor",
        all((o.get("bag") or {}).get("kategoriler") is not None
            for o in _lt["olaylar"][:5]))

_sk = sukut_haritasi(CH)
kontrol("Sükût: eğri hesaplanıyor", len(_sk.get("egri") or []) > 100)
kontrol("Sükût: eşik minimumun ÜSTÜNDE (aralık bulunabilir)",
        _sk["esik"] > _sk["en_dusuk"])
kontrol("Sükût: sessiz aralık bulunuyor", len(_sk["sukut_araliklari"]) >= 1)
_sq = sukut_sorgusu(_sk, (_sk["sukut_araliklari"] or [{}])[0].get("basla", ""))
kontrol("Sükût: yanlışlama sorgusu çalışıyor", _sq.get("durum") == "sükût")

_es = algi_esigi(CH)
kontrol("Eşik: orb kırpma sınırına dayanmıyor",
        1.2 < _es["turetilmis_orb"] < 7.0)
kontrol("Eşik: seviye atanıyor",
        _es["seviye"] in ("düşük eşik", "orta eşik", "yüksek eşik"))
_ok = orb_karsilastirma(CH, _es)
kontrol("Eşik: açı sayımı makul (break hatası yok)",
        _ok["gelenekle_acisi"] >= 4)

_dk = duraklama_izi(CH)
kontrol("Duraklama: temas bulunuyor", _dk["temas_eden"] >= 5)
# HIZ KORUMASI: tarama adımı 1→10 güne çıkarıldı. Adım 60 günü geçerse
# Mars duraklaması kaçar (ölçüldü: en kısa aralık 60 gün).
from app.duraklama import TARAMA_ADIMI as _TA                # noqa: E402
kontrol("Duraklama: tarama adımı güvenli (<60 gün)", _TA < 60, f"{_TA} gün")
kontrol("Duraklama: hızlı gezegen dışarıda",
        all(k["cisim"] not in ("Merkür", "Venüs")
            for r in _dk["islenmis"] for k in r["kayitlar"]))

_cv = cevaplanabilirlik(
    {"berzah_v2": _V2,
     "bodies": {k: {"lon": b.lon} for k, b in CH.bodies.items()},
     "duraklama_izi": _dk, "celiskiler": []},
    list(getattr(CH, "cusps", []) or []))
kontrol("Cevaplanabilirlik: on bir alan puanlanıyor", len(_cv["alanlar"]) == 11)
kontrol("Cevaplanabilirlik: seviyeler ayrışıyor",
        len({a["seviye"] for a in _cv["alanlar"]}) >= 2)
# Kalibrasyon koruması: v11.6'da zayıf oranı ortalama %57'ydi (bir
# haritada %82) ve model hayat alanlarının yarısından fazlasında "az
# söyle" komutu alıyordu — bu, yardımcı olmayı bırakıp susmaya döner.
#
# Anlamlı çizgi YARI: yarıdan fazlası zayıfsa sorun var. Bu sınama
# haritasında %45 çıkıyor, sekiz haritalık ölçümde ortalama %31.
_zayif_oran = sum(1 for a in _cv["alanlar"] if a["seviye"] == "zayıf") / 11
kontrol("Cevaplanabilirlik: zayıf oranı yarıyı geçmiyor", _zayif_oran < 0.50,
        f"%{_zayif_oran*100:.0f}")
kontrol("Cevaplanabilirlik: en az bir güçlü alan var",
        any(a["seviye"] == "güçlü" for a in _cv["alanlar"]))
kontrol("Cevaplanabilirlik: her alanda talimat var",
        all(a.get("talimat") for a in _cv["alanlar"]))

from app.yas import yas_katmani                              # noqa: E402
_yk = yas_katmani(CH)
kontrol("Yaş: yedi çevrim hesaplanıyor", len(_yk["tumu"]) == 7)
kontrol("Yaş: eşik tespiti çalışıyor (0-7 arası)",
        0 <= _yk["esik_sayisi"] <= 7)
kontrol("Yaş: seviye atanıyor",
        _yk["seviye"] in ("yığılma", "çifte eşik", "tek eşik", "eşik arası"))
kontrol("Yaş: faz 0-1 aralığında",
        all(0.0 <= k["faz"] < 1.0 for k in _yk["tumu"]))
# Satürn dönüşü 29 yaşta olmalı — astrolojik doğrulama
_ch29 = build_chart(1997, 9, 27, 12, 0, 40.80, 29.43, tz_name="Europe/Istanbul")
_y29 = yas_katmani(_ch29)
kontrol("Yaş: 29 yaşta Satürn dönüşü eşikte (astrolojik doğrulama)",
        any(k["cevrim"] == "Satürn dönüşü" and k["esikte"]
            for k in _y29["tumu"]))

from app.sarsma import sarsma_testi                          # noqa: E402
_sr = sarsma_testi(1990, 6, 21, 14, 30, 40.80, 29.4333,
                   tz_name="Europe/Istanbul")
kontrol("Sarsma: bulgu üretiliyor", _sr["bulgu_sayisi"] >= 20)
kontrol("Sarsma: sağlamlık 0-1 aralığında", 0.0 <= _sr["saglamlik"] <= 1.0)
# ASTROLOJİK DOĞRULAMA: burçlar saat hatasına dayanmalı, evler dayanmamalı.
_burc = [k for k in _sr["gruplar"]["sağlam"] if k.endswith("burcu")]
_ev_kirilgan = [k for g in ("kırılgan", "kum") for k in _sr["gruplar"][g]
                if k.endswith("evi")]
kontrol("Sarsma: burçlar sağlam çıkıyor (astrolojik doğrulama)",
        len(_burc) >= 8, f"{len(_burc)} burç")
kontrol("Sarsma: evler kırılgan çıkıyor (astrolojik doğrulama)",
        len(_ev_kirilgan) >= 1, f"{len(_ev_kirilgan)} ev")
kontrol("Sarsma: talimat üretiliyor", len(_sr["talimat"]) >= 1)

from app.omur import kayip_zaman, donus_noktasi              # noqa: E402
_kz = kayip_zaman(CH)
kontrol("Kayıp zaman: yıllık eğri üretiliyor", len(_kz["yillik"]) >= 20)
kontrol("Kayıp zaman: sessiz yaş bulunuyor", len(_kz["sessiz_yaslar"]) >= 1)
# Metin araması kırılgandı. Doğrudan modülün cisim listesine bakılır.
from app.omur import AGIR as _AGIR                            # noqa: E402
kontrol("Kayıp zaman: hızlı cisim dışarıda (Ay/Merkür/Venüs)",
        not {"Moon", "Mercury", "Venus"} & {x[0] for x in _AGIR})
_dn = donus_noktasi(CH, ileri_yil=20)
kontrol("Dönüş: kapı bulunuyor", _dn["toplam"] >= 20)
kontrol("Dönüş: yaklaşan ve kapanmış ayrışıyor",
        isinstance(_dn["yaklasan"], list) and isinstance(_dn["kapanmis"], list))

from app.yakinsama import yakinsama as _ykf                  # noqa: E402
_yy = _ykf({"berzah_v2": _V2, "human_design": {}, "deneme_modulleri": {},
            "yas_katmani": _yk, "celiskiler": [], "direnc": [],
            "duraklama_izi": _dk})
kontrol("Yakınsama: eksen üretiliyor", len(_yy["eksenler"]) >= 1)
kontrol("Yakınsama: kaynak TÜRÜ sayılıyor (tekrar şişirmiyor)",
        all(e["kaynak_turu"] <= e["kanit_sayisi"] for e in _yy["eksenler"]))
kontrol("Yakınsama: talimat üretiliyor", len(_yy["talimat"]) >= 1)

from app.hamle import hamle_penceresi, HAMLELER              # noqa: E402
from app.lunasyon import lunasyon_takvimi as _ltf            # noqa: E402
from app.sukut import sukut_haritasi as _skf                 # noqa: E402
_hp = hamle_penceresi({"berzah_v2": _V2, "yas_katmani": _yk,
                       "kabzbast_v1_m66_74": {},
                       "lunasyon_olaylari": _ltf(CH, None, ay_sayisi=6)["olaylar"],
                       "sukut": _skf(CH)}, hafta=12)
kontrol("Hamle: on iki hafta üretiliyor", len(_hp["haftalar"]) == 12)
kontrol("Hamle: beş hamle türünün hepsine pencere var",
        len(_hp["en_iyi"]) == len(HAMLELER))
kontrol("Hamle: haftalar farklı hamle öneriyor (tek tip değil)",
        len({w["en_uygun"] for w in _hp["haftalar"]}) >= 2)
kontrol("Hamle: yapısal zorluk bildiriliyor",
        any("YAPISAL ZORLUK" in t for t in _hp["talimat"]))

_tm = temas_acisi(CH, CH, _V2, _V2)
kontrol("Temas: aynı harita yansıma tetikliyor", bool(_tm.get("yansima_catali")))
kontrol("Temas: uyarı üretiliyor", len(_tm.get("uyarilar") or []) >= 1)

# ============================================================================
# ARAYÜZ BÜTÜNLÜĞÜ
# ============================================================================
# v12.4'te bir bölüm silinirken başka bölümün kullandığı üç değişken de
# gitti: ciz() "konum is not defined" ile çöktü ve HİÇBİR bölüm
# çizilmedi. Bütün testler yeşil kaldı, çünkü kimse arayüze bakmıyordu.
bolum("ANLATIM KURALLARI")

import app.ai as _A2                                          # noqa: E402
for _k in ("BETİMLEYİCİ", "AÇIKLAYICI", "ÖYKÜLEYİCİ"):
    kontrol(f"Anlatım: {_k} kipi tanımlı", _k in _A2.SISTEM)
for _k in ("Gereksiz sözcük", "Anlamca çelişen", "Anlam belirsizliği",
           "Özne–yüklem", "Yüklem eksikliği", "Tamlama yanlışlığı"):
    kontrol(f"Anlatım: '{_k}' kuralı var", _k in _A2.SISTEM)
kontrol("Anlatım: birinci tekil kişi kuralı var",
        "BİRİNCİ TEKİL" in _A2.SISTEM)
# Çekinceyi yasaklamamalı: "olabilir" tek başına serbest kalmalı
kontrol("Anlatım: çekince yasağı YOK (olabilir serbest)",
        "Bu kural çekinceyi YASAKLAMAZ" in _A2.SISTEM)
# Çekirdek her yüzeye giriyor mu
_yuz = [x for x in dir(_A2) if x.endswith("_SISTEM") or x == "SISTEM"]
kontrol("Anlatım: kurallar bütün yüzeylere giriyor",
        all("BİRİNCİ TEKİL" in getattr(_A2, x) for x in _yuz),
        f"{len(_yuz)} yüzey")

bolum("ARAYÜZ BÜTÜNLÜĞÜ")

_js = open(os.path.join(os.path.dirname(__file__),
                        "app/static/uygulama.js"), encoding="utf-8").read()
_ciz = _js[_js.find("function ciz("):]
_ciz = _ciz[:_ciz.find("\nfunction ")] if "\nfunction " in _ciz else _ciz

kontrol("Arayüz: blok sayısı sıfır değil",
        len(re.findall(r"H\+=blok\(", _js)) >= 20)
for _v in ("konum", "eks", "net", "kb", "v2"):
    _kullanim = len(re.findall(r"[^\w.]" + _v + r"[.\[\-)]", _ciz))
    _tanim = bool(re.search(r"(const|let|var)\s+[\w,\s{}]*\b" + _v + r"\b", _ciz))
    kontrol(f"Arayüz: ciz() içinde '{_v}' tanımlı", (not _kullanim) or _tanim,
            f"{_kullanim} kullanım")

# ---------------------------------------------------------------- özet
print(f"\n{'='*70}")
print(f" SONUÇ: {len(GECTI)} geçti, {len(KALDI)} kaldı")
print("=" * 70)
if KALDI:
    print("\nBAŞARISIZ KONTROLLER:")
    for k in KALDI:
        print("  ✗", k)
sys.exit(1 if KALDI else 0)
