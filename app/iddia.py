#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""İDDİA DEFTERİ — tekrarı sözcükten davranış çekirdeğine taşır.

v13.3 ``alan + yön + zaman`` üçlüsüyle parafrazı ölçmeye başladı; fakat aynı
davranış farklı hayat alanlarında anlatıldığında tekrar yine kaçıyordu. Daha
kötüsü, anahtar taşımayan iki cümle ``genel`` sınıfında çakışıp sahte 1.00
üretiyordu. v13.4 iddiayı ``davranış + alan + yön + zaman`` dörtlüsü yapar.

Davranış kapalı bir sözlüktür; astrolojik hüküm değildir. Yalnız danışmanlık
metninde tekrar eden davranış kalıbını işaretler. Ölçülemeyen ``genel`` sınıfı
tekrar kanıtı sayılmaz.
"""
from __future__ import annotations

import re
import time
import uuid
from typing import Any, Callable, Dict, Iterable, List, Set, Tuple

from . import depo

ASGARI_BRIER = 30
GRI_ALT = 0.20
GRI_UST = 0.45
GRI_KOK_ESIGI = 0.45

_ALAN = {
    "kimlik": ("kimlik", "benlik", "karar", "irade", "öz", "merkez"),
    "kaynak": ("para", "gelir", "kazanç", "kaynak", "rızık", "emek", "üret", "iş", "kariyer", "meslek"),
    "iliski": ("ilişki", "bağ", "eş", "partner", "sevgi", "güven", "yakınlık", "evlilik"),
    "kok": ("aile", "kök", "ev", "geçmiş", "anne", "baba", "çocukluk"),
    "yaratim": ("yaratı", "yetenek", "üretken", "ifade", "sahne", "görünür"),
    "duzen": ("düzen", "rutin", "soruml", "disiplin", "çalış", "sistem"),
    "anlam": ("anlam", "inanç", "öğren", "ufuk", "yol", "amaç"),
    "iceri": ("iç", "duygu", "kork", "öfke", "sezgi", "huzur", "kayg"),
    "cevre": ("çevre", "arkadaş", "topluluk", "ekip", "network", "sosyal"),
    "yer": ("şehir", "ülke", "yer", "taşın", "mekân", "lokasyon"),
    "zaman": ("zaman", "dönem", "ay", "hafta", "yıl", "şimdi", "yakın"),
}

# Aynı davranışın başka hayat alanı giysisiyle tekrar anlatılması danışmanın
# şikâyet ettiği asıl tekrar biçimidir. Liste kapalı tutulur; yeni bir davranış
# gözlenmeden sözlüğü genişletmek ölçeri yine "her şeyi bulan" hale getirir.
_DAVRANIS = {
    # (eşanlamlı, güven). Çekirdek fiiller 1.0'dır; tek başına davranış kurması
    # kolayca hayalet iddia üreten mecazlar 0.5 tutulur. İki ayrı dolaylı işaret
    # aynı davranışa yığılırsa toplam yine 1.0'a ulaşabilir.
    "bekleme": (("bekle", 1.0), ("duraksa", 1.0), ("geciktir", 1.0),
                 ("sabret", 1.0), ("zamanını bekle", 1.0),
                 ("hazır olana kadar", 1.0), ("olgunlaş", 0.5),
                 ("zamanı gel", 0.5)),
    "geri_cekilme": (("geri çek", 1.0), ("uzaklaş", 1.0), ("içe çek", 1.0),
                      ("mesafe koy", 1.0), ("kapan", 1.0), ("geri dur", 1.0)),
    "asiri_verme": (("fazla ver", 1.0), ("çok ver", 1.0), ("kendinden ver", 1.0),
                     ("yükünü al", 1.0), ("taşı", 0.5), ("fedakâr", 0.5)),
    "sinir_koyamama": (("sınır koyama", 1.0), ("hayır diyeme", 1.0),
                        ("sınır er", 1.0), ("fazla izin", 1.0),
                        ("kendini koruyama", 1.0)),
    "kontrol": (("kontrol", 1.0), ("yönetmeye çalış", 1.0), ("elde tut", 1.0),
                 ("denetle", 1.0), ("hakim ol", 1.0), ("hâkim ol", 1.0)),
    "kacinma": (("kaçın", 1.0), ("kaç", 1.0), ("yüzleşme", 0.5),
                 ("erteleyip uzak", 1.0), ("görmezden gel", 1.0)),
    "asiri_hazirlik": (("fazla hazırlan", 1.0), ("aşırı hazırlan", 1.0),
                        ("kusursuz hazır", 1.0), ("hazırlığı uzat", 1.0),
                        ("planı uzat", 1.0)),
    "ani_kopus": (("ani kop", 1.0), ("birden kes", 1.0), ("bir anda bırak", 1.0),
                   ("köprüleri yak", 1.0), ("sert kop", 1.0)),
    "onay_arama": (("onay ara", 1.0), ("takdir bekle", 1.0), ("beğenil", 1.0),
                    ("kabul gör", 1.0), ("başkasının onayı", 1.0)),
    "sessiz_direnc": (("sessiz diren", 1.0), ("içten diren", 1.0),
                       ("söylemeden karşı", 1.0), ("pasif diren", 1.0),
                       ("susup diren", 1.0)),
    "yuklenme": (("yüklen", 1.0), ("fazla soruml", 1.0), ("her şeyi üstlen", 1.0),
                  ("yükü al", 1.0), ("kendine yük", 1.0)),
    "erteleme": (("ertele", 1.0), ("sonraya bırak", 1.0), ("ötele", 1.0),
                  ("geciktir", 1.0), ("başlamayı uzat", 1.0)),
}

_OLUM = ("kolay", "güçlü", "destek", "açıl", "uygun", "verimli", "başar", "art", "iyi", "rahat")
_OLUMSUZ = ("zor", "tıkan", "kaybet", "azal", "çatış", "kriz", "kork", "kaçın", "yıpr", "gecik", "boşa")

_EKLER = (
    "lerinizden", "larınızdan", "lerindeki", "larındaki", "lerinin", "larının",
    "lerden", "lardan", "leri", "ları", "siniz", "sınız", "sunuz", "sünüz",
    "mekten", "maktan", "mesi", "ması", "iyor", "ıyor", "uyor", "üyor",
    "acak", "ecek", "miş", "mış", "muş", "müş", "dir", "dır", "dur", "dür",
    "dan", "den", "tan", "ten", "lik", "lık", "luk", "lük", "ci", "cı", "cu", "cü",
    "yorum", "yorsun", "yor", "arak", "erek", "ınca", "ince", "unca", "ünce",
)


def kok(kelime: str) -> str:
    k = re.sub(r"[^a-zçğıöşüâîû]", "", (kelime or "").lower())
    for ek in _EKLER:
        if len(k) - len(ek) >= 4 and k.endswith(ek):
            return k[:-len(ek)]
    return k


def _kokler(metin: str) -> Set[str]:
    return {kok(x) for x in re.findall(r"[A-Za-zÇĞİÖŞÜçğıöşüÂÎÛâîû]+", metin or "") if len(kok(x)) >= 3}


def _esles(token: str, aday: str) -> bool:
    a = kok(aday)
    if len(a) <= 3:
        return token == a
    return token.startswith(a) or a.startswith(token)


def _alan(secim: str) -> str:
    kl = _kokler(secim)
    ham = (secim or "").lower()
    puan: List[Tuple[int, int, str]] = []
    for sira, (alan, adaylar) in enumerate(_ALAN.items()):
        toplam = 0
        for x in kl:
            for y in adaylar:
                if y == "yakın":
                    uy = x == "yakın" or "yakın dönem" in ham or "yakın zaman" in ham
                else:
                    uy = _esles(x, y)
                if uy:
                    toplam += 1
                    break
        puan.append((toplam, -sira, alan))
    en = max(puan, default=(0, 0, "genel"))
    return en[2] if en[0] else "genel"


def _davranis(secim: str) -> str:
    kl = _kokler(secim)
    ham = (secim or "").lower()
    puan: List[Tuple[float, int, str]] = []
    for sira, (kod, adaylar) in enumerate(_DAVRANIS.items()):
        skor = 0.0
        gorulen: Set[str] = set()
        for aday, guven in adaylar:
            if " " in aday:
                uydu = aday in ham
            else:
                ak = kok(aday)
                uydu = any(_esles(x, ak) for x in kl)
            if uydu and aday not in gorulen:
                skor += float(guven)
                gorulen.add(aday)
        puan.append((skor, -sira, kod))
    en = max(puan, default=(0.0, 0, "genel"))
    # Tek bir dolaylı/mecazî işaret davranış iddiası kuramaz. v13.4'te
    # "olgunluk" sözcüğü tek başına bekleme üretip ilişki metnine hayalet
    # davranış ekliyordu; 1.0 eşiği bu yanlış pozitifliği sessiz bırakır.
    return en[2] if en[0] >= 1.0 else "genel"


def _yon(secim: str) -> str:
    m = secim.lower()
    if any(x in m for x in ("eğer", "ancak", "koşul", "şart", "olursa", "olduğunda", "yaparsa")):
        return "koşullu"
    if any(x in m for x in ("güç geliyor", "güç gelmek", "kolay değil", "mümkün değil")):
        return "olumsuz"
    kl = _kokler(secim)
    olum = {kok(x) for x in _OLUM}
    olumsuz = {kok(x) for x in _OLUMSUZ}
    ol = sum(1 for x in kl if any(_esles(x, y) for y in olum))
    neg = sum(1 for x in kl if any(_esles(x, y) for y in olumsuz))
    neg += int(" değil" in m or " yok" in m)
    if neg > ol:
        return "olumsuz"
    if ol > neg:
        return "olumlu"
    return "koşullu"


def _zaman(secim: str) -> str:
    m = secim.lower()
    if any(x in m for x in ("bu yıl", "solar", "yıllık", "202")):
        return "bu_yıl"
    if any(x in m for x in ("bu hafta", "yakın dönem", "yakın zamanda", "yakında", "önümüzdeki", "önündeki", "şimdi", "bu ay")):
        return "yakın_dönem"
    if any(x in m for x in ("geçmiş", "önceden", "çocukluk", "eskiden")):
        return "geçmiş"
    return "kalıcı"


def iddialar(metin: str) -> Set[Tuple[str, str, str, str]]:
    parcalar = [x.strip() for x in re.split(r"(?<=[.!?])\s+|\n+|\s+[;•]\s*", metin or "") if len(x.strip()) >= 10]
    return {(_davranis(x), _alan(x), _yon(x), _zaman(x)) for x in parcalar}


def _olculebilir(kume: Set[Tuple[str, str, str, str]]) -> Set[Tuple[str, str, str, str]]:
    return {x for x in kume if not (x[0] == "genel" and x[1] == "genel")}


def _eslesme_orani(a: Set[str], b: Set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / max(1, min(len(a), len(b)))


def _oran_detay(a: str, b: str) -> Dict[str, Any]:
    A0, B0 = iddialar(a), iddialar(b)
    A, B = _olculebilir(A0), _olculebilir(B0)
    if not A or not B:
        return {"oran": 0.0, "skor": 0.0, "olculemedi": True,
                "davranis_eslesmesi": [], "davranis": 0.0,
                "alan": 0.0, "zaman": 0.0}

    da = {x[0] for x in A if x[0] != "genel"}
    db = {x[0] for x in B if x[0] != "genel"}
    ortak_d = sorted(da & db)
    aa, ab = {x[1] for x in A}, {x[1] for x in B}
    za, zb = {x[3] for x in A}, {x[3] for x in B}
    davranis = _eslesme_orani(da, db)
    alan = _eslesme_orani(aa, ab)
    zaman = _eslesme_orani(za, zb)
    skor = 0.55 * davranis + 0.30 * alan + 0.15 * zaman
    return {"oran": skor, "skor": skor, "olculemedi": False,
            "davranis_eslesmesi": ortak_d, "davranis": davranis,
            "alan": alan, "zaman": zaman}

def oran(a: str, b: str) -> float:
    return float(_oran_detay(a, b)["oran"])


def kok_orani(a: str, b: str) -> float:
    A, B = _kokler(a), _kokler(b)
    if not A or not B:
        return 0.0
    return len(A & B) / max(1, len(A | B))


def karsilastir(a: str, b: str,
                hakem: Callable[[str, str], bool | None] | None = None,
                sozel: float = 0.0) -> Dict[str, Any]:
    """İki metni RABT kararıyla karşılaştırır.

    v13.4 aynı davranışı iki farklı alanda görünce doğrudan ``tekrar`` sayıyor
    ve modeli gereksiz yeniden yazmaya zorluyordu. RABT davranış, alan ve zaman
    eşleşmesini ayrı tartar: aynı davranış başka alanda görünürse çoğunlukla
    ``bağla`` olur; aynı iddia gerçekten yeniden kurulmuşsa ``tekrar`` kalır.
    """
    detay = _oran_detay(a, b)
    skor = float(detay.get("skor", 0.0))
    kr = kok_orani(a, b)
    if detay.get("olculemedi"):
        karar = "farklı"
    elif skor >= 0.85:
        karar = "tekrar"
    elif skor >= 0.55:
        karar = "bağla"
    else:
        karar = "farklı"
    # Eski hakem parametresi geriye uyum için imzada kalır; RABT'in eşikleri
    # mekanik ve ölçülebilir olduğundan artık gri bantta yeni model çağrısı
    # yaptırılmaz. Böylece "bağla" kararı maliyet düşürürken denetlenebilir kalır.
    return {
        "sozel": round(float(sozel), 3), "iddia": round(skor, 3),
        "skor": round(skor, 3), "kok": round(kr, 3), "karar": karar,
        "hakem_cagrildi": False, "hakem": None,
        "olculemedi": bool(detay.get("olculemedi")),
        "davranis_eslesmesi": detay.get("davranis_eslesmesi") or [],
        "bilesenler": {k: round(float(detay.get(k, 0.0)), 3)
                        for k in ("davranis", "alan", "zaman")},
    }

def kaydet(oturum: str, bolum: str, metin: str, mercek: str | None = None,
           referans_yil: int | None = None) -> List[str]:
    uc = sorted(_olculebilir(iddialar(metin)))
    if not uc:
        return []
    simdi = time.time()
    kayitlar: List[Dict[str, Any]] = []
    ids: List[str] = []
    for davranis, alan, yon, zaman in uc:
        kimlik = "id_" + uuid.uuid4().hex[:16]
        ids.append(kimlik)
        kayitlar.append({
            "id": kimlik, "ts": simdi, "oturum": oturum or "anon", "bolum": bolum,
            "mercek": mercek or bolum, "davranis": davranis, "alan": alan, "yon": yon,
            "zaman": zaman, "olasilik": 0.75, "sonuc": None, "isaret_ts": None,
            "referans_yil": int(referans_yil) if referans_yil is not None else None,
            "iddia_metin": f"{davranis} · {alan} · {yon} · {zaman}",
        })
    depo.iddia_ekle(kayitlar)
    return ids


def getir_ids(kimlikler: Iterable[str]) -> List[Dict[str, Any]]:
    aranan = set(kimlikler)
    if not aranan:
        return []
    return [{k: x.get(k) for k in ("id", "oturum", "ts", "bolum", "mercek", "davranis", "alan", "yon", "zaman", "sonuc", "referans_yil", "iddia_metin")}
            for x in depo.iddia_liste() if x.get("id") in aranan]


def isaretle(kimlik: str, sonuc: str | None) -> Dict[str, Any]:
    # Yanlış tıklamanın aylarca biriken Brier kaydını bozmasına izin verilmez;
    # ``geri_al`` sonucu NULL'a çevirir ve sayaçtan çıkarır.
    if sonuc in (None, "", "geri_al"):
        sonuc_db = None
    elif sonuc in ("tuttu", "tutmadı", "belirsiz"):
        sonuc_db = sonuc
    else:
        raise ValueError("sonuc tuttu / tutmadı / belirsiz / geri_al olmalı")
    kayit = depo.iddia_isaretle(kimlik, sonuc_db)
    if not kayit:
        raise KeyError(kimlik)
    return kayit


def gecmis(limit: int = 500) -> Dict[str, Any]:
    ls = depo.iddia_liste()[-max(1, min(int(limit), 2000)):]
    # Defter kişi adı taşımaz. UI'daki "iddia metni" yapılandırılmış iddianın
    # kanonik ifadesidir; tam danışman konuşmasını kalıcı diske taşımayız.
    kayitlar = [{k: x.get(k) for k in
                 ("id", "ts", "oturum", "bolum", "mercek", "iddia_metin",
                  "davranis", "alan", "yon", "zaman", "sonuc", "isaret_ts",
                  "referans_yil")}
                for x in ls]
    gecerli = sum(1 for x in ls if x.get("sonuc") in ("tuttu", "tutmadı"))
    return {"kayitlar": kayitlar, "toplam": len(ls), "brier_isaret": gecerli,
            "brier_kalan": max(0, ASGARI_BRIER - gecerli),
            "brier": brier_ozeti()}


def _brier(kayitlar: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    ks = [x for x in kayitlar if x.get("sonuc") in ("tuttu", "tutmadı")]
    if len(ks) < ASGARI_BRIER:
        return {"durum": "ornek_yetersiz", "n": len(ks), "asgari": ASGARI_BRIER, "brier": None}
    deger = sum((_p(x) - (1.0 if x.get("sonuc") == "tuttu" else 0.0)) ** 2 for x in ks) / len(ks)
    return {"durum": "olculdu", "n": len(ks), "brier": round(deger, 4)}


def _p(x: Dict[str, Any]) -> float:
    try:
        return max(0.0, min(1.0, float(x.get("olasilik", 0.75))))
    except Exception:
        return 0.75


def brier_ozeti() -> Dict[str, Any]:
    ls = depo.iddia_liste()
    bolumler = {k: _brier([x for x in ls if x.get("bolum") == k]) for k in sorted({x.get("bolum") for x in ls if x.get("bolum")})}
    mercekler = {k: _brier([x for x in ls if x.get("mercek") == k]) for k in sorted({x.get("mercek") for x in ls if x.get("mercek")})}
    return {"genel": _brier(ls), "bolumler": bolumler, "mercekler": mercekler,
            "depo": str(depo.db_yolu())}
