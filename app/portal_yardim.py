#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2 sahnesinin v1 sonuç sözlüğünden harita nesnesi kurması için küçük köprü."""
from __future__ import annotations
from typing import Any, Dict
from .astro import build_chart


def chart_analizden(analiz: Dict[str, Any]):
    g = analiz.get("girdi") or {}
    an = str(g.get("an") or "")
    if len(an) < 16:
        raise ValueError("Analiz girdisinde doğum anı yok.")
    lat = float(g.get("enlem", g.get("lat", 0)) or 0)
    lng = float(g.get("boylam", g.get("lng", 0)) or 0)
    # Analiz çıktısındaki `an` UT olduğundan tekrar yerel saat dönüşümü yapılmaz.
    return build_chart(int(an[:4]), int(an[5:7]), int(an[8:10]), int(an[11:13]), int(an[14:16]),
                       lat, lng, tz_offset=0.0, label=str(g.get("ad") or "Danışan"),
                       house_system=str(g.get("ev_sistemi") or "P"))
