#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DENEME MODÜLLERİ — Astro Pro v9.2.4 hücrelerinden (CELL 2.8–2.30) ayrıştırıldı.
Her fonksiyon saf hesap yapar ve JSON-uyumlu dict döner; HTML/JS katmanı yoktur.
Matematik, kaynak hücre başlıklarında belgelenen formüllerin birebir uygulamasıdır.
"""
from __future__ import annotations
import math
import datetime as dt
from typing import Dict, List, Optional, Sequence, Tuple

import swisseph as swe

from .astro import (NatalChart, BODY_IDS, CORE10, MEAN_SPEED, TR_NAME,
                    EPHFLAG, chart_at_jd, jd_to_iso, calc_lon)
from .circular import (norm360, sep, signed_sep, project, sign_of, deg_in_sign,
                       fmt_lon, circular_mean_weighted, circular_median,
                       rayleigh_R, house_of, ELEMENT, RULER, SIGNS)

NURANI_W = {"Sun": 3.0, "Moon": 3.0, "Mercury": 2.0, "Venus": 2.0, "Mars": 2.0,
            "Jupiter": 1.5, "Saturn": 1.5, "Uranus": 1.0, "Neptune": 1.0,
            "Pluto": 1.0}
# Açı tablosu — Astro Pro v9.2.4 ASPECTS ile BİREBİR aynı orb ve güç ölçeği.
# (ad, glif, açı, orb°, güç 0..1, majör mü)
# v2.1'de buradaki orblar 2.5/2.0/1.5 idi; referansın ~4 katı darı. Bu yüzden
# Asabiyye grafı boş kalıyor, λ₂ daima 0 çıkıyor ve harita "kopuk" görünüyordu.
_ASPECTS = [("Kavuşum", "☌", 0, 8.0, 1.00, True),
            ("Karşıt", "☍", 180, 8.0, 1.00, True),
            ("Üçgen", "△", 120, 7.0, 0.90, True),
            ("Kare", "□", 90, 7.0, 0.90, True),
            ("Altmışlık", "⚹", 60, 5.0, 0.60, True),
            ("Yarım-altmış", "⚺", 30, 2.0, 0.20, False),
            ("Yarım-kare", "∠", 45, 2.0, 0.20, False),
            ("Sesqui", "⚼", 135, 2.0, 0.20, False),
            ("Quincunx", "⚻", 150, 3.0, 0.30, False)]


# Asabiyye λ₂ referans dağılımı — 1935-2020 arası 400 rastgele Türkiye haritası
# üzerinden ölçüldü. Mutlak λ₂ ağırlıklı Laplasyenin ölçeğine bağlıdır ve tek
# başına yorumlanamaz; bu yüzden harita, kendi türünün dağılımındaki YÜZDELİK
# konumuyla bildirilir. (v2.1 eşikleri >1.2 / >0.4 idi: 400 haritanın 397'si
# "zayıf" çıkıyor, sınıflandırma hiçbir şeyi ayırt etmiyordu.)
_ASABIYYE_DAGILIM = [0.0001, 0.0134, 0.0362, 0.0724, 0.1200, 0.1603, 1.8082]
_ASABIYYE_YUZDE = [0, 10, 25, 50, 75, 90, 100]


def _asabiyye_yuzdelik(lam: float) -> int:
    """λ₂'yi referans dağılımdaki yüzdelik konumuna çevirir (0..100)."""
    d, y = _ASABIYYE_DAGILIM, _ASABIYYE_YUZDE
    if lam <= d[0]:
        return 0
    for i in range(1, len(d)):
        if lam <= d[i]:
            t = (lam - d[i - 1]) / max(d[i] - d[i - 1], 1e-12)
            return int(round(y[i - 1] + t * (y[i] - y[i - 1])))
    return 100


def _orb_gucu(sapma: float, orb: float) -> float:
    """
    Orba göre normalize edilmiş kenar gücü — Astro Pro'nun kendi eğrisi:
        (1 − sapma/orb)^1.35
    Merkezde yoğun, orb sınırında yumuşakça sıfırlanır. Önceki sürümdeki
    sabit σ=1° Gauss'u orbtan bağımsızdı ve 2°'nin ötesini siliyordu.
    """
    if orb <= 0 or sapma >= orb:
        return 0.0
    return (1.0 - sapma / orb) ** 1.35
_HARMONIC_TXT = {1: "Toplanma / vahdet ekseni", 2: "Karşıtlık — gerilim, kutuplaşma",
                 3: "Üçgen — akış, yetenek, lütuf", 4: "Kare-haç — irade, yapı kurma",
                 5: "Kentil — özgün yaratıcılık", 6: "Sekstil — fırsat, işbirliği",
                 7: "Septil — kader, mistik cezbe", 8: "Yarım-kare — tetikleyici kriz",
                 9: "Novil — bilgelik, olgunlaşma", 10: "Desil — incelik, sanat",
                 11: "Onbirli — dahiyane sapma", 12: "Yarım-sekstil — ince ayar"}


def _lonw(ch: NatalChart) -> List[Tuple[float, float]]:
    return [(ch.bodies[k].lon, NURANI_W[k]) for k in CORE10]


def _aspects_to(point: float, ch: NatalChart, limit: int = 8) -> List[dict]:
    hits = []
    targets = {**{k: ch.bodies[k].lon for k in CORE10},
               "Asc": ch.asc, "MC": ch.mc,
               "TrueNode": ch.bodies["TrueNode"].lon, "Vertex": ch.vertex}
    for tk, tl in targets.items():
        d = sep(point, tl)
        for name, glyph, ang, orb, w, _maj in _ASPECTS:
            o = abs(d - ang)
            if o <= orb:
                hits.append({"hedef": TR_NAME.get(tk, tk), "hedef_key": tk,
                             "acim": name, "glyph": glyph, "orb": round(o, 2),
                             "guc": round(w * _orb_gucu(o, orb), 3)})
                break
    hits.sort(key=lambda x: -x["guc"])
    return hits[:limit]


# ============================================================================
# 1) KRN — Kader Rezonans Noktası  (CELL 2.8)
#    RN = ☉ + 0.618·Δ(☽,☉) · DK = ASC/MC orta · KÇ = KAD + 0.382·Δ(Vx,KAD)
#    KRN = arg(3·RN + 2·DK + 1·KÇ) · Anti-KRN = KRN+180
# ============================================================================
def krn(ch: NatalChart) -> dict:
    rn = project(ch.bodies["Sun"].lon, ch.bodies["Moon"].lon, 0.618)
    dk = norm360(ch.asc + 0.5 * signed_sep(ch.mc, ch.asc))
    kc = project(ch.bodies["TrueNode"].lon, ch.vertex, 0.382)
    k, _ = circular_mean_weighted([(rn, 3.0), (dk, 2.0), (kc, 1.0)])
    anti = norm360(k + 180)
    asp = _aspects_to(k, ch)
    score = 38.0 + min(34.0, sum(a["guc"] * 8.5 for a in asp))
    hv = ch.house(k) or 0
    score += 10 if hv in (1, 4, 7, 10) else 6 if hv in (2, 5, 8, 11) else 4
    if any(a["hedef_key"] in ("Sun", "Moon", "Asc", "MC", "TrueNode", "Vertex")
           for a in asp): score += 10
    score = int(max(0, min(100, round(score))))
    lvl = ("çok güçlü" if score >= 85 else "güçlü" if score >= 70
           else "orta" if score >= 55 else "zayıf/deneysel")
    return {"modul": "Kader Rezonans Noktası (KRN)",
            "RN": fmt_lon(rn), "DK": fmt_lon(dk), "KC": fmt_lon(kc),
            "KRN": {"lon": round(k, 3), "konum": fmt_lon(k), "ev": hv},
            "Anti_KRN": {"lon": round(anti, 3), "konum": fmt_lon(anti),
                         "ev": ch.house(anti),
                         "anlam": "kaderi kilitleyen eski alışkanlık alanı"},
            "acilar": asp, "skor": score, "seviye": lvl,
            "yontem": "KRN = arg(3RN+2DK+KÇ); RN altın-oran ☉→☽ izdüşümü."}


# ============================================================================
# 2) VAHDET — Vahdet Noktası + V-K İndeksi + Rezonans Spektrumu H1-H12 (CELL 2.9)
# ============================================================================
def vahdet(ch: NatalChart) -> dict:
    lw = _lonw(ch)
    v, R = circular_mean_weighted(lw)
    spec = [{"H": h, "R": round(rayleigh_R(lw, h), 3), "anlam": _HARMONIC_TXT[h]}
            for h in range(1, 13)]
    dom = max(spec, key=lambda s: s["R"])
    rejim = ("VAHDET — enerji tek noktada toplanıyor" if R >= 0.55 else
             "GEÇİŞ — toplanma ile dağılım dengede" if R >= 0.30 else
             "KESRET — enerji çok merkezli dağılmış")
    return {"modul": "Vahdet Noktası (Vahdet–Kesret İndeksi)",
            "vahdet_noktasi": {"lon": round(v, 3), "konum": fmt_lon(v),
                               "ev": ch.house(v)} if v is not None else None,
            "R_indeksi": round(R, 3), "rejim": rejim,
            "rezonans_spektrumu": spec,
            "baskin_harmonik": dom,
            "yontem": "arg Σ wᵢe^{iλᵢ}; nurânî ağırlıklar ☉☽3 ☿♀♂2 ♃♄1.5 dış1."}


# ============================================================================
# 3) MİZAN — Tecellî Topografyası  ρ(θ)=Σw·e^{κcos(θ−λ)}  (CELL 2.10)
#    tepe=Sekîne (makam) · çukur=Berzah (eşik)
# ============================================================================
def mizan(ch: NatalChart, kappa: float = 12.0, step: float = 1.0) -> dict:
    lw = _lonw(ch)
    n = int(360 / step)
    rho = [sum(w * math.exp(kappa * math.cos(math.radians(i * step - lon)))
               for lon, w in lw) for i in range(n)]
    mx = max(rho)
    rho = [r / mx for r in rho]
    peaks, valleys = [], []
    for i in range(n):
        a, b, c = rho[(i - 1) % n], rho[i], rho[(i + 1) % n]
        if b > a and b >= c:
            peaks.append({"tip": "Sekîne (makam)", "lon": round(i * step, 1),
                          "konum": fmt_lon(i * step), "ev": ch.house(i * step),
                          "yogunluk": round(b, 3)})
        if b < a and b <= c:
            valleys.append({"tip": "Berzah (eşik)", "lon": round(i * step, 1),
                            "konum": fmt_lon(i * step), "ev": ch.house(i * step),
                            "yogunluk": round(b, 3)})
    peaks.sort(key=lambda x: -x["yogunluk"])
    valleys.sort(key=lambda x: x["yogunluk"])
    return {"modul": "Mizan Alanı (Tecellî Topografyası)", "kappa": kappa,
            "sekineler": peaks[:6], "berzahlar": valleys[:6],
            "alan_ornek": [round(rho[i], 3) for i in range(0, n, max(1, n // 72))],
            "yontem": "ρ(θ)=Σ wᵢ·e^{κ·cos(θ−λᵢ)}; κ→0 Vahdet'e çöker, κ↑ kesret."}


# ============================================================================
# 4) ASABİYYE — spektral graf, λ₂ Fiedler  (CELL 2.11)
# ============================================================================
def _jacobi_eig(A: List[List[float]], iters: int = 100):
    n = len(A)
    A = [row[:] for row in A]
    V = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    for _ in range(iters):
        p, q, mx = 0, 1, 0.0
        for i in range(n):
            for j in range(i + 1, n):
                if abs(A[i][j]) > mx: mx, p, q = abs(A[i][j]), i, j
        if mx < 1e-10: break
        if abs(A[p][p] - A[q][q]) < 1e-14: th = math.pi / 4
        else: th = 0.5 * math.atan2(2 * A[p][q], A[p][p] - A[q][q])
        c, s = math.cos(th), math.sin(th)
        for k in range(n):
            apk, aqk = A[p][k], A[q][k]
            A[p][k], A[q][k] = c * apk + s * aqk, -s * apk + c * aqk
        for k in range(n):
            akp, akq = A[k][p], A[k][q]
            A[k][p], A[k][q] = c * akp + s * akq, -s * akp + c * akq
        for k in range(n):
            vkp, vkq = V[k][p], V[k][q]
            V[k][p], V[k][q] = c * vkp + s * vkq, -s * vkp + c * vkq
    eig = [(A[i][i], [V[k][i] for k in range(n)]) for i in range(n)]
    eig.sort(key=lambda e: e[0])
    return eig


def asabiyye(ch: NatalChart) -> dict:
    keys = CORE10
    n = len(keys)
    W = [[0.0] * n for _ in range(n)]
    kenarlar = []
    for i in range(n):
        for j in range(i + 1, n):
            d = sep(ch.bodies[keys[i]].lon, ch.bodies[keys[j]].lon)
            for _nm, _g, ang, orb, wgt, _maj in _ASPECTS:
                o = abs(d - ang)
                if o <= orb:
                    g = wgt * _orb_gucu(o, orb)
                    if g > 0:
                        W[i][j] = W[j][i] = g
                        kenarlar.append({"a": TR_NAME[keys[i]], "b": TR_NAME[keys[j]],
                                         "aci": _nm, "orb": round(o, 2),
                                         "guc": round(g, 3)})
                    break
    kenarlar.sort(key=lambda e: -e["guc"])
    deg = [sum(W[i]) for i in range(n)]
    Lap = [[(deg[i] if i == j else 0.0) - W[i][j] for j in range(n)]
           for i in range(n)]
    eig = _jacobi_eig(Lap)
    lam2, fied = eig[1][0], eig[1][1]

    # Bağlı bileşenleri bul. Graf kopuksa λ₂ MATEMATİKSEL OLARAK her zaman 0'dır
    # ve Fiedler vektörünün verdiği "kamplar" anlamsızdır. v2.0 bu durumda
    # rastgele bir bölünme bildiriyordu. Artık gerçek bloklar bildirilir ve
    # iç bağlılık EN BÜYÜK bileşen üzerinden ölçülür.
    komsu = {i: {j for j in range(n) if j != i and W[i][j] > 0} for i in range(n)}
    gorulen, bloklar = set(), []
    for i in range(n):
        if i in gorulen: continue
        yigin, blok = [i], []
        while yigin:
            x = yigin.pop()
            if x in gorulen: continue
            gorulen.add(x); blok.append(x)
            yigin.extend(komsu[x] - gorulen)
        bloklar.append(sorted(blok))
    bloklar.sort(key=len, reverse=True)
    kopuk = len(bloklar) > 1

    if kopuk and len(bloklar[0]) > 1:
        idx = bloklar[0]
        Wb = [[W[i][j] for j in idx] for i in idx]
        db = [sum(r) for r in Wb]
        Lb = [[(db[i] if i == j else 0.0) - Wb[i][j] for j in range(len(idx))]
              for i in range(len(idx))]
        eb = _jacobi_eig(Lb)
        lam2_ic = eb[1][0] if len(eb) > 1 else 0.0
        fied_ic = eb[1][1] if len(eb) > 1 else [0.0] * len(idx)
        kamp_a = [TR_NAME[keys[idx[i]]] for i in range(len(idx)) if fied_ic[i] >= 0]
        kamp_b = [TR_NAME[keys[idx[i]]] for i in range(len(idx)) if fied_ic[i] < 0]
        hinge_i = idx[min(range(len(idx)), key=lambda i: abs(fied_ic[i]))]
    else:
        lam2_ic = lam2
        kamp_a = [TR_NAME[keys[i]] for i in range(n) if fied[i] >= 0]
        kamp_b = [TR_NAME[keys[i]] for i in range(n) if fied[i] < 0]
        hinge_i = min(range(n), key=lambda i: abs(fied[i]))
    reis = keys[max(range(n), key=lambda i: deg[i])]
    yalniz = keys[min(range(n), key=lambda i: deg[i])]
    hinge = keys[hinge_i]
    yalnizlar = [TR_NAME[keys[i]] for i in range(n) if deg[i] <= 1e-12]
    return {"modul": "Asabiyye Matrisi (iç ictimâ')",
            "asabiyye_lambda2": round(lam2, 4),
            "ic_baglilik_lambda2": round(lam2_ic, 4),
            "yuzdelik": _asabiyye_yuzdelik(lam2_ic),
            "yorum": ("kopuk yapı — tek kabile yok; birbirine değmeyen bloklar var"
                      if kopuk else
                      "güçlü iç dayanışma — kabile tek yumruk"
                      if _asabiyye_yuzdelik(lam2_ic) >= 75 else
                      "orta bağlılık — hizip riski var"
                      if _asabiyye_yuzdelik(lam2_ic) >= 25 else
                      "zayıf asabiyye — iç fay hattı belirgin"),
            "reis": TR_NAME[reis], "yalniz": TR_NAME[yalniz],
            "yalnizlar": yalnizlar, "mentese": TR_NAME[hinge],
            "kenar_sayisi": len(kenarlar),
            "en_guclu_baglar": kenarlar[:5],
            "fay_hatti": {"kamp_A": kamp_a, "kamp_B": kamp_b,
                          "kapsam": "en büyük blok içi" if kopuk else "tüm harita"},
            "bloklar": [[TR_NAME[keys[i]] for i in blk] for blk in bloklar],
            "ada_sayisi": len(bloklar),
            "yontem": ("L=D−A; λ₂(L) Fiedler. Orblar Astro Pro v9.2.4 tablosuyla "
                       "aynı (8/8/7/7/5 + minörler), kenar gücü (1−sapma/orb)^1.35. "
                       "Graf kopuksa λ₂ daima 0'dır ve global Fiedler bölünmesi "
                       "anlamsızdır; o durumda bloklar gerçek yapı, iç bağlılık en "
                       "büyük blok üzerinden ölçülür. Mutlak λ₂ ölçeğe bağlı "
                       "olduğu için 400 haritalık referans dağılımdaki yüzdelik "
                       "konum bildirilir.")}


# ============================================================================
# 5) ARŞ EKSENİ — 3B düşey mizan  (CELL 2.12)
# ============================================================================
def ars_ekseni(ch: NatalChart) -> dict:
    vx = vy = vz = sw = 0.0
    rows = []
    for k in CORE10:
        b = ch.bodies[k]; w = NURANI_W[k]
        lam, bet = math.radians(b.lon), math.radians(b.lat)
        x, y, z = math.cos(bet) * math.cos(lam), math.cos(bet) * math.sin(lam), math.sin(bet)
        vx += w * x; vy += w * y; vz += w * z; sw += w
        rows.append((k, b.lat, w))
    vx, vy, vz = vx / sw, vy / sw, vz / sw
    tilt = math.degrees(math.atan2(vz, math.hypot(vx, vy)))
    cik = max(rows, key=lambda r: abs(r[1]) * r[2])
    north = [TR_NAME[k] for k, la, _ in rows if la > 0.5]
    south = [TR_NAME[k] for k, la, _ in rows if la < -0.5]
    lam_c = norm360(math.degrees(math.atan2(vy, vx)))
    return {"modul": "Arş Ekseni (düşey mizan)",
            "egim_derece": round(tilt, 3),
            "yon": "URÛC — merkez ekliptiğin kuzeyinde (yükseliş)" if tilt > 0
                   else "İNİŞ — merkez güneyde (tenezzül)",
            "omurga_boylami": fmt_lon(lam_c),
            "cikinti": {"cisim": TR_NAME[cik[0]], "enlem": round(cik[1], 2)},
            "kuzey_kampi": north, "guney_kampi": south,
            "yontem": "Gerçek 3B birim vektörler (β+λ); ağırlık merkezinin işaretli sapması."}


# ============================================================================
# 6) FELEK SAATİ — sinodik kafes  (CELL 2.14)
# ============================================================================
def _jd_bugun() -> float:
    return swe.julday(*dt.datetime.utcnow().timetuple()[:3], 0.0)


def _gercek_kavusum(ka: str, kb: str, ufuk_yil: float = 60.0) -> Optional[float]:
    """İki cismin bir sonraki gerçek kavuşumu — efemeris taraması + ikiye bölme."""
    faz = lambda jd: ((calc_lon(jd, ka) - calc_lon(jd, kb) + 180.0) % 360.0) - 180.0
    j0 = _jd_bugun()
    onceki, pj = faz(j0), j0
    for i in range(1, int(ufuk_yil * 36.5)):
        jd = j0 + i * 10.0
        cur = faz(jd)
        if onceki < 0 <= cur and abs(cur - onceki) < 90:
            lo, hi = pj, jd
            for _ in range(50):
                mid = (lo + hi) / 2
                if faz(mid) < 0: lo = mid
                else: hi = mid
            return (lo + hi) / 2
        onceki, pj = cur, jd
    return None


def felek_saati(ch: NatalChart, months: int = 24) -> dict:
    keys = CORE10
    clocks = []
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            vi, vj = MEAN_SPEED[keys[i]], MEAN_SPEED[keys[j]]
            dv = abs(vi - vj)
            if dv < 1e-6: continue
            P = 360.0 / dv
            # NOT: faz DOĞUM anından, takvim BUGÜNden ölçülür. v2.0'da ikisi
            # aynı alanda karışıyordu ve "sıradaki kavuşum" yanlış okunuyordu.
            dogum_faz = norm360(ch.bodies[keys[i]].lon - ch.bodies[keys[j]].lon)
            simdi_faz = norm360(calc_lon(_jd_bugun(), keys[i])
                                - calc_lon(_jd_bugun(), keys[j]))
            hizli, yavas = (keys[i], keys[j]) if vi > vj else (keys[j], keys[i])
            isaret = 1.0 if vi > vj else -1.0
            f_now = simdi_faz if isaret > 0 else norm360(-simdi_faz)
            clocks.append({"cift": f"{TR_NAME[keys[i]]}–{TR_NAME[keys[j]]}",
                           "periyot_yil": round(P / 365.25, 2),
                           "dogum_fazi": round(dogum_faz, 1),
                           "bugunku_faz": round(simdi_faz, 1),
                           "kavusuma_gun_bugunden": round(((360 - f_now) % 360) / dv, 0),
                           "karsita_gun_bugunden": round(((180 - f_now) % 360) / dv, 0)})
    clocks.sort(key=lambda c: -c["periyot_yil"])
    slow = clocks[:8]
    # En yavaş üç çiftin kavuşumunu GERÇEK efemerisle doğrula (ortalama hareket
    # 20 yıllık çevrimlerde yıllarca sapar; Kadim Lab ile çelişki bundan doğuyordu)
    for c in slow[:3]:
        try:
            ad_a, ad_b = c["cift"].split("–")
            ka = next(k for k in keys if TR_NAME[k] == ad_a)
            kb = next(k for k in keys if TR_NAME[k] == ad_b)
            jd = _gercek_kavusum(ka, kb)
            if jd:
                c["kavusum_efemeris"] = jd_to_iso(jd)[:10]
        except Exception:
            pass
    # Vuruş takvimi: her çift, yarım çevrimde bir (kavuşum → karşıt → kavuşum)
    # vurur. Tarihler BUGÜNden ölçülür; ağır çiftler daha yüksek ağırlık taşır.
    horizon_d = months * 30.44
    hist = [0.0] * months
    for c in clocks:
        yarim = c["periyot_yil"] * 365.25 / 2.0
        if yarim <= 0:
            continue
        agirlik = math.log1p(c["periyot_yil"])
        for anahtar in ("kavusuma_gun_bugunden", "karsita_gun_bugunden"):
            g = c[anahtar]
            adet = 0
            while g < horizon_d and adet < 500:
                ay = int(g / 30.44)
                if 0 <= ay < months:
                    hist[ay] += agirlik
                g += yarim
                adet += 1
    today = dt.date.today()
    beats = sorted(range(months), key=lambda m: -hist[m])[:5]
    takvim = [{"ay": (today + dt.timedelta(days=30.44 * m)).strftime("%Y-%m"),
               "yogunluk": round(hist[m], 2)} for m in sorted(beats)]
    # rezonant kilitler
    res = []
    for a in range(len(slow)):
        for b in range(a + 1, len(slow)):
            r = slow[a]["periyot_yil"] / max(slow[b]["periyot_yil"], 1e-9)
            for p_, q_ in ((1, 2), (2, 3), (1, 3), (3, 4), (2, 5)):
                if abs(r - p_ / q_) < 0.04 or abs(r - q_ / p_) < 0.04:
                    res.append({"a": slow[a]["cift"], "b": slow[b]["cift"],
                                "oran": f"{p_}:{q_}"}); break
    return {"modul": "Felek Saati (edvar / sinodik kafes)",
            "en_yavas_saatler": slow, "vurus_takvimi": takvim,
            "rezonant_kilitler": res[:6],
            "yontem": "Pᵢⱼ=360/|vᵢ−vⱼ|; faz=λᵢ−λⱼ; ortalama-hareket projeksiyonu."}


# ============================================================================
# 7) AYNA EKSENİ — antisya genellemesi  (CELL 2.15)
#    E(θ)=Σᵢ minⱼ d((2θ−λᵢ),λⱼ) → θ*=argmin
# ============================================================================
def ayna_ekseni(ch: NatalChart, step: float = 0.25) -> dict:
    lons = [ch.bodies[k].lon for k in CORE10]
    names = [TR_NAME[k] for k in CORE10]
    best_t, best_e, base = 0.0, math.inf, 0.0
    n = int(180 / step)
    es = []
    for i in range(n):
        th = i * step
        e = sum(min(sep(norm360(2 * th - li), lj) for lj in lons) for li in lons)
        es.append(e)
        if e < best_e: best_e, best_t = e, th
    base = sum(es) / len(es)
    sym = max(0.0, 1 - best_e / max(base, 1e-9))
    twins, on_axis = [], []
    for i, li in enumerate(lons):
        mir = norm360(2 * best_t - li)
        d_self = sep(mir, li)
        if d_self < 2.0:
            on_axis.append(names[i]); continue
        jbest = min(((sep(mir, lj), j) for j, lj in enumerate(lons) if j != i),
                    default=(999, -1))
        if jbest[0] < 2.0 and i < jbest[1]:
            twins.append({"a": names[i], "b": names[jbest[1]],
                          "sapma": round(jbest[0], 2)})
    return {"modul": "Ayna Ekseni (antisya genellemesi)",
            "eksen": {"lon": round(best_t, 2), "konum": fmt_lon(best_t),
                      "karsi": fmt_lon(norm360(best_t + 180))},
            "simetri_skoru": round(sym, 3),
            "gizli_ikizler": twins, "eksen_uzerindekiler": on_axis,
            "kanonik_sapma": {"antisya_90": round(sep(best_t, 90), 1),
                              "kontra_0": round(sep(best_t, 0), 1)},
            "yontem": "E(θ)=Σᵢ minⱼ d((2θ−λᵢ),λⱼ); θ*=argmin — haritanın KENDİ aynası."}


# ============================================================================
# 8) DEVR-İ DAİM — tecdid yılları  (CELL 2.16)
#    D(t)=Σ_{i<j} d(Δᵢⱼ(t), Δᵢⱼ(natal)) — desen iç geometrisi
# ============================================================================
def devri_daim(ch: NatalChart, years: int = 60) -> dict:
    keys = CORE10
    nat = {k: ch.bodies[k].lon for k in keys}
    nat_d = {(i, j): norm360(nat[keys[i]] - nat[keys[j]])
             for i in range(len(keys)) for j in range(i + 1, len(keys))}
    j0 = swe.julday(*dt.datetime.utcnow().timetuple()[:3], 0.0)
    series = []
    for m in range(0, years * 12, 3):  # 3 aylık örnekleme
        jd = j0 + m * 30.4375
        lons = {k: calc_lon(jd, k) for k in keys}
        D = sum(sep(norm360(lons[keys[i]] - lons[keys[j]]), nat_d[(i, j)])
                for i in range(len(keys)) for j in range(i + 1, len(keys)))
        series.append((jd, D))
    Dmax = max(d for _, d in series)
    mins = []
    for i in range(1, len(series) - 1):
        if series[i][1] < series[i - 1][1] and series[i][1] <= series[i + 1][1]:
            jd, D = series[i]
            mins.append({"tarih": jd_to_iso(jd)[:7],
                         "benzerlik": round(100 * (1 - D / Dmax), 1)})
    mins.sort(key=lambda x: -x["benzerlik"])
    top = sorted(mins[:6], key=lambda x: x["tarih"])
    buyuk = max(mins, key=lambda x: x["benzerlik"]) if mins else None
    return {"modul": "Devr-i Daim (kozmik tecdid yılları)",
            "tecdid_pencereleri": top, "buyuk_devir": buyuk,
            "yontem": "D(t)=Σ d(Δᵢⱼ(t),Δᵢⱼ(natal)); yerel min = Poincaré dönüşü."}


# ============================================================================
# 9) NOKTA-İ SÜVEYDA — dairesel medyan  (CELL 2.17)
# ============================================================================
def suveyda(ch: NatalChart) -> dict:
    lw = _lonw(ch)
    s, _cost = circular_median(lw)
    v, R = circular_mean_weighted(lw)
    gap = sep(s, v) if v is not None else None
    # çeken aykırı: Vahdet'i medyandan en çok koparan
    worst, wname = -1.0, None
    for (lon, w), k in zip(lw, CORE10):
        pull = w * sep(lon, s)
        if pull > worst: worst, wname = pull, TR_NAME[k]
    return {"modul": "Nokta-i Süveyda (sağlam kalp / dairesel medyan)",
            "suveyda": {"lon": round(s, 2), "konum": fmt_lon(s),
                        "ev": ch.house(s)},
            "kalp_kull_farki": round(gap, 2) if gap is not None else None,
            "ceken_aykiri": wname, "toplanmislik_R": round(R, 3),
            "yorum": ("kalp ile küll hizalı — iç tutarlılık yüksek" if (gap or 99) < 10
                      else "aykırı gezegen ortalamayı çekiyor; sağlam merkez medyandadır"),
            "yontem": "S=argmin Σw·d(φ,λ) — L1 medyan, aykırılara dirençli."}


# ============================================================================
# 10) MİZÂC PUSULASI — ahlât-ı erbaa dinamiği  (CELL 2.20)
#     x(t+1)=x+α(m₀−x)+β(f(t)−x) · Sû-i mizâc S(t) · İtidal=100−k·S
# ============================================================================
_HILT = ["Dem", "Safrâ", "Sevdâ", "Balgam"]          # hava ateş toprak su
_ELEM2HILT = {"Hava": 0, "Ateş": 1, "Toprak": 2, "Su": 3}
_PLANET_HILT = {  # gezegen tabiatı (sıcak-nem klasiği) → hılt dağılımı
    "Sun": (0.1, 0.7, 0.15, 0.05), "Moon": (0.1, 0.0, 0.1, 0.8),
    "Mercury": (0.5, 0.2, 0.2, 0.1), "Venus": (0.35, 0.05, 0.1, 0.5),
    "Mars": (0.05, 0.8, 0.1, 0.05), "Jupiter": (0.6, 0.2, 0.05, 0.15),
    "Saturn": (0.05, 0.05, 0.8, 0.1), "Uranus": (0.6, 0.1, 0.25, 0.05),
    "Neptune": (0.1, 0.05, 0.1, 0.75), "Pluto": (0.05, 0.3, 0.6, 0.05)}


def _mizac_vec(chart_lons: Dict[str, float]) -> List[float]:
    v = [0.0] * 4; sw = 0.0
    for k in CORE10:
        w = NURANI_W[k]
        ph = _PLANET_HILT[k]
        eh = [0.0] * 4
        eh[_ELEM2HILT[ELEMENT[sign_of(chart_lons[k])]]] = 1.0
        for i in range(4): v[i] += w * (0.5 * ph[i] + 0.5 * eh[i])
        sw += w
    return [x / sw for x in v]


def mizac_pusulasi(ch: NatalChart, months: int = 18,
                   alpha: float = 0.35, beta: float = 0.30) -> dict:
    m0 = _mizac_vec({k: ch.bodies[k].lon for k in CORE10})
    j0 = swe.julday(*dt.datetime.utcnow().timetuple()[:3], 0.0)
    x = m0[:]
    rows = []
    today = dt.date.today()
    for m in range(months):
        jd = j0 + m * 30.4375
        lons = {k: calc_lon(jd, k) for k in CORE10}
        f = _mizac_vec(lons)
        x = [x[i] + alpha * (m0[i] - x[i]) + beta * (f[i] - x[i]) for i in range(4)]
        S = math.sqrt(sum((x[i] - m0[i]) ** 2 for i in range(4)))
        itidal = max(0, min(100, round(100 - 320 * S)))
        rows.append({"ay": (today + dt.timedelta(days=30.44 * m)).strftime("%Y-%m"),
                     "itidal": itidal,
                     "durum": "BAKIM penceresi" if itidal < 55
                              else "ŞARJ penceresi" if itidal > 80 else "denge"})
    dom = max(range(4), key=lambda i: m0[i])
    return {"modul": "Mizâc Pusulası (ahlât-ı erbaa dinamiği)",
            "bunye_m0": {h: round(v, 3) for h, v in zip(_HILT, m0)},
            "baskin_hilt": _HILT[dom],
            "itidal_takvimi": rows,
            "bakim_aylari": [r["ay"] for r in rows if r["durum"].startswith("BAKIM")],
            "yontem": "x(t+1)=x+α(m₀−x)+β(f−x); Sû-i mizâc=|x−m₀|; İtidal=100−k·S."}


# ============================================================================
# 11) VUSLAT KAPILARI — ilişki faz-dönüş takvimi  (CELL 2.22)
# ============================================================================
def vuslat(ch: NatalChart, months: int = 18) -> dict:
    def L(k): return ch.bodies[k].lon
    sig = {"tutku": norm360(L("Venus") - L("Mars")),
           "sefkat": norm360(L("Venus") - L("Moon")),
           "kavusum": norm360(L("Sun") - L("Moon"))}
    pairs = {"tutku": ("Venus", "Mars"), "sefkat": ("Venus", "Moon"),
             "kavusum": ("Sun", "Moon")}
    j0 = swe.julday(*dt.datetime.utcnow().timetuple()[:3], 0.0)
    days = int(months * 30.44)
    natV, natMo, dsc = L("Venus"), L("Moon"), norm360(ch.asc + 180)
    gates = []
    for d in range(0, days):
        jd = j0 + d
        lons = {k: calc_lon(jd, k) for k in ("Sun", "Moon", "Venus", "Mars", "Jupiter", "Saturn")}
        for name, (a, b) in pairs.items():
            cur = norm360(lons[a] - lons[b])
            if sep(cur, sig[name]) < 1.0:
                score = 0.0; tags = []
                for tp in ("Venus", "Jupiter"):
                    for tgt in (natV, natMo, dsc):
                        dd = sep(lons[tp], tgt)
                        for ang in (0, 60, 120):
                            if abs(dd - ang) < 3: score += 1; tags.append(f"+{TR_NAME[tp]}")
                for tp in ("Saturn", "Mars"):
                    for tgt in (natV, natMo):
                        dd = sep(lons[tp], tgt)
                        for ang in (90, 180):
                            if abs(dd - ang) < 3: score -= 1; tags.append(f"−{TR_NAME[tp]}")
                gates.append({"tarih": jd_to_iso(jd)[:10], "faz": name,
                              "puan": score, "etiket": sorted(set(tags))})
    gates.sort(key=lambda g: (-g["puan"], g["tarih"]))
    best = gates[:8]
    hicran = [g for g in gates if g["puan"] <= -2][:4]
    return {"modul": "Vuslat Kapıları (ilişki faz-dönüş takvimi)",
            "bag_imzasi": {k: round(v, 1) for k, v in sig.items()},
            "vuslat_kapilari": sorted(best, key=lambda g: g["tarih"]),
            "hicran_pencereleri": hicran,
            "yontem": "Doğum faz açıları ♀–♂/♀–☽/☉–☽ gökte yeniden kurulduğunda; "
                      "destek ♀♃(0/60/120), sınama ♄♂(90/180), orb 3°."}


# ============================================================================
# 12) İKBAL MERDİVENİ — kariyer irtifa  (CELL 2.23)
#     I(t+1)=I+g·K−ρ(I−50) · mühür tarihleri
# ============================================================================
def ikbal(ch: NatalChart, months: int = 36) -> dict:
    targets = {"MC": ch.mc, "Sun": ch.bodies["Sun"].lon,
               "Saturn": ch.bodies["Saturn"].lon}
    r10 = RULER.get(sign_of(ch.cusps[9]))
    r10k = {v: k for k, v in TR_NAME.items()}.get(r10)
    if r10k: targets["Y10"] = ch.bodies[r10k].lon
    carriers = ("Saturn", "Jupiter", "Sun", "Mars", "Uranus", "Pluto")
    j0 = swe.julday(*dt.datetime.utcnow().timetuple()[:3], 0.0)
    I, g, rho = 50.0, 6.0, 0.10
    today = dt.date.today()
    curve, muhur = [], []
    for m in range(months):
        jd = j0 + m * 30.4375
        K = 0.0
        for c in carriers:
            lo = calc_lon(jd, c)
            for tk, tl in targets.items():
                d = sep(lo, tl)
                for ang, sgn in ((0, +1), (60, +1), (120, +1), (90, -1), (180, -1)):
                    o = abs(d - ang)
                    if o < 4:
                        K += sgn * math.exp(-(o ** 2) / 4.5) * (1.4 if c in ("Saturn", "Jupiter") else 1.0)
                        if o < 0.8 and c in ("Jupiter", "Saturn", "Pluto") and tk in ("MC", "Sun"):
                            muhur.append({"tarih": (today + dt.timedelta(days=30.44 * m)).strftime("%Y-%m"),
                                          "muhur": f"{TR_NAME[c]} {'☌△✶' if sgn>0 else '□☍'} natal {tk}"})
        I = I + g * K - rho * (I - 50)
        curve.append({"ay": (today + dt.timedelta(days=30.44 * m)).strftime("%Y-%m"),
                      "irtifa": round(I, 1)})
    zirve = max(curve, key=lambda r: r["irtifa"])
    cukur = min(curve, key=lambda r: r["irtifa"])
    return {"modul": "İkbal Merdiveni (kariyer irtifa dinamiği)",
            "irtifa_egrisi": curve, "zirve": zirve, "konsolidasyon": cukur,
            "muhur_tarihleri": muhur[:8],
            "yontem": "I(t+1)=I+g·K−ρ(I−50); imzalı Gauss katkılar → birikim."}


# ============================================================================
# 13) SAHİB-KIRÂN PENCERESİ — üst-sentez  (CELL 2.25)
# ============================================================================
def sahib_kiran(vus: dict, ikb: dict, fel: dict, miz: dict) -> dict:
    def _months(items, key):
        out = set()
        for it in items:
            t = it.get(key, "")
            if len(t) >= 7: out.add(t[:7])
        return out
    m_vus_p = _months(vus.get("vuslat_kapilari", []), "tarih")
    m_vus_n = _months(vus.get("hicran_pencereleri", []), "tarih")
    m_ikb = _months(ikb.get("muhur_tarihleri", []), "tarih") | {ikb.get("zirve", {}).get("ay", "")[:7]}
    m_fel = _months(fel.get("vurus_takvimi", []), "ay")
    m_miz_b = set(miz.get("bakim_aylari", []))
    m_miz_s = {r["ay"] for r in miz.get("itidal_takvimi", []) if r["durum"].startswith("ŞARJ")}
    all_m = m_vus_p | m_vus_n | m_ikb | m_fel | m_miz_b | m_miz_s
    wins = []
    for m in sorted(x for x in all_m if x):
        pos = sum([m in m_vus_p, m in m_ikb, m in m_fel, m in m_miz_s])
        neg = sum([m in m_vus_n, m in m_miz_b])
        tot = pos + neg
        if tot >= 2:
            tip = ("Kırân-ı Sa'deyn (çifte uğur)" if pos >= 2 and neg == 0 else
                   "Kırân-ı Nahseyn (çifte sınav)" if neg >= 2 and pos == 0 else
                   "Kırân-ı Mümtezic (karışık)")
            kay = [k for k, ok in (("Vuslat+", m in m_vus_p), ("Hicran", m in m_vus_n),
                                    ("İkbal", m in m_ikb), ("Felek", m in m_fel),
                                    ("Mizâc-Şarj", m in m_miz_s), ("Mizâc-Bakım", m in m_miz_b)) if ok]
            wins.append({"ay": m, "tip": tip, "kesisen": kay, "yogunluk": tot})
    wins.sort(key=lambda w: (-w["yogunluk"], w["ay"]))
    return {"modul": "Sahib-Kırân Penceresi (üçlü zaman mührü)",
            "pencereler": wins[:8],
            "yontem": "Kavuşan gezegenler değil, kavuşan TAKVİMLER: dört bağımsız "
                      "tekniğin vuruşları aynı aya düşerse o ay hayatın kırânıdır."}


# ============================================================================
# 14) NOKTA-İ İCÂBET — rıza rezonansı  (CELL 2.26)
#     A(λ)=Σ w·K(δ): △✶ +0.8 · □☍ −0.8 · ☌ tabiat · Gauss σ=3°
# ============================================================================
_BENEFIC = {"Sun": 0.4, "Moon": 0.5, "Mercury": 0.2, "Venus": 0.9, "Mars": -0.6,
            "Jupiter": 1.0, "Saturn": -0.8, "Uranus": -0.2, "Neptune": 0.1,
            "Pluto": -0.4}


def _uc_rafine(fn, lon0: float, buyuk: bool, pencere: float = 1.0) -> float:
    """
    Izgara üzerinde bulunan uç noktayı altın oran aramasıyla keskinleştirir.

    İcâbet ve Noksan 1°'lik ızgarada bulunuyordu; bu noktalar çark üzerinde
    gösterilip açı hesabına girdiği için tam sayı derecelere yapışmaları
    YAPAY tam açılar üretiyordu (ör. iki nokta arasında tastamam 120°).
    Rafine edilince bu yapaylık kalkar.
    """
    a, b = lon0 - pencere, lon0 + pencere
    gr = (math.sqrt(5) - 1) / 2
    c, d = b - gr * (b - a), a + gr * (b - a)
    isaret = 1.0 if buyuk else -1.0
    for _ in range(40):
        if isaret * fn(norm360(c)) > isaret * fn(norm360(d)):
            b, d = d, c
            c = b - gr * (b - a)
        else:
            a, c = c, d
            d = a + gr * (b - a)
    return norm360((a + b) / 2)


def icabet(ch: NatalChart, step: float = 1.0) -> dict:
    sig = 3.0
    n = int(360 / step)
    A = [0.0] * n
    for k in CORE10:
        lon, w = ch.bodies[k].lon, NURANI_W[k]
        for i in range(n):
            d = sep(i * step, lon)
            for ang, kv in ((120, 0.8), (60, 0.8), (90, -0.8), (180, -0.8),
                            (0, _BENEFIC[k])):
                o = d - ang
                A[i] += w * kv * math.exp(-(o ** 2) / (2 * sig ** 2))
    imax = max(range(n), key=lambda i: A[i])
    imin = min(range(n), key=lambda i: A[i])
    scale = max(abs(A[imax]), abs(A[imin]), 1e-9)

    def _A(lon: float) -> float:
        t = 0.0
        for k in CORE10:
            l2, w = ch.bodies[k].lon, NURANI_W[k]
            d = sep(lon, l2)
            for ang, kv in ((120, 0.8), (60, 0.8), (90, -0.8), (180, -0.8),
                            (0, _BENEFIC[k])):
                t += w * kv * math.exp(-((d - ang) ** 2) / (2 * sig ** 2))
        return t

    lon_max = _uc_rafine(_A, imax * step, True, step)
    lon_min = _uc_rafine(_A, imin * step, False, step)
    return {"modul": "Nokta-i İcâbet (rıza rezonans noktası)",
            "icabet": {"lon": round(lon_max, 3), "konum": fmt_lon(lon_max),
                       "ev": ch.house(lon_max),
                       "riza": round(100 * A[imax] / scale, 0),
                       "anlam": "kimsenin oturmadığı ama herkesin desteklediği derece — "
                                "niyet, lansman, isim koyma anteni"},
            "ibtila": {"lon": round(lon_min, 3), "konum": fmt_lon(lon_min),
                       "ev": ch.house(lon_min),
                       "anlam": "her şeyin kare bastığı sınanma derecesi"},
            "yontem": "A(λ)=Σw·K(δ); △✶+0.8, □☍−0.8, ☌ gezegen tabiatı; σ=3°."}


# ============================================================================
# 15) NOKTA-İ NOKSAN — tekmil açığı  (CELL 2.27)
#     P(λ)=Σ w·exp(−δ²/2σ²), σ=30° → min = Noksan
# ============================================================================
def noksan(ch: NatalChart, step: float = 1.0) -> dict:
    sig = 30.0
    n = int(360 / step)
    P = [sum(NURANI_W[k] * math.exp(-(sep(i * step, ch.bodies[k].lon) ** 2)
                                    / (2 * sig ** 2)) for k in CORE10)
         for i in range(n)]
    imin = min(range(n), key=lambda i: P[i])

    def _P(lon: float) -> float:
        return sum(NURANI_W[k] * math.exp(-(sep(lon, ch.bodies[k].lon) ** 2)
                                          / (2 * sig ** 2)) for k in CORE10)

    void = _uc_rafine(_P, imin * step, False, step)
    depth = 100 * (1 - _P(void) / max(P))
    elem = ELEMENT[sign_of(void)]
    d_ad = ("derin" if depth > 70 else "belirgin" if depth > 45 else "hafif")
    return {"modul": "Nokta-i Noksan (tekmil açığı)",
            "noksan": {"lon": round(void, 3), "konum": fmt_lon(void),
                       "ev": ch.house(void),
                       "unsur": elem, "derinlik": round(depth, 0),
                       "derinlik_ad": d_ad},
            "anlam": "hiçbir gezegenin ulaşamadığı en ıssız derece — doğal kaynağı "
                     "olmayan, irade ile inşa edilecek fakülte",
            "yontem": "P(λ)=Σw·exp(−δ²/2σ²), σ=30°; açı mantığı yok, saf varlık alanı."}


# ============================================================================
# 16) SEVK-İ FELEK v2 — akış mizanı  (CELL 2.30)
#     dR/dt=(C·Ċ+S·Ṡ)/(M·W) · faz portresi · d²V/dt² manevra
# ============================================================================
def sevk_felek(ch: NatalChart) -> dict:
    C = S = Cd = Sd = W = 0.0
    for k in CORE10:
        b = ch.bodies[k]; w = NURANI_W[k]
        r = math.radians(b.lon); v = math.radians(b.speed)
        C += w * math.cos(r); S += w * math.sin(r)
        Cd += -w * math.sin(r) * v; Sd += w * math.cos(r) * v
        W += w
    M = math.hypot(C, S)
    Vlon = norm360(math.degrees(math.atan2(S, C)))
    dR = (C * Cd + S * Sd) / (M * W) if M > 0 else 0.0
    dV = math.degrees((C * Sd - S * Cd) / (M * M)) if M > 0 else 0.0
    kb_ax = "BAST — gök toplanıyor (merkez güçleniyor)" if dR > 0 \
        else "KABZ — gök dağılıyor (merkez zayıflıyor)"
    if dV > 0 and dR > 0: kip = "sarmal içe — toplanarak dönüş"
    elif dV > 0 and dR < 0: kip = "sarmal dışa — dağılarak dönüş"
    elif abs(dV) > abs(dR) * 5: kip = "saf dönüş"
    else: kip = "saf nefes (genişleme/daralma)"
    dumenci = max(CORE10, key=lambda k: NURANI_W[k] * abs(ch.bodies[k].speed) / MEAN_SPEED[k])
    lenger = min(CORE10, key=lambda k: abs(ch.bodies[k].speed) / MEAN_SPEED[k])
    return {"modul": "Sevk-i Felek v2 (Akış Mizanı)",
            "merkez": {"lon": round(Vlon, 2), "konum": fmt_lon(Vlon)},
            "kabz_bast_ekseni": {"dR_dt": round(dR, 6), "kutup": kb_ax},
            "sevk_hizi_dV_dt": round(dV, 5),
            "faz_portresi": kip,
            "dumenci": TR_NAME[dumenci], "lenger": TR_NAME[lenger],
            "yontem": "dR/dt=(C·Ċ+S·Ṡ)/(M·W); konum+hızdan analitik, ek efemeris yok."}


# ============================================================================
# TOPLU ÇALIŞTIRICI
# ============================================================================
def run_all_deneme(ch: NatalChart, months: int = 18) -> dict:
    v = vuslat(ch, months)
    i = ikbal(ch, max(months, 24))
    f = felek_saati(ch, months)
    m = mizac_pusulasi(ch, months)
    return {
        "krn": krn(ch),
        "vahdet": vahdet(ch),
        "mizan": mizan(ch),
        "asabiyye": asabiyye(ch),
        "ars_ekseni": ars_ekseni(ch),
        "felek_saati": f,
        "ayna_ekseni": ayna_ekseni(ch),
        "devri_daim": devri_daim(ch),
        "suveyda": suveyda(ch),
        "mizac_pusulasi": m,
        "vuslat_kapilari": v,
        "ikbal_merdiveni": i,
        "sahib_kiran": sahib_kiran(v, i, f, m),
        "nokta_i_icabet": icabet(ch),
        "nokta_i_noksan": noksan(ch),
        "sevk_i_felek_v2": sevk_felek(ch),
    }
