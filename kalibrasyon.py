#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ZÎC kalibrasyon koşucusu — MİZAN-5 + ŞAHİT-7.

Kalibrasyon iki farklı işi ayırır:

* ``--kaynak sentetik`` regresyon ve geliştirme için tekrarlanabilir örneklem
  üretir. Bu tablo üretimde yedektir; gerçek danışan dağılımı olduğu iddia edilmez.
* ``--kaynak gercek --girdi <dizin>`` daha önce /api/v1/full ile üretilmiş JSON
  çıktılarını okur. Yeterli gerçek örnek varsa referans bunun üzerinden kurulabilir.

``--dogrula`` referansı değiştirmez; verilen örneklemde referans kaymasının ne
kadar olduğunu ölçer. Böylece quantile tablosunun ne zaman yenilenmesi gerektiği
hissiyatla değil dağılım kaymasıyla görülebilir.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from app.kapsam import GOREVLER, kapsam_ozeti
from app import oruntu_omurgasi as mizan_mod
from app import tanik as tanik_mod
from app.oruntu_omurgasi import oruntu_omurgasi, referans_sifirla as mizan_referans_sifirla
from app.tanik import MERCEKLER, ham_mercekler, referans_sifirla as sahit_referans_sifirla, sahit_agi
from app import ayar as ayar_mod
from app import depo as depo_mod
from app import iddia as iddia_mod
from app import hasv as hasv_mod

KOK = Path(__file__).parent
MIZAN_REF = KOK / "app" / "mizan_quantiles.json"
MIZAN_REF_GERCEK = KOK / "app" / "mizan_quantiles_gercek.json"
SAHIT_REF = KOK / "app" / "sahit_quantiles.json"
SAHIT_REF_GERCEK = KOK / "app" / "sahit_quantiles_gercek.json"


def _obj(adet: int) -> list:
    return [{} for _ in range(max(0, adet))]


def _cizgiler(r: random.Random) -> list:
    # Çizgi adedi değil aynı meridyen çevresindeki yoğunlaşma sinyaldir.
    merkezler = [r.uniform(-180, 180) for _ in range(r.randint(1, 6))]
    out = []
    for i in range(10):
        c = r.choice(merkezler)
        mc = ((c + r.gauss(0, 10) + 180) % 360) - 180
        ic = ((mc + 180 + 180) % 360) - 180
        asc = [{"enlem": e, "boylam": ((c + r.gauss(0, 13) + e * .08 + 180) % 360) - 180}
               for e in range(-60, 61, 12)]
        dsc = [{"enlem": x["enlem"], "boylam": ((x["boylam"] + 180 + 180) % 360) - 180} for x in asc]
        out.append({"kod": f"p{i}", "MC": mc, "IC": ic, "ASC": asc, "DSC": dsc})
    return out


def _cevaplanabilirlik(r: random.Random) -> Dict[str, Any]:
    alan_kodlari = ["kimlik", "kaynak", "yakin", "kok", "yaratim", "duzen",
                    "iliski", "anlam", "gorunurluk", "cevre", "iceri"]
    alanlar = []
    for kod in alan_kodlari:
        # Gerçek motorun 0..10 puanına benzer ama tek noktaya yığılmayan dağılım.
        puan = min(10.0, max(0.0, r.betavariate(2.2, 2.4) * 10.0))
        ger = 0
        if r.random() < .18:
            ger = 1
        if r.random() < .035:
            ger += 1
        alanlar.append({"kod": kod, "puan": round(puan, 3), "gerilim": ger})
    return {"alanlar": alanlar}


def sentetik(r: random.Random, iliski_modu: bool | None = None) -> Dict[str, Any]:
    sag = min(1.0, max(0.15, r.betavariate(5, 2)))
    sr = r.random() < .62
    kart_var = r.random() < .88
    if iliski_modu is None:
        iliski_modu = r.random() < .42
    v: Dict[str, Any] = {
        "berzah_v2": {
            "mercekleme": _obj(r.randint(0, 4)),
            "yapisal_ikizler": _obj(r.randint(0, 5)),
            "asal_acilar": _obj(r.randint(0, 7)),
            "kurtarici": _obj(r.randint(0, 3)),
            "alan_topolojisi": {"ok": True} if r.random() < .72 else {},
            "AD": {"ev": r.randint(1, 12)}, "KD": {"ev": r.randint(1, 12)},
            "berzah": {"ev": r.randint(1, 12)},
        },
        "hukum": {"mode": "natal+solar" if sr else "natal",
                  "cross": {"adet": r.randint(0, 6) if sr else 0}},
        "yas_katmani": {"esik_sayisi": r.randint(0, 4), "yigilma": round(r.random()*3.2, 2)} if r.random() < .9 else {},
        "sarsma": {"saglamlik": sag,
                   "gruplar": {"kum": _obj(r.randint(0, 5)), "kırılgan": _obj(r.randint(0, 6))}},
        "duraklama_izi": {"el_degmemis": _obj(r.randint(0, 7)),
                           "ilk_kez_yaklasan": _obj(r.randint(0, 4))} if r.random() < .9 else {},
        "hamle_penceresi": {"en_iyi": {"a": {"puan": round(r.random()*5, 2), "ad": "hamle"}}} if r.random() < .82 else {},
        "yakinsama": {"cekirdek": _obj(r.randint(0, 4))} if r.random() < .86 else {},
        "celiskiler": _obj(r.randint(0, 5)),
        "direnc": _obj(r.randint(0, 5)),
        "kabzbast_v1_m66_74": {"ok": True} if r.random() < .8 else {},
        "deneme_modulleri": {"ok": True} if r.random() < .75 else {},
        "kadim_katman": {"ok": True} if r.random() < .78 else {},
        "human_design": {"ok": True} if r.random() < .82 else {},
        "hudud_felek": {"ok": True} if r.random() < .76 else {},
        "temas_acisi": {"ok": True} if r.random() < .74 else {},
        "kayip_zaman": {"ok": True} if r.random() < .55 else {},
        "sira_cevrimi": {"ok": True} if r.random() < .7 else {},
        "cevaplanabilirlik": _cevaplanabilirlik(r),
    }
    if sr:
        v["solar_v2"] = {"berzah_v2": {"AD": {}, "KD": {}, "berzah": {}}}
    if iliski_modu:
        for k, p in (("sinastri", .84), ("davison", .72), ("deklinasyon", .68), ("kompozit", .8)):
            if r.random() < p:
                v[k] = {"ok": True}
    if kart_var:
        v["kartografi"] = {
            "natal": {"cizgiler": _cizgiler(r)},
            "gunes_donusu": {"cizgiler": _cizgiler(r)} if sr else {},
            "natal_paran": _obj(r.randint(0, 8)),
            "hudud_arz": {"sessiz_kusaklar": _obj(r.randint(0, 5))},
        }
    return v


def kaydirilmis(r: random.Random) -> Dict[str, Any]:
    """Gerçek-popülasyon kayması için stres örneği; referans üretiminde kullanılmaz."""
    v = sentetik(r)
    v["sarsma"] = {"saglamlik": min(1.0, max(.2, r.betavariate(8, 2))),
                   "gruplar": {"kum": _obj(r.randint(0, 2)), "kırılgan": _obj(r.randint(0, 3))}}
    v["solar_v2"] = {"berzah_v2": {"AD": {}, "KD": {}, "berzah": {}}}
    v["hukum"] = {"mode": "natal+solar", "cross": {"adet": r.randint(2, 6)}}
    b = v.get("berzah_v2") or {}
    b["mercekleme"] = _obj(r.randint(0, 2))
    b["kurtarici"] = _obj(r.randint(0, 1))
    v["celiskiler"] = _obj(r.randint(0, 2))
    v["direnc"] = _obj(r.randint(0, 2))
    for a in (v.get("cevaplanabilirlik") or {}).get("alanlar", []):
        a["puan"] = min(10.0, round(float(a.get("puan", 0)) * 1.25, 3))
    if not v.get("kartografi"):
        v["kartografi"] = {"natal": {"cizgiler": _cizgiler(r)}, "gunes_donusu": {"cizgiler": _cizgiler(r)},
                           "natal_paran": _obj(r.randint(0, 8)), "hudud_arz": {"sessiz_kusaklar": _obj(r.randint(0, 5))}}
    return v


def _jsonlar(dizin: Path) -> List[Dict[str, Any]]:
    if not dizin.exists() or not dizin.is_dir():
        raise SystemExit(f"Gerçek veri dizini bulunamadı: {dizin}")
    out: List[Dict[str, Any]] = []
    for p in sorted(dizin.rglob("*.json")):
        try:
            v = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(v, dict):
            continue
        # /api/v1/full çıktısının çekirdeği yoksa bu bir kalibrasyon haritası
        # değildir. Sırf JSON olduğu için referansa karışmasına izin verilmez.
        if isinstance(v.get("berzah_v2"), dict):
            out.append(v)
    if not out:
        raise SystemExit("Dizinde /api/v1/full biçiminde kullanılabilir JSON bulunamadı.")
    return out


def quantile(xs: List[float], q: float) -> float:
    s = sorted(xs)
    if not s:
        return 0.0
    if len(s) == 1:
        return float(s[0])
    p = q * (len(s) - 1)
    a, b = int(math.floor(p)), int(math.ceil(p))
    if a == b:
        return float(s[a])
    return float(s[a] + (s[b] - s[a]) * (p - a))


def _qtablo(v: List[float]) -> List[Dict[str, float]]:
    # v13.3'te %2 aralıklı tablo özellikle ayrık Zaman ham puanlarında geniş
    # plato oluşturup aynı değeri 53–54 yüzdelik civarına itebiliyordu. %1 ağ
    # referans dosyasını hâlâ küçük tutar ama mid-rank merkezini daha doğru taşır.
    return [{"q": q, "v": round(quantile(v, q), 6)} for q in (i / 100 for i in range(0, 101))]


def _yuzdelik_ref(ham: float, noktalar: List[Dict[str, float]]) -> float:
    pts = sorted((float(x["q"]), float(x["v"])) for x in noktalar if "q" in x and "v" in x)
    if not pts:
        return max(0.0, min(100.0, ham))
    es = [q for q, v in pts if abs(v - ham) < 1e-9]
    if es:
        return sum(es) / len(es) * 100
    if ham < pts[0][1]:
        return pts[0][0] * 100
    if ham > pts[-1][1]:
        return pts[-1][0] * 100
    for (q0, v0), (q1, v1) in zip(pts, pts[1:]):
        if v0 <= ham <= v1:
            q = (q0 + q1) / 2 if abs(v1 - v0) < 1e-12 else q0 + (ham-v0)/(v1-v0)*(q1-q0)
            return q * 100
    return 50.0


def _ayar_taban(raw: List[float], qt: List[Dict[str, float]]) -> Tuple[Dict[str, Any], List[float]]:
    ys = [round(_yuzdelik_ref(x, qt), 2) for x in raw]
    n = max(1, len(ys))
    return ({"n": len(ys), "ortalama": round(statistics.mean(ys), 4),
             "le20": round(sum(1 for x in ys if x <= 20) / n * 100, 4),
             "ge80": round(sum(1 for x in ys if x >= 80) / n * 100, 4)}, ys)


def mizan_referans_tablosu(hamlar: Dict[str, List[float]], n: int, tohum: int | None,
                           kaynak: str) -> Dict[str, Any]:
    eksenler: Dict[str, Any] = {}
    for k, v in hamlar.items():
        qt = _qtablo(v)
        tab, ornek = _ayar_taban(v, qt)
        eksenler[k] = {"quantiles": qt, "min": min(v), "max": max(v),
                       "ortalama": statistics.mean(v), "ayar_taban": tab, "ayar_ornek": ornek}
    return {
        "surum": 4, "n": n, "ornek_sayisi": n, "tohum": tohum, "kaynak": kaynak,
        "uretim_tarihi": datetime.now(timezone.utc).isoformat(), "eksenler": eksenler,
    }


def sahit_referans_tablosu(hamlar: Dict[str, Dict[str, List[float]]], n: int,
                           tohum: int | None, kaynak: str) -> Dict[str, Any]:
    mercekler: Dict[str, Any] = {}
    for k, v in hamlar.items():
        qt = _qtablo(v["belirginlik"])
        tab, ornek = _ayar_taban(v["belirginlik"], qt)
        mercekler[k] = {
            "quantiles": qt, "gerilim_q75": round(quantile(v["gerilim"], .75), 6),
            "ortalama_ham": round(statistics.mean(v["belirginlik"]), 6),
            "gerilim_ortalama": round(statistics.mean(v["gerilim"]), 6),
            "ayar_taban": tab, "ayar_ornek": ornek,
        }
    return {
        "surum": 3, "n": n, "ornek_sayisi": n, "tohum": tohum, "kaynak": kaynak,
        "uretim_tarihi": datetime.now(timezone.utc).isoformat(), "mercekler": mercekler,
    }


def _kapsam_ornek() -> str:
    basliklar = [
        "GÜVEN NOTU — bu uyarılara harfiyen uy", "SARSMA TESTİ — neyin arkasında durabilirsin",
        "NEREDE KONUŞ, NEREDE SUS — bunu her bölümde uygula", "TEMAS AÇISI — okuma bu kanaldan geçiyor",
        "HAMLE PENCERESİ — hangi hafta hangi hamleye uygun", "ÇEKİRDEK YAKINSAMA — okumanın omurgası",
        "KATMANLAR ARASI BAĞ — önce bunu oku", "DİRENÇ — nasıl söylersen dinlenir",
        "ÇELİŞKİLER — saklanmaz, kullanılır", "ALAN TOPOLOJİSİ", "YÜRÜYEN BERZAH", "DENEME MODÜLLERİ",
        "KABZ/BAST", "KADİM KATMAN", "DURAKLAMA İZİ", "HUDÛD-I FELEK", "BUGÜNKÜ GÖK",
        "KAYIP ZAMAN", "YAŞ KATMANI", "YILIN HARİTASI — solar dönüş", "KAPILAR", "YER",
        "ŞİRÂ ÇEVRİMİ", "HUMAN DESIGN", "SİNASTRİ", "DAVISON", "DEKLİNASYON SİNASTRİSİ", "KOMPOZİT",
        "ÇEKİRDEK", "SÜKÛT", "ALGI EŞİĞİ", "DÖNÜŞ NOKTASI",
    ]
    return "ANALİZ MODU: Kişisel\nDoğum anı: örnek\n" + "\n".join(f"\n[{b}]\nörnek veri {i}" for i, b in enumerate(basliklar))


def _mizan_ham(veriler: List[Dict[str, Any]]) -> Dict[str, List[float]]:
    hamlar = {k: [] for k in ("cekirdek", "zaman", "gerilim", "hareket", "mekan")}
    for v in veriler:
        o = oruntu_omurgasi(v, kalibre=False)
        for e in o["eksenler"]:
            hamlar[e["kod"]].append(float(e["ham_puan"]))
    return hamlar


def _sahit_ham(veriler: List[Dict[str, Any]]) -> Dict[str, Dict[str, List[float]]]:
    out = {k: {"belirginlik": [], "gerilim": []} for k in MERCEKLER}
    for v in veriler:
        # ŞAHİT MİZAN yüzdeliğini kullanır. Referans yenilendikten sonra her
        # örneğe güncel omurga yerleştirilir; aksi hâlde eski dağılım yeni
        # ŞAHİT referansına sızardı.
        v["oruntu_omurgasi"] = oruntu_omurgasi(v, kalibre=True)
        for k, h in ham_mercekler(v).items():
            out[k]["belirginlik"].append(float(h["ham_belirginlik"]))
            out[k]["gerilim"].append(float(h["ham_gerilim"]))
    return out


def _mizan_olcum(veriler: List[Dict[str, Any]]) -> Dict[str, Any]:
    puanlar = {k: [] for k in ("cekirdek", "zaman", "gerilim", "hareket", "mekan")}
    baskin = {k: 0 for k in puanlar}
    for v in veriler:
        o = oruntu_omurgasi(v, kalibre=True)
        v["oruntu_omurgasi"] = o
        for e in o["eksenler"]:
            puanlar[e["kod"]].append(float(e["puan"]))
        baskin[o["baskin"]] += 1
    n = max(1, len(veriler))
    return {
        k: {
            "min": min(v), "max": max(v), "ortalama": round(statistics.mean(v), 2),
            "medyan": round(statistics.median(v), 2),
            "le20": round(sum(1 for x in v if x <= 20) / n * 100, 2),
            "ge80": round(sum(1 for x in v if x >= 80) / n * 100, 2),
            "yuzde_100": round(sum(1 for x in v if x >= 100) / n * 100, 2),
            "baskin_yuzde": round(baskin[k] / n * 100, 2),
        } for k, v in puanlar.items()
    }


def _sahit_olcum(veriler: List[Dict[str, Any]]) -> Dict[str, Any]:
    puanlar = {k: [] for k in MERCEKLER}
    durumlar = {k: {"güçlü": 0, "orta": 0, "sessiz": 0, "celiskili": 0} for k in MERCEKLER}
    iliski_mod = {"kisisel": [], "iliski": []}
    for v in veriler:
        v["oruntu_omurgasi"] = oruntu_omurgasi(v, kalibre=True)
        ag = sahit_agi(v)
        for m in ag["mercekler"]:
            k = m["kod"]
            p = float(m["belirginlik"])
            puanlar[k].append(p)
            durumlar[k][m["durum"]] += 1
            if m.get("celiskili"):
                durumlar[k]["celiskili"] += 1
            if k == "iliski":
                mod = "iliski" if any(v.get(x) for x in ("sinastri", "davison", "deklinasyon", "kompozit")) else "kisisel"
                iliski_mod[mod].append(p)
    n = max(1, len(veriler))
    mercekler = {}
    for k, v in puanlar.items():
        mercekler[k] = {
            "ortalama": round(statistics.mean(v), 2),
            "medyan": round(statistics.median(v), 2),
            "le20": round(sum(1 for x in v if x <= 20) / n * 100, 2),
            "ge80": round(sum(1 for x in v if x >= 80) / n * 100, 2),
            "durum": {
                "güçlü": round(durumlar[k]["güçlü"] / n * 100, 2),
                "orta": round(durumlar[k]["orta"] / n * 100, 2),
                "sessiz": round(durumlar[k]["sessiz"] / n * 100, 2),
            },
            "celiskili": round(durumlar[k]["celiskili"] / n * 100, 2),
        }
    return {
        "mercekler": mercekler,
        "iliski_mod_karsilastirma": {
            k: {"n": len(v), "ortalama": round(statistics.mean(v), 2) if v else None}
            for k, v in iliski_mod.items()
        },
    }


def _sessiz_katman(veriler: List[Dict[str, Any]]) -> Dict[str, Any]:
    say = 0
    for v in veriler:
        say += sum(1 for k in ("yas_katmani", "hamle_penceresi", "yakinsama", "kartografi", "hudud_felek") if not v.get(k))
    return {"adet": say, "ornek_basina": round(say / max(1, len(veriler)), 3)}


def _kapsam_olcum() -> Dict[str, Any]:
    baglam = _kapsam_ornek()
    oranlar = []
    daralmalar = []
    for kod in GOREVLER:
        x = kapsam_ozeti(baglam, kod)
        tam, dar = int(x["tam_bayt"]), int(x["dar_bayt"])
        # v13.1 raporunda ``ortalama_daralma`` diye yayımlanan değer geriye
        # dönük rapor sözleşmesinde korunan oran olarak yorumlanmıştı. v13.2
        # alan adlarını bu sözleşmeye göre açıkça ayırır; eski sayının anlamını
        # sessizce tersine çevirmeyiz.
        daralma = float(x.get("daralma", 0.0))
        oranlar.append(1.0 - daralma)
        daralmalar.append(daralma)
    return {
        "korunan_oran": round(statistics.mean(oranlar), 3),
        "daralma_orani": round(statistics.mean(daralmalar), 3),
        "min_daralma": round(min(daralmalar), 3),
        "max_daralma": round(max(daralmalar), 3),
    }


def _iddia_kapsam_olcum() -> Dict[str, Any]:
    yol = KOK / "app" / "ornek_metinler.json"
    try:
        satirlar = json.loads(yol.read_text(encoding="utf-8"))
    except Exception:
        return {"olculdu": False, "neden": "app/ornek_metinler.json okunamadı"}
    metinler = [str(x.get("metin") or "") for x in satirlar if isinstance(x, dict) and x.get("metin")]
    davranis = alan = 0
    gorevler = set()
    for x in satirlar:
        if isinstance(x, dict):
            gorevler.add(str(x.get("gorev") or ""))
    for m in metinler:
        uc = iddia_mod.iddialar(m)
        if any(x[0] != "genel" for x in uc): davranis += 1
        if any(x[1] != "genel" for x in uc): alan += 1
    n = max(1, len(metinler))
    return {"olculdu": True, "n": len(metinler), "gorev_sayisi": len(gorevler),
            "davranis_kapsama": round(davranis/n*100, 2), "alan_kapsama": round(alan/n*100, 2)}


def _rabt_olcum() -> Dict[str, Any]:
    """Sabit danışman dili kümesinde RABT kararlarının dağılımını ölçer."""
    yol = KOK / "app" / "ornek_metinler.json"
    try:
        satirlar = [x for x in json.loads(yol.read_text(encoding="utf-8"))
                    if isinstance(x, dict) and x.get("metin")]
    except Exception:
        return {"olculdu": False, "neden": "örnek metin kümesi yok"}
    say = {"tekrar": 0, "bağla": 0, "farklı": 0}
    n = 0
    for i, a in enumerate(satirlar):
        for b in satirlar[i+1:]:
            if a.get("gorev") == b.get("gorev"):
                continue
            r = iddia_mod.karsilastir(str(a["metin"]), str(b["metin"]))
            say[r.get("karar", "farklı")] = say.get(r.get("karar", "farklı"), 0) + 1
            n += 1
    return {"olculdu": True, "n": n,
            **{k: {"adet": v, "yuzde": round(v / max(1, n) * 100, 2)} for k, v in say.items()}}


def _hasv_ornek_olcum(veriler: List[Dict[str, Any]]) -> Dict[str, Any]:
    yol = KOK / "app" / "ornek_metinler.json"
    try:
        satirlar = json.loads(yol.read_text(encoding="utf-8"))
    except Exception:
        return {"olculdu": False, "neden": "örnek metin kümesi yok"}
    oranlar = []
    for i, x in enumerate(satirlar):
        if not veriler: break
        metin = str(x.get("metin") or "") if isinstance(x, dict) else ""
        if metin:
            oranlar.append(float(hasv_mod.olc(metin, veriler[i % len(veriler)]).get("hasv_orani", 0.0)))
    return {"olculdu": bool(oranlar), "n": len(oranlar),
            "ortalama_hasv_orani": round(statistics.mean(oranlar), 4) if oranlar else None,
            "not": "Sabit danışman metin kümesi üzerinde karşılaştırmalı HAŞV benchmarkı; canlı model kalitesi değildir."}


def _kaynak_veri(kaynak: str, n: int, tohum: int, girdi: Path | None) -> List[Dict[str, Any]]:
    if kaynak == "gercek":
        if girdi is None:
            raise SystemExit("--kaynak gercek için --girdi <dizin> zorunludur.")
        if n and n < 60:
            raise SystemExit(f"Gerçek kalibrasyon örneklemi en az 60 olmalı; --n={n}")
        veriler = _jsonlar(girdi)
        if n and len(veriler) > n:
            veriler = veriler[:n]
        if len(veriler) < 60:
            raise SystemExit(f"Gerçek kalibrasyon reddedildi: en az 60 /api/v1/full çıktısı gerekir; bulunan={len(veriler)}")
        if len(veriler) < 200:
            print(f"UYARI: gerçek referans için 200+ harita önerilir; bulunan={len(veriler)}")
        return veriler
    r = random.Random(tohum)
    return [sentetik(r) for _ in range(n)]


def _aktif_ref_yolu(kaynak: str, sahit: bool = False) -> Path:
    if kaynak == "gercek":
        return depo_mod.referans_yolu("sahit" if sahit else "mizan")
    return SAHIT_REF if sahit else MIZAN_REF


def kos(n: int, tohum: int, cikti: Path, ai: bool = False, kaynak: str = "sentetik",
        girdi: Path | None = None, sahit_referans: bool = False,
        referans_yaz: bool = True) -> Dict[str, Any]:
    veriler = _kaynak_veri(kaynak, n, tohum, girdi)
    if referans_yaz:
        mref = mizan_referans_tablosu(_mizan_ham(veriler), len(veriler),
                                      tohum if kaynak == "sentetik" else None, kaynak)
        _aktif_ref_yolu(kaynak).write_text(json.dumps(mref, ensure_ascii=False, indent=2), encoding="utf-8")
        mizan_referans_sifirla()
        if kaynak == "gercek":
            ayar_mod.sifirla()
    else:
        try:
            kalici = depo_mod.referans_yolu("mizan")
            yol = kalici if kalici.exists() else (MIZAN_REF_GERCEK if MIZAN_REF_GERCEK.exists() else MIZAN_REF)
            mref = json.loads(yol.read_text(encoding="utf-8"))
        except Exception:
            mref = {}
    if sahit_referans:
        sref = sahit_referans_tablosu(_sahit_ham(veriler), len(veriler),
                                      tohum if kaynak == "sentetik" else None, kaynak)
        _aktif_ref_yolu(kaynak, sahit=True).write_text(json.dumps(sref, ensure_ascii=False, indent=2), encoding="utf-8")
        sahit_referans_sifirla()
        if kaynak == "gercek":
            ayar_mod.sifirla()
    else:
        try:
            kalici = depo_mod.referans_yolu("sahit")
            yol = kalici if kalici.exists() else (SAHIT_REF_GERCEK if SAHIT_REF_GERCEK.exists() else SAHIT_REF)
            sref = json.loads(yol.read_text(encoding="utf-8"))
        except Exception:
            sref = None

    mizan = _mizan_olcum(veriler)
    sahit = _sahit_olcum(veriler)
    tekrar = {"olculdu": False, "ortalama": None, "azami": None,
              "neden": "--ai verilmedi; yapay bölüm metni gerçek modeli temsil etmez."}
    sizinti = {"olculdu": False, "adet": None,
               "neden": "--ai verilmedi; teknik sızıntı yalnız üretilmiş danışan metninde ölçülür."}
    if ai:
        tekrar["neden"] = "--ai istendi; ücretli model çağrıları bu koşucuda otomatik başlatılmaz. /api/v2/bolum kayıtlarını ölçün."
        sizinti["neden"] = tekrar["neden"]

    rapor = {
        "surum": "13.5", "n": len(veriler), "tohum": tohum if kaynak == "sentetik" else None,
        "kaynak": kaynak, "referans": mref, "sahit_referans": sref,
        "mizan": mizan, "sahit_7": sahit, "kapsam": _kapsam_olcum(),
        "sessiz_katman": _sessiz_katman(veriler), "tekrar": tekrar, "teknik_sizinti": sizinti,
        "iddia_kapsami": _iddia_kapsam_olcum(), "rabt": _rabt_olcum(),
        "hasv": _hasv_ornek_olcum(veriler) if ai else {"olculdu": False, "neden": "--ai verilmedi"},
    }
    cikti.write_text(json.dumps(rapor, ensure_ascii=False, indent=2), encoding="utf-8")
    return rapor


def dogrula(referans: Path, veriler: List[Dict[str, Any]], cikti: Path | None = None) -> Dict[str, Any]:
    ref = json.loads(referans.read_text(encoding="utf-8"))
    mref = ref.get("referans") if isinstance(ref.get("referans"), dict) else ref
    sref = ref.get("sahit_referans") if isinstance(ref.get("sahit_referans"), dict) else None
    eski_m = mizan_mod._REFERANS
    eski_s = tanik_mod._REFERANS
    try:
        # Doğrulama cevap anahtarını depoya yazmaz. Modül önbelleğine verilen
        # referans yalnız bu süreçte yaşar; koşu bittiğinde üretim dosyaları
        # byte düzeyinde bile değişmemiş kalır.
        mizan_mod._REFERANS = mref
        if sref is not None:
            tanik_mod._REFERANS = sref
        else:
            tanik_mod._REFERANS = None
        rapor = {
            "mizan": _mizan_olcum(veriler), "sahit_7": _sahit_olcum(veriler),
            "orneklem_n": len(veriler), "referans_kaynagi": mref.get("kaynak", "bilinmiyor"),
        }
    finally:
        mizan_mod._REFERANS = eski_m
        tanik_mod._REFERANS = eski_s
    if cikti:
        cikti.write_text(json.dumps(rapor, ensure_ascii=False, indent=2), encoding="utf-8")
    return rapor

def ayar_raporu(veriler: List[Dict[str, Any]]) -> Dict[str, Any]:
    kayitlar = []
    for v in veriler:
        v["oruntu_omurgasi"] = oruntu_omurgasi(v, kalibre=True)
        v["sahit_7"] = sahit_agi(v)
        kayitlar.append(ayar_mod.analizden_kayit(v))
    return ayar_mod.rapor(kayitlar)


def _tablo(r: Dict[str, Any]) -> None:
    print("\nMİZAN-5")
    print("eksen       ort   <=20  >=80  baskın")
    for k, v in r["mizan"].items():
        print(f"{k:<11} {v['ortalama']:>5.1f} {v['le20']:>5.1f} {v['ge80']:>5.1f} {v['baskin_yuzde']:>6.1f}")
    print("\nŞAHİT-7")
    print("mercek      ort   med  sessiz güçlü çelişki")
    for k, v in r["sahit_7"]["mercekler"].items():
        print(f"{k:<11} {v['ortalama']:>5.1f} {v['medyan']:>5.1f} {v['durum']['sessiz']:>6.1f} {v['durum']['güçlü']:>5.1f} {v['celiskili']:>7.1f}")
    print("ilişki mod", r["sahit_7"]["iliski_mod_karsilastirma"])
    print("kapsam", r.get("kapsam"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=400)
    ap.add_argument("--cikti", default="kalibrasyon_v134.json")
    ap.add_argument("--tohum", type=int, default=132)
    ap.add_argument("--ai", action="store_true")
    ap.add_argument("--kaynak", choices=("sentetik", "gercek"), default="sentetik")
    ap.add_argument("--girdi", type=Path)
    ap.add_argument("--referans-yaz", action="store_true",
                    help="MİZAN referansını bu örneklemden açıkça yeniden üret")
    ap.add_argument("--sahit-referans", action="store_true",
                    help="ŞAHİT-7 quantile + gerilim q75 referansını üret")
    ap.add_argument("--dogrula", type=Path,
                    help="Referansı verilen örneklemde sınar; referans dosyalarını kalıcı değiştirmez")
    ap.add_argument("--ayar-raporu", action="store_true",
                    help="Örneklem yüzdeliklerinin uniform referanstan sapmasını AYÂR ile ölç")
    ap.add_argument("--kaydirilmis", action="store_true",
                    help="Referans kayması stres örneklemini kullan; referans üretmez")
    a = ap.parse_args()
    n = max(20, a.n)
    if a.kaydirilmis:
        if a.kaynak != "sentetik":
            raise SystemExit("--kaydirilmis yalnız sentetik stres doğrulamasında kullanılır.")
        rr = random.Random(a.tohum)
        veriler = [kaydirilmis(rr) for _ in range(n)]
    else:
        veriler = _kaynak_veri(a.kaynak, n, a.tohum, a.girdi)
    if a.ayar_raporu:
        ar = ayar_raporu(veriler)
        print(json.dumps(ar, ensure_ascii=False, indent=2))
        if not a.dogrula and not a.referans_yaz and not a.sahit_referans:
            return
    if a.dogrula:
        r = dogrula(a.dogrula, veriler, Path(a.cikti))
        _tablo({"mizan": r["mizan"], "sahit_7": r["sahit_7"], "kapsam": None})
        return
    # Tohum 909 gibi doğrulama koşuları referansı kendileri üretmemelidir; aksi
    # hâlde test ile cevap anahtarı aynı örneklem olur. Referans yazmak artık
    # açık bir eylemdir. Gerçek veri modu da kullanıcı ayrıca yazmayı istemedikçe
    # yalnız dağılımı ölçer.
    r = kos(n, a.tohum, Path(a.cikti), a.ai, a.kaynak, a.girdi, a.sahit_referans, a.referans_yaz)
    _tablo(r)


if __name__ == "__main__":
    main()
