#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MİZAN-5 / ÖRÜNTÜ OMURGASI — kalibre edilmiş beş eksenli öncelik endeksi.

v12.9 ham toplamlara aynı 0-100 cetvelini uyguluyordu. Eksenlerin teorik
tavanları farklı olduğu için Gerilim/Zaman sürekli tavana dayanıyor, Hareket
ve Mekân ise yapısal olarak öne çıkamıyordu. v13'te ham toplam korunur;
yayınlanan puan her eksenin kendi referans dağılımındaki yüzdelik dilimidir.

Bu puan astrolojik doğruluk, kişilik değeri ya da iyi/kötü değildir. Yalnız
mevcut hesaplardan hangi kategori ailesinin bu haritada daha ayırt edici veri
ürettiğini sıralar.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from . import depo
from typing import Any, Dict, List, Tuple

_REFERANS_DOSYA = Path(__file__).with_name("mizan_quantiles.json")
_REFERANS_GERCEK_DOSYA = Path(__file__).with_name("mizan_quantiles_gercek.json")
_REFERANS: Dict[str, Any] | None = None


def _dict(v: Any) -> Dict[str, Any]:
    return v if isinstance(v, dict) else {}


def _list(v: Any) -> List[Any]:
    return v if isinstance(v, list) else []


def _ok(v: Any) -> bool:
    return isinstance(v, dict) and bool(v) and not v.get("hata")


def _cap(v: float) -> int:
    return int(round(max(0.0, min(100.0, v))))


def _sayi(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _kaynak(ad: str, deger: Any, not_: str = "") -> Dict[str, Any]:
    return {"ad": ad, "deger": deger, "not": not_}


def _etiket(p: int) -> str:
    if p >= 80:
        return "ayırt edici"
    if p >= 60:
        return "ortalamanın üstü"
    if p >= 40:
        return "orta bant"
    if p >= 20:
        return "ince"
    return "sessiz"


def _hamle_tepe(hamle: Dict[str, Any]) -> Tuple[float, str]:
    en_iyi = _dict(hamle.get("en_iyi"))
    aday = []
    for kod, kayit in en_iyi.items():
        if isinstance(kayit, dict):
            aday.append((_sayi(kayit.get("puan")), str(kayit.get("ad") or kod)))
    return max(aday, key=lambda x: x[0]) if aday else (0.0, "")


def _referans_yukle() -> Dict[str, Any]:
    global _REFERANS
    if _REFERANS is not None:
        return _REFERANS
    try:
        kalici = depo.referans_yolu("mizan")
        yol = kalici if kalici.exists() else (_REFERANS_GERCEK_DOSYA if _REFERANS_GERCEK_DOSYA.exists() else _REFERANS_DOSYA)
        _REFERANS = json.loads(yol.read_text(encoding="utf-8"))
    except Exception:
        _REFERANS = {}
    return _REFERANS


def referans_sifirla() -> None:
    """Kalibrasyon koşucusu aynı süreçte yeni tablo yazarsa önbelleği temizler."""
    global _REFERANS
    _REFERANS = None


def _yuzdelik(kod: str, ham: float) -> Tuple[int, str, str]:
    ref_tam = _referans_yukle()
    ref = (ref_tam.get("eksenler") or {}).get(kod) or {}
    kaynak = str(ref_tam.get("kaynak") or "bilinmiyor")
    noktalar = ref.get("quantiles") or []
    if not noktalar:
        return _cap(ham), "yok", kaynak
    # Quantile tablosu [{q:0.00,v:...}, ...]. Aynı değerin uzun plato yaptığı
    # yerde ortadaki yüzdelik seçilir; aksi hâlde uçtaki ilk eşleşme puanı
    # gereksiz biçimde sıçratıyordu.
    pts = sorted((float(x["q"]), float(x["v"])) for x in noktalar
                 if "q" in x and "v" in x)
    if not pts:
        return _cap(ham), "yok", kaynak
    # Discrete eksenlerde (özellikle Hareket/Mekân) aynı ham değer çok geniş
    # bir quantile platosunu kaplayabilir. Uçtaki ilk q'ya yapışmak dağılımın
    # ortalamasını aşağı kaydırıyordu; eşit değerlerin orta-rank'i kullanılır.
    esler = [q for q, v in pts if abs(v - ham) < 1e-9]
    if esler:
        return _cap(sum(esler) / len(esler) * 100), "referans", kaynak
    if ham < pts[0][1]:
        return _cap(pts[0][0] * 100), "referans", kaynak
    if ham > pts[-1][1]:
        return _cap(pts[-1][0] * 100), "referans", kaynak
    for (q0, v0), (q1, v1) in zip(pts, pts[1:]):
        if v0 <= ham <= v1:
            if abs(v1 - v0) < 1e-9:
                q = (q0 + q1) / 2
            else:
                q = q0 + (ham - v0) / (v1 - v0) * (q1 - q0)
            return _cap(q * 100), "referans", kaynak
    return _cap(ham), "yok", kaynak


def _boylam_farki(a: float, b: float) -> float:
    return abs(((a - b + 180.0) % 360.0) - 180.0)


def _mekan_yogunlasma(kart: Dict[str, Any], kusak: float = 5.0) -> Dict[str, Any]:
    """Aynı ±5° boylam kuşağına giren AYRI çizgilerin en yüksek sayısı.

    v12.9 çizgi sayısını kullanıyordu; her harita neredeyse aynı sayıda cisim
    çizdiği için bu bir sinyal değil gizli tabandı. Burada çizgi adedi değil,
    ayrı çizgilerin aynı meridyen kuşağında gerçekten yığılması ölçülür.
    """
    cizgiler: Dict[str, List[float]] = {}
    for katman in ("natal", "gunes_donusu", "ay_donusu"):
        for i, c in enumerate(_list(_dict(kart.get(katman)).get("cizgiler"))):
            if not isinstance(c, dict):
                continue
            ad = str(c.get("kod") or c.get("cisim") or i)
            for tur in ("MC", "IC"):
                if isinstance(c.get(tur), (int, float)):
                    cizgiler[f"{katman}:{ad}:{tur}"] = [float(c[tur])]
            for tur in ("ASC", "DSC"):
                vals = [float(x["boylam"]) for x in _list(c.get(tur))
                        if isinstance(x, dict) and isinstance(x.get("boylam"), (int, float))]
                if vals:
                    cizgiler[f"{katman}:{ad}:{tur}"] = vals
    aday = [x for vals in cizgiler.values() for x in vals]
    if not aday:
        return {"tepe": 0, "boylam": None, "cizgi": 0}
    en = (0, None)
    for merkez in aday:
        sayi = sum(1 for vals in cizgiler.values()
                   if any(_boylam_farki(v, merkez) <= kusak for v in vals))
        if sayi > en[0]:
            en = (sayi, merkez)
    return {"tepe": en[0], "boylam": round(float(en[1]), 1) if en[1] is not None else None,
            "cizgi": len(cizgiler)}


def _eksen(kod: str, ad: str, ham: float, ozet: str,
           kaynaklar: List[Dict[str, Any]], bolumler: List[str], kalibre: bool) -> Dict[str, Any]:
    if kalibre:
        puan, durum, kaynak = _yuzdelik(kod, ham)
    else:
        puan, durum, kaynak = _cap(ham), "ham", "ham"
    return {"kod": kod, "ad": ad, "puan": puan, "ham_puan": round(ham, 3),
            "kalibrasyon": durum, "kalibrasyon_kaynagi": kaynak,
            "seviye": _etiket(puan), "ozet": ozet,
            "kaynaklar": kaynaklar, "bolumler": bolumler}


def oruntu_omurgasi(veri: Dict[str, Any], kalibre: bool = True) -> Dict[str, Any]:
    """Mevcut ZÎC kategorilerini beş eksende karşılaştırılabilir hâle getirir."""
    v2 = _dict(veri.get("berzah_v2"))
    hukum = _dict(veri.get("hukum"))
    top = _dict(v2.get("alan_topolojisi"))
    yas = _dict(veri.get("yas_katmani"))
    sarsma = _dict(veri.get("sarsma"))
    durak = _dict(veri.get("duraklama_izi"))
    hamle = _dict(veri.get("hamle_penceresi"))
    yakin = _dict(veri.get("yakinsama"))
    kart = _dict(veri.get("kartografi"))
    hudud = _dict(veri.get("hudud_felek"))
    kb = _dict(veri.get("kabzbast_v1_m66_74"))
    den = _dict(veri.get("deneme_modulleri"))
    kad = _dict(veri.get("kadim_katman"))
    hd = _dict(veri.get("human_design"))

    mercek = len(_list(v2.get("mercekleme")))
    ikiz = len(_list(v2.get("yapisal_ikizler")))
    asal = len(_list(v2.get("asal_acilar")))
    kurt = len(_list(v2.get("kurtarici")))
    sr_tetik = int(_sayi(_dict(hukum.get("cross")).get("adet"), 0))
    saglamlik = max(0.0, min(1.0, _sayi(sarsma.get("saglamlik"), 1.0))) if sarsma else 1.0
    cekirdek_ham0 = 28 + min(mercek, 4) * 8 + min(ikiz, 5) * 5 + min(asal, 6) * 4 + min(kurt, 3) * 4 + min(sr_tetik, 4) * 3
    cekirdek_ham = cekirdek_ham0 * saglamlik
    cekirdek = _eksen(
        "cekirdek", "Çekirdek", cekirdek_ham,
        "Natal karar geometrisinin kaç bağımsız işaretle aynı merkeze yığıldığını, doğum saati dayanıklılığıyla birlikte gösterir.",
        [_kaynak("Mercekleme", mercek), _kaynak("Yapısal ikiz", ikiz), _kaynak("Asal açı", asal),
         _kaynak("Kurtarıcı adayı", kurt), _kaynak("Solar tetik", sr_tetik),
         _kaynak("Sarsma sağlamlığı", f"%{round(saglamlik*100)}", "çekirdek güven cezası")],
        ["hukum", "halka", "catal", "kutleler", "kenarlar", "topoloji"], kalibre)

    esik = int(_sayi(yas.get("esik_sayisi"), 0))
    yigilma = _sayi(yas.get("yigilma"), 0)
    solar_var = 1 if hukum.get("mode") == "natal+solar" else 0
    hamle_puan, hamle_ad = _hamle_tepe(hamle)
    zaman_kaynak = sum(1 for x in (yas, kb, hamle, veri.get("kayip_zaman"), veri.get("sira_cevrimi")) if _ok(x))
    zaman_ham = 24 + solar_var * 12 + min(sr_tetik, 5) * 5 + min(esik, 4) * 9 + min(yigilma, 3.0) * 6 + min(zaman_kaynak, 5) * 3 + max(0.0, min(hamle_puan, 4.0)) * 2
    zaman = _eksen(
        "zaman", "Zaman", zaman_ham,
        "Yıllık aktivasyon, gelişim eşikleri ve yakın dönem hamle pencerelerinin aynı anda ne kadar görünür olduğunu gösterir.",
        [_kaynak("Solar Return", "bağlı" if solar_var else "bağlı değil"), _kaynak("Solar tetik", sr_tetik),
         _kaynak("Açık yaş eşiği", esik), _kaynak("Eşik yığılması", round(yigilma, 2)), _kaynak("Öne çıkan hamle", hamle_ad or "—")],
        ["sira", "kabzbast", "lunasyon", "donus", "esik", "sukut", "hamle"], kalibre)

    cel = len(_list(veri.get("celiskiler")))
    diren = len(_list(veri.get("direnc")))
    sag_g = max(0.0, min(1.0, _sayi(sarsma.get("saglamlik"), 0.5)))
    kum = len(_list(_dict(sarsma.get("gruplar")).get("kum")))
    kir = len(_list(_dict(sarsma.get("gruplar")).get("kırılgan")))
    ham_n = len(_list(durak.get("el_degmemis")))
    gerilim_ham = 18 + min(cel, 5) * 11 + min(diren, 5) * 7 + min(kum, 5) * 10 + min(kir, 6) * 5 + min(ham_n, 6) * 3 + (1.0 - sag_g) * 20
    gerilim = _eksen(
        "gerilim", "Gerilim", gerilim_ham,
        "Katmanların birbirini ne kadar zorladığını ve hangi bulguların doğum saati belirsizliğine hassas olduğunu toplar.",
        [_kaynak("Çelişki", cel), _kaynak("Direnç", diren), _kaynak("Sarsma sağlamlığı", f"%{round(sag_g*100)}"),
         _kaynak("5 dk kırılan", kum), _kaynak("15 dk kırılan", kir), _kaynak("El değmemiş nokta", ham_n)],
        ["sarsma", "duraklama", "celiski", "direnc", "cevaplanabilirlik"], kalibre)

    yak_cek = _list(yakin.get("cekirdek"))
    ilk_yak = _list(durak.get("ilk_kez_yaklasan"))
    top_var = 1 if _ok(top) else 0
    kb_var = 1 if _ok(kb) else 0
    hareket_ham = 26 + min(len(yak_cek), 3) * 12 + min(len(ilk_yak), 4) * 8 + top_var * 7 + kb_var * 7 + (8 if _ok(hamle) else 0)
    hareket = _eksen(
        "hareket", "Hareket", hareket_ham,
        "Yakınsama, Kabz/Bast, duraklama ve alan topolojisinin hareket için ne kadar belirgin yön ürettiğini gösterir.",
        [_kaynak("Yakınsayan eksen", len(yak_cek)), _kaynak("İlk kez yaklaşan", len(ilk_yak)),
         _kaynak("Alan topolojisi", "var" if top_var else "yok"), _kaynak("Kabz/Bast", "var" if kb_var else "yok"),
         _kaynak("Hamle penceresi", "var" if _ok(hamle) else "yok")],
        ["yakinsama", "kabzbast", "duraklama", "topoloji", "hamle"], kalibre)

    yog = _mekan_yogunlasma(kart)
    paran = len(_list(kart.get("natal_paran") or kart.get("paranlar")))
    hud_arz = _dict(kart.get("hudud_arz"))
    sessiz = len(_list(hud_arz.get("sessiz_kusaklar")))
    hud_var = 1 if _ok(hudud) else 0
    mekan_ham = 14 + min(yog["tepe"], 24) * 3.0 + min(paran, 8) * 4 + min(sessiz, 5) * 4 + hud_var * 8
    mekan = _eksen(
        "mekan", "Mekân", mekan_ham,
        "Yer çizgilerinin sayısını değil, aynı boylam kuşağında gerçekten ne kadar yoğunlaştığını ölçer.",
        [_kaynak("±5° çizgi yoğunlaşması", yog["tepe"], f"tepe boylam {yog['boylam']}°" if yog["boylam"] is not None else "ölçülmedi"),
         _kaynak("Ölçülen ayrı çizgi", yog["cizgi"]), _kaynak("Paran", paran), _kaynak("Sessiz kuşak", sessiz),
         _kaynak("Küresel hudûd", "var" if hud_var else "yok")],
        ["kartografi", "hudud", "sehir"], kalibre)

    eksenler = [cekirdek, zaman, gerilim, hareket, mekan]
    sirali = sorted(eksenler, key=lambda x: (x["puan"], x["ham_puan"]), reverse=True)
    birincil, ikincil = sirali[0], sirali[1]
    katman_sagligi = {
        "modern_cekirdek": _ok(v2), "zamanlama": any(_ok(x) for x in (yas, kb, hamle)),
        "dayaniklilik": _ok(sarsma) or _ok(durak), "geleneksel": _ok(kad) or _ok(den),
        "human_design": _ok(hd), "mekan": _ok(kart),
    }
    hazir = sum(1 for v in katman_sagligi.values() if v)
    kal_durum = "referans" if all(e["kalibrasyon"] == "referans" for e in eksenler) else "yok"
    _ref_meta = _referans_yukle() if kal_durum == "referans" else {}
    kal_kaynak = str(_ref_meta.get("kaynak") or "yok") if kal_durum == "referans" else "yok"
    return {
        "modul": "MİZAN-5 · Örüntü Omurgası", "surum": 4, "kalibrasyon": kal_durum,
        "kalibrasyon_kaynagi": kal_kaynak,
        "referans_bilgisi": {"kaynak": kal_kaynak, "uretim_tarihi": _ref_meta.get("uretim_tarihi"),
                             "ornek_sayisi": _ref_meta.get("ornek_sayisi", _ref_meta.get("n"))},
        "eksenler": eksenler, "baskin": birincil["kod"], "ikincil": ikincil["kod"],
        "okuma": (f"Bu haritada göreli belirginlik {birincil['ad'].lower()} ekseninde en yüksek; "
                  f"ikinci {ikincil['ad'].lower()}. Yüzdelikler her ekseni kendi referans dağılımıyla "
                  "kıyaslar; eksenlerin ham toplamları artık birbirine doğrudan karıştırılmaz."),
        "rota": [{"sira": i + 1, "kod": e["kod"], "ad": e["ad"], "puan": e["puan"],
                  "ham_puan": e["ham_puan"], "bolumler": e["bolumler"]} for i, e in enumerate(sirali)],
        "katman_sagligi": katman_sagligi, "hazir_kategori": hazir, "toplam_kategori": len(katman_sagligi),
        "yontem": ("Her eksen önce kendi ham toplamını üretir. Yayınlanan puan, kalibrasyon örnekleminde "
                   "o ham toplamın yüzdelik dilimidir. Mekân çizgi adedini değil ±5° boylam yoğunlaşmasını; "
                   "Çekirdek ise doğum saati sarsma sağlamlığını kullanır."),
        "sinir": ("MİZAN-5 bilimsel doğruluk ölçüsü değildir ve astrolojik hükmün yerine geçmez. "
                  "Kalibrasyon dosyası yoksa puan ham ölçeğe düşer ve kalibrasyon='yok' açıkça yazılır."),
    }
