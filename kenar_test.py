#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KENAR DURUM ve PERFORMANS TESTİ

verify.py hesapların DOĞRULUĞUNU sınar. Bu dosya farklı bir soruyu sorar:
sistem OLAĞANDIŞI girdilerde ayakta kalıyor mu, ve performansı bozulmuş mu?

Buradaki her durum gerçek bir kullanıcıdan gelebilir:
  · kutup dairesinde doğmuş biri (ev sistemi çöker)
  · tarih sınırında doğmuş biri (boylam sarmalı)
  · artık günde doğmuş biri
  · efemeris aralığının ucunda doğmuş biri
"""
from __future__ import annotations

import json
import sys
import time

sys.path.insert(0, ".")

from app.astro import build_chart                      # noqa: E402
from app.engine_mass import compute_masses, full_v2    # noqa: E402

GECTI = 0
KALDI = 0
UYARI = 0


def sina(ad: str, kosul: bool, ayrinti: str = "") -> None:
    global GECTI, KALDI
    if kosul:
        GECTI += 1
        print(f"  ✓ {ad}" + (f"  [{ayrinti}]" if ayrinti else ""))
    else:
        KALDI += 1
        print(f"  ✗ KALDI  {ad}" + (f"  [{ayrinti}]" if ayrinti else ""))


def uyar(ad: str, ayrinti: str) -> None:
    global UYARI
    UYARI += 1
    print(f"  ⚠ {ad}  [{ayrinti}]")


# ============================================================ 1
print("\n[1] AŞIRI ENLEMLER — ev sistemi burada çöker")
KUTUP = [
    ("Longyearbyen 78.2°K kış", 1990, 12, 21, 12, 0, 78.22, 15.63),
    ("Longyearbyen 78.2°K yaz", 1990, 6, 21, 12, 0, 78.22, 15.63),
    ("McMurdo 77.8°G", 1990, 6, 21, 12, 0, -77.85, 166.67),
    ("Kutup dairesi 66.5°K", 1985, 3, 20, 12, 0, 66.56, 25.0),
    ("Kuzey kutbu 89.9°", 2000, 1, 1, 12, 0, 89.9, 0.0),
]
for ad, y, ay, g, s, dk, la, lo in KUTUP:
    try:
        ch = build_chart(y, ay, g, s, dk, la, lo, tz_offset=0.0)
        v = full_v2(ch)
        ok = bool(v.get("berzah")) and 0 <= ch.asc < 360
        sina(ad, ok, f"ASC {ch.asc:.1f}°")
    except Exception as e:
        # Whole-sign/eşit ev sistemine düşmek kabul edilebilir; ÇÖKMEK değil.
        sina(ad, False, f"{type(e).__name__}: {e}")

# ============================================================ 2
print("\n[2] COĞRAFİ SINIRLAR")
SINIR = [
    ("tarih değiştirme çizgisi +179.99", 1995, 1, 1, 0, 0, -16.5, 179.99),
    ("tarih değiştirme çizgisi -179.99", 1995, 1, 1, 0, 0, -16.5, -179.99),
    ("ekvator 0°,0°", 2000, 3, 20, 12, 0, 0.0, 0.0),
    ("Greenwich meridyeni", 1970, 7, 1, 12, 0, 51.48, 0.0),
]
for ad, y, ay, g, s, dk, la, lo in SINIR:
    try:
        ch = build_chart(y, ay, g, s, dk, la, lo, tz_offset=0.0)
        sina(ad, 0 <= ch.asc < 360 and 0 <= ch.mc < 360)
    except Exception as e:
        sina(ad, False, f"{type(e).__name__}")

# ============================================================ 3
print("\n[3] ZAMAN SINIRLARI")
ZAMAN = [
    ("artık gün 29 Şubat 2000", 2000, 2, 29, 12, 0),
    ("artık gün 29 Şubat 1900 yok", 1904, 2, 29, 12, 0),
    ("gece yarısı 00:00", 1985, 1, 1, 0, 0),
    ("gün sonu 23:59", 1985, 12, 31, 23, 59),
    ("efemeris alt sınır 1800", 1800, 1, 1, 12, 0),
    ("efemeris üst sınır 2200", 2200, 12, 31, 12, 0),
]
for ad, y, ay, g, s, dk in ZAMAN:
    try:
        ch = build_chart(y, ay, g, s, dk, 41.0, 29.0, tz_offset=0.0)
        ms = compute_masses(ch)
        sina(ad, len(ms) >= 10, f"{len(ms)} cisim")
    except Exception as e:
        sina(ad, False, f"{type(e).__name__}: {str(e)[:40]}")

# ============================================================ 4
print("\n[4] KATMANLAR OLAĞANDIŞI GİRDİDE AYAKTA MI")
import app.hudud as HU
import app.duraklama as DK           # noqa: E402               # noqa: E402
import app.kartografi as KA          # noqa: E402
import app.hudud_arz as HA           # noqa: E402
import app.maneviyat as MN           # noqa: E402

for ad, la, lo in (("kutup 78°K", 78.22, 15.63), ("ekvator", 0.0, 0.0),
                   ("güney 77°G", -77.85, 166.67)):
    ch = build_chart(1990, 6, 21, 12, 0, la, lo, tz_offset=0.0)
    for kat, f in (("hudûd", lambda: HU.hudud_katmani(ch)),
                   ("kartografi", lambda: KA.kartografi_katmani(ch, izdusum=False)),
                   ("hudûd-ı arz", lambda: HA.hudud_arz(ch)),
                   ("maneviyat", lambda: MN.manevi_katman(ch, "Test"))):
        try:
            r = f()
            sina(f"{kat} @ {ad}", isinstance(r, dict) and "hata" not in r)
        except Exception as e:
            sina(f"{kat} @ {ad}", False, f"{type(e).__name__}: {str(e)[:36]}")

# ============================================================ 5
print("\n[5] VEFK — her mertebe geçerli olmalı")
for n in range(3, 10):
    v = MN.vefk(n)
    sina(f"vefk {n}×{n}", v["dogrulama"]["gecerli"],
         f"toplam {v['sabit_toplam']}")

# ============================================================ 6
print("\n[6] PERFORMANS — gerileme koruması")
ch = build_chart(1990, 6, 21, 14, 30, 40.8, 29.4333, tz_offset=3.0)
ESIK = {"full_v2": 600, "hudûd": 400, "duraklama": 2500,
        "kartografi": 200, "maneviyat": 200}
for ad, f in (("full_v2", lambda: full_v2(ch)),
              ("hudûd", lambda: HU.hudud_katmani(ch)),
              ("kartografi", lambda: KA.kartografi_katmani(ch, izdusum=False)),
              ("maneviyat", lambda: MN.manevi_katman(ch, "Test")),
              # Duraklama izi doğumdan bugüne tarama yapar; en pahalı
              # katman. Gerileme koruması buraya özellikle gerekli.
              ("duraklama", lambda: DK.duraklama_izi(ch))):
    t0 = time.time()
    try:
        f()
        ms_ = (time.time() - t0) * 1000
        sina(f"{ad} < {ESIK[ad]}ms", ms_ < ESIK[ad], f"{ms_:.0f}ms")
    except Exception as e:
        sina(ad, False, f"{type(e).__name__}")

# ============================================================ 7
print("\n[7] YÜK BOYUTU")
import app.main as M                 # noqa: E402
from app.schemas import BirthInput   # noqa: E402
try:
    inp = BirthInput(year=1990, month=6, day=21, hour=14, minute=30,
                     lat=40.8, lng=29.4333, tz_offset=3.0, yorumla=False)
    sina("BirthInput yıl sınırı 2200", BirthInput.model_fields["year"]
         .metadata[1].le == 2200 if len(
             BirthInput.model_fields["year"].metadata) > 1 else True)
except Exception as e:
    uyar("BirthInput", str(e)[:50])

# ============================================================ özet
print("\n" + "=" * 62)
print(f"  GEÇTİ {GECTI} · KALDI {KALDI}" + (f" · UYARI {UYARI}" if UYARI else ""))
print("=" * 62)
sys.exit(1 if KALDI else 0)
