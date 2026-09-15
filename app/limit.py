#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HIZ SINIRI — kaba kuvvet ve kota yakımına karşı

İki ayrı tehdit var ve ikisi de gerçek:

  1. PAROLA KABA KUVVETİ — sızma testinde 12 deneme de kabul edildi.
     Yönetici parolası sınırsız denenebiliyordu.

  2. AI KOTASI YAKIMI — servis herkese açık. URL'yi bilen biri /api/v1/chat'i
     döngüye sokup gateway kotasını tüketebilir. Kullanıcı bu kotayı zaten bir
     kez doldurdu (52M/50M jeton); bu, teorik değil yaşanmış bir risk.

Bellek içi, süreç ömrüyle sınırlı kayan pencere sayacı. Render tek örnekte
çalıştığı için yeterli; çok örneğe çıkılırsa Redis'e taşınmalı.
"""
from __future__ import annotations

import threading
import time
from typing import Dict, List, Tuple

_KILIT = threading.Lock()
_KOVA: Dict[str, List[float]] = {}

# Kova -> (izin, pencere saniye). Ortam değişkenleriyle ayarlanabilir:
#   ZIC_LIMIT_AUTH=5/900   ZIC_LIMIT_AI=30/3600   ZIC_LIMIT_AGIR=60/3600
# Sıfır izin ("0/0") o kovayı tamamen kapatır — sızma testi ve yük denemesi
# için gerekli, üretimde kullanılmamalı.
import os as _os


def _kural(ad: str, izin: int, pencere: int) -> Tuple[int, int]:
    ham = _os.environ.get(f"ZIC_LIMIT_{ad.upper()}", "")
    if "/" in ham:
        try:
            a, b = ham.split("/", 1)
            return int(a), int(b)
        except Exception:
            pass
    return izin, pencere


KURALLAR: Dict[str, Tuple[int, int]] = {
    "auth": _kural("auth", 5, 900),      # parola: 15 dakikada 5 deneme
    "ai": _kural("ai", 30, 3600),        # AI çağrıları: saatte 30
    "agir": _kural("agir", 60, 3600),    # pahalı hesap: saatte 60
    # IP'den bağımsız küresel tavan: başlık sahteciliğiyle atlatılamaz
    "auth_kuresel": _kural("auth_kuresel", 20, 900),
}


def _anahtar(kova: str, kimlik: str) -> str:
    return f"{kova}:{kimlik}"


def kontrol(kova: str, kimlik: str) -> Tuple[bool, int]:
    """
    Döner: (izin_var, kalan_saniye).
    İzin yoksa kalan_saniye, pencerenin ne zaman açılacağını söyler.
    """
    izin, pencere = KURALLAR.get(kova, (60, 3600))
    if izin <= 0 and pencere <= 0:
        return True, 0        # kova kapalı (yalnız test amaçlı)
    simdi = time.time()
    a = _anahtar(kova, kimlik)
    with _KILIT:
        # bellek şişmesin: ara ara tamamen temizlenen kovalar
        if len(_KOVA) > 5000:
            for k in list(_KOVA):
                _KOVA[k] = [t for t in _KOVA[k] if simdi - t < pencere]
                if not _KOVA[k]:
                    _KOVA.pop(k, None)
        vurus = [t for t in _KOVA.get(a, []) if simdi - t < pencere]
        if len(vurus) >= izin:
            _KOVA[a] = vurus
            return False, int(pencere - (simdi - vurus[0])) + 1
        vurus.append(simdi)
        _KOVA[a] = vurus
        return True, 0


def sifirla(kova: str, kimlik: str) -> None:
    """Başarılı girişten sonra sayacı sıfırla."""
    with _KILIT:
        _KOVA.pop(_anahtar(kova, kimlik), None)


def durum() -> dict:
    with _KILIT:
        return {"kova_sayisi": len(_KOVA), "kurallar": KURALLAR}
