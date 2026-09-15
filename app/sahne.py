#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ZÎC v2 SAHNE API — dar bağlam, defter ve parça parça belge üretimi.

v13.3 iki üretim yolunu aynı kanıt/iddia motorunda birleştirir: yeni Sahne ve eski
``/api/v1/chat-bolum``. Böylece misafir portalının eski AI düğmeleri tam
bağlama dönmez; v1 yanıt sözleşmesi korunurken kapsam ve tekrar denetimi de
çalışır.

Belge tek istekte sekiz bölüm üretmez. Başlatma bağlamı bir kez hesaplar ve
önbelleğe koyar; istemci bölümleri tek tek ister. Bu, ters vekil zaman aşımını
ve aynı ``baglam_ozeti`` hesabının sekiz kez tekrarlanmasını önler.
"""
from __future__ import annotations

import json
import threading
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from . import ai as ai_mod
from . import oturum as oturum_mod
from . import sorular
from .kapsam import (
    ESLEME, GOREVLER, TEKRAR_ESIGI, en_yuksek_tekrar, gorev_haritasi,
    gorev_kodu, jeton, kanitlar, kapsam_ozeti, sil, sistem_eki, suz, yaz,
)
from .tanik import sahit_agi
from . import ayar as ayar_mod
from . import iddia as iddia_mod
from . import isnad as isnad_mod
from . import hasv as hasv_mod
from . import depo as depo_mod
from . import sicil as sicil_mod

router = APIRouter(prefix="/api/v2", tags=["sahne"])

SAHNELER = [
    {"kod": "hukum", "ad": "Hüküm", "gorevler": ["hukum", "guc", "gelisim", "iliski", "is", "yer"]},
    {"kod": "soru", "ad": "Soru", "gorevler": ["soru"]},
    {"kod": "zaman", "ad": "Zaman", "gorevler": ["zaman", "kapanis"]},
    {"kod": "belge", "ad": "Belge", "gorevler": ["hukum", "guc", "gelisim", "iliski", "is", "zaman", "yer", "kapanis"]},
]

BELGE_SIRA = ["hukum", "guc", "gelisim", "iliski", "is", "zaman", "yer", "kapanis"]

RASATHANE = [
    {"kod": "omurga", "ad": "MİZAN-5", "aile": "cekirdek"},
    {"kod": "sarsma", "ad": "Sarsma", "aile": "gerilim"},
    {"kod": "cevaplanabilirlik", "ad": "Cevaplanabilirlik", "aile": "gerilim"},
    {"kod": "yakinsama", "ad": "Yakınsama", "aile": "cekirdek"},
    {"kod": "duraklama", "ad": "Duraklama izi", "aile": "hareket"},
    {"kod": "topoloji", "ad": "Alan topolojisi", "aile": "hareket"},
    {"kod": "kabzbast", "ad": "Kabz/Bast", "aile": "zaman"},
    {"kod": "kadim", "ad": "Kadim katman", "aile": "gelenek"},
    {"kod": "hd", "ad": "Human Design", "aile": "gelenek"},
    {"kod": "kartografi", "ad": "Yer ölçümleri", "aile": "mekan"},
]

# baglam_ozeti pahalı bir AI çağrısı değildir ama 22 bin satırlık analizden çok
# sayıda özet derler. Belge akışında sekiz HTTP isteği aynı özeti yeniden
# kurmasın diye oturum anahtarıyla üç saat tutulur; Defter ile aynı ömür seçildi.
_BAGLAM_OMRU = 3 * 60 * 60
_BAGLAM_KILIT = threading.RLock()
_BAGLAM: Dict[str, Dict[str, Any]] = {}
_BAGLAM_HESAP = 0


def _sinir(request: Request, kova: str = "ai") -> None:
    # main'i modül yüklenirken içeri almak döngü yaratır. Sınır yalnız istek
    # anında bağlanır; v1'in güvenlik davranışı kopyalanmaz, aynen kullanılır.
    from .main import _sinir as sinir
    sinir(request, kova)


def _coz(payload: Dict[str, Any]) -> tuple[Dict[str, Any], str, Optional[str], str]:
    oturum = str(payload.get("oturum") or "").strip()
    if oturum:
        o = oturum_mod.getir(oturum)
        if not o:
            raise HTTPException(status_code=410, detail="Oturum süresi doldu. Analizi yeniden çalıştırın.")
        analiz = o.get("analiz") or {}
        mod = str(o.get("mod") or payload.get("mod") or "Kişisel")
        model = o.get("model") or payload.get("model")
        return analiz, mod, model, oturum
    analiz = payload.get("analiz") or {}
    mod = str(payload.get("mod") or "Kişisel")
    model = payload.get("model")
    g = analiz.get("girdi") or payload.get("girdi") or {}
    anahtar = f"anon:{g.get('an','?')}:{g.get('ad') or g.get('name') or '?'}"
    return analiz, mod, model, anahtar


def _baglam_temizle() -> None:
    simdi = time.time()
    with _BAGLAM_KILIT:
        eski = [k for k, v in _BAGLAM.items() if simdi - float(v.get("ts", 0)) > _BAGLAM_OMRU]
        for k in eski:
            _BAGLAM.pop(k, None)


def _baglam_sil(anahtar: str) -> None:
    with _BAGLAM_KILIT:
        _BAGLAM.pop(anahtar, None)


def oturum_onbellek_sil(anahtar: str) -> None:
    """Referans yılı değişince Sahne'nin bütün metin izini tek yerden temizler."""
    _baglam_sil(anahtar)
    sil(anahtar)


def _baglam_al(analiz: Dict[str, Any], mod: str, anahtar: str, tazele: bool = False) -> str:
    global _BAGLAM_HESAP
    _baglam_temizle()
    with _BAGLAM_KILIT:
        kayit = _BAGLAM.get(anahtar)
        if kayit and not tazele and kayit.get("mod") == mod:
            kayit["ts"] = time.time()
            return str(kayit.get("baglam") or "")
    baglam = ai_mod.baglam_ozeti(analiz, mod)
    with _BAGLAM_KILIT:
        _BAGLAM_HESAP += 1
        _BAGLAM[anahtar] = {"baglam": baglam, "mod": mod, "ts": time.time()}
    return baglam


def baglam_hesap_sayisi() -> int:
    """Regresyon testleri belge başına tek özet hesabını doğrulayabilsin."""
    return _BAGLAM_HESAP


def _kanit_durumu(analiz: Dict[str, Any], bolum: str) -> List[Dict[str, Any]]:
    out = []
    for k in kanitlar(bolum):
        v = analiz.get(k)
        if k == "alan_topolojisi":
            v = (analiz.get("berzah_v2") or {}).get("alan_topolojisi")
        var = bool(v) and not (isinstance(v, dict) and v.get("hata"))
        out.append({"kod": k, "durum": "var" if var else "sessiz"})
    return out


def _sessiz_bolum(analiz: Dict[str, Any], kod: str) -> Optional[Dict[str, Any]]:
    kan = _kanit_durumu(analiz, kod)
    if kan and all(x["durum"] == "sessiz" for x in kan):
        return {
            "bolum": kod, "gorev": gorev_kodu(kod) or kod,
            "baslik": GOREVLER[gorev_kodu(kod) or kod].ad,
            "metin": "Bu başlıkta belirgin ve bağımsız veri yeterli değil; ölçülmediği yeri doldurmuyorum.",
            "tekrar": 0.0, "kanit": kan, "sizinti": [], "kapsam": {},
            "yeniden_yazildi": False, "benzer_bolum": None,
            "tekrar_detay": {"sozel": 0.0, "iddia": 0.0, "oran": 0.0, "karar": "farklı"},
            "isnad_orani": None, "paragraflar": [], "iddia_ids": [], "hasv_orani": 0.0, "hasv": {},
        }
    return None


def _iddia_hakemi(model: Optional[str]):
    """Gri bantta tek ve kısa bir model kararı; sağlayıcı yoksa ölçüm sessiz kalır."""
    def hakem(a: str, b: str) -> bool | None:
        try:
            metin, _p, _k = ai_mod.cagir(
                "İki kısa danışmanlık metninin ana iddiasını kıyasla. Yalnız AYNI veya FARKLI yaz.",
                [{"role": "user", "content": f"A:\n{a[:900]}\n\nB:\n{b[:900]}"}],
                12, model)
            t = (metin or "").strip().upper()
            if "AYNI" in t:
                return True
            if "FARKLI" in t:
                return False
        except Exception:
            return None
        return None
    return hakem


def _bolum_uret(analiz: Dict[str, Any], mod: str, model: Optional[str],
                 anahtar: str, bolum: str, soru: str = "",
                 baglam: Optional[str] = None) -> Dict[str, Any]:
    kod = gorev_kodu(bolum)
    if not kod or kod not in GOREVLER:
        raise HTTPException(status_code=422, detail=f"Bilinmeyen bölüm: {bolum}")
    tam = baglam if baglam is not None else _baglam_al(analiz, mod, anahtar)
    dar = suz(tam, bolum, soru, analiz.get("referans"))
    gorev = GOREVLER[kod]
    sistem = ai_mod.SISTEM + sistem_eki(bolum, anahtar, sert=False) + isnad_mod.talimat(dar)
    icerik = (f'<analiz_verisi mod="{mod}">\n{dar}\n</analiz_verisi>\n\n'
              f'Görev: {gorev.ad}. Yalnız bu görev için yaz.')
    if soru:
        icerik += f"\nDanışanın doğrudan sorusu: {soru[:1800]}"
    mesaj = [{"role": "user", "content": icerik}]
    ham, protokol, _ = ai_mod._temiz_uret(
        sistem, mesaj, jeton(bolum), model,
        "Bu bir danışan metnidir; teknik hesap adlarını gösterme.")
    isnad = isnad_mod.dogrula(ham, dar)
    metin = isnad["metin"]
    tekrar = en_yuksek_tekrar(metin, anahtar, bolum, _iddia_hakemi(model))
    yeniden = False
    if tekrar.get("karar") == "tekrar":
        sistem2 = ai_mod.SISTEM + sistem_eki(bolum, anahtar, sert=True) + isnad_mod.talimat(dar)
        ham2, protokol2, _ = ai_mod._temiz_uret(
            sistem2, mesaj, jeton(bolum), model,
            "Bu bir danışan metnidir; teknik hesap adlarını gösterme.")
        isnad2 = isnad_mod.dogrula(ham2, dar)
        metin2 = isnad2["metin"]
        tekrar2 = en_yuksek_tekrar(metin2, anahtar, bolum, _iddia_hakemi(model))
        yeniden = True
        # İkinci deneme ancak kararı gerçekten yumuşatıyorsa tercih edilir.
        # "bağla" tekrar değildir; aynı davranışın başka alandaki sonucudur.
        derece = {"farklı": 0, "bağla": 1, "tekrar": 2}
        if (derece.get(tekrar2.get("karar"), 0), float(tekrar2.get("oran", 0.0))) < \
           (derece.get(tekrar.get("karar"), 0), float(tekrar.get("oran", 0.0))):
            metin, protokol, tekrar, isnad = metin2, protokol2, tekrar2, isnad2
    tekrar_bastirildi = False
    if tekrar.get("karar") == "tekrar":
        # İkinci deneme de aynı iddiayı taşıyorsa üçüncü model çağrısı yapmak yerine
        # sessizliği görünür kılarız. Aynı yorumu başka sözcüklerle sunmak derinlik değildir.
        metin = ("Bu başlıkta önceki bölümlerde söylenenden ayrışan yeni bir bulgu ölçülmedi; "
                 "aynı yorumu başka sözlerle tekrarlamıyorum.")
        tekrar = {"sozel": 0.0, "iddia": 0.0, "oran": 0.0, "karar": "bastirildi",
                  "benzer_bolum": tekrar.get("benzer_bolum"), "hakem_cagrildi": tekrar.get("hakem_cagrildi", False)}
        isnad = {"metin": metin, "paragraflar": [], "isnad_orani": None, "uyari": None}
        tekrar_bastirildi = True
    hasv = hasv_mod.olc(metin, analiz, isnad.get("paragraflar") or [])
    isnad["paragraflar"] = hasv.get("paragraflar") or isnad.get("paragraflar") or []
    yaz(anahtar, bolum, metin)
    ref_yil = (analiz.get("referans") or {}).get("yil")
    iddia_ids = [] if tekrar_bastirildi else iddia_mod.kaydet(
        anahtar, kod, metin, kod, int(ref_yil) if ref_yil is not None else None)
    iddialar = iddia_mod.getir_ids(iddia_ids)
    return {
        "bolum": bolum, "gorev": kod, "baslik": gorev.ad, "metin": metin,
        "protokol": protokol, "tekrar": round(float(tekrar.get("oran", 0.0)), 3),
        "tekrar_detay": tekrar, "benzer_bolum": tekrar.get("benzer_bolum"),
        "yeniden_yazildi": yeniden, "tekrar_bastirildi": tekrar_bastirildi,
        "kapsam": kapsam_ozeti(tam, bolum, soru),
        "kanit": _kanit_durumu(analiz, bolum), "sizinti": ai_mod.teknik_sizinti(metin),
        "isnad_orani": isnad.get("isnad_orani"), "isnad_uyari": isnad.get("uyari"),
        "paragraflar": isnad.get("paragraflar") or [], "iddia_ids": iddia_ids, "iddialar": iddialar,
        "hasv_orani": hasv.get("hasv_orani", 0.0), "hasv": hasv,
    }


def v1_bolum_yanit(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Eski /api/v1/chat-bolum sözleşmesini yeni motorla üretir.

    ``baslik/yanit/protokol`` aynen kalır; yeni istemciler kapsam, kanıt ve
    tekrar alanlarını da okuyabilir. Bu yardımcı hız sınırı uygulamaz; v1 uç
    bunu main.py'deki mevcut sınırla zaten yapar.
    """
    analiz, mod, model, anahtar = _coz(payload)
    if not analiz:
        raise HTTPException(status_code=422, detail="Analiz verisi yok.")
    sonuc = _bolum_uret(analiz, mod, model, anahtar, str(payload.get("bolum") or "hukum"))
    return {
        "baslik": sonuc["baslik"], "yanit": sonuc["metin"], "protokol": sonuc.get("protokol"),
        "tekrar": sonuc["tekrar"], "kanit": sonuc["kanit"], "kapsam": sonuc["kapsam"],
        "yeniden_yazildi": sonuc["yeniden_yazildi"], "tekrar_bastirildi": sonuc.get("tekrar_bastirildi", False), "sizinti": sonuc["sizinti"],
        "tekrar_detay": sonuc.get("tekrar_detay"), "isnad_orani": sonuc.get("isnad_orani"),
        "paragraflar": sonuc.get("paragraflar") or [], "iddia_ids": sonuc.get("iddia_ids") or [],
        "iddialar": sonuc.get("iddialar") or [], "hasv_orani": sonuc.get("hasv_orani", 0.0),
        "hasv": sonuc.get("hasv") or {},
    }


@router.get("/harita")
def harita() -> Dict[str, Any]:
    from .zaman import KATMAN_SINIFLARI
    return {
        "surum": "13.5", "sahneler": SAHNELER, "gorevler": gorev_haritasi(),
        "esleme": ESLEME, "rasathane": RASATHANE,
        "katman_siniflari": KATMAN_SINIFLARI,
        "ilke": "Ölçüm Rasathane'de kalır; AI yalnız dokuz danışmanlık görevinde konuşur.",
    }


@router.post("/ayar")
def ayar(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _sinir(request, "agir")
    return ayar_mod.rapor()


@router.get("/ayar/ozet")
def ayar_ozet() -> Dict[str, Any]:
    return ayar_mod.ozet()


@router.post("/iddia/isaretle")
def iddia_isaretle(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _sinir(request, "agir")
    try:
        kayit = iddia_mod.isaretle(str(payload.get("id") or ""), str(payload.get("sonuc") or ""))
    except KeyError:
        raise HTTPException(status_code=404, detail="İddia kaydı bulunamadı.")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {"ok": True, "kayit": kayit, "brier": iddia_mod.brier_ozeti()}


@router.get("/iddia/ozet")
def iddia_ozet() -> Dict[str, Any]:
    return iddia_mod.brier_ozeti()


@router.get("/iddia/gecmis")
def iddia_gecmis(limit: int = 500) -> Dict[str, Any]:
    return iddia_mod.gecmis(limit)


@router.get("/defter/ozet")
def defter_ozet() -> Dict[str, Any]:
    return depo_mod.defter_ozeti()


@router.get("/defter/disaria")
def defter_disaria() -> Response:
    """Ücretsiz katmanda kalıcılığın tek güvencesi olan yedeği tek dosya indirir."""
    veri = depo_mod.disaria_aktar()
    govde = json.dumps(veri, ensure_ascii=False, indent=2).encode("utf-8")
    tarih = time.strftime("%Y%m%d")
    return Response(
        content=govde, media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="zic_defter_yedek_{tarih}.json"'},
    )


@router.post("/defter/iceri")
def defter_iceri(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _sinir(request, "agir")
    veri = payload.get("veri") if isinstance(payload.get("veri"), dict) else payload
    try:
        sayilar = depo_mod.iceri_aktar(veri, bool(payload.get("birlestir", False)))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {"ok": True, "yuklenen": sayilar, "brier": iddia_mod.brier_ozeti()}


@router.get("/sicil/ozet")
def sicil_ozet() -> Dict[str, Any]:
    return sicil_mod.ozet()


@router.post("/sicil/referans-kur")
def sicil_referans_kur(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _sinir(request, "agir")
    try:
        return sicil_mod.referans_kur()
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/acilis")
def acilis(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _sinir(request, "agir")
    analiz, _mod, _model, _anahtar = _coz(payload)
    ag = sahit_agi(analiz)
    try:
        kodlar = sorular.onerilen(analiz, adet=4)
        ss = [s.sozluk() for s in sorular.getir(kodlar)]
    except Exception:
        ss = []
    acilacak = ["hukum"]
    for m in ag.get("mercekler") or []:
        if m.get("durum") == "güçlü" or m.get("celiskili"):
            acilacak.append(m.get("kod"))
    return {"sahit": ag, "acilacak": list(dict.fromkeys(acilacak))[:6],
            "sorular": ss, "kanit": {k: _kanit_durumu(analiz, k) for k in GOREVLER},
            "sicil": sicil_mod.ozet(), "sicil_konum": sicil_mod.konum(analiz)}


@router.post("/bolum")
def bolum(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _sinir(request, "ai")
    analiz, mod, model, anahtar = _coz(payload)
    return _bolum_uret(analiz, mod, model, anahtar,
                       str(payload.get("bolum") or "hukum"),
                       str(payload.get("soru") or "").strip())


@router.post("/defter-sil")
def defter_sil(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _sinir(request, "agir")
    _analiz, _mod, _model, anahtar = _coz(payload)
    sil(anahtar)
    _baglam_sil(anahtar)
    return {"ok": True}


@router.post("/zaman")
def zaman(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _sinir(request, "agir")
    analiz, _mod, _model, anahtar = _coz(payload)
    from .zaman import serit, referans_ani
    dogum = payload.get("dogum")
    if isinstance(dogum, dict) and dogum:
        # v1 analiz çıktısı koordinatı tekrar etmez. Portal doğum girdisini bu
        # çağrıda gönderir; 0/0 koordinatla sessizce yanlış zaman haritası
        # kurmak yerine gerçek giriş yeniden doğrulanır.
        from .schemas import BirthInput
        from .main import _chart
        ch = _chart(BirthInput(**dogum))
    else:
        from .portal_yardim import chart_analizden
        ch = chart_analizden(analiz)
    # Formdaki Solar Return anahtarı veri akışının tek kaynağıdır. Eski uç,
    # yıl bulunamadığında yürürlükteki SR yılını kendiliğinden türetiyordu; bu
    # davranış checkbox kapalı bir Natal okumaya yıllık katman ekleyebiliyordu.
    solar_aktif = payload.get("solar_aktif", None)
    secili_yil = payload.get("year")
    if secili_yil in (None, "") and isinstance(dogum, dict):
        secili_yil = dogum.get("sr_year")
    if secili_yil in (None, ""):
        rr = analiz.get("referans") or {}
        if rr.get("kaynak") == "solar_return":
            secili_yil = rr.get("yil")
    if secili_yil in (None, ""):
        sv = analiz.get("solar_v2") or {}
        if isinstance(sv, dict) and not sv.get("hata"):
            secili_yil = sv.get("yil")

    # Açıkça kapalıysa veya hiçbir yıllık seçim yoksa yalnız Natal + bugün
    # kullanılır. Böylece `solar_aktif` göndermeyen eski istemci bile analiz
    # içinde SR yoksa kendiliğinden yıllık harita kurmaz.
    yil = None if solar_aktif is False else (
        int(secili_yil) if secili_yil not in (None, "") else None
    )
    ref = referans_ani(ch, yil)
    sr = ref.get("chart") if ref.get("aktif") else None
    jd_bas = float(ref["jd"])
    z = serit(ch, sr, ay_sayisi=int(payload.get("ay_sayisi") or 12),
              jd_bas=jd_bas, solar_year=ref.get("yil"))
    z["solar_yil"] = ref.get("yil")
    z["referans"] = {k: ref.get(k) for k in
                     ("an", "yil", "kaynak", "bugun", "fark_yil", "aktif")}
    analiz["zaman_seridi"] = z
    analiz["sahit_7"] = sahit_agi(analiz)
    _baglam_sil(anahtar)  # zaman katmanı değişti; eski özet belgeye sızmasın.
    return z


@router.post("/belge/baslat")
def belge_baslat(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    """Belge defterini açar ve bağlamı bir kez hazırlar; model çağrısı yapmaz."""
    _sinir(request, "agir")
    analiz, mod, _model, anahtar = _coz(payload)
    sil(anahtar)
    _baglam_sil(anahtar)
    once = baglam_hesap_sayisi()
    _baglam_al(analiz, mod, anahtar, tazele=True)
    return {"ok": True, "sira": BELGE_SIRA, "toplam": len(BELGE_SIRA),
            "baglam_hesap": baglam_hesap_sayisi() - once}


@router.post("/belge/bolum")
def belge_bolum(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    """Tek HTTP isteğinde yalnız bir belge bölümü üretir."""
    _sinir(request, "ai")
    analiz, mod, model, anahtar = _coz(payload)
    toplam = len(BELGE_SIRA)
    ham_sira = payload.get("sira")
    if ham_sira is not None:
        try:
            sira = int(ham_sira)
        except (TypeError, ValueError):
            raise HTTPException(status_code=422, detail="sira 1..8 arasında olmalı.")
        if not 1 <= sira <= toplam:
            raise HTTPException(status_code=422, detail="sira 1..8 arasında olmalı.")
        kod = BELGE_SIRA[sira - 1]
    else:
        kod = gorev_kodu(str(payload.get("bolum") or "")) or str(payload.get("bolum") or "")
        if kod not in BELGE_SIRA:
            raise HTTPException(status_code=422, detail="Belge bölümü tanınmadı.")
        sira = BELGE_SIRA.index(kod) + 1
    sessiz = _sessiz_bolum(analiz, kod)
    baglam = _baglam_al(analiz, mod, anahtar)
    sonuc = sessiz or _bolum_uret(analiz, mod, model, anahtar, kod, baglam=baglam)
    return {"sira": sira, "toplam": toplam, "bolum": sonuc}


@router.post("/belge")
def belge(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    """Geri uyumlu toplu uç; tek istekte en fazla üç bölüm üretir.

    Eski istemci tamamen kırılmasın diye uç korunur. Sekiz bölümlük üretim için
    ``/belge/baslat`` + ``/belge/bolum`` kullanılmalıdır.
    """
    _sinir(request, "ai")
    analiz, mod, model, anahtar = _coz(payload)
    sil(anahtar)
    azami = max(1, min(3, int(payload.get("azami_bolum") or 3)))
    baglam = _baglam_al(analiz, mod, anahtar, tazele=True)
    bolumler = []
    for kod in BELGE_SIRA[:azami]:
        sessiz = _sessiz_bolum(analiz, kod)
        bolumler.append(sessiz or _bolum_uret(analiz, mod, model, anahtar, kod, baglam=baglam))
    tekrarlar = [float(x.get("tekrar", 0)) for x in bolumler]
    isnadlar = [float(x["isnad_orani"]) for x in bolumler if isinstance(x.get("isnad_orani"), (int, float))]
    hasvlar = [float(x.get("hasv_orani", 0.0)) for x in bolumler]
    return {
        "modul": "DANIŞAN DOSYASI · kanıtlı derin okuma",
        "sahit": sahit_agi(analiz), "bolumler": bolumler,
        "ortalama_tekrar": round(sum(tekrarlar) / max(1, len(tekrarlar)), 3),
        "azami_tekrar": round(max(tekrarlar or [0]), 3),
        "isnad_orani": round(sum(isnadlar) / len(isnadlar), 3) if isnadlar else None,
        "hasv_orani": round(sum(hasvlar) / len(hasvlar), 3) if hasvlar else 0.0,
        "toplam": len(BELGE_SIRA), "uretilen": len(bolumler),
        "tamamlandi": len(bolumler) == len(BELGE_SIRA),
        "ilke": "Tek istekte en fazla üç bölüm; tam belge istemci tarafından parça parça kurulur.",
    }
