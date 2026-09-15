#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MODÜL DENETİMİ — her modülü çok sayıda çeşitli harita üzerinde koşturur ve
  • istisna atan
  • boş / None dönen
  • her haritada aynı sabit değeri veren (ölü modül)
  • istenen listede olup hiç üretilmeyen
modülleri işaretler.
"""
from __future__ import annotations
import json
import random
import sys
import traceback
from collections import defaultdict

sys.path.insert(0, ".")
from app.astro import build_chart
from app.engine_mass import full_v2
from app.engine_kabzbast import run_kabzbast
from app.modules_deneme import run_all_deneme
from app.modules_kadim import isim_tecellisi, kadim_lab, huviyet_muhru
from app.module_hd import human_design

# Kullanıcının istediği modül listesi — hiçbiri eksik kalmamalı
ISTENEN = {
    "m66_67_kabz_bast": "66-67 Kabz/Bast Uzay-Zaman + Eksen",
    "m68_einstein_rosen": "68 Einstein–Rosen Köprüsü",
    "m69_ufuk_bogaz": "69 Olay Ufku / Boğaz",
    "m70_kuramoto": "70 Kuramoto Faz Uyumu",
    "m71_528hz": "71 528 Hz Harmonik İmza",
    "m72_lqc": "72 LQC ρ/ρc Basıncı",
    "m73_anlik_sicrama": "73 Kuantum Sıçrama",
    "m74_gecit": "74 Tayy-i Mekân / Geçit",
    "krn": "Kader Rezonans Noktası + Anti-KRN",
    "vahdet": "Vahdet Noktası + V-K İndeksi + Spektrum H1-H12",
    "mizan": "Mizan Alanı + Sekîne + Berzah",
    "asabiyye": "Asabiyye Matrisi",
    "ars_ekseni": "Arş Ekseni",
    "felek_saati": "Felek Saati",
    "ayna_ekseni": "Ayna Ekseni",
    "devri_daim": "Devr-i Daim",
    "suveyda": "Nokta-i Süveyda",
    "mizac_pusulasi": "Mizâc Pusulası",
    "vuslat_kapilari": "Vuslat Kapıları",
    "ikbal_merdiveni": "İkbal Merdiveni",
    "sahib_kiran": "Sahib-Kırân Penceresi",
    "nokta_i_icabet": "Nokta-i İcâbet",
    "nokta_i_noksan": "Nokta-i Noksan",
    "sevk_i_felek_v2": "Sevk-i Felek v2",
    "kadim_lab": "Kadim Arap–Osmanlı Laboratuvarı",
    "huviyet_muhru": "Hüviyet Mührü",
    "isim_tecellisi": "İsim Tecellîsi",
    "human_design": "Human Design Analizi",
    "berzah_v2": "BERZAH v2 kütle motoru",
}

BOS_SAYAC = defaultdict(int)
HATA = defaultdict(list)
IMZA = defaultdict(set)
GORULEN = defaultdict(int)


def bos_mu(v) -> bool:
    if v is None:
        return True
    if isinstance(v, (list, dict, str)) and len(v) == 0:
        return True
    return False


def derin_bos_alanlar(ad: str, obj, yol="", out=None):
    """Modül içinde boş kalan alt alanları toplar."""
    if out is None:
        out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("yontem", "not", "aciklama", "etik_ilke"):
                continue
            derin_bos_alanlar(ad, v, f"{yol}.{k}" if yol else k, out)
    elif isinstance(obj, list):
        if not obj:
            out.append(yol)
    elif obj is None:
        out.append(yol)
    return out


def denetle(n=40, seed=5):
    rng = random.Random(seed)
    print(f"{n} harita üzerinde denetim başlıyor…\n")
    for i in range(n):
        y = rng.randint(1935, 2020)
        mo = rng.randint(1, 12)
        d = rng.randint(1, 28)
        h = rng.randint(0, 23)
        mi = rng.randint(0, 59)
        # coğrafyayı geniş tut: Türkiye + güney yarımküre + yüksek enlem
        secim = rng.random()
        if secim < 0.6:
            lat, lng = rng.uniform(36, 42), rng.uniform(26, 44)
        elif secim < 0.85:
            lat, lng = rng.uniform(-40, -10), rng.uniform(-70, 150)
        else:
            lat, lng = rng.uniform(58, 70), rng.uniform(-20, 30)
        try:
            ch = build_chart(y, mo, d, h, mi, lat, lng, tz_offset=0.0)
        except Exception as e:
            HATA["build_chart"].append(f"{y}-{mo}-{d} {lat:.1f},{lng:.1f}: {e}")
            continue

        parcalar = {}
        for ad, fn in [
            ("berzah_v2", lambda: full_v2(ch)),
            ("kabzbast", lambda: run_kabzbast(ch, days=200, sr_year=2026)),
            ("deneme", lambda: run_all_deneme(ch, months=12)),
            ("kadim_lab", lambda: kadim_lab(ch)),
            ("human_design", lambda: human_design(ch)),
            ("isim_tecellisi", lambda: isim_tecellisi(ch, "Ahmet Yılmaz", "Ayşe")),
        ]:
            try:
                parcalar[ad] = fn()
            except Exception as e:
                HATA[ad].append(f"{y}-{mo:02d}-{d:02d} {lat:.1f},{lng:.1f}: "
                                f"{type(e).__name__}: {e}")

        try:
            if "deneme" in parcalar and "berzah_v2" in parcalar:
                parcalar["huviyet_muhru"] = huviyet_muhru(
                    ch, parcalar["deneme"], parcalar["berzah_v2"])
        except Exception as e:
            HATA["huviyet_muhru"].append(f"{type(e).__name__}: {e}")

        # düzleştir
        duz = {}
        for k, v in parcalar.items():
            if k == "kabzbast":
                duz.update({kk: vv for kk, vv in v.items() if kk.startswith("m")})
            elif k == "deneme":
                duz.update(v)
            else:
                duz[k] = v

        for anahtar in ISTENEN:
            if anahtar not in duz:
                continue
            GORULEN[anahtar] += 1
            v = duz[anahtar]
            if bos_mu(v):
                BOS_SAYAC[anahtar] += 1
            else:
                bos_alt = derin_bos_alanlar(anahtar, v)
                for b in bos_alt:
                    BOS_SAYAC[f"{anahtar}→{b}"] += 1
            try:
                IMZA[anahtar].add(json.dumps(v, ensure_ascii=False, sort_keys=True)[:400])
            except Exception:
                pass

    # ---- rapor ----
    print("=" * 74)
    print(" A) İSTENEN MODÜL VARLIĞI")
    print("=" * 74)
    eksik = [k for k in ISTENEN if GORULEN.get(k, 0) == 0]
    for k, ad in ISTENEN.items():
        g = GORULEN.get(k, 0)
        print(f"  {'✗ EKSİK' if g == 0 else '✓':8} {ad}")
    print(f"\n  toplam {len(ISTENEN) - len(eksik)}/{len(ISTENEN)} modül üretiliyor")

    print()
    print("=" * 74)
    print(" B) İSTİSNA ATAN MODÜLLER")
    print("=" * 74)
    if not HATA:
        print("  yok")
    for k, v in HATA.items():
        print(f"  ✗ {k}: {len(v)} hata")
        for x in v[:3]:
            print(f"      {x[:110]}")

    print()
    print("=" * 74)
    print(" C) SIK BOŞ KALAN ALANLAR (>%25 haritada)")
    print("=" * 74)
    esik = max(1, int(0.25 * max(GORULEN.values() or [1])))
    bulundu = False
    for k, c in sorted(BOS_SAYAC.items(), key=lambda x: -x[1]):
        kok = k.split("→")[0]
        toplam = GORULEN.get(kok, 1)
        if c >= esik and c > 1:
            bulundu = True
            print(f"  ⚠ {k}: {c}/{toplam} haritada boş")
    if not bulundu:
        print("  yok")

    print()
    print("=" * 74)
    print(" D) ÖLÜ MODÜL (her haritada aynı çıktı)")
    print("=" * 74)
    olu = [k for k, v in IMZA.items() if len(v) == 1 and GORULEN.get(k, 0) > 3]
    print("  " + (", ".join(olu) if olu else "yok"))


if __name__ == "__main__":
    denetle(n=int(sys.argv[1]) if len(sys.argv) > 1 else 40)
