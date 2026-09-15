#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BÖLÜM KAPSAMI — aynı bağlamdan aynı metni üretme sorununu keser.

v12.9'da otuz yedi ayrı düğme aynı yaklaşık 10 KB bağlamı modele taşıyordu.
Başlık değişiyor, veri değişmiyordu; modelin birbirine benzeyen paragraflar
üretmesi bu yüzden rastlantı değildi. Bu katman üç ayrı yerde ayrım yaratır:

1) Her yazı görevi yalnız kendi kanıt bloklarını görür.
2) Dokuz yazı görevinin biçimleri birbirinden kasıtlı olarak farklıdır.
3) Oturum defteri önceki metinlerin yalnız ilk iki cümlesini gösterir ve
   n-gram örtüşmesini ölçer; model aynı hikâyeyi başka başlıkla tekrar edemez.

Bu dosya astrolojik yeni hüküm üretmez. Yalnız mevcut hesapların hangi yazı
yüzeyine ne kadar taşınacağını düzenler.
"""
from __future__ import annotations

import re
import threading
import datetime as dt
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Tuple

TEKRAR_ESIGI = 0.28
DEFTER_OMRU = 3 * 60 * 60

ORTAK = {
    "GÜVEN NOTU",
    "SARSMA TESTİ",
    "NEREDE KONUŞ, NEREDE SUS",
    "ÇEKİRDEK YAKINSAMA",
}


@dataclass(frozen=True)
class Gorev:
    ad: str
    bicim: str
    kapsam: Tuple[str, ...]
    jeton: int
    kanit: Tuple[str, ...]


GOREVLER: Dict[str, Gorev] = {
    "hukum": Gorev(
        "Hüküm",
        "İlk satır tek cümlelik hüküm olsun ve 25 kelimeyi geçmesin. Ardından "
        "iki kısa paragraf yaz. Toplam 200 kelimeyi geçme; madde işareti kullanma.",
        ("KATMANLAR ARASI BAĞ", "DİRENÇ", "ÇELİŞKİLER", "ÇEKİRDEK", "YILIN HARİTASI", "YAŞ KATMANI"),
        900,
        ("hukum", "yakinsama", "sarsma", "cevaplanabilirlik", "solar_v2"),
    ),
    "guc": Gorev(
        "Ne iyi yapıyor",
        "Tam üç madde yaz. Her madde şu yapıda olsun: «güç — hangi ortamda çıkar — "
        "hangi ortamda körelir». Madde başına 40 kelimeyi geçme. Giriş ve kapanış yazma.",
        ("HUMAN DESIGN", "DENEME MODÜLLERİ", "KAPILAR", "KADİM KATMAN", "TEMAS AÇISI", "ALAN TOPOLOJİSİ"),
        650,
        ("berzah_v2", "human_design", "kabzbast_v1_m66_74", "yakinsama"),
    ),
    "gelisim": Gorev(
        "Neyi geliştirmeli",
        "İki kısa paragraf yaz ve sonuna tek satır «İlk adım: …» ekle. Toplam "
        "160 kelimeyi geçme. Eksikliği kişilik kusuru gibi anlatma.",
        ("ÇELİŞKİLER", "DURAKLAMA İZİ", "KAYIP ZAMAN", "KADİM KATMAN", "SÜKÛT"),
        760,
        ("celiskiler", "direnc", "duraklama_izi", "yas_katmani"),
    ),
    "iliski": Gorev(
        "İlişkilerde",
        "İlk üç satır TAM olarak «Hamle:», «Kendine verdiği ad:», "
        "«Karşıdakinin gördüğü:» ile başlasın. Ardından tek paragraf yaz; bu paragraf "
        "90 kelimeyi geçmesin.",
        ("SİNASTRİ", "DAVISON", "DEKLİNASYON SİNASTRİSİ", "KOMPOZİT", "ÇELİŞKİLER", "DİRENÇ",
         "HUDÛD-I FELEK", "TEMAS AÇISI"),
        720,
        ("sinastri", "davison", "deklinasyon", "kompozit", "direnc",
         "hudud_felek", "temas_acisi", "berzah_v2"),
    ),
    "is": Gorev(
        "İş ve rızık",
        "Paragraf yazma. «Şu koşulda üretken:» başlığı altında tam üç madde; "
        "«Emeğin boşa gittiği yer:» tek cümle; «Uyan alanlar:» 2-3 kısa öbek yaz. "
        "Meslek kehaneti ya da para vaadi verme.",
        ("KABZ/BAST", "ALAN TOPOLOJİSİ", "HAMLE PENCERESİ", "ŞİRÂ ÇEVRİMİ"),
        700,
        ("berzah_v2", "human_design", "hamle_penceresi", "alan_topolojisi"),
    ),
    "zaman": Gorev(
        "Önündeki dönem",
        "En fazla beş satır yaz. Her satır «‹ay› — ‹ne kolaylaşıyor› / "
        "‹ne kolaylaşmıyor›» biçiminde olsun. Paragraf ve kader dili kullanma.",
        ("HAMLE PENCERESİ", "BUGÜNKÜ GÖK", "KAYIP ZAMAN", "YAŞ KATMANI", "YILIN HARİTASI", "ŞİRÂ ÇEVRİMİ", "SÜKÛT", "ALGI EŞİĞİ", "DÖNÜŞ NOKTASI"),
        650,
        ("zaman_seridi", "hamle_penceresi", "yas_katmani", "solar_v2"),
    ),
    "yer": Gorev(
        "Yer",
        "İki kısa paragraf yaz: ilki bulunduğu yerin neyi öne çıkardığı, ikincisi "
        "alternatif yerin neyi değiştirebileceği. Her paragraf 70 kelimeyi geçmesin. "
        "Taşınmayı çözüm ya da garanti gibi sunma.",
        ("YER", "HUDÛD-I FELEK", "ŞİRÂ ÇEVRİMİ"),
        700,
        ("kartografi", "hudud_felek", "hudud_arz"),
    ),
    "soru": Gorev(
        "Danışan sorusu",
        "Soruyu tekrar etmeden en fazla iki paragraf yaz; toplam 170 kelimeyi geçme. "
        "Başlık kullanma. Veri zayıfsa bunu açıkça söyle ve boşluğu doldurma.",
        ("TEMAS AÇISI", "BUGÜNKÜ GÖK", "DÖNÜŞ NOKTASI", "ALGI EŞİĞİ", "KADİM KATMAN", "HUMAN DESIGN"),
        760,
        ("cevaplanabilirlik", "yakinsama", "sarsma"),
    ),
    "kapanis": Gorev(
        "Kapanış",
        "Tam iki cümle yaz. İlk cümle «Bu yıl: …» ile, ikinci cümle "
        "«Bu hafta: …» ile başlasın. Üçüncü cümle yazma.",
        ("YILIN HARİTASI", "BUGÜNKÜ GÖK", "HAMLE PENCERESİ", "TEMAS AÇISI", "DİRENÇ"),
        280,
        ("solar_v2", "hamle_penceresi", "temas_acisi", "direnc"),
    ),
}

# Eski kodlar korunur. Buradaki eşleme v1 düğmelerini ve kaydedilmiş oturumları
# kırmadan yeni dokuz yazı biçimine taşır. Ölçüm modülleri artık kendi başına
# yeni bir genel paragraf istemez; en yakın danışmanlık sorusuna hizmet eder.
ESLEME: Dict[str, str] = {
    "omurga": "hukum", "zaman_ozet": "zaman", "hareket_ozet": "gelisim", "guven": "gelisim",
    "hukum": "hukum", "halka": "hukum", "catal": "gelisim", "kutleler": "guc",
    "kenarlar": "gelisim", "kabzbast": "zaman", "deneme": "gelisim", "kadim": "gelisim",
    "hd": "guc", "hamveri": "gelisim", "sentez": "hukum", "formul": "gelisim",
    "duraklama": "gelisim", "donus": "zaman", "esik": "zaman", "sukut": "zaman",
    "lunasyon": "zaman", "celiski": "gelisim", "direnc": "gelisim", "sorular": "soru",
    "manevi": "gelisim", "kartografi": "yer", "hudud": "yer", "sira": "zaman",
    "topoloji": "is", "sinastri": "iliski", "alanbukmesi": "iliski", "davison": "iliski",
    "iliski_solar": "iliski", "deklinasyon": "iliski", "kompozit": "iliski",
    "kisi_a": "hukum", "kisi_b": "hukum",
    # v12.x'te arayüzde/raporda dolaşmış eski adlar
    "chrono": "zaman", "dinamik": "zaman", "sehir": "yer", "cevaplanabilirlik": "gelisim",
    "yakinsama": "hukum", "hamle": "zaman", "sarsma": "gelisim",
}

_BASLIK_RE = re.compile(r"(?m)^\[([^\]\n]+)\]\s*$")


def _norm_baslik(baslik: str) -> str:
    b = (baslik or "").strip().upper()
    # Baglam başlıklarında açıklama tireyle ekleniyor; kapsam isimleri temel
    # başlığı hedefler. Bu yüzden tam eşleşme yerine başlangıç karşılaştırması
    # kullanılır.
    return b


def _bloklara_ayir(baglam: str) -> Tuple[str, List[Tuple[str, str]]]:
    eslesmeler = list(_BASLIK_RE.finditer(baglam or ""))
    if not eslesmeler:
        return baglam or "", []
    onsoz = (baglam or "")[:eslesmeler[0].start()].rstrip()
    bloklar: List[Tuple[str, str]] = []
    for i, m in enumerate(eslesmeler):
        son = eslesmeler[i + 1].start() if i + 1 < len(eslesmeler) else len(baglam)
        bloklar.append((_norm_baslik(m.group(1)), (baglam or "")[m.start():son].rstrip()))
    return onsoz, bloklar


def _eslesen_baslik(baslik: str, istenen: Iterable[str]) -> bool:
    b = _norm_baslik(baslik)
    for x in istenen:
        n = _norm_baslik(x)
        if b == n or b.startswith(n + " —") or b.startswith(n + " -") or b.startswith(n + ":"):
            return True
    return False


def gorev_kodu(bolum: str) -> str | None:
    if bolum in GOREVLER:
        return bolum
    return ESLEME.get(bolum)


def _soru_kapsami(soru: str) -> Tuple[str, ...]:
    """Katalogdaki seçili soruyu gerçekten ihtiyaç duyduğu bloklara indirger.

    Soru genel okuma değildir. v13.2'de ``soru`` Hüküm'ün omurga bloklarını
    neredeyse bütünüyle tekrar gördüğü için kapsam ayrışması bozuluyordu.
    Burada ``sorular.py`` zaten var olan soru→katman bilgisinin kendisi kullanılır.
    """
    if not (soru or "").strip():
        return GOREVLER["soru"].kapsam
    try:
        from . import sorular as soru_mod
        q = " ".join((soru or "").lower().split())
        secilen = None
        for x in soru_mod.SORULAR:
            m = " ".join(x.metin.lower().split())
            if q == x.kod.lower() or q == m or (len(q) > 18 and (q in m or m in q)):
                secilen = x
                break
        if secilen is None:
            # Serbest soru katalogla birebir eşleşmiyorsa kategori sözcükleriyle
            # dar bir başlangıç seçilir; Hüküm omurgasına geri düşülmez.
            if any(k in q for k in ("iş", "kariyer", "para", "rızık", "meslek", "çalış")):
                return ("KABZ/BAST", "HAMLE PENCERESİ", "YAŞ KATMANI")
            if any(k in q for k in ("ilişki", "eş", "partner", "evlilik", "aşk")):
                return ("SİNASTRİ", "DAVISON", "DEKLİNASYON SİNASTRİSİ", "KOMPOZİT", "TEMAS AÇISI")
            if any(k in q for k in ("şehir", "ülke", "taşın", "yer", "nerede")):
                return ("YER", "HUDÛD-I FELEK")
            if any(k in q for k in ("ne zaman", "dönem", "ay", "yıl", "hafta")):
                return ("BUGÜNKÜ GÖK", "YILIN HARİTASI", "HAMLE PENCERESİ")
            return GOREVLER["soru"].kapsam
        esleme = {
            soru_mod.K_CEKIRDEK: ("ÇEKİRDEK",), soru_mod.K_KUTLE: ("ÇEKİRDEK",),
            soru_mod.K_TOPO: ("ALAN TOPOLOJİSİ",), soru_mod.K_HUDUD: ("HUDÛD-I FELEK",),
            soru_mod.K_SIRA: ("ŞİRÂ ÇEVRİMİ",), soru_mod.K_KABZ: ("KABZ/BAST",),
            soru_mod.K_KADIM: ("KADİM KATMAN",), soru_mod.K_HD: ("HUMAN DESIGN",),
            soru_mod.K_DENEME: ("DENEME MODÜLLERİ",), soru_mod.K_YER: ("YER",),
            soru_mod.K_TRANSIT: ("BUGÜNKÜ GÖK",), soru_mod.K_SOLAR: ("YILIN HARİTASI",),
            soru_mod.K_KAPI: ("KAPILAR",),
            soru_mod.K_ILISKI: ("SİNASTRİ", "DAVISON", "DEKLİNASYON SİNASTRİSİ", "KOMPOZİT"),
        }
        out: List[str] = []
        for katman in secilen.katmanlar:
            out.extend(esleme.get(katman, ()))
        # Soruya özel çerçeve dar kalmalı; ortak konuşma ayarları ``ORTAK`` ile
        # ayrıca eklenir. Hükmün KATMANLAR ARASI BAĞ omurgası burada yoktur.
        return tuple(dict.fromkeys(out)) or GOREVLER["soru"].kapsam
    except Exception:
        return GOREVLER["soru"].kapsam


def _cag(yas: int) -> str:
    # ai.py değişmeden kalmalı. Yaş satırını burada düzeltirken eşikler oradaki
    # 29/42/56 sınırlarıyla birebir tutulur; iki ayrı yaş sözlüğü oluşmaz.
    return ("kuruluş çağı (kimlik ve yön arayışı)" if yas < 29 else
            "inşa çağı (yapı kurma, sorumluluk)" if yas < 42 else
            "dönüm çağı (kurduğunu sorgulama)" if yas < 56 else
            "hasat çağı (aktarma, sadeleşme)")


def _referansla_onsoz(onsoz: str, referans: Dict[str, Any] | None) -> str:
    r = referans or {}
    kaynak = str(r.get("kaynak") or "bugun")
    if kaynak != "solar_return" or not r.get("yil"):
        satir = "REFERANS ANI: bugün. Yıllık katman kurulmadı."
        return (satir + ("\n" + onsoz if onsoz else "")).strip()

    yil = int(r["yil"])
    an = str(r.get("an") or "")
    try:
        tarih = dt.date.fromisoformat(an[:10]).strftime("%d.%m.%Y")
    except Exception:
        tarih = str(yil)
    satir = (f'REFERANS ANI: {yil} Solar Return ({tarih}). Yıllık katmanların tamamı bu ana göredir. '
             '"Bugünkü gök" bloğu varsa o BUGÜNÜ gösterir ve bu okumanın dışındadır.')

    # baglam_ozeti() yaşı bugünden hesaplıyor ve ai.py özellikle değişmeden
    # tutuluyor. Tarihsel SR okumasında bu tek satır düzeltilmezse model 2018
    # haritasına 2026 yaş tavsiyesi verir. Doğum yılı önsözden okunur.
    dm = re.search(r"Doğum anı \(UT\):\s*(\d{4})-", onsoz or "")
    if dm:
        dogum_yili = int(dm.group(1))
        ref_yas = yil - dogum_yili
        bugun_yas = dt.datetime.utcnow().year - dogum_yili
        yeni = (f"YAŞ: {ref_yas} — {_cag(ref_yas)}. Bu okuma {yil} Solar Return anına göredir; "
                f"kişinin bugünkü yaşı {bugun_yas}'dır. Tavsiyeyi {ref_yas} yaşına göre ölç.")
        onsoz = re.sub(r"(?m)^YAŞ:\s*\d+\s*—.*$", yeni, onsoz or "", count=1)
    return (satir + ("\n" + onsoz if onsoz else "")).strip()


def suz(baglam: str, bolum: str, soru: str = "",
        referans: Dict[str, Any] | None = None) -> str:
    """Tam bağlamdan ortak konuşma ayarı + göreve ait kanıt bloklarını tutar."""
    kod = gorev_kodu(bolum)
    if not kod:
        return baglam
    gorev = GOREVLER[kod]
    onsoz, bloklar = _bloklara_ayir(baglam)
    onsoz = _referansla_onsoz(onsoz, referans)
    if not bloklar:
        return onsoz or baglam
    kapsam = _soru_kapsami(soru) if kod == "soru" else gorev.kapsam
    istenen = set(ORTAK) | set(kapsam)
    secilen = [metin for baslik, metin in bloklar if _eslesen_baslik(baslik, istenen)]
    # Bütün blokları yanlış eşleyip veri kaybetmek, fazla bağlamdan daha tehlikeli.
    if not secilen:
        return baglam
    cikti = "\n\n".join(([onsoz] if onsoz else []) + secilen).strip()
    return cikti or baglam


def kapsam_ozeti(baglam: str, bolum: str, soru: str = "",
                  referans: Dict[str, Any] | None = None) -> Dict[str, Any]:
    dar = suz(baglam, bolum, soru, referans)
    _, tam_b = _bloklara_ayir(baglam)
    _, dar_b = _bloklara_ayir(dar)
    tam = len((baglam or "").encode("utf-8"))
    db = len((dar or "").encode("utf-8"))
    return {
        "tam_bayt": tam,
        "dar_bayt": db,
        "tam_blok": len(tam_b),
        "dar_blok": len(dar_b),
        "daralma": round(1 - (db / tam), 3) if tam else 0.0,
    }


# ---------------------------------------------------------------------------
# Oturum defteri
# ---------------------------------------------------------------------------
_KILIT = threading.RLock()
_DEFTER: Dict[str, Dict[str, Any]] = {}


def _temizle() -> None:
    simdi = time.time()
    for anahtar in list(_DEFTER):
        if simdi - float(_DEFTER[anahtar].get("ts", 0)) > DEFTER_OMRU:
            _DEFTER.pop(anahtar, None)


def yaz(anahtar: str, bolum: str, metin: str) -> None:
    if not anahtar or not metin:
        return
    with _KILIT:
        _temizle()
        kayit = _DEFTER.setdefault(anahtar, {"ts": time.time(), "metinler": []})
        kayit["ts"] = time.time()
        kayit["metinler"].append({"bolum": bolum, "metin": metin, "ts": time.time()})
        # Üç saatlik bir seansta yüzlerce üretim beklenmez; yine de bozuk istemci
        # belleği şişirmesin diye yakın geçmiş tutulur.
        kayit["metinler"] = kayit["metinler"][-40:]


def oku(anahtar: str, haric: str | None = None) -> List[Dict[str, str]]:
    if not anahtar:
        return []
    with _KILIT:
        _temizle()
        kayit = _DEFTER.get(anahtar) or {}
        return [dict(x) for x in (kayit.get("metinler") or []) if x.get("bolum") != haric]


def sil(anahtar: str) -> None:
    with _KILIT:
        _DEFTER.pop(anahtar, None)


def _ilk_iki_cumle(metin: str) -> str:
    parca = re.split(r"(?<=[.!?])\s+", (metin or "").strip())
    return " ".join([x.strip() for x in parca if x.strip()][:2])[:600]


def defter_talimati(anahtar: str, haric: str | None = None) -> str:
    kayitlar = oku(anahtar, haric)
    if not kayitlar:
        return ""
    satirlar = []
    for x in kayitlar[-8:]:
        kisa = _ilk_iki_cumle(x.get("metin", ""))
        if kisa:
            satirlar.append(f"- {x.get('bolum')}: {kisa}")
    if not satirlar:
        return ""
    return (
        "\n\n== DAHA ÖNCE SÖYLENENLER — TEKRAR ETME ==\n"
        "Bunlar yalnız tekrar kontrolü içindir. Cümlelerini, metaforlarını ve "
        "sonuçlarını kopyalama; yeni bölüm yalnız kendi kanıtından konuşsun.\n" + "\n".join(satirlar)
    )


def _gramlar(metin: str, n: int = 4) -> set[Tuple[str, ...]]:
    kel = re.findall(r"[\wçğıöşüâîû]+", (metin or "").lower(), flags=re.UNICODE)
    return {tuple(kel[i:i+n]) for i in range(len(kel) - n + 1)}


def tekrar_orani(a: str, b: str) -> float:
    A, B = _gramlar(a), _gramlar(b)
    # Kısa metinde bir ortak kalıp oranı anlamsız biçimde şişirir. En az sekiz
    # dört-gram yoksa tekrar ölçülmüş sayılmaz.
    if len(A) < 8 or len(B) < 8:
        return 0.0
    return len(A & B) / max(1, min(len(A), len(B)))


def en_yuksek_tekrar(metin: str, anahtar: str, haric: str | None = None,
                       hakem: Callable[[str, str], bool | None] | None = None) -> Dict[str, Any]:
    """Sözel kopya ile RABT iddia kararını birlikte ölçer.

    Sözel dört-gram aynen korunur. İddia tarafında ``tekrar`` en sert,
    ``bağla`` ikinci, ``farklı`` en hafif karardır. ``bağla`` yüksek bir
    semantik skor taşısa bile yeniden yazma nedeni değildir.
    """
    from .iddia import karsilastir
    agirlik = {"farklı": 0, "bağla": 1, "tekrar": 2}
    adaylar: List[Dict[str, Any]] = []
    for x in oku(anahtar, haric):
        onceki = x.get("metin", "")
        sozel = tekrar_orani(metin, onceki)
        idd = karsilastir(metin, onceki, None, sozel=sozel)
        karar = "tekrar" if sozel > TEKRAR_ESIGI else str(idd.get("karar") or "farklı")
        adaylar.append({"sozel": sozel, "iddia": float(idd.get("iddia", 0.0)),
                        "skor": float(idd.get("skor", 0.0)), "karar": karar,
                        "bolum": x.get("bolum"), "onceki": onceki,
                        "davranis_eslesmesi": idd.get("davranis_eslesmesi") or [],
                        "olculemedi": bool(idd.get("olculemedi"))})
    if not adaylar:
        return {"sozel": 0.0, "iddia": 0.0, "skor": 0.0, "oran": 0.0,
                "karar": "farklı", "benzer_bolum": None,
                "hakem_cagrildi": False, "davranis_eslesmesi": []}
    en = max(adaylar, key=lambda x: (agirlik.get(x["karar"], 0),
                                     max(float(x["sozel"]), float(x["skor"]))))
    oran = max(float(en["sozel"]), float(en["skor"]))
    return {"sozel": round(float(en["sozel"]), 3),
            "iddia": round(float(en["iddia"]), 3),
            "skor": round(float(en["skor"]), 3), "oran": round(oran, 3),
            "karar": en["karar"], "benzer_bolum": en["bolum"],
            "hakem_cagrildi": False,
            "davranis_eslesmesi": en.get("davranis_eslesmesi") or [],
            "olculemedi": bool(en.get("olculemedi"))}


def _rabt_talimati(anahtar: str, bolum: str) -> str:
    """Önceden geçen davranışı yeni alanda tekrar ettirmek yerine bağlatır."""
    if not anahtar:
        return ""
    try:
        from .iddia import iddialar
        gorulen: Dict[str, str] = {}
        for x in oku(anahtar, bolum)[-8:]:
            for davranis, _alan, _yon, _zaman in iddialar(x.get("metin", "")):
                if davranis != "genel" and davranis not in gorulen:
                    gorulen[davranis] = str(x.get("bolum") or "önceki")
        if not gorulen:
            return ""
        sat = [
            f"- {d}: Bu davranışı {b} bölümünde zaten anlattın. Burada baştan anlatma; "
            "aynı davranışın BU ALANDAKİ sonucunu söyle ve bağı tek cümleyle kur."
            for d, b in list(gorulen.items())[:8]
        ]
        return "\n\n== RABT — DAHA ÖNCE GÖRÜLEN DAVRANIŞLAR ==\n" + "\n".join(sat)
    except Exception:
        return ""

def sistem_eki(bolum: str, anahtar: str = "", sert: bool = False) -> str:
    kod = gorev_kodu(bolum) or bolum
    gorev = GOREVLER.get(kod)
    if not gorev:
        return ""
    # Ortak manifesto v13.2'de promptların çoğunu aynılaştırıyordu. Tek ortak
    # cümle güvenlik sınırını korur; asıl prompt ağırlığı görevin kendi biçiminde kalır.
    metin = (
        f"\n\n== {gorev.ad.upper()} ==\n"
        f"Biçim: {gorev.bicim}\n"
        "Yalnız verilen kanıttan konuş; ölçülmeyeni doldurma ve teknik hesap adı gösterme."
    )
    metin += defter_talimati(anahtar, bolum)
    metin += _rabt_talimati(anahtar, bolum)
    if sert:
        metin += "\nÖnceki deneme başka bölümün iddiasını tekrar etti; aynı sonuç zincirini kullanmadan yalnız bu görevin kanıtından yeniden kur."
    return metin


def kanitlar(bolum: str) -> List[str]:
    kod = gorev_kodu(bolum)
    g = GOREVLER.get(kod or "")
    return list(g.kanit) if g else []


def jeton(bolum: str, varsayilan: int = 900) -> int:
    kod = gorev_kodu(bolum)
    g = GOREVLER.get(kod or "")
    return g.jeton if g else varsayilan


def gorev_haritasi() -> Dict[str, Any]:
    return {
        k: {"ad": g.ad, "bicim": g.bicim, "kapsam": list(g.kapsam),
            "jeton": g.jeton, "kanit": list(g.kanit)}
        for k, g in GOREVLER.items()
    }
