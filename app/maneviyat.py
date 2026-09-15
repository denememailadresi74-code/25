#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MÎZÂN-I EBVÂB — Kapıların Tartısı

İCADIN FİKRİ
    İskenderiye hermetizmi, Zohar kozmolojisi, Bûnî'nin harf ilmi, Picatrix'in
    tılsım vakti, İhvân-ı Safâ'nın sayı düzeni ve Porphyrios'un teürjisi —
    hepsi ayrı ayrı şunu söyler: kişinin kendine ait BİR KAPISI vardır.

    Ama hangi kapı olduğunda anlaşamazlar. Biri bir gezegen, biri bir harf,
    biri bir sefira, biri bir menzil gösterir.

    Bugüne kadar kimse bu altı kapıyı AYNI HARİTADAN bağımsız hesaplayıp
    birbirleriyle ne kadar ÖRTÜŞTÜĞÜNÜ ölçmedi. Bu modül tam olarak onu
    yapar ve tek bir sayı üretir:

        YAKINSAMA = altı gelenekten kaçı aynı gezegeni işaret ediyor

    Yüksek yakınsama, sembolik sistemin kendi içinde bu kişi için tutarlı
    olduğu anlamına gelir. Düşük yakınsama, gelenekler arasında gerçek bir
    ayrışma var demektir ve bu gizlenmez — asıl bilgi orada olabilir.

NE İDDİA EDİLMİYOR
    · Bu hesaplar bir şeyi MEYDANA GETİRMEZ. Tılsım, vefk ve saat
      hesapları sembolik/tefekkürî çerçevededir.
    · Yakınsama yüksek çıkması "doğru" demek değildir; altı gelenek de
      aynı geç antik kaynaklardan beslendiği için ORTAK KÖKENDEN gelen
      bir uyum olabilir. Modül bunu açıkça yazar.
    · Sağlık, para, ölüm konularında hüküm üretilmez.

TESLA HAKKINDA DÜRÜSTLÜK
    "Evreni anlamak istiyorsan enerji, frekans ve titreşim diye düşün"
    sözü Tesla'ya atfedilir ama doğrulanmış yazılarında bu cümle YOKTUR;
    yaygınlaşması 20. yüzyıl sonudur. Tesla gerçekten rezonansla çalıştı
    (Tesla bobini, mekanik osilatör) — bu tarihsel olarak doğrudur.
    "3-6-9" mistisizmi ise ona sonradan yakıştırılmıştır.
    Bu modüldeki frekans katmanı SEMBOLİK EŞLEMEDİR; fiziksel bir etki
    iddiası taşımaz ve öyle sunulmaz.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

import swisseph as swe

from .astro import (NatalChart, CORE10, TR_NAME, EPHFLAG, ensure_ephe,
                    jd_to_iso, BODY_IDS)
from .circular import norm360, sep, fmt_lon
from .engine_mass import compute_masses, find_kd_ad, MassBody

# ---------------------------------------------------------------- sabitler
KALDE_SIRASI = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]
GUN_SAHIBI = {6: "Saturn", 0: "Sun", 1: "Moon", 2: "Mars",
              3: "Mercury", 4: "Jupiter", 5: "Venus"}   # Pazartesi=0

# Zohar / Kabalistik: gezegen ↔ sefira (klasik eşleme)
SEFIRA = {
    "Saturn": ("Binah", "anlayış — sınırı ve biçimi kuran"),
    "Jupiter": ("Chesed", "lütuf — genişleten, veren"),
    "Mars": ("Geburah", "kudret — kesen, sınırlayan"),
    "Sun": ("Tiferet", "güzellik — dengeleyen merkez"),
    "Venus": ("Netzach", "zafer — süren, çeken"),
    "Mercury": ("Hod", "haşmet — ayıran, adlandıran"),
    "Moon": ("Yesod", "temel — aktaran, biriktiren"),
}

# Bûnî: harflerin unsur ve gezegen nispeti (Şemsü'l-Maârif düzeni)
HARF_UNSUR = {
    "ateş": "ا ه ط م ف ش ذ", "hava": "ب و ي ن ص ت ض",
    "su": "ج ز ك س ق ث ظ", "toprak": "د ح ل ع ر خ غ",
}
EBCED = {  # Türkçe harflerin ebced karşılığı (yaklaşık nispet)
    "a": 1, "e": 1, "b": 2, "c": 3, "ç": 3, "d": 4, "h": 5, "v": 6, "u": 6,
    "o": 6, "ö": 6, "ü": 6, "z": 7, "j": 7, "i": 10, "ı": 10, "y": 10,
    "k": 20, "g": 20, "ğ": 20, "l": 30, "m": 40, "n": 50, "s": 60,
    "ş": 300, "p": 2, "f": 80, "r": 200, "t": 400, "q": 100, "w": 6, "x": 600,
}

# İhvân-ı Safâ: sayı nispetleri
IHVAN_SAYI = {1: "birlik — kaynak", 2: "akıl — ilk ayrılık",
              3: "nefs — üçlü düzen", 4: "unsurlar — madde düzeni",
              5: "duyular — âlemle temas", 6: "tam sayı — denge",
              7: "gezegenler — zaman düzeni", 8: "felekler",
              9: "âlemler — tamamlanma", 0: "hiçlik — henüz açılmamış"}

# 28 menzil (Picatrix ve Bûnî ortak kullanır)
MENAZIL = [
    "Şeretân", "Butayn", "Süreyyâ", "Deberân", "Hak'a", "Hen'a", "Zirâ",
    "Nesre", "Tarf", "Cebhe", "Zübre", "Sarfe", "Avvâ", "Simâk", "Gafr",
    "Zübânâ", "İklîl", "Kalb", "Şevle", "Neâim", "Belde", "Sa'dü'z-zâbih",
    "Sa'dü bül'a", "Sa'dü's-suûd", "Sa'dü'l-ahbiye", "Fer'u'd-delvi'l-mukaddem",
    "Fer'u'd-delvi'l-muahhar", "Batnü'l-hût",
]


# ============================================================================
# VEFK — sihirli kare (Bûnî)
# ============================================================================
def vefk(n: int) -> dict:
    """
    n×n vefk üretir ve DOĞRULAR.

    Bûnî'de her gezegenin bir mertebesi vardır: Zühal 3, Müşteri 4, Merih 5,
    Şems 6, Zühre 7, Utârid 8, Kamer 9. Kare, her satır–sütun–köşegen
    toplamı eşit olacak biçimde kurulur; modül bunu HESAPLAYIP SINAR,
    tabloyu ezberden vermez.
    """
    n = max(3, min(9, int(n)))
    kare: List[List[int]] = [[0] * n for _ in range(n)]
    if n % 2 == 1:                                   # tek — Siyam yöntemi
        i, j = 0, n // 2
        for s in range(1, n * n + 1):
            kare[i][j] = s
            yi, yj = (i - 1) % n, (j + 1) % n
            if kare[yi][yj]:
                i = (i + 1) % n
            else:
                i, j = yi, yj
    elif n % 4 == 0:                                 # çift-çift — tümleyen
        s = 1
        for i in range(n):
            for j in range(n):
                kare[i][j] = s
                s += 1
        for i in range(n):
            for j in range(n):
                if (i % 4 in (0, 3)) == (j % 4 in (0, 3)):
                    kare[i][j] = n * n + 1 - kare[i][j]
    else:                                            # tek-çift — Strachey/LUX
        # Önceki uygulama yanlıştı ve doğrulama bunu yakaladı: 6×6 karede
        # satır/sütun/köşegen toplamları tutmuyordu. Doğru yöntem:
        # dört çeyreğe tek mertebeli kare yerleştirilir, sonra sol k sütun
        # A↔D, sağ k−1 sütun C↔B takas edilir; orta satırda sol takas bir
        # sütun sağa kaydırılır.
        m = n // 2
        k = (n - 2) // 4
        alt = vefk(m)["kare"]
        for i in range(m):
            for j in range(m):
                kare[i][j] = alt[i][j]                    # A · sol üst
                kare[i + m][j + m] = alt[i][j] + m * m    # B · sağ alt
                kare[i][j + m] = alt[i][j] + 2 * m * m    # C · sağ üst
                kare[i + m][j] = alt[i][j] + 3 * m * m    # D · sol alt
        orta = m // 2
        for i in range(m):
            sutunlar = (list(range(1, k + 1)) if i == orta
                        else list(range(0, k)))
            for j in sutunlar:
                kare[i][j], kare[i + m][j] = kare[i + m][j], kare[i][j]
        for i in range(m):
            for j in range(n - k + 1, n):
                kare[i][j], kare[i + m][j] = kare[i + m][j], kare[i][j]

    hedef = n * (n * n + 1) // 2
    satir = all(sum(r) == hedef for r in kare)
    sutun = all(sum(kare[i][j] for i in range(n)) == hedef for j in range(n))
    kose = (sum(kare[i][i] for i in range(n)) == hedef and
            sum(kare[i][n - 1 - i] for i in range(n)) == hedef)
    return {"mertebe": n, "kare": kare, "sabit_toplam": hedef,
            "dogrulama": {"satirlar": satir, "sutunlar": sutun,
                          "kosegenler": kose,
                          "gecerli": satir and sutun and kose},
            "not": ("Kare burada HESAPLANIR ve toplamları sınanır; hazır "
                    "tablodan alınmaz. Geçerli değilse öyle yazılır.")}


# ============================================================================
# GEZEGEN SAATLERİ (Picatrix, Bûnî)
# ============================================================================
def gezegen_saatleri(jd_gun: float, lat: float, lng: float) -> dict:
    """
    Gündüz ve gece on ikişer eşit olmayan saat; her birinin sahibi Kalde
    sırasıyla döner. Gün sahibi, gündüzün ilk saatinin sahibidir.

    Bu klasik hesaptır ve tamdır: doğuş–batış anları efemeristen alınır,
    saatler o araya bölünür. Mevsime göre saat uzunluğu değişir.
    """
    ensure_ephe()
    yer = (lng, lat, 0.0)
    try:
        _r, dog = swe.rise_trans(jd_gun - 0.5, swe.SUN, swe.CALC_RISE,
                                 yer, 0.0, 0.0, EPHFLAG)
        _r, bat = swe.rise_trans(dog[0], swe.SUN, swe.CALC_SET,
                                 yer, 0.0, 0.0, EPHFLAG)
        _r, dog2 = swe.rise_trans(bat[0], swe.SUN, swe.CALC_RISE,
                                  yer, 0.0, 0.0, EPHFLAG)
    except Exception as e:
        return {"hata": f"doğuş/batış hesaplanamadı: {e}"}
    dogus, batis, dogus2 = dog[0], bat[0], dog2[0]
    gunduz = (batis - dogus) / 12.0
    gece = (dogus2 - batis) / 12.0

    import datetime as dt
    gun_no = dt.datetime.utcfromtimestamp(
        (dogus - 2440587.5) * 86400).weekday()
    sahip = GUN_SAHIBI[gun_no]
    bas = KALDE_SIRASI.index(sahip)

    saatler = []
    for i in range(24):
        s = KALDE_SIRASI[(bas + i) % 7]
        if i < 12:
            b, e = dogus + i * gunduz, dogus + (i + 1) * gunduz
            tur = "gündüz"
        else:
            b, e = batis + (i - 12) * gece, batis + (i - 11) * gece
            tur = "gece"
        saatler.append({"sira": i + 1, "tur": tur, "sahip": TR_NAME[s],
                        "kod": s, "baslangic": jd_to_iso(b),
                        "bitis": jd_to_iso(e), "_b": b, "_e": e})
    return {"gun_sahibi": TR_NAME[sahip], "gun_sahibi_kod": sahip,
            "dogus": jd_to_iso(dogus), "batis": jd_to_iso(batis),
            "gunduz_saat_dk": round(gunduz * 1440, 1),
            "gece_saat_dk": round(gece * 1440, 1),
            "saatler": saatler,
            "yontem": ("Doğuş–batış arası 12 eşit olmayan saate bölünür. "
                       "Gün sahibi gündüzün ilk saatini tutar, sonrakiler "
                       "Kalde sırasıyla döner (Zühal→Müşteri→Merih→Şems→"
                       "Zühre→Utârid→Kamer).")}


def sonraki_saat(saatler: dict, kod: str,
                 simdi_jd: Optional[float] = None) -> Optional[dict]:
    """Belirli bir gezegenin bugünkü ilk uygun saati."""
    import datetime as dt
    if "hata" in saatler:
        return None
    if simdi_jd is None:
        u = dt.datetime.utcnow()
        simdi_jd = swe.julday(u.year, u.month, u.day,
                              u.hour + u.minute / 60.0)
    for s in saatler["saatler"]:
        if s["kod"] == kod and s["_e"] > simdi_jd:
            return {k: v for k, v in s.items() if not k.startswith("_")}
    for s in saatler["saatler"]:
        if s["kod"] == kod:
            return {k: v for k, v in s.items() if not k.startswith("_")}
    return None


# ============================================================================
# ALTI KAPI — her gelenek bağımsız hesaplanır
# ============================================================================
KLASIK_YEDI = ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn")


def _klasik(ms: Sequence[MassBody]) -> List[MassBody]:
    """
    Altı geleneğin hepsi 1781 ÖNCESİDİR: Uranüs, Neptün ve Plüton
    bilinmiyordu. Dolayısıyla hiçbirinin bu cisimler için kapısı yoktur.
    Hesap klasik yedi ile sınırlandırılır — yoksa Kabalistik katmanda
    sefira boş kalıyordu (doğrulamada görüldü).
    """
    adlar = {TR_NAME[k] for k in KLASIK_YEDI}
    yedi = [m for m in ms if m.name in adlar]
    return yedi or list(ms)


def _baskin(ms: Sequence[MassBody]) -> MassBody:
    return max(_klasik(ms), key=lambda m: m.abs_mass)


def kapi_hermetik(chart: NatalChart, ms: Sequence[MassBody]) -> dict:
    """
    İskenderiye hermetizmi: "yukarıdaki gibi aşağıdaki".
    Kapı, haritanın en ağır cismidir — alanda en çok yer kaplayan.
    """
    b = _baskin(ms)
    kod = next((k for k in CORE10 if TR_NAME[k] == b.name), "Sun")
    return {"gelenek": "Hermetik (İskenderiye)", "kapi": b.name, "kod": kod,
            "dayanak": f"Alanda en ağır cisim ({b.abs_mass:.2f}).",
            "anlam": ("Hermetik anlayışta kişinin kapısı, kendisinde en çok "
                      "yer tutan yandır: en görünür olan değil, en çok "
                      "çeken.")}


def kapi_kabalistik(chart: NatalChart, ms: Sequence[MassBody]) -> dict:
    """
    Zohar kozmolojisi: sefirot dengesi. Kapı, en dolu sefiranın gezegenidir;
    en boş olan ise 'eksik kanal' olarak ayrıca verilir.
    """
    sirali = sorted(_klasik(ms), key=lambda m: -m.abs_mass)
    dolu = sirali[0]
    bos = sirali[-1]
    kod = next((k for k in CORE10 if TR_NAME[k] == dolu.name), "Sun")
    bkod = next((k for k in CORE10 if TR_NAME[k] == bos.name), "Moon")
    sd = SEFIRA.get(kod, ("—", ""))
    sb = SEFIRA.get(bkod, ("—", ""))
    return {"gelenek": "Kabalistik (Zohar)", "kapi": dolu.name, "kod": kod,
            "sefira": sd[0], "sefira_anlam": sd[1],
            "eksik_kanal": {"cisim": bos.name, "sefira": sb[0],
                            "anlam": sb[1]},
            "dayanak": f"En dolu kanal {sd[0]}, en boş {sb[0]}.",
            "anlam": ("Zohar'da akış yukarıdan aşağı iner ve bir kanalda "
                      "tıkanır. Dolu olan kapıdır; boş olan çalışılacak "
                      "yerdir.")}


def kapi_buni(chart: NatalChart, ms: Sequence[MassBody],
              isim: str = "") -> dict:
    """
    Bûnî / harf ilmi: ismin ebced toplamı ve yükselen derecesinin harfi.
    İsim verilmezse yalnız yükselenden türetilir.
    """
    toplam = sum(EBCED.get(c, 0) for c in (isim or "").lower())
    # yükselenin harf nispeti: 28 harf, 12 burç → derece bazlı bölüm
    harf_no = int((chart.asc % 360) / (360 / 28)) % 28
    unsurlar = list(HARF_UNSUR.keys())
    unsur = unsurlar[harf_no % 4]
    # ebced toplamı 7'ye indirgenip gezegene bağlanır (Kalde sırası)
    if toplam:
        kok = toplam % 7
        kod = KALDE_SIRASI[kok]
    else:
        kod = KALDE_SIRASI[harf_no % 7]
    return {"gelenek": "Bûnî · harf ilmi", "kapi": TR_NAME[kod], "kod": kod,
            "ebced_toplam": toplam or None,
            "menzil_harfi": harf_no + 1, "unsur": unsur,
            "vefk_mertebesi": 3 + (KALDE_SIRASI.index(kod)),
            "dayanak": (f"İsmin ebced toplamı {toplam}" if toplam else
                        f"Yükselen derecesinin harf nispeti ({harf_no + 1}.)"),
            "anlam": ("Harf ilminde kapı, adın sayısıdır. İsim verilmediğinde "
                      "yükselenin harfi kullanılır — daha zayıf bir dayanak "
                      "olduğu için burada belirtilir.")}


def kapi_picatrix(chart: NatalChart) -> dict:
    """
    Picatrix: Ay'ın menzili tılsımın vaktini belirler. Kapı, o menzilin
    sırasına düşen gezegendir.
    """
    ay = chart.bodies["Moon"].lon
    m = int(ay / (360 / 28)) % 28
    kod = KALDE_SIRASI[m % 7]
    return {"gelenek": "Picatrix · menâzil", "kapi": TR_NAME[kod], "kod": kod,
            "menzil_no": m + 1, "menzil": MENAZIL[m],
            "ay_konumu": fmt_lon(ay),
            "dayanak": f"Ay {m + 1}. menzilde ({MENAZIL[m]}).",
            "anlam": ("Picatrix'te iş, Ay'ın menziline göre vakitlenir. "
                      "Menzil ne olduğunu değil, NE ZAMAN olacağını söyler.")}


def kapi_ihvan(chart: NatalChart, ms: Sequence[MassBody]) -> dict:
    """
    İhvân-ı Safâ: sayı düzeni. Kapı, alandaki cisim dağılımının indirgenmiş
    sayısına karşılık gelir.
    """
    agir = [m for m in _klasik(ms) if m.abs_mass > 0]
    s = int(sum(m.abs_mass for m in agir) * 10) % 10
    kod = KALDE_SIRASI[s % 7]
    return {"gelenek": "İhvân-ı Safâ · sayı", "kapi": TR_NAME[kod], "kod": kod,
            "sayi": s, "sayi_anlam": IHVAN_SAYI.get(s, "—"),
            "dayanak": f"Alan toplamının indirgenmiş sayısı {s}.",
            "anlam": ("İhvân'da âlem sayılarla katmanlanır: 1 kaynak, 4 "
                      "unsur, 7 gezegen, 12 burç. Kişinin sayısı hangi "
                      "katmanda durduğunu söyler.")}


def kapi_porphyrios(chart: NatalChart, ms: Sequence[MassBody]) -> dict:
    """
    Yeni Platoncu teürji: yükseliş üç mertebededir — maddî, nefsî, aklî.
    Kapı, köşelere en yakın cisimdir (teürjide temas köşeden olur).
    """
    koseler = [chart.asc, chart.mc, (chart.asc + 180) % 360,
               (chart.mc + 180) % 360]
    en_yakin = min(_klasik(ms), key=lambda m: min(sep(m.lon, k) for k in koseler))
    d = min(sep(en_yakin.lon, k) for k in koseler)
    kod = next((k for k in CORE10 if TR_NAME[k] == en_yakin.name), "Sun")
    mertebe = ("aklî — doğrudan temas" if d < 3 else
               "nefsî — dolaylı temas" if d < 10 else
               "maddî — temas uzak")
    return {"gelenek": "Porphyrios · teürji", "kapi": en_yakin.name,
            "kod": kod, "kose_uzakligi": round(d, 2), "mertebe": mertebe,
            "dayanak": f"Köşeye en yakın cisim, {d:.1f}° uzaklıkta.",
            "anlam": ("Teürjide yükseliş köşeden başlar: ufuk ve meridyen "
                      "âlemle temas noktalarıdır. Temas yakınsa iş "
                      "doğrudan, uzaksa dolaylıdır.")}


# ============================================================================
# YAKINSAMA — icadın çıktısı
# ============================================================================
def mizan_i_ebvab(chart: NatalChart, isim: str = "",
                  ms: Optional[Sequence[MassBody]] = None) -> dict:
    """Altı geleneği bağımsız hesaplar ve örtüşmelerini ölçer."""
    ms = list(ms or compute_masses(chart))
    kapilar = [
        kapi_hermetik(chart, ms),
        kapi_kabalistik(chart, ms),
        kapi_buni(chart, ms, isim),
        kapi_picatrix(chart),
        kapi_ihvan(chart, ms),
        kapi_porphyrios(chart, ms),
    ]
    sayim: Dict[str, int] = {}
    for k in kapilar:
        sayim[k["kod"]] = sayim.get(k["kod"], 0) + 1
    en = max(sayim.items(), key=lambda x: x[1])
    oran = en[1] / len(kapilar)

    if en[1] >= 4:
        hukum = (f"Güçlü yakınsama: altı gelenekten {en[1]}'i aynı kapıyı "
                 f"({TR_NAME[en[0]]}) işaret ediyor.")
    elif en[1] == 3:
        hukum = (f"Kısmî yakınsama: {en[1]} gelenek {TR_NAME[en[0]]} diyor, "
                 "kalanı dağınık.")
    elif en[1] == 2:
        hukum = ("Zayıf yakınsama: en fazla iki gelenek örtüşüyor. Bu "
                 "haritada sistemler ayrışıyor.")
    else:
        hukum = ("Yakınsama YOK: altı gelenek altı ayrı kapı gösteriyor. "
                 "Bu bir hata değil — bu haritada sembolik sistemler "
                 "birbirini doğrulamıyor demektir.")

    return {
        "modul": "MÎZÂN-I EBVÂB — altı geleneğin kapı ölçümü",
        "kapilar": kapilar,
        "dagilim": {TR_NAME[k]: v for k, v in
                    sorted(sayim.items(), key=lambda x: -x[1])},
        "yakinsama": {"kapi": TR_NAME[en[0]], "kod": en[0],
                      "kac_gelenek": en[1], "toplam": len(kapilar),
                      "oran": round(oran, 3)},
        "hukum": hukum,
        "kapsam": ("Altı gelenek de 1781 öncesidir; Uranüs, Neptün ve "
                   "Plüton hesaba KATILMAZ çünkü hiçbirinde karşılıkları "
                   "yoktur. Modern gezegenleri zorla eşlemek geleneği "
                   "bozar."),
        "uyari": ("Yüksek yakınsama 'doğru' demek DEĞİLDİR. Altı gelenek de "
                  "büyük ölçüde aynı geç antik kaynaklardan beslenir; uyum "
                  "ortak kökenden geliyor olabilir. Ölçülen şey gerçeklik "
                  "değil, sistemin kendi içindeki tutarlılığıdır."),
    }


def manevi_katman(chart: NatalChart, isim: str = "",
                  lat: Optional[float] = None,
                  lng: Optional[float] = None) -> dict:
    """Spiritüel çalışmalar katmanının tamamı."""
    import datetime as dt
    ms = compute_masses(chart)
    mz = mizan_i_ebvab(chart, isim, ms)
    kod = mz["yakinsama"]["kod"]

    # amel vakti: yakınsayan gezegenin bugünkü saati
    la = chart.lat if lat is None else lat
    lo = chart.lng if lng is None else lng
    u = dt.datetime.utcnow()
    bugun = swe.julday(u.year, u.month, u.day, 12.0)
    sa = gezegen_saatleri(bugun, la, lo)
    vakit = sonraki_saat(sa, kod) if "hata" not in sa else None

    mertebe = 3 + KALDE_SIRASI.index(kod)
    return {
        "mizan": mz,
        "gezegen_saatleri": {k: v for k, v in sa.items() if k != "saatler"}
        if "hata" not in sa else sa,
        "bugunun_saatleri": (sa.get("saatler") or [])[:24]
        if "hata" not in sa else [],
        "amel_vakti": vakit,
        "vefk": vefk(mertebe),
        "cerceve": (
            "Bu katman sembolik ve tefekkürî bir çerçevededir. Hesaplar "
            "(gezegen saatleri, menziller, vefk toplamları) tamdır ve "
            "doğrulanır; ANLAMLARI ise geleneğin dilidir, fiziksel bir "
            "nedensellik iddiası taşımaz."),
        "tesla_notu": (
            "\"Evreni anlamak istiyorsan enerji, frekans, titreşim diye "
            "düşün\" sözü Tesla'ya atfedilir ama doğrulanmış yazılarında "
            "bu cümle YOKTUR. Tesla gerçekten rezonansla çalıştı; '3-6-9' "
            "mistisizmi ise ona sonradan yakıştırılmıştır. Bu ayrımı "
            "bilerek kullanmak, bilmeden kullanmaktan güçlüdür."),
    }
