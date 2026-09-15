#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ŞAHİT-7 — danışman için kalibre edilmiş kanıt ağı.

ŞAHİT-7 astrolojik hüküm üretmez. Mevcut hesapların yedi danışmanlık
merceğinde ne kadar AYIRT EDİCİ veri taşıdığını ve aynı mercekteki kanıtların
ne kadar gerilim ürettiğini iki ayrı eksende ölçer.

v13.1'de ``durum=çelişkili`` belirginliğin yerini alıyordu. Bu, çok güçlü ama
iki yönlü bir merceği "güçlü" olmaktan çıkarıyor; veri miktarı ile veri içi
gerilimi tek değişkende karıştırıyordu. v13.2'de belirginlik ve çelişki
bağımsızdır: bir mercek aynı anda ``güçlü`` ve ``celiskili=True`` olabilir.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import depo
from typing import Any, Dict, List, Tuple

_REFERANS_DOSYA = Path(__file__).with_name("sahit_quantiles.json")
_REFERANS_GERCEK_DOSYA = Path(__file__).with_name("sahit_quantiles_gercek.json")
_REFERANS: Dict[str, Any] | None = None


def _d(v: Any) -> Dict[str, Any]:
    return v if isinstance(v, dict) else {}


def _ok(v: Any) -> bool:
    return isinstance(v, dict) and bool(v) and not v.get("hata")


def _liste(v: Any) -> List[Any]:
    return v if isinstance(v, list) else []


def _sayi(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


MERCEKLER: Dict[str, Dict[str, Any]] = {
    "benlik": {
        "ad": "Benlik ve karar",
        "alan": ("kimlik", "iceri"),
        "kaynak": ("berzah_v2", "hukum", "yakinsama", "sarsma"),
        "omurga": "cekirdek",
        "ev_bagimli": True,
    },
    "guc": {
        "ad": "Güç ve doğal kullanım",
        "alan": ("yaratim", "gorunurluk", "duzen"),
        "kaynak": ("human_design", "berzah_v2", "deneme_modulleri", "kabzbast_v1_m66_74"),
        "omurga": "hareket",
        "ev_bagimli": False,
    },
    "gelisim": {
        "ad": "Gelişim ve kör nokta",
        "alan": ("iceri", "kok", "anlam"),
        "kaynak": ("celiskiler", "direnc", "duraklama_izi", "yas_katmani"),
        "omurga": "gerilim",
        "ev_bagimli": False,
    },
    "iliski": {
        "ad": "İlişkide davranış",
        "alan": ("iliski", "yaratim"),
        # Kişisel haritada da ilişki konuşabilsin diye çekirdek, temas ve hudûd
        # kanıtları korunur; sinastri/kompozit katmanları varsa bunlar onların
        # üstüne eklenir. İlişki merceği artık yalnız iki kişilik modun yan ürünü
        # değildir.
        "kaynak": (
            "berzah_v2", "hudud_felek", "temas_acisi", "direnc",
            "sinastri", "davison", "deklinasyon", "kompozit",
        ),
        "kisisel_kaynak": ("berzah_v2", "hudud_felek", "temas_acisi", "direnc"),
        "iliski_kaynak": ("sinastri", "davison", "deklinasyon", "kompozit", "direnc"),
        "omurga": "cekirdek",
        "ev_bagimli": False,
    },
    "is": {
        "ad": "İş, üretim ve kaynak",
        "alan": ("gorunurluk", "duzen", "kaynak"),
        "kaynak": ("berzah_v2", "human_design", "hamle_penceresi", "yas_katmani"),
        "omurga": "hareket",
        "ev_bagimli": True,
    },
    "zaman": {
        "ad": "Zaman ve eşikler",
        "alan": ("gorunurluk", "anlam", "iceri"),
        "kaynak": ("zaman_seridi", "solar_v2", "hamle_penceresi", "yas_katmani", "kayip_zaman"),
        "omurga": "zaman",
        "ev_bagimli": False,
    },
    "yer": {
        "ad": "Yer ve çevre",
        "alan": ("gorunurluk", "anlam", "kok"),
        "kaynak": ("kartografi", "hudud_felek"),
        "omurga": "mekan",
        "ev_bagimli": True,
    },
}


def _var(veri: Dict[str, Any], kod: str) -> bool:
    v = veri.get(kod)
    if kod in ("celiskiler", "direnc"):
        return bool(v)
    if isinstance(v, list):
        return bool(v)
    return _ok(v)


def _iliski_modu(veri: Dict[str, Any]) -> str:
    return "iliski" if any(_var(veri, k) for k in ("sinastri", "davison", "deklinasyon", "kompozit")) else "kisisel"


def _beklenen_kaynak(veri: Dict[str, Any], kod: str, meta: Dict[str, Any]) -> Tuple[str, ...]:
    if kod != "iliski":
        return tuple(meta["kaynak"])
    if _iliski_modu(veri) == "iliski":
        # İki kişilik modda kişisel kanıtlar hâlâ destek olabilir; fakat kapsama
        # oranını ilişki katmanlarının gerçekten kurulup kurulmadığı belirler.
        return tuple(meta["iliski_kaynak"])
    return tuple(meta["kisisel_kaynak"])


def _referans_yukle() -> Dict[str, Any]:
    global _REFERANS
    if _REFERANS is not None:
        return _REFERANS
    try:
        kalici = depo.referans_yolu("sahit")
        yol = kalici if kalici.exists() else (_REFERANS_GERCEK_DOSYA if _REFERANS_GERCEK_DOSYA.exists() else _REFERANS_DOSYA)
        _REFERANS = json.loads(yol.read_text(encoding="utf-8"))
    except Exception:
        _REFERANS = {}
    return _REFERANS


def referans_sifirla() -> None:
    global _REFERANS
    _REFERANS = None


def _yuzdelik(kod: str, ham: float) -> Tuple[float, str, str]:
    ref_tam = _referans_yukle()
    ref = (ref_tam.get("mercekler") or {}).get(kod) or {}
    noktalar = ref.get("quantiles") or []
    kaynak = str(ref_tam.get("kaynak") or "bilinmiyor")
    if not noktalar:
        return max(0.0, min(100.0, ham)), "yok", kaynak
    pts = sorted((float(x["q"]), float(x["v"])) for x in noktalar if "q" in x and "v" in x)
    if not pts:
        return max(0.0, min(100.0, ham)), "yok", kaynak
    if ham <= pts[0][1]:
        return round(pts[0][0] * 100, 1), "referans", kaynak
    if ham >= pts[-1][1]:
        return round(pts[-1][0] * 100, 1), "referans", kaynak
    for (q0, v0), (q1, v1) in zip(pts, pts[1:]):
        if v0 <= ham <= v1:
            q = (q0 + q1) / 2 if abs(v1 - v0) < 1e-9 else q0 + (ham - v0) / (v1 - v0) * (q1 - q0)
            return round(q * 100, 1), "referans", kaynak
    return max(0.0, min(100.0, ham)), "yok", kaynak


def _gerilim_esigi(kod: str) -> Tuple[float | None, str]:
    ref_tam = _referans_yukle()
    ref = (ref_tam.get("mercekler") or {}).get(kod) or {}
    kaynak = str(ref_tam.get("kaynak") or "bilinmiyor")
    if "gerilim_q75" not in ref:
        return None, kaynak
    return _sayi(ref.get("gerilim_q75")), kaynak


def _durum(belirginlik: float) -> str:
    # Eşikler bilinçli olarak yüzdelik cetvelindedir; ham puana uygulanmaz.
    if belirginlik <= 20:
        return "sessiz"
    if belirginlik >= 70:
        return "güçlü"
    return "orta"


def _talimat(durum: str, celiskili: bool) -> str:
    if durum == "sessiz":
        return "ölçülmedi de, doldurma"
    if durum == "güçlü" and celiskili:
        return "iki tarafı da göster, birini seçme"
    if celiskili:
        return "çelişkiyi göster; kesin bir tarafa kapatma"
    if durum == "güçlü":
        return "birden çok bağımsız kanıta yaslan; gündelik davranışa çevir"
    return "ölçüyü aşmadan anlat; kesinlik dili kurma"


def ham_mercekler(veri: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Kalibrasyondan önceki ŞAHİT-7 ölçülerini üretir.

    Ham belirginlik mercekler arasında doğrudan kıyaslanmaz; her mercek kendi
    referans dağılımında yüzdeliğe çevrilir. Bu fonksiyon kalibrasyon koşucusuna
    aynı matematiği kullanma imkânı verir.
    """
    cv = _d(veri.get("cevaplanabilirlik"))
    alanlar = {x.get("kod"): x for x in (cv.get("alanlar") or []) if isinstance(x, dict)}
    om = _d(veri.get("oruntu_omurgasi"))
    ompuan = {x.get("kod"): _sayi(x.get("puan"), 0.0) for x in (om.get("eksenler") or []) if isinstance(x, dict)}
    sars = _d(veri.get("sarsma"))
    sag = max(0.0, min(1.0, _sayi(sars.get("saglamlik"), 0.5)))
    cel_say = len(_liste(veri.get("celiskiler")))
    diren_say = len(_liste(veri.get("direnc")))

    out: Dict[str, Dict[str, Any]] = {}
    for kod, meta in MERCEKLER.items():
        ilgili = [alanlar[a] for a in meta["alan"] if a in alanlar]
        cevap = max([_sayi(a.get("puan"), 0.0) for a in ilgili] or [0.0])
        alan_gerilim = sum(int(_sayi(a.get("gerilim"), 0.0)) for a in ilgili)
        beklenen = _beklenen_kaynak(veri, kod, meta)
        bulunan = [k for k in tuple(meta["kaynak"]) if _var(veri, k)]
        beklenen_bulunan = [k for k in beklenen if _var(veri, k)]
        kapsama = len(beklenen_bulunan) / max(1, len(beklenen))
        om_k = _sayi(ompuan.get(meta["omurga"]), 0.0)

        # Cevaplanabilirlik en ağır sinyaldir; kapsama bağımsız kaynak sayısını,
        # MİZAN ise aynı temanın genel analiz içindeki ayırt ediciliğini taşır.
        ham = cevap * 4.2 + kapsama * 28.0 + om_k * 0.24
        if meta.get("ev_bagimli"):
            # Sarsma yalnız ev/eksen bağımlı mercekleri etkiler. v13.1'de aynı
            # global değer yedi merceğe birden yazılıyor, gerçekte güven farkı
            # yaratmıyordu.
            ham *= 0.68 + 0.32 * sag

        # Gerilim ayrı cetveldir. Genel çelişki/direnç yalnız küçük bir arka plan
        # katkısıdır; asıl ağırlık merceğin cevaplanabilirlik alanlarındaki
        # gerilim sayacındadır.
        gerilim = alan_gerilim * 2.0 + min(cel_say, 5) * 0.35 + min(diren_say, 5) * 0.2
        out[kod] = {
            "ham_belirginlik": round(ham, 4),
            "ham_gerilim": round(gerilim, 4),
            "cevap": round(cevap, 3),
            "kapsama": round(kapsama, 4),
            "omurga": round(om_k, 2),
            "kaynaklar": bulunan,
            "beklenen_kaynaklar": list(beklenen),
            "sarsma_saglamligi": round(sag, 3) if meta.get("ev_bagimli") else None,
            "mod": _iliski_modu(veri) if kod == "iliski" else "kisisel",
        }
    return out


def sahit_agi(veri: Dict[str, Any]) -> Dict[str, Any]:
    hamlar = ham_mercekler(veri)
    mercekler: List[Dict[str, Any]] = []
    _ref_meta = _referans_yukle()
    ref_kaynak = str(_ref_meta.get("kaynak") or "yok")
    for kod, meta in MERCEKLER.items():
        h = hamlar[kod]
        belirginlik, kal, kaynak = _yuzdelik(kod, float(h["ham_belirginlik"]))
        esik, _ = _gerilim_esigi(kod)
        # Referans yoksa çelişkiyi sırf sayı var diye icat etmeyiz. Ölçülemeyen
        # yerde sessizlik, yanlış bir sınıflandırmadan daha değerlidir.
        celiskili = bool(esik is not None and float(h["ham_gerilim"]) > float(esik))
        durum = _durum(belirginlik)
        mercekler.append({
            "kod": kod,
            "ad": meta["ad"],
            "belirginlik": belirginlik,
            "ham_belirginlik": h["ham_belirginlik"],
            "durum": durum,
            "celiskili": celiskili,
            "gerilim": h["ham_gerilim"],
            "gerilim_q75": esik,
            "kaynaklar": h["kaynaklar"],
            "beklenen_kaynaklar": h["beklenen_kaynaklar"],
            "kapsama": h["kapsama"],
            "kalibrasyon": kal,
            "kalibrasyon_kaynagi": kaynak,
            "sarsma_saglamligi": h["sarsma_saglamligi"],
            "talimat": _talimat(durum, celiskili),
        })
    mercekler.sort(key=lambda x: x["belirginlik"], reverse=True)
    return {
        "modul": "ŞAHİT-7 · Danışman Kanıt Ağı",
        "surum": 3,
        "kalibrasyon_kaynagi": ref_kaynak,
        "referans_bilgisi": {"kaynak": ref_kaynak, "uretim_tarihi": _ref_meta.get("uretim_tarihi"),
                             "ornek_sayisi": _ref_meta.get("ornek_sayisi", _ref_meta.get("n"))},
        "mercekler": mercekler,
        "once": [x["kod"] for x in mercekler if x["durum"] == "güçlü"][:3],
        "sessiz": [x["kod"] for x in mercekler if x["durum"] == "sessiz"],
        "celiskili": [x["kod"] for x in mercekler if x["celiskili"]],
        "yontem": (
            "Yeni astrolojik gösterge üretmez. Cevaplanabilirlik, MİZAN-5, kaynak kapsamı ve yalnız "
            "ev-bağımlı merceklerde sarsma sağlamlığını ham kanıt indeksine dönüştürür; yayınlanan "
            "belirginlik her merceğin kendi referans dağılımındaki yüzdelik dilimidir. Çelişki, aynı "
            "merceğin gerilim dağılımının üst çeyreği olarak ayrıca işaretlenir."
        ),
        "sinir": (
            "Belirginlik doğruluk ya da kader puanı değildir. Sessiz mercek hayatın o alanında sorun "
            "olmadığını değil, bu analizde yeterince ayırt edici kanıt bulunmadığını söyler."
        ),
    }
