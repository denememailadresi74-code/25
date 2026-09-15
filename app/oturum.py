#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OTURUM DEPOSU — misafir kipinde gerçek veri kısıtlaması

Sorun: misafire yalnız arayüzde bölüm gizlemek KISITLAMA DEĞİLDİR; tarayıcı
konsolundan gelen JSON'un tamamı okunabilir. Öte yandan danışman sohbetinin
iyi cevap verebilmesi için analizin TAMAMINA ihtiyacı var.

Çözüm: analiz sunucuda tutulur, misafire yalnız harita çizimi için gereken
kısım gönderilir ve bir oturum kimliği verilir. Sohbet o kimliği yollar,
sunucu tam bağlamı kendi belleğinden okur. Böylece misafir hem eksiksiz
danışmanlık alır hem hesaplanan modüllerin ham verisini görmez.

Not: bellek içi ve süreç ömrüyle sınırlıdır. Render ücretsiz katmanda servis
uykuya geçtiğinde oturumlar silinir; kullanıcı analizi yeniden çalıştırır.
Kalıcılık gerekirse burası Redis ile değiştirilebilir.
"""
from __future__ import annotations

import secrets
import threading
import time
from typing import Any, Dict, Optional

_KILIT = threading.Lock()
_DEPO: Dict[str, Dict[str, Any]] = {}

OMUR = 3 * 3600          # saniye — oturumun yaşam süresi
AZAMI = 300              # aynı anda tutulacak azami oturum


def _temizle() -> None:
    """Süresi dolanları at; sınır aşılırsa en eskiden başlayarak boşalt."""
    simdi = time.time()
    olu = [k for k, v in _DEPO.items() if simdi - v["ts"] > OMUR]
    for k in olu:
        _DEPO.pop(k, None)
    if len(_DEPO) > AZAMI:
        for k, _ in sorted(_DEPO.items(), key=lambda x: x[1]["ts"])[:len(_DEPO) - AZAMI]:
            _DEPO.pop(k, None)


def kaydet(analiz: Dict[str, Any], mod: str = "Kişisel",
           model: Optional[str] = None, dogum: Optional[Dict[str, Any]] = None) -> str:
    with _KILIT:
        _temizle()
        kimlik = secrets.token_urlsafe(18)
        _DEPO[kimlik] = {"analiz": analiz, "mod": mod, "model": model,
                           "dogum": dogum or {}, "revision": 1,
                           "ts": time.time()}
        # AYÂR yalnız kişisel /full popülasyonunu izler. İlişki oturumlarını
        # aynı referans havuzuna katmak dağılımı yapay biçimde değiştirirdi.
        if mod == "Kişisel":
            try:
                from .ayar import kaydet as _ayar_kaydet
                _ayar_kaydet(analiz)
            except Exception:
                pass
        return kimlik


def getir(kimlik: str) -> Optional[Dict[str, Any]]:
    with _KILIT:
        v = _DEPO.get(kimlik)
        if not v:
            return None
        if time.time() - v["ts"] > OMUR:
            _DEPO.pop(kimlik, None)
            return None
        v["ts"] = time.time()      # kullanıldıkça tazelenir
        return v


def durum() -> Dict[str, Any]:
    with _KILIT:
        _temizle()
        return {"acik_oturum": len(_DEPO), "omur_sn": OMUR, "azami": AZAMI}


# ---------------------------------------------------------------- misafir süzgeci
def misafir_payi(tam: Dict[str, Any]) -> Dict[str, Any]:
    """
    Misafirin göreceği kısım: yalnız harita çizimi için gerekli alanlar.
    Hesaplanan modüllerin ham verisi (deneme modülleri, kadim katman,
    Kabz/Bast, Şi'râ, Human Design, alan topolojisi) GÖNDERİLMEZ.
    """
    def halka_payi(v2: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not isinstance(v2, dict):
            return None
        anahtar = ("phi_alani", "kutleler", "KD", "AD", "berzah", "ev_uclari",
                   "asc", "mc", "noktalar", "nokta_acilari")
        d = {k: v2[k] for k in anahtar if k in v2}
        # Berzah'ın yalnız konumu; yorum alanları misafire gitmez
        b = v2.get("berzah")
        if isinstance(b, dict):
            d["berzah"] = {k: b[k] for k in ("lon", "konum", "ev", "tur")
                           if k in b}
        return d

    g = tam.get("girdi", {})
    out: Dict[str, Any] = {
        "servis": tam.get("servis"),
        "rol": "misafir",
        "girdi": {k: g.get(k) for k in ("ad", "an", "tz", "ev_sistemi", "mod",
                                        "A", "B") if k in g},
        "berzah_v2": halka_payi(tam.get("berzah_v2")),
    }
    if tam.get("solar_v2"):
        s = tam["solar_v2"]
        out["solar_v2"] = {"yil": s.get("yil"), "an": s.get("an"),
                           "berzah_v2": halka_payi(s.get("berzah_v2"))}
    for k in ("A_berzah", "B_berzah"):
        if tam.get(k):
            out[k] = halka_payi(tam[k])
    for k in ("A_solar_v2", "B_solar_v2"):
        if tam.get(k):
            out[k] = {"yil": tam[k].get("yil"), "an": tam[k].get("an"),
                      "berzah_v2": halka_payi(tam[k].get("berzah_v2"))}
    if tam.get("transit"):
        out["transit"] = tam["transit"]
    if tam.get("misafir_kategoriler"):
        out["kategoriler"] = tam["misafir_kategoriler"]
    if tam.get("kompozit"):
        out["kompozit"] = {"kisiler": tam["kompozit"].get("kisiler"),
                           "berzah_v2": halka_payi(tam["kompozit"].get("berzah_v2"))}
    return out
