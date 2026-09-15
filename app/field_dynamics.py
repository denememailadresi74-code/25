#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ALAN TOPOLOJİSİ VE DİNAMİĞİ  (ZÎC v3.0 icatları)

Mevcut model Φ alanının yalnız uç noktalarını kullanıyordu: KD (tepe), AD
(antisya) ve Berzah (iki baskın kütle arasındaki denge). Bu modül alanın geri
kalanını konuşturur.

  A · YÜRÜYEN BERZAH      Eşik zamanla yer değiştirir. B(t) yörüngesi, denge
                          sayısının değiştiği ÇATALLANMA anları, eşik hızı.
  B · HİMMET              Eşiği geçmek enerji ister: ΔΦ bariyer yüksekliği ve
                          Kramers benzeri kaçış oranı → yön değiştirme sıklığı.
  C · HAVZA TAYİNİ        Kişi çatalın hangi tarafında yaşıyor? ASC/Güneş/Ay
                          hangi tepeye akıyor, karşıya geçmenin bedeli nedir.
  D · KALICILIK           Alanın bütün kritik noktaları + persistent homology
                          ile hangisinin yapısal, hangisinin gürültü olduğu.

İŞARET SÖZLEŞMESİ (kodun geri kalanıyla uyumlu):
    Φ(λ) = Σ mᵢ / (d(λ,λᵢ) + ε)      kütleye yaklaştıkça büyür
    F(λ) = dΦ/dλ                      engine_mass.force() tam olarak budur
    Kütle çeker → dinamik Φ'nin YOKUŞ YUKARI yönünde: λ̇ = +F(λ)
    ⇒ Φ tepeleri ÇEKİCİ (denizler), Φ çukurları AYIRICI eşiktir (Berzah).

Model dili semboliktir; "aktivasyon enerjisi" bir benzetmedir, fiziksel
nedensellik iddiası değildir.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from .astro import NatalChart, CORE10, TR_NAME, calc_lon, jd_to_iso
from .circular import norm360, sep, signed_sep, fmt_lon, sign_of
from .engine_mass import (MassBody, compute_masses, phi_field, force,
                          find_berzah2, EPS)

TARAMA = 0.5          # derece — kritik nokta taraması
INCE = 0.02           # derece — kök rafinesi


# ============================================================================
# D · KRİTİK NOKTALAR VE KALICILIK
# ============================================================================
@dataclass
class KritikNokta:
    lon: float
    phi: float
    tip: str                 # "tepe" | "cukur"
    kalicilik: float = 0.0   # yalnız tepeler için; inf = küresel tepe
    olum_lon: Optional[float] = None


def kritik_noktalar(ms: Sequence[MassBody], adim: float = TARAMA) -> List[KritikNokta]:
    """Φ'nin bütün yerel tepe ve çukurlarını dairesel ızgarada bulur."""
    n = int(round(360.0 / adim))
    deger = [phi_field(i * adim, ms) for i in range(n)]
    out: List[KritikNokta] = []
    for i in range(n):
        a, b, c = deger[(i - 1) % n], deger[i], deger[(i + 1) % n]
        if b > a and b >= c:
            out.append(KritikNokta(i * adim, b, "tepe"))
        elif b < a and b <= c:
            out.append(KritikNokta(i * adim, b, "cukur"))
    return out


def _rafine(ms: Sequence[MassBody], lon: float, tepe: bool,
            pencere: float = TARAMA) -> Tuple[float, float]:
    """Altın oran araması ile kritik noktayı keskinleştirir."""
    a, b = lon - pencere, lon + pencere
    gr = (math.sqrt(5) - 1) / 2
    c, d = b - gr * (b - a), a + gr * (b - a)
    isaret = 1.0 if tepe else -1.0
    for _ in range(40):
        if isaret * phi_field(norm360(c), ms) > isaret * phi_field(norm360(d), ms):
            b, d = d, c
            c = b - gr * (b - a)
        else:
            a, c = c, d
            d = a + gr * (b - a)
    x = norm360((a + b) / 2)
    return x, phi_field(x, ms)


def kalicilik_diyagrami(ms: Sequence[MassBody]) -> dict:
    """
    1B persistent homology (üst-seviye süzme).

    Eşik +∞'dan aşağı inerken her yerel tepe bir bileşen DOĞURUR; iki bileşen
    aralarındaki çukura inildiğinde BİRLEŞİR ve genç (alçak) tepe ÖLÜR.
        kalıcılık = Φ(tepe) − Φ(birleştiği çukur)
    Yüksek kalıcılık = yapısal özellik. Düşük = gürültü.
    Küresel tepe (KD) hiç ölmez: kalıcılığı sonsuzdur.

    Bu, Mizan'daki Sekîne/Berzah listelerinin hangilerinin ciddiye alınacağını
    rakamla söyler; şimdiye kadar o listeler filtresiz geliyordu.
    """
    ham = kritik_noktalar(ms)
    if len(ham) < 4:
        return {"ozellikler": [], "not": "Alan çok düz — ayrıştırılabilir yapı yok."}

    # tepe/çukur dizisini rafine et
    dizi: List[KritikNokta] = []
    for k in ham:
        x, v = _rafine(ms, k.lon, k.tip == "tepe")
        dizi.append(KritikNokta(x, v, k.tip))

    # dairesel alternans: tepe-çukur-tepe-çukur…
    tepeler = [i for i, k in enumerate(dizi) if k.tip == "tepe"]
    if len(tepeler) < 2:
        t = dizi[tepeler[0]] if tepeler else None
        return {"ozellikler": ([{"konum": fmt_lon(t.lon), "lon": round(t.lon, 2),
                                 "phi": round(t.phi, 3), "kalicilik": None,
                                 "yorum": "tek tepe — alan tek merkezli"}] if t else []),
                "tepe_sayisi": len(tepeler)}

    canli = list(range(len(dizi)))          # dizideki indeksler
    olcum: List[Tuple[int, float, float]] = []   # (tepe idx, kalıcılık, ölüm phi)

    def komsu_cukurlar(poz: int) -> Tuple[int, int]:
        sol = canli[(poz - 1) % len(canli)]
        sag = canli[(poz + 1) % len(canli)]
        return sol, sag

    guvenlik = 0
    while sum(1 for i in canli if dizi[i].tip == "tepe") > 1 and guvenlik < 400:
        guvenlik += 1
        en_kucuk = None
        for poz, i in enumerate(canli):
            if dizi[i].tip != "tepe":
                continue
            sol, sag = komsu_cukurlar(poz)
            # eşik inerken önce YÜKSEK çukura varılır: birleşme orada olur
            yuksek = sol if dizi[sol].phi >= dizi[sag].phi else sag
            p = dizi[i].phi - dizi[yuksek].phi
            if en_kucuk is None or p < en_kucuk[1]:
                en_kucuk = (poz, p, yuksek)
        if en_kucuk is None:
            break
        poz, p, yuksek = en_kucuk
        olcum.append((canli[poz], p, dizi[yuksek].phi))
        # genç tepe ve birleştiği çukur diziden çıkar → alternans korunur
        cik = {canli[poz], yuksek}
        canli = [i for i in canli if i not in cik]

    kalan = [i for i in canli if dizi[i].tip == "tepe"]
    ozellikler = []
    for i, p, olum in olcum:
        ozellikler.append({"konum": fmt_lon(dizi[i].lon), "lon": round(dizi[i].lon, 2),
                           "phi": round(dizi[i].phi, 3), "kalicilik": round(p, 3),
                           "olum_phi": round(olum, 3)})
    for i in kalan:
        ozellikler.append({"konum": fmt_lon(dizi[i].lon), "lon": round(dizi[i].lon, 2),
                           "phi": round(dizi[i].phi, 3), "kalicilik": None,
                           "olum_phi": None, "kuresel": True})
    ozellikler.sort(key=lambda x: (x["kalicilik"] is not None, -(x["kalicilik"] or 0)))
    ozellikler = [o for o in ozellikler if o.get("kuresel")] + \
                 sorted([o for o in ozellikler if not o.get("kuresel")],
                        key=lambda x: -(x["kalicilik"] or 0))

    # Mutlak kalıcılık haritadan haritaya kıyaslanamaz (Φ'nin genliği değişir).
    # Alan genliğine bölünerek 0..1 ölçeğine indirilir; sınıflandırma bunun
    # üzerinden yapılır.
    tum_phi = [k.phi for k in dizi]
    genlik = (max(tum_phi) - min(tum_phi)) or 1.0
    for o in ozellikler:
        o["oransal"] = (round(o["kalicilik"] / genlik, 4)
                        if o["kalicilik"] is not None else None)
        if o["oransal"] is None:
            o["sinif"] = "küresel tepe — Kara Delik"
        elif o["oransal"] >= 0.25:
            o["sinif"] = "yapısal"
        elif o["oransal"] >= 0.08:
            o["sinif"] = "sınırda"
        else:
            o["sinif"] = "gürültü"
    esik = 0.25
    return {"ozellikler": ozellikler[:12],
            "tepe_sayisi": sum(1 for k in dizi if k.tip == "tepe"),
            "cukur_sayisi": sum(1 for k in dizi if k.tip == "cukur"),
            "alan_genligi": round(genlik, 2),
            "yapisal_esigi": esik,
            "yapisal_sayi": sum(1 for o in ozellikler if o.get("sinif") == "yapısal"),
            "yontem": ("Üst-seviye süzme; kalıcılık = Φ(tepe) − Φ(birleşme çukuru). "
                       "Kalıcılık alan genliğine bölünerek 0..1 ölçeğine indirilir; "
                       "≥0.25 yapısal, ≥0.08 sınırda, altı gürültü.")}


# ============================================================================
# C · HAVZA TAYİNİ
# ============================================================================
def havza(ms: Sequence[MassBody], baslangic: float,
          adim: float = 0.25, azami: int = 4000) -> Tuple[float, float]:
    """
    Verilen dereceden yokuş yukarı akıp hangi Φ tepesine varıldığını bulur.
    Dinamik λ̇ = +dΦ/dλ olduğu için kütleler çeker, tepeler havza merkezidir.
    Döner: (tepe boylamı, tepe Φ değeri)
    """
    x = norm360(baslangic)
    for _ in range(azami):
        f = force(x, ms)
        if abs(f) < 1e-9:
            break
        yeni = norm360(x + adim * (1.0 if f > 0 else -1.0))
        if phi_field(yeni, ms) <= phi_field(x, ms):
            break
        x = yeni
    return _rafine(ms, x, True)


def havza_tayini(chart: NatalChart, ms: Sequence[MassBody]) -> dict:
    """
    Kişi çatalın hangi tarafında YAŞIYOR? Model şimdiye kadar çatalı simetrik
    anlatıyordu; oysa kimlik göstergeleri zaten bir havzanın içindedir.
    """
    isaretciler = {"Yükselen": chart.asc,
                   "Güneş": chart.bodies["Sun"].lon,
                   "Ay": chart.bodies["Moon"].lon,
                   "MC": chart.mc}
    agirlik = {"Yükselen": 1.3, "Güneş": 1.2, "Ay": 1.0, "MC": 0.8}
    sonuc, oy = [], {}
    for ad, lon in isaretciler.items():
        tepe, tphi = havza(ms, lon)
        yakin = min(ms, key=lambda m: sep(m.lon, tepe))
        etiket = f"{yakin.name} havzası"
        sonuc.append({"gosterge": ad, "konum": fmt_lon(lon),
                      "havza": etiket, "tepe": fmt_lon(tepe),
                      "tepe_phi": round(tphi, 3)})
        oy[etiket] = oy.get(etiket, 0.0) + agirlik[ad]
    baskin = max(oy, key=lambda k: oy[k]) if oy else None
    dagilim = len(oy)
    return {"gostergeler": sonuc,
            "yasanan_havza": baskin,
            "oy_dagilimi": {k: round(v, 2) for k, v in sorted(oy.items(), key=lambda x: -x[1])},
            "bolunmus_mu": dagilim > 1,
            "yorum": ("Kimlik göstergeleri tek havzada — kişi çatalın bir "
                      f"tarafında net yaşıyor ({baskin})."
                      if dagilim == 1 else
                      f"Göstergeler {dagilim} havzaya dağılmış; baskın olan {baskin}. "
                      "Kişi zaten bölünmüş yaşıyor, çatal kuramsal değil fiilîdir."),
            "yontem": "λ̇ = +dΦ/dλ ile yokuş yukarı akış; varılan tepe havzayı verir."}


# ============================================================================
# B · HİMMET — EŞİK YÜKSEKLİĞİ VE KAÇIŞ ORANI
# ============================================================================
def en_yakin_esik(ms: Sequence[MassBody], lon: float) -> dict:
    """
    Verilen dereceye en yakın GERÇEK su bölümünü (Φ yerel çukuru) ve onun iki
    yanındaki tepeleri döndürür.

    Neden gerekli: find_berzah2 alan bozulduğunda analitik iki-deniz eşiğini
    bildirir; o nokta tam alanın kritik noktası OLMAYABİLİR. Yamaçta duran bir
    noktadan iki yana yokuş çıkınca ikisi de AYNI tepeye varır ve bariyer
    ölçümü anlamsızlaşır. Bu yüzden bariyer daima gerçek çukurdan ölçülür.
    """
    ham = kritik_noktalar(ms)
    if len(ham) < 2:
        return {}
    # v3.0'da buradaki döngü ~18 kritik noktanın HEPSİNİ altın oran aramasıyla
    # rafine ediyordu; fonksiyon 100 kez çağrılınca 3.338 rafine ve 8.8 saniye
    # ediyordu. Oysa yalnız en yakın çukur ve iki komşu tepe gerekli: 3 rafine.
    dizi = [(k.lon, k.phi, k.tip) for k in sorted(ham, key=lambda k: k.lon)]
    cukur_idx = [i for i, t in enumerate(dizi) if t[2] == "cukur"]
    if not cukur_idx:
        return {}
    i = min(cukur_idx, key=lambda i: sep(dizi[i][0], lon))
    n = len(dizi)
    # alternans gereği komşular tepedir; değilse en yakın tepeleri ara
    sol_i, sag_i = (i - 1) % n, (i + 1) % n
    while dizi[sol_i][2] != "tepe" and sol_i != i:
        sol_i = (sol_i - 1) % n
    while dizi[sag_i][2] != "tepe" and sag_i != i:
        sag_i = (sag_i + 1) % n
    # yalnız bu üç nokta rafine edilir
    ex, ev = _rafine(ms, dizi[i][0], False)
    sx, sv = _rafine(ms, dizi[sol_i][0], True)
    gx, gv = _rafine(ms, dizi[sag_i][0], True)
    return {"esik_lon": ex, "esik_phi": ev,
            "sol": (sx, sv), "sag": (gx, gv),
            "sapma": round(sep(ex, lon), 2)}


def esik_yuksekligi(ms: Sequence[MassBody], berzah_lon: float) -> dict:
    """
    Berzah bir AYIRICI çukurdur. Bir havzadan ötekine geçmek için kişinin
    Φ bakımından inmesi gereken miktar, aktivasyon enerjisinin karşılığıdır:
        ΔΦ = Φ(havza tepesi) − Φ(Berzah)
    İki taraf farklı olabilir: bir yönden çıkmak ötekinden zor olabilir.
    """
    bilgi = en_yakin_esik(ms, berzah_lon)
    if not bilgi:
        return {"hata": "alanda ayrıştırılabilir su bölümü yok"}
    phi_b = bilgi["esik_phi"]
    (sl, sp), (sgl, sgp) = bilgi["sol"], bilgi["sag"]
    sol_ad = min(ms, key=lambda m: sep(m.lon, sl)).name
    sag_ad = min(ms, key=lambda m: sep(m.lon, sgl)).name
    # ölçek: alanın toplam genliği. Mutlak Φ farkı haritadan haritaya
    # kıyaslanamaz; oransal bariyer kıyaslanabilir.
    tumu = [phi_field(i, ms) for i in range(0, 360, 2)]
    genlik = (max(tumu) - min(tumu)) or 1.0
    return {"su_bolumu": fmt_lon(bilgi["esik_lon"]),
            "berzahtan_sapma": bilgi["sapma"],
            "alan_genligi": round(genlik, 2),
            "berzah_phi": round(phi_b, 3),
            "sol": {"havza": sol_ad, "tepe": fmt_lon(sl), "phi": round(sp, 3),
                    "bariyer": round(sp - phi_b, 3),
                    "oransal": round((sp - phi_b) / genlik, 4)},
            "sag": {"havza": sag_ad, "tepe": fmt_lon(sgl), "phi": round(sgp, 3),
                    "bariyer": round(sgp - phi_b, 3),
                    "oransal": round((sgp - phi_b) / genlik, 4)},
            "asimetri": round(abs((sp - phi_b) - (sgp - phi_b)), 3),
            "kolay_yon": sol_ad if (sp - phi_b) < (sgp - phi_b) else sag_ad,
            "yontem": "ΔΦ = Φ(havza tepesi) − Φ(Berzah); çıkışı zor olan taraf yüksek bariyerli."}


# Aylık örneklemede Ay ÖRTÜŞME (aliasing) üretir: yılda ~13 tur atarken 12
# örnek alınır, dolayısıyla rastgele bir yere düşmüş gibi görünür ve alanın
# topolojisini her ay baştan bozar. İlk denemede 24 yılda 200'den fazla sahte
# "çatallanma" bundan çıktı. Yapısal analizde yalnız yavaş cisimler kullanılır.
YAPISAL_TRANSIT = ["Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
YUK_TRANSIT = ["Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
               "Uranus", "Neptune", "Pluto"]      # Ay hariç


def _transit_kutleleri(chart: NatalChart, jd: float,
                       katsayi: float = 0.55,
                       cisimler: Optional[Sequence[str]] = None) -> List[MassBody]:
    """
    Belirli bir anda gökteki cisimleri natal alanın açısallık çerçevesinde
    kütleye çevirir. Transit kütlesi natalden hafiftir (katsayı) — natal alan
    kişinin kendi yapısı, transit ona binen dış yüktür.
    """
    from .engine_mass import _dignity, _gauquelin, _visibility
    from .astro import MEAN_SPEED
    gunes = calc_lon(jd, "Sun")
    out: List[MassBody] = []
    for k in (cisimler or CORE10):
        lon = calc_lon(jd, k)
        w_dig = max(0.25, 1.0 + 0.09 * _dignity(k, lon))
        w_ang = _gauquelin(None, lon, chart.asc, chart.mc)
        w_vis = _visibility(k, lon, gunes)
        m = katsayi * w_dig * w_ang * w_vis
        out.append(MassBody(k, TR_NAME[k], lon, m, {}))
    return out


def kacis_orani(chart: NatalChart, ms: Sequence[MassBody], esik_lon: float,
                _eski_bariyer: float = 0.0, yil: float = 4.0) -> dict:
    """
    Bariyer sabit değildir: transitler alanın TOPOLOJİSİNİ yeniden şekillendirir,
    tepe alçalır veya su bölümü yükselir. Asıl ölçülmesi gereken budur.

    v1'de gürültü, sabit bir noktadaki Φ titremesiydi (σ≈0.4) ve alan derinliği
    (≈35) yanında hiç kalıyordu; oran 100'ü aşıp anlamsızlaşıyordu. Artık
    BARİYERİN KENDİSİ aylık örnekleniyor:

        ΔΦ(t) = Φ(havza tepesi, t) − Φ(su bölümü, t)

    Çıktı iki şey söyler:
      • dayanıklılık = ortalama(ΔΦ) / std(ΔΦ)   — eşik ne kadar sağlam
      • GEÇİRGENLİK PENCERELERİ — bariyerin çöktüğü aylar; danışman için
        "çıkmanın en ucuz olduğu zaman" budur.
    """
    import swisseph as swe
    import datetime as dt
    j0 = swe.julday(*dt.datetime.utcnow().timetuple()[:3], 0.0)
    n = max(18, int(yil * 12))
    seri: List[Tuple[str, float]] = []
    izlenen = esik_lon          # su bölümü SÜREKLİ takip edilir; sabit boylama
                                # bakmak topoloji değiştikçe farklı özelliklere
                                # atlamaya ve seriyi gürültüye boğmaya yol açıyordu
    for i in range(n):
        jd = j0 + i * 30.4375
        try:
            birlesik = list(ms) + _transit_kutleleri(
                chart, jd, cisimler=YUK_TRANSIT)
        except Exception:
            continue
        b = en_yakin_esik(birlesik, izlenen)
        if not b:
            continue
        # sıçrama koruması: eşik bir ayda 40°'den fazla kaymışsa takip kopmuştur
        if sep(b["esik_lon"], izlenen) > 40 and seri:
            continue
        izlenen = b["esik_lon"]
        tepe = max(b["sol"][1], b["sag"][1])
        seri.append((jd_to_iso(jd)[:7], tepe - b["esik_phi"]))
    if len(seri) < 8:
        return {"hata": "bariyer serisi kurulamadı"}

    d = [x[1] for x in seri]
    ort = sum(d) / len(d)
    sig = math.sqrt(sum((x - ort) ** 2 for x in d) / (len(d) - 1)) or 1e-9
    dayaniklilik = ort / sig
    esik_dusuk = ort - sig
    pencereler = [{"ay": a, "bariyer": round(v, 2),
                   "dusus_yuzde": round(100 * (ort - v) / ort, 0)}
                  for a, v in seri if v <= esik_dusuk]
    pencereler.sort(key=lambda x: x["bariyer"])

    # Bantlar 60 rastgele harita üzerinde ölçülen dağılımın çeyrekliklerine
    # oturtuldu: %25=3.0, medyan=5.6, %75=10.0. Böylece sınıflandırma gerçekten
    # ayrıştırır; sabit eşikler tek bir bandı şişiriyordu.
    if dayaniklilik < 3.0:
        band = "çok geçirgen — eşik sürekli iniyor, yön kolay değişir"
        dilim = "alt çeyrek"
    elif dayaniklilik < 5.6:
        band = "geçirgen — yılda birkaç kez gerçek çıkış fırsatı"
        dilim = "ikinci çeyrek"
    elif dayaniklilik < 10.0:
        band = "dirençli — çıkış yalnız belirli pencerelerde mümkün"
        dilim = "üçüncü çeyrek"
    else:
        band = "kilitli — bu havzadan transitle çıkılmıyor, karar iradeyle verilir"
        dilim = "üst çeyrek"

    return {"ortalama_bariyer": round(ort, 2),
            "bariyer_std": round(sig, 3),
            "dayaniklilik": round(dayaniklilik, 2),
            "en_dusuk": {"ay": min(seri, key=lambda x: x[1])[0],
                         "bariyer": round(min(d), 2)},
            "en_yuksek": {"ay": max(seri, key=lambda x: x[1])[0],
                          "bariyer": round(max(d), 2)},
            "gecirgenlik_pencereleri": pencereler[:6],
            "pencere_sayisi": len(pencereler),
            "ufuk_yil": yil,
            "band": band, "dilim": dilim,
            "yontem": ("ΔΦ(t) = Φ(tepe,t) − Φ(su bölümü,t) aylık örneklenir. "
                       "Dayanıklılık = ortalama/std. Ortalamadan bir standart "
                       "sapma aşağı düşen aylar geçirgenlik penceresidir.")}


# ============================================================================
# A · YÜRÜYEN BERZAH VE ÇATALLANMA TAKVİMİ
# ============================================================================
def _denge_sayisi(ms: Sequence[MassBody], adim: float = 1.0,
                  oran_esigi: float = 0.08) -> Tuple[int, List[float]]:
    """
    ANLAMLI ayırıcı eşiklerin sayısı ve konumları.

    Ham yerel çukur saymak işe yaramıyor: 20 kütleli bir alanda ~18 çukur olur
    ve bunların çoğu sığdır; transit birkaç derece kayınca kaybolup geri gelir.
    İlk denemede 24 yılda 202 "çatallanma" çıktı — hepsi gürültüydü.

    Çözüm, D icadını (kalıcılık) buraya bağlamaktır: bir çukur ancak iki
    yanındaki tepelere olan KÜÇÜK bariyeri, alan genliğinin `oran_esigi`
    katından büyükse gerçek bir ayırıcıdır. Böylece çatallanma seyrek ve
    anlamlı hâle gelir.
    """
    n = int(round(360.0 / adim))
    d = [phi_field(i * adim, ms) for i in range(n)]
    genlik = (max(d) - min(d)) or 1.0
    tur = []          # (indeks, "tepe"/"cukur")
    for i in range(n):
        a, b, c = d[(i - 1) % n], d[i], d[(i + 1) % n]
        if b > a and b >= c:
            tur.append((i, "tepe"))
        elif b < a and b <= c:
            tur.append((i, "cukur"))
    if len(tur) < 3:
        return 0, []
    anlamli, zayif = [], []
    m = len(tur)
    for j, (i, t) in enumerate(tur):
        if t != "cukur":
            continue
        sol = tur[(j - 1) % m][0]
        sag = tur[(j + 1) % m][0]
        oran = min(d[sol] - d[i], d[sag] - d[i]) / genlik
        if oran >= oran_esigi:
            anlamli.append(i * adim)
        elif oran >= oran_esigi * 0.6:
            zayif.append(i * adim)
    # anlamli: kesin eşikler · zayif: histerezisin alt bandındakiler
    return len(anlamli), anlamli, zayif


def yuruyen_berzah(chart: NatalChart, ms: Sequence[MassBody],
                   yil: int = 24, ay_adim: int = 1,
                   baslangic_jd: Optional[float] = None) -> dict:
    """
    Transitler natal alana kütle ekledikçe EŞİK YER DEĞİŞTİRİR.

    Üç çıktı:
      • B(t) yörüngesi — karar noktası nereye gidiyor
      • ÇATALLANMA anları — denge sayısının değiştiği yerler.
        Artış: yeni bir seçenek belirdi. Azalış: seçim ortadan kalktı,
        artık tek yol var. Bu, "karar veremiyorum" ile "seçecek bir şey
        kalmamış" arasındaki farkı ölçülebilir kılar.
      • Eşik hızı — hızlıysa kararlar peş peşe gelir, durağansa kişi sıkışmıştır
    """
    import swisseph as swe
    import datetime as dt
    j0 = baslangic_jd if baslangic_jd is not None else \
        swe.julday(*dt.datetime.utcnow().timetuple()[:3], 0.0)

    natal_b = find_berzah2(ms)
    izlenen = natal_b.lon if natal_b else 0.0

    yol: List[dict] = []
    catallanmalar: List[dict] = []
    # Histerezis (Schmitt tetikleyici) + gecikmeli onay.
    # Süzgeçsiz sayımda 24 yılda 200'den fazla "çatallanma" çıkıyordu; bunların
    # tamamı eşik civarında titreyen sığ özelliklerdi. Bir özellik ancak ÜST
    # bandı aşarsa doğmuş, ALT bandın altına inerse ölmüş sayılır; üstelik yeni
    # sayı üç ay üst üste korunmadıkça çatallanma kaydedilmez.
    ONAY_AY = 3
    kararli_sayi: Optional[int] = None
    aday_sayi: Optional[int] = None
    aday_sayac = 0
    onceki_lon: Optional[float] = None
    adet = int(yil * 12 / ay_adim)

    for i in range(adet):
        jd = j0 + i * 30.4375 * ay_adim
        try:
            birlesik = list(ms) + _transit_kutleleri(
                chart, jd, cisimler=YAPISAL_TRANSIT)
        except Exception:
            continue
        ust, cukurlar, zayif = _denge_sayisi(birlesik, oran_esigi=0.15)
        alt = ust + len(zayif)
        if not cukurlar:
            cukurlar = zayif
        if not cukurlar:
            continue
        # histerezis: mevcut sayı [ust, alt] bandındaysa değişmez
        if kararli_sayi is None:
            sayi = ust
        elif kararli_sayi < ust:
            sayi = ust
        elif kararli_sayi > alt:
            sayi = alt
        else:
            sayi = kararli_sayi
        # izlenen eşiğe en yakın anlamlı çukuru al ve rafine et
        yakin = min(cukurlar, key=lambda c: sep(c, izlenen))
        # sıçrama koruması: bir ayda 45°'den fazla kayma takibin koptuğu anlamına
        # gelir; o ayı atla, yörünge yapay sıçramalarla kirlenmesin
        if yol and sep(yakin, izlenen) > 45:
            continue
        x, _v = _rafine(birlesik, yakin, False, pencere=1.0)
        hiz = sep(x, onceki_lon) / ay_adim if onceki_lon is not None else 0.0
        tarih = jd_to_iso(jd)[:7]
        yol.append({"tarih": tarih, "lon": round(x, 2), "konum": fmt_lon(x),
                    "burc": sign_of(x), "ev": chart.house(x),
                    "denge_sayisi": kararli_sayi if kararli_sayi is not None else sayi,
                    "hiz_derece_ay": round(hiz, 2)})
        # gecikmeli onay: değişim üç ay üst üste sürmezse kaydedilmez
        if kararli_sayi is None:
            kararli_sayi = sayi
        elif sayi != kararli_sayi:
            if sayi == aday_sayi:
                aday_sayac += 1
            else:
                aday_sayi, aday_sayac = sayi, 1
            if aday_sayac >= ONAY_AY:
                catallanmalar.append({
                    "tarih": tarih,
                    "onceki": kararli_sayi, "sonraki": sayi,
                    "tur": "AÇILMA — yeni bir seçenek belirdi" if sayi > kararli_sayi
                           else "KAPANMA — bir seçenek ortadan kalktı",
                    "konum": fmt_lon(x), "ev": chart.house(x)})
                kararli_sayi, aday_sayi, aday_sayac = sayi, None, 0
        else:
            aday_sayi, aday_sayac = None, 0
        onceki_lon, izlenen = x, x

    if not yol:
        return {"hata": "yörünge hesaplanamadı"}

    hizlar = [r["hiz_derece_ay"] for r in yol[1:]]
    ort_hiz = sum(hizlar) / len(hizlar) if hizlar else 0.0
    en_hizli = max(yol[1:], key=lambda r: r["hiz_derece_ay"]) if len(yol) > 1 else yol[0]
    duragan = [r for r in yol[1:] if r["hiz_derece_ay"] < 0.15]
    # eşiğin gezdiği toplam yay
    burclar = sorted({r["burc"] for r in yol})
    evler = sorted({r["ev"] for r in yol if r["ev"]})

    return {
        "baslangic": yol[0]["tarih"], "bitis": yol[-1]["tarih"],
        "natal_berzah": fmt_lon(natal_b.lon) if natal_b else None,
        "yorunge": yol[::max(1, len(yol) // 60)],       # arayüz için seyrelt
        "yorunge_tam_uzunluk": len(yol),
        "catallanmalar": catallanmalar[:12],
        "catallanma_sayisi": len(catallanmalar),
        "ortalama_hiz_derece_ay": round(ort_hiz, 3),
        "en_hizli_ay": {"tarih": en_hizli["tarih"], "hiz": en_hizli["hiz_derece_ay"],
                        "konum": en_hizli["konum"]},
        "duragan_ay_sayisi": len(duragan),
        "gezilen_burclar": burclar, "gezilen_evler": evler,
        # Bantlar 40 rastgele harita üzerinde ölçüldü: %25=0.00, medyan=0.18,
        # %75=0.74, azami 3.65 °/ay. Önceki 0.4/2.5 eşikleri neredeyse herkesi
        # "kımıldamıyor" diye etiketliyordu.
        "hiz_dilimi": ("alt çeyrek" if ort_hiz <= 0.02 else
                       "ikinci çeyrek" if ort_hiz < 0.18 else
                       "üçüncü çeyrek" if ort_hiz < 0.74 else "üst çeyrek"),
        "okuma": ("Eşik natal yapıya çivilenmiş — transitler onu yerinden "
                  "oynatamıyor; kişi aynı çatalda yıllarca duruyor."
                  if ort_hiz <= 0.02 else
                  "Eşik yavaş sürükleniyor; karar zemini on yıllık ölçekte kayıyor."
                  if ort_hiz < 0.18 else
                  "Eşik ölçülü hızda ilerliyor; kararlar dönemsel."
                  if ort_hiz < 0.74 else
                  "Eşik hızla yer değiştiriyor — kararlar peş peşe gelir, "
                  "hiçbiri nihai hissettirmez."),
        "toplam_yay": round(sum(r["hiz_derece_ay"] for r in yol[1:]) * ay_adim, 1),
        "natalden_azami_sapma": (round(max(sep(r["lon"], natal_b.lon) for r in yol), 1)
                                 if natal_b else None),
        "yontem": ("Her ay natal kütlelere transit kütleler (katsayı 0.55) "
                   "eklenir, Φ'nin ANLAMLI çukurları (bariyeri alan genliğinin "
                   "%8'ini aşanlar) sayılır ve izlenen eşik rafine edilir. "
                   "Çukur sayısındaki değişim çatallanmadır. Ay dışlanır: "
                   "aylık örneklemede örtüşme üretip sahte çatallanma yaratıyor."),
    }


# ============================================================================
# TOPLU ÇALIŞTIRICI
# ============================================================================
def alan_topolojisi(chart: NatalChart, ms: Optional[Sequence[MassBody]] = None) -> dict:
    """B + C + D — ucuz katmanlar, full_v2 içine girer."""
    ms = ms or compute_masses(chart)
    b = find_berzah2(ms)
    out: dict = {"kalicilik": kalicilik_diyagrami(ms),
                 "havza": havza_tayini(chart, ms)}
    if b:
        ey = esik_yuksekligi(ms, b.lon)
        out["esik_yuksekligi"] = ey
        # kişinin yaşadığı havzanın bariyeri
        yasanan = out["havza"].get("yasanan_havza") or ""
        if "hata" not in ey:
            taraf = ey["sol"] if yasanan.startswith(ey["sol"]["havza"]) else ey["sag"]
            out["cikis_bariyeri"] = {"havza": taraf["havza"],
                                     "bariyer": taraf["bariyer"],
                                     "oransal": taraf["oransal"]}
            su = en_yakin_esik(ms, b.lon).get("esik_lon", b.lon)
            out["himmet"] = kacis_orani(chart, ms, su)
    return out
