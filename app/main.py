#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BERZAH SERVİSİ — FastAPI uygulaması.
Render.com Web Service olarak dağıtım için tasarlandı (bkz. render.yaml).

Uçlar:
  GET  /                        WEB ARAYÜZÜ (tek dosya, derleme gerektirmez)
  GET  /healthz                 sağlık kontrolü
  GET  /api                     servis kartviziti (JSON)
  POST /api/v1/full             HER ŞEY (v2 + 66-74 + 16 deneme + kadim + HD)
  POST /api/v1/berzah2          yalnız v2 kütle motoru (KD/AD/B)
  POST /api/v1/kabzbast         yalnız 66-74 (Kabz/Bast v1)
  POST /api/v1/deneme           yalnız 16 deneme modülü
  POST /api/v1/kadim            İsim Tecellîsi + Kadim Lab + Hüviyet Mührü
  POST /api/v1/hd               Human Design
  POST /api/v1/ai-context       mevcut Astro Pro AI sohbetine kanıt kartları
"""
from __future__ import annotations
import os
import re
import json
from typing import Optional
import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse

from .schemas import (BirthInput, IliskiInput, SohbetInput, BolumInput,
                      KisiselInput, DinamikInput, RektifikasyonInput, SolarReturnAttachInput,
                      SentezInput, FormulInput,
                      SehirInput, ManeviInput,
                      SoruInput, RaporInput, LunasyonInput)
from .astro import (build_chart, jd_to_iso, chart_at_jd,
                    solar_return_jd, CORE10)
from .circular import fmt_lon
from .engine_mass import full_v2
from .hukum import hukum_baglam
from .oruntu_omurgasi import oruntu_omurgasi
from .engine_kabzbast import run_kabzbast
from .modules_deneme import run_all_deneme
from .modules_kadim import isim_tecellisi, kadim_lab, huviyet_muhru
from .module_hd import human_design
from .relationship import sinastri, kompozit, davison, deklinasyon_sinastri
from .sira import sira_cevrimi
from .hudud import hudud_katmani
from .kartografi import kartografi_katmani
from .hudud_arz import hudud_arz, sehir_cozumle
from .maneviyat import manevi_katman
from .zaman import referans_ani
from . import ai as ai_mod
from . import oturum as oturum_mod
from . import limit as limit_mod
import secrets as _secrets
from fastapi import Request

VERSION = "ZÎC v13.5 · Referans Anı ve Saha"

app = FastAPI(
    title="BERZAH Servisi",
    version=VERSION,
    description=("Kütle motoru (KD/AD/Berzah) + Kabz/Bast v1 (modül 66-74) + "
                 "16 deneme modülü + Kadim Arap–Osmanlı katmanı + Human Design. "
                 "Astro Pro v9.2.4'ten ayrıştırılmış, bağımsız hesap mikroservisi."))
from .sahne import router as sahne_router
app.include_router(sahne_router)

# CORS: varsayılan açık ama ortam değişkeniyle daraltılabilir. Servis kendi
# arayüzünü sunduğu için üretimde kendi alan adınıza kısmanız önerilir:
#   CORS_ORIGINS=https://siteniz.onrender.com
# Arayüz servisin kendisinden sunulduğu için çapraz kaynak erişimine gerek
# yoktur. Varsayılan artık KAPALI; başka bir siteden çağırmak gerekirse
# CORS_ORIGINS ile açıkça izin verilir (CORS_ORIGINS=* eski davranışı verir).
_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()]
if _ORIGINS:
    app.add_middleware(CORSMiddleware, allow_origins=_ORIGINS,
                       allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def _erisim_ara_katman(request: Request, call_next):
    """
    Erişim anahtarı tanımlıysa tüm API ve arayüz kapalıdır. Sağlık kontrolü
    (Render'ın kullandığı /healthz) her zaman açık bırakılır.
    """
    yol = request.url.path
    if ERISIM_ANAHTARI and yol not in ("/healthz",):
        verilen = (request.headers.get("x-zic-anahtar")
                   or request.query_params.get("anahtar") or "")
        if not _secrets.compare_digest(str(verilen), ERISIM_ANAHTARI):
            from fastapi.responses import JSONResponse, HTMLResponse
            if yol == "/":
                return HTMLResponse(
                    "<!doctype html><meta charset='utf-8'>"
                    "<title>ZÎC</title>"
                    "<body style=\"font-family:system-ui;padding:40px;"
                    "background:#F0EEE8;color:#14110F\">"
                    "<h1 style='font-size:20px'>Erişim anahtarı gerekli</h1>"
                    "<p>Bağlantıya <code>?anahtar=…</code> ekleyin.</p></body>",
                    status_code=401)
            return JSONResponse({"detail": "Erişim anahtarı gerekli."},
                                status_code=401)
    return await call_next(request)


# X-Forwarded-For'a ancak GERÇEKTEN bir vekil arkasındaysak güvenilir.
# Render'da ZIC_TRUST_PROXY=1 verin. Doğrudan açıkta çalışırken kapalı
# kalmalı: aksi hâlde istemci başlığı uydurup kendini her istekte başka
# biri gibi gösterir ve IP tabanlı her sınır anlamsızlaşır.
TRUST_PROXY = os.environ.get("ZIC_TRUST_PROXY", "").strip().lower() in ("1", "true", "evet")
# Boş bırakılmış değişken int("") ile import'u çökertiyordu; ai._sayi
# aynı korumayı burada da sağlar.
PROXY_HOPS = max(1, int(ai_mod._sayi("ZIC_PROXY_HOPS", 1)))


def _ip(req: Request) -> str:
    """
    İstemci kimliği.

    KRİTİK DÜZELTME: önceden X-Forwarded-For'un EN SOLDAKİ değeri alınıyordu.
    O değeri istemci kendisi yazabilir; sızma testinde başlığı her istekte
    değiştirerek 40 parola denemesinin hiçbiri engellenmedi — kaba kuvvet
    koruması tamamen atlatılabiliyordu.

    Doğrusu EN SAĞDAN saymaktır: zincirin sağ ucundaki değerler, isteği
    gerçekten gören güvenilir vekiller tarafından EKLENİR; istemcinin
    uydurduğu değerler sola itilir. Tek vekil arkasında (Render) sağdan
    birinci değer, vekilin doğrudan gördüğü gerçek istemci adresidir.
    """
    if TRUST_PROXY:
        xff = req.headers.get("x-forwarded-for", "")
        parcalar = [p.strip() for p in xff.split(",") if p.strip()]
        if parcalar:
            return parcalar[-min(PROXY_HOPS, len(parcalar))]
    return req.client.host if req.client else "bilinmiyor"


def _sinir(req: Request, kova: str) -> None:
    # "_kuresel" ile biten kovalar tek bir sayaç kullanır: istemci kimliğinden
    # bağımsızdır, dolayısıyla başlık sahteciliğiyle atlatılamaz.
    kimlik = "hepsi" if kova.endswith("_kuresel") else _ip(req)
    ok, kalan = limit_mod.kontrol(kova, kimlik)
    if not ok:
        raise HTTPException(
            status_code=429,
            detail=f"Çok fazla istek. {kalan // 60 + 1} dakika sonra tekrar deneyin.")


def _oturum_baglam(oturum: Optional[str], analiz: dict, mod: str,
                   model: Optional[str]):
    """Oturum varsa analiz/mod/model için sunucu tarafındaki kilitli değeri kullan."""
    if not oturum:
        return analiz, mod, model
    o = oturum_mod.getir(oturum)
    if not o:
        raise HTTPException(status_code=410,
                            detail="Oturum süresi doldu. Analizi yeniden çalıştırın.")
    return o["analiz"], o["mod"], o.get("model") or model


def _oturum_model(oturum: Optional[str], model: Optional[str]) -> Optional[str]:
    if not oturum:
        return model
    o = oturum_mod.getir(oturum)
    if not o:
        raise HTTPException(status_code=410, detail="Oturum süresi doldu.")
    return o.get("model") or model


def _rektifiye_et(inp: BirthInput):
    """
    Kullanıcı seçtiyse ve yeterli olay verdiyse doğum saatini olaylardan çözer.
    Sonuç 'belirsiz' ise SAAT DEĞİŞTİRİLMEZ — yanlış saatle analiz üretmek,
    belirsiz saatle üretmekten kötüdür.
    """
    from .rektifikasyon import rektifikasyon
    ol = [o if isinstance(o, dict) else o.model_dump() for o in (inp.olaylar or [])]
    ol = [o for o in ol if o.get("tarih")]
    if not inp.rektifiye or len(ol) < 3:
        return None, inp.hour, inp.minute
    r = rektifikasyon(inp.year, inp.month, inp.day, inp.hour, inp.minute,
                      inp.lat, inp.lng, ol, inp.tz_name, inp.tz_offset,
                      inp.house_system)
    if r.get("onerilen_saat"):
        hh, mm = (int(x) for x in r["onerilen_saat"].split(":"))
        return r, hh, mm
    return r, inp.hour, inp.minute


@app.post("/api/v1/rektifikasyon")
def api_rektifikasyon(inp: RektifikasyonInput, request: Request):
    _sinir(request, "agir")
    """Doğum saatini hayat olaylarından geri çözer (tek başına kullanım)."""
    from .rektifikasyon import rektifikasyon
    ol = [o.model_dump() for o in inp.olaylar]
    if len(ol) < 3:
        raise HTTPException(status_code=422,
                            detail="En az 3 tarihli olay gerekiyor.")
    try:
        return rektifikasyon(inp.year, inp.month, inp.day, inp.hour, inp.minute,
                             inp.lat, inp.lng, ol, inp.tz_name, inp.tz_offset,
                             inp.house_system, inp.pencere_dk, inp.adim_dk)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rektifikasyon: {e}")


def _chart(inp: BirthInput):
    try:
        return build_chart(inp.year, inp.month, inp.day, inp.hour, inp.minute,
                           inp.lat, inp.lng, inp.tz_name, inp.tz_offset,
                           label=inp.name, house_system=inp.house_system)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Harita kurulamadı: {e}")


@app.get("/healthz")
def healthz():
    """Efemeris kipini de bildirir — 'seas_18.se1 not found' teşhisi için."""
    import swisseph as swe
    from . import astro as _a
    ephe_var = os.path.isdir(_a._EPHE_DIR) and any(
        f.endswith(".se1") for f in os.listdir(_a._EPHE_DIR)) \
        if os.path.isdir(_a._EPHE_DIR) else False
    return {"ok": True, "service": VERSION, "ts": time.time(),
            "efemeris": {"kip": "SWIEPH" if _a.EPHFLAG & swe.FLG_SWIEPH else "MOSEPH",
                         "dizin": _a._EPHE_DIR, "se1_dosyalari_var": ephe_var}}


_STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


@app.get("/static/{dosya}")
def statik(dosya: str):
    """
    Stil ve betik dosyalarını sunar.

    index.html bölündüğünde bu uç YOKTU: sayfa açılıyor ama stil ve betik
    404 dönüyordu — yani uygulama tamamen çalışmıyordu. Dosya adı
    temizlenir; dizin dışına çıkış denemesi reddedilir.
    """
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,60}", dosya or ""):
        raise HTTPException(status_code=404, detail="Bulunamadı.")
    yol = os.path.join(_STATIC, dosya)
    if not os.path.isfile(yol):
        raise HTTPException(status_code=404, detail="Bulunamadı.")
    tip = {"css": "text/css; charset=utf-8",
           "js": "application/javascript; charset=utf-8",
           "json": "application/json; charset=utf-8",
           "svg": "image/svg+xml", "png": "image/png",
           "ico": "image/x-icon"}.get(dosya.rsplit(".", 1)[-1].lower(),
                                      "application/octet-stream")
    return FileResponse(yol, media_type=tip,
                        headers={"Cache-Control": "public, max-age=300"})


@app.get("/", response_class=HTMLResponse)
def arayuz():
    """Web arayüzü. Dosya yoksa servis kartvizitine düşer."""
    index = os.path.join(_STATIC, "index.html")
    if os.path.isfile(index):
        return FileResponse(index, media_type="text/html; charset=utf-8")
    return HTMLResponse("<h1>BERZAH Servisi</h1><p>Arayüz dosyası bulunamadı. "
                        "API için <a href='/docs'>/docs</a>.</p>")


@app.get("/api")
def root():
    return {"service": VERSION,
            "arayuz": "/",
            "endpoints": ["/api/v1/full", "/api/v1/berzah2", "/api/v1/kabzbast",
                          "/api/v1/deneme", "/api/v1/kadim", "/api/v1/hd",
                          "/api/v1/ai-context", "/docs"],
            "not": "POST gövdesi için /docs içindeki BirthInput şemasına bakın."}


@app.post("/api/v1/tz-check")
def api_tz_check(inp: BirthInput):
    """
    Hesaplamadan ÖNCE saat dilimini ve koordinatı doğrula.
    Arayüz bunu canlı çağırır; kullanıcı UTC ofsetini ve yaz saati durumunu
    haritayı kurmadan görür. Sessiz saat dilimi hatasının panzehri budur.
    """
    import datetime as dt
    from .astro import resolve_tz
    try:
        when = dt.datetime(inp.year, inp.month, inp.day, inp.hour, inp.minute)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Geçersiz tarih/saat: {e}")
    try:
        off, kaynak = resolve_tz(inp.lat, inp.lng, when, inp.tz_name, inp.tz_offset)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    utc = when - dt.timedelta(hours=off)
    uyarilar = []
    if kaynak.startswith("⚠"):
        uyarilar.append(kaynak)
    if abs(inp.lat) > 66.5:
        uyarilar.append("Kutup dairesi ötesi — Placidus tanımsız, Whole Sign kullanılacak.")
    # Boylam ile saat dilimi tutarlılığı: 1 saat = 15° boylam
    beklenen = inp.lng / 15.0
    if abs(beklenen - off) > 3.0:
        uyarilar.append(
            f"Boylam {inp.lng:.2f}° güneş saati olarak UTC{beklenen:+.1f} demek, "
            f"ama seçilen dilim UTC{off:+.1f}. Koordinat ile saat dilimi uyuşmuyor "
            "olabilir — doğu/batı işaretini kontrol edin.")
    return {"yerel_saat": when.strftime("%d.%m.%Y %H:%M"),
            "utc_ofseti": off,
            "utc_karsiligi": utc.strftime("%d.%m.%Y %H:%M") + " UTC",
            "kaynak": kaynak,
            "enlem": inp.lat, "boylam": inp.lng,
            "uyarilar": uyarilar}


@app.post("/api/v1/berzah2")
def api_berzah2(inp: BirthInput):
    ch = _chart(inp)
    return {"girdi": {"an": jd_to_iso(ch.jd_ut), "tz": ch.tz_offset, "tz_kaynak": ch.tz_source},
            "berzah_v2": full_v2(ch)}


@app.post("/api/v1/kabzbast")
def api_kabzbast(inp: BirthInput):
    ch = _chart(inp)
    return {"girdi": {"an": jd_to_iso(ch.jd_ut), "tz": ch.tz_offset, "tz_kaynak": ch.tz_source},
            "kabzbast_v1": run_kabzbast(ch, days=inp.days, sr_year=inp.sr_year)}


@app.post("/api/v1/deneme")
def api_deneme(inp: BirthInput):
    ch = _chart(inp)
    return {"girdi": {"an": jd_to_iso(ch.jd_ut), "tz": ch.tz_offset, "tz_kaynak": ch.tz_source},
            "deneme": run_all_deneme(ch, months=inp.months)}


@app.post("/api/v1/kadim")
def api_kadim(inp: BirthInput):
    ch = _chart(inp)
    den = run_all_deneme(ch, months=inp.months)
    v2 = full_v2(ch)
    out = {"kadim_lab": kadim_lab(ch),
           "huviyet_muhru": huviyet_muhru(ch, den, v2)}
    if inp.isim:
        out["isim_tecellisi"] = isim_tecellisi(ch, inp.isim, inp.anne)
    return {"girdi": {"an": jd_to_iso(ch.jd_ut)}, "kadim": out}


@app.post("/api/v1/hd")
def api_hd(inp: BirthInput):
    ch = _chart(inp)
    return {"girdi": {"an": jd_to_iso(ch.jd_ut)}, "human_design": human_design(ch)}


@app.post("/api/v1/full")
def api_full(inp: BirthInput, request: Request):
    _sinir(request, "agir")
    try:
        locked_model = ai_mod.kilitli_model(inp.model)
    except ai_mod.AIHatasi as e:
        raise HTTPException(status_code=422, detail=str(e))
    rekt, s_h, s_mi = _rektifiye_et(inp)
    if rekt and (s_h, s_mi) != (inp.hour, inp.minute):
        inp = inp.model_copy(update={"hour": s_h, "minute": s_mi})
    ch = _chart(inp)
    # v13.4.1 yalnız bazı yıllık modülleri seçili SR yılına bağlamıştı; aynı
    # payload içinde yaş/duraklama bugünü, lunasyon ise geçmiş yılı okuyordu.
    # Tek referans nesnesi bu parçalı zaman çapalarını aynı ana toplar.
    ref = referans_ani(ch, inp.sr_year)
    v2 = full_v2(ch)
    kb = run_kabzbast(ch, days=inp.days, sr_year=inp.sr_year)
    den = run_all_deneme(ch, months=inp.months)
    kad = {"kadim_lab": kadim_lab(ch),
           "huviyet_muhru": huviyet_muhru(ch, den, v2)}
    if inp.isim:
        # deneme çıktısındaki mizan/vahdet yeniden hesaplanmasın
        kad["isim_tecellisi"] = isim_tecellisi(ch, inp.isim, inp.anne,
                                               mz=den.get("mizan"), vh=den.get("vahdet"))
    # Solar Return haritası da referans_ani() tarafından kurulur; dönüş anını
    # burada ikinci kez hesaplamak, modüllerin birkaç farklı SR nesnesi taşımasına
    # yol açıyordu.
    solar = None
    if ref.get("aktif"):
        try:
            sch = ref["chart"]
            solar = {"yil": ref["yil"], "an": ref["an"],
                     "berzah_v2": full_v2(sch, topoloji=False)}
        except Exception as e:
            solar = {"yil": ref.get("yil"), "hata": str(e)[:200]}
    # DURAKLAMA İZİ — hangi yanlar işlenmiş, hangileri ham.
    # Chrono-Gravitron'un yerine geldi: o modül gravitasyonu hesaplıyordu
    # ama sistem yerçekiminin nedensel rolü olmadığını zaten söylüyordu —
    # yani dürüstlüğünü kanıtlamak için var olan bir katmandı, seansta
    # kullanılamıyordu. Bu modül doğrudan kullanılabilir bir şey söylüyor.
    try:
        from .duraklama import duraklama_izi
        drk = duraklama_izi(ch, bugun_jd=float(ref["jd"]))
    except Exception as e:
        drk = {"hata": str(e)[:200]}
    # CEVAPLANABİLİRLİK — hangi alanda veri güçlü, hangisinde ince.
    # Bir bölüm ÜRETMEZ; doğrudan AI promptuna girer ve modelin bütün
    # yüzeylerde nasıl konuştuğunu değiştirir.
    try:
        from .cevaplanabilirlik import cevaplanabilirlik
        cev = cevaplanabilirlik(
            {"berzah_v2": v2, "bodies": {k: {"lon": b.lon}
                                         for k, b in ch.bodies.items()},
             "duraklama_izi": drk, "celiskiler": []},
            list(getattr(ch, "cusps", []) or []))
    except Exception as e:
        cev = {"hata": str(e)[:200]}
    # TEMAS AÇISI — danışmanın kendi haritası tanımlıysa hesaplanır.
    # ZIC_DANISMAN_DOGUM="YYYY-MM-DD HH:MM,enlem,boylam[,saat_dilimi]"
    # Saat dilimi verilmezse Europe/Istanbul varsayılır.
    #
    # İlk sürümde `tz_offset=0.0` yazmıştım: danışman haritası UTC olarak
    # kuruluyordu ve üç saat kayıyordu. Danışman kendi haritasını okuduğunda
    # bile "yansıma yok" çıkması bunu ele verdi — aynı harita, farklı çatal
    # olamaz.
    tms = {}
    _dd = os.environ.get("ZIC_DANISMAN_DOGUM", "").strip()
    if _dd:
        try:
            _par = [x.strip() for x in _dd.split(",")]
            _an, _la, _lo = _par[0], _par[1], _par[2]
            _tz = _par[3] if len(_par) > 3 else "Europe/Istanbul"
            _dch = _chart(BirthInput(
                year=int(_an[:4]), month=int(_an[5:7]), day=int(_an[8:10]),
                hour=int(_an[11:13]), minute=int(_an[14:16]),
                lat=float(_la), lng=float(_lo), tz_name=_tz))
            from .temas import temas_acisi
            tms = temas_acisi(_dch, ch, v2, full_v2(_dch, topoloji=False))
        except Exception as e:
            tms = {"hata": str(e)[:160]}
    # YAŞ KATMANI — kaç gelişim eşiğinin ortasında.
    # Astroloji yaşı bir sayı olarak görür; oysa yaş, aynı anda dönen
    # birkaç çarkın o andaki bileşimidir. Kimse "bu kişi ŞU ANDA kaç
    # eşiğin ortasında" diye sormuyor.
    try:
        from .yas import yas_katmani
        yk = yas_katmani(ch, jd=float(ref["jd"]))
    except Exception as e:
        yk = {"hata": str(e)[:200]}
    # SARSMA TESTİ — hangi bulgu doğum saati hatasına dayanır.
    # Yirmi beş kategori tek bir sayıya dayanıyor: doğum saati. Astroloji
    # bunu bilir ve uyarır, ama sonra BÜTÜN bulguları aynı güvenle
    # anlatır. Bu modül uyarıyı ölçüme çevirir.
    try:
        from .sarsma import sarsma_testi
        _g = inp
        srs = sarsma_testi(_g.year, _g.month, _g.day, _g.hour, _g.minute,
                           _g.lat, _g.lng, tz_name=_g.tz_name,
                           tz_offset=_g.tz_offset,
                           house_system=getattr(_g, "house_system", "P"))
    except Exception as e:
        srs = {"hata": str(e)[:200]}
    # KAYIP ZAMAN — hangi yıllar sessiz geçti. Bedava (0.0 sn).
    try:
        from .omur import kayip_zaman
        kz = kayip_zaman(ch, bugun_jd=float(ref["jd"]))
    except Exception as e:
        kz = {"hata": str(e)[:200]}
    # ASTROKARTOGRAFİ — yalnız yönetici. Arz izdüşümü ızgara taraması
    # yaptığı için (330 nokta ≈ 3.6 sn) istek üzerine ayrı uçtan alınır.
    try:
        _sr_jd_kart = float(ref["jd"]) if ref.get("aktif") else None
        kart = kartografi_katmani(ch, sr_jd=_sr_jd_kart, izdusum=False,
                                  solar_aktif=bool(ref.get("aktif")))
        # ASC/DSC eğri noktaları yanıtın 102 KB'ını kaplıyordu (üç zaman
        # düzlemi × 10 cisim × 90 nokta) ve arayüz bunları HİÇ kullanmıyor;
        # yalnız MC/IC değerleri ve paran listesi gösteriliyor. Noktalar
        # paran hesabında sunucuda kullanılıp yanıttan çıkarılır. Harita
        # çizimi gerekirse /api/v1/kartografi-cizgi ucundan alınır.
        for _blok in ("natal", "gunes_donusu", "ay_donusu"):
            _b = kart.get(_blok)
            if isinstance(_b, dict):
                for _c in _b.get("cizgiler", []):
                    _c["asc_nokta"] = len(_c.pop("ASC", []))
                    _c["dsc_nokta"] = len(_c.pop("DSC", []))
    except Exception as e:
        kart = {"hata": str(e)[:200]}
    # HUDÛD-I ARZ — iki katmanın birleşimi (hafif, ızgara taraması yok)
    try:
        kart["hudud_arz"] = hudud_arz(ch)
    except Exception as e:
        kart["hudud_arz"] = {"hata": str(e)[:200]}
    # SPİRİTÜEL ÇALIŞMALAR — yalnız yönetici
    try:
        manevi = manevi_katman(ch, (inp.isim or inp.name or ""))
        if ref.get("aktif") and isinstance(manevi, dict):
            manevi["referans_disi"] = True
            manevi["referans_fark_yil"] = ref.get("fark_yil")
    except Exception as e:
        manevi = {"hata": str(e)[:200]}
    # Çift çark için o anki gök konumları (hafif)
    try:
        from .engine_mass import transit_konumlari, capraz_acilar_basit
        tr = transit_konumlari(ch)
        if ref.get("aktif"):
            tr["referans_disi"] = True
            tr["referans_fark_yil"] = ref.get("fark_yil")
            tr["referans_an"] = ref.get("an")
        else:
            tr["referans_disi"] = False
            tr["referans_fark_yil"] = 0
        tr["acilar"] = capraz_acilar_basit(
            [(ch.bodies[k].name_tr, ch.bodies[k].lon) for k in CORE10]
            + [("Yükselen", ch.asc), ("MC", ch.mc)], tr["cisimler"])
    except Exception as e:
        tr = {"hata": str(e)[:150]}
    # HUDÛD-I FELEK — deklinasyon katmanı ve küresel alan
    try:
        hudud = hudud_katmani(ch)
    except Exception as e:
        hudud = {"hata": str(e)[:200]}
    # ŞİRÂ ÇEVRİMİ — ikili yıldız saati ve sekiz alan önerisi
    try:
        sira = sira_cevrimi(ch, v2.get("alan_topolojisi"), inp.isim, inp.anne,
                            simdi_jd=float(ref["jd"]))
    except Exception as e:
        sira = {"hata": str(e)[:200]}
    sonuc = {"servis": VERSION,
             "girdi": {"ad": inp.name, "an": jd_to_iso(ch.jd_ut),
                       "tz": ch.tz_offset, "tz_kaynak": ch.tz_source,
                       "ev_sistemi": ch.house_system},
             "referans": {k: ref.get(k) for k in ("an", "yil", "kaynak", "bugun", "fark_yil", "aktif")},
             "berzah_v2": v2,
            "solar_v2": solar,
            "hukum": hukum_baglam(v2, solar),
            "hudud_felek": hudud,
            "kartografi": kart,
            "duraklama_izi": drk,
            "cevaplanabilirlik": cev,
            "temas_acisi": tms,
            "yas_katmani": yk,
            "sarsma": srs,
            "kayip_zaman": kz,
            "maneviyat": manevi,
            "transit": tr,
            "sira_cevrimi": sira,
            "kabzbast_v1_m66_74": kb,
            "deneme_modulleri": den,
             "kadim_katman": kad,
             "human_design": human_design(ch)}
    # Kişiselleştirme ARKA PLANDA, aynı istekte tamamlanır. v3.1'de arayüz
    # önce şablon metni gösterip sonra ayrı bir çağrıyla değiştiriyordu;
    # çağrı düşünce kullanıcı ekranda ham hata görüyordu. Artık tek seferde
    # biter; başarısız olursa şablon metin sessizce kalır.
    # Halkada gösterilecek hesaplanmış noktaları topla ve gezegenlerle
    # açılarını çıkar — kullanıcı bunları çark üzerinde gezegen gibi görecek.
    try:
        from .engine_mass import nokta_acilari
        ek = []
        krn = den.get("krn", {})
        if krn.get("KRN"):
            ek.append({"ad": "Kader Rezonansı", "kod": "KRN",
                       "lon": krn["KRN"]["lon"], "glif": "⊕"})
            ek.append({"ad": "Anti-KRN", "kod": "aKRN",
                       "lon": krn["Anti_KRN"]["lon"], "glif": "⊖"})
        vh = (den.get("vahdet") or {}).get("vahdet_noktasi")
        if vh:
            ek.append({"ad": "Vahdet", "kod": "VHD", "lon": vh["lon"], "glif": "✦"})
        sv = (den.get("suveyda") or {}).get("suveyda")
        if sv:
            ek.append({"ad": "Süveyda", "kod": "SVY", "lon": sv["lon"], "glif": "♥"})
        ic = (den.get("nokta_i_icabet") or {}).get("icabet")
        if ic:
            ek.append({"ad": "İcâbet", "kod": "İCB", "lon": ic["lon"], "glif": "▲"})
        nk = (den.get("nokta_i_noksan") or {}).get("noksan")
        if nk:
            ek.append({"ad": "Noksan", "kod": "NKS", "lon": nk["lon"], "glif": "▽"})
        ay = (den.get("ayna_ekseni") or {}).get("eksen")
        if ay:
            ek.append({"ad": "Ayna Ekseni", "kod": "AYN", "lon": ay["lon"], "glif": "⇔"})
        sr = (sira or {}).get("sira_a", {}).get("dogumda", {})
        if sr.get("lon") is not None:
            ek.append({"ad": "Şi'râ", "kod": "ŞRA", "lon": sr["lon"], "glif": "★"})
        v2["noktalar"] = (v2.get("noktalar") or []) + ek
        for n in v2["noktalar"]:
            n["ev"] = ch.house(n["lon"])
            n["konum"] = fmt_lon(n["lon"])
        v2["nokta_acilari"] = nokta_acilari(ch, v2["noktalar"])
    except Exception as e:
        v2["nokta_acilari"] = {"hata": str(e)[:150]}

    if rekt:
        sonuc["rektifikasyon"] = rekt
    # Katmanların birbiriyle çeliştiği yerler. AI çağrısı yok; hesaplanmış
    # veriden çıkar. Çelişki saklanmaz — seansta en işe yarayan bilgi
    # çoğu zaman oradadır.
    try:
        _cel = ai_mod.katmanlar_arasi_celiski(sonuc)
        if _cel:
            sonuc["celiskiler"] = _cel
    except Exception:
        pass
    try:
        _dir = ai_mod.direnc_haritasi(sonuc)
        if _dir:
            sonuc["direnc"] = _dir
    except Exception:
        pass
    # MİZAN-5 ilk geçişi: misafir akışında da kategori omurgası hazır olsun.
    # Yönetici akışında hamle/yakınsama eklendikten sonra aşağıda yeniden
    # hesaplanır; fonksiyon hızlı ve yalnız sonuç sözlüğünü okur.
    try:
        sonuc["oruntu_omurgasi"] = oruntu_omurgasi(sonuc)
    except Exception as e:
        sonuc["oruntu_omurgasi"] = {"hata": str(e)[:200]}
    if inp.rol == "misafir":
        # Misafir BÜTÜN kategorileri görür ama ham veriyi almaz: her kategori
        # AI tarafından terimsiz bir yoruma çevrilir ve yalnız o yorum gider.
        try:
            sonuc["misafir_kategoriler"] = ai_mod.misafir_yorumlari(
                sonuc, "Kişisel", locked_model)
        except Exception as e:
            sonuc["misafir_kategoriler"] = {"_hata": str(e)[:200]}
        kimlik = oturum_mod.kaydet(sonuc, "Kişisel", locked_model,
                                    inp.model_dump())
        pay = oturum_mod.misafir_payi(sonuc)
        pay["oturum"] = kimlik
        pay["ai"] = {"model": locked_model, "locked": True}
        return pay
    if inp.yorumla:
        try:
            sonuc["kisisel"] = ai_mod.kisisellestir(sonuc, "Kişisel", locked_model)
        except Exception:
            sonuc["kisisel"] = {}
    # HAMLE PENCERESİ — hangi hafta hangi hamleye uygun.
    # Silinen Yürüyen Berzah çatalın ne zaman tetiklendiğini söylüyordu:
    # TARİF. Bu modül ne yapılabileceğini söylüyor: KARAR.
    #
    # Lunasyon (6 ay) ve sükût burada ayrıca hesaplanıyor; ikisi de ucuz
    # (0.04 + 0.02 sn) ve hamle penceresi ikisine de dayanıyor.
    try:
        from .lunasyon import lunasyon_takvimi as _lt_f
        from .sukut import sukut_haritasi as _sk_f
        from .hamle import hamle_penceresi as _hp_f
        _sr_hamle = ref.get("chart") if ref.get("aktif") else None
        _jd_hamle = float(ref["jd"])
        _lt = _lt_f(ch, _sr_hamle, jd_bas=_jd_hamle, ay_sayisi=6)
        _sk = _sk_f(ch, jd_bas=_jd_hamle)
        sonuc["hamle_penceresi"] = _hp_f(
            {"berzah_v2": v2, "yas_katmani": sonuc.get("yas_katmani") or {},
             "kabzbast_v1_m66_74": sonuc.get("kabzbast_v1_m66_74") or {},
             "lunasyon_olaylari": _lt.get("olaylar") or [], "sukut": _sk},
            hafta=12, jd_bas=_jd_hamle)
    except Exception as e:
        sonuc["hamle_penceresi"] = {"hata": str(e)[:200]}

    # YAKINSAMA ÇEKİRDEĞİ — "ÖNCE BUNLARI OKU" bloğunun yerine.
    # O blok beş bulguyu ELLE seçiyordu: sabit liste, her haritada aynı
    # beşi. Bu modül her haritada KENDİ ağırlık merkezini buluyor ve kaç
    # bağımsız katmandan geldiğini söylüyor.
    #
    # sonuc sözlüğü kurulduktan SONRA çağrılır: çelişki ve direnç
    # katmanlarını da okuyor.
    try:
        from .yakinsama import yakinsama as _yk_f
        sonuc["yakinsama"] = _yk_f({
            "berzah_v2": v2, "human_design": sonuc.get("human_design") or {},
            "deneme_modulleri": sonuc.get("deneme_modulleri") or {},
            "yas_katmani": sonuc.get("yas_katmani") or {},
            "celiskiler": sonuc.get("celiskiler") or [],
            "direnc": sonuc.get("direnc") or [],
            "duraklama_izi": sonuc.get("duraklama_izi") or {}})
    except Exception as e:
        # Sessiz yutma YASAK: hata görünmezse blok bağlama hiç girmez ve
        # kimse fark etmez. Bu bir kez yaşandı.
        sonuc["yakinsama"] = {"hata": str(e)[:200]}

    # MİZAN-5 ikinci geçişi: hamle penceresi ve yakınsama artık mevcut.
    try:
        sonuc["oruntu_omurgasi"] = oruntu_omurgasi(sonuc)
    except Exception as e:
        sonuc["oruntu_omurgasi"] = {"hata": str(e)[:200]}

    # AYÂR tek analiz-sonu ölçüm kancasıdır; v13.4'te aynı çağrı SİCİL'in
    # ham, kimliksiz endeks kaydını da yazar. Böylece üretim akışında iki ayrı
    # kalıcılık kancası yarışmaz.
    try:
        from .ayar import kaydet as _ayar_kaydet
        _ayar_kaydet(sonuc)
    except Exception:
        pass

    sonuc["ai"] = {"model": locked_model, "locked": True}
    kimlik = oturum_mod.kaydet(sonuc, "Kişisel", locked_model, inp.model_dump())
    sonuc["oturum"] = kimlik
    return sonuc



@app.get("/api/v1/misafir-kategoriler")
def api_misafir_kategoriler():
    """Misafir kategorilerinin kimlik ve başlıkları — arayüz sırayı buradan alır."""
    return {"kategoriler": [{"kod": k, "ad": ad}
                            for k, ad, _o in ai_mod.MISAFIR_KATEGORI]}


_VERI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


# ============================================================================
# ÖN-KAYIT DEFTERİ — yalnız yönetici (ADMIN_SIFRE tanımlıysa parola şart)
# ============================================================================
def _yonetici_mi(request: Request) -> None:
    """Defter yöneticiye özeldir: puanlama danışana gösterilecek bir şey değil."""
    if not ADMIN_SIFRE:
        return                     # parola tanımlı değilse ayrım da yok
    verilen = request.headers.get("x-zic-yonetici", "")
    if not _secrets.compare_digest(str(verilen), ADMIN_SIFRE):
        raise HTTPException(status_code=401, detail="Yönetici parolası gerekli.")

@app.get("/api/v1/ulkeler")
def api_ulkeler():
    """244 ülkenin dizini. Şehir verisi ülke başına ayrı dosyada tutulur ve
    yalnız seçildiğinde indirilir; toplam 2.3 MB'lık veri tek seferde
    yüklenmez."""
    yol = os.path.join(_VERI, "ulkeler.json")
    if not os.path.isfile(yol):
        raise HTTPException(status_code=500, detail="Ülke dizini bulunamadı.")
    return FileResponse(yol, media_type="application/json")


# Ülke verisi DİSKTE iki dosyada tutulur (önceden 244 ayrı dosyaydı):
#   turkiye.json — en sık istenen, 77 KB, tek başına
#   dunya.json   — kalan 243 ülke, 2.3 MB, süreç belleğine bir kez alınır
# Ağda değişen bir şey yok: istemci yine yalnız seçtiği ülkenin dilimini
# alır. Değişikliğin sebebi GitHub'ın web yükleyicisinin 100 dosya sınırı
# ve 244 küçük dosyanın depoyu gereksiz şişirmesiydi.
_DUNYA: Optional[dict] = None


def _dunya_yukle() -> dict:
    global _DUNYA
    if _DUNYA is None:
        yol = os.path.join(_VERI, "dunya.json")
        with open(yol, encoding="utf-8") as f:
            _DUNYA = json.load(f)
    return _DUNYA


@app.get("/api/v1/ulke/{kod}")
def api_ulke(kod: str):
    """Tek ülkenin bölge → şehir ağacı. Her şehirde saat dilimi de gelir."""
    kod = "".join(ch for ch in kod.upper() if ch.isalpha())[:2]
    if kod == "TR":
        yol = os.path.join(_VERI, "turkiye.json")
        if not os.path.isfile(yol):
            raise HTTPException(status_code=500, detail="Türkiye verisi eksik.")
        return FileResponse(yol, media_type="application/json")
    try:
        d = _dunya_yukle().get(kod)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ülke verisi okunamadı: {e}")
    if not d:
        raise HTTPException(status_code=404, detail=f"{kod} için veri yok.")
    return {"kod": kod, "ad": d["ad"], "bolgeler": d["bolgeler"]}


@app.post("/api/v1/iliski")
def api_iliski(inp: IliskiInput, request: Request):
    _sinir(request, "agir")
    """Sinastri veya kompozit. Kompozitte ilişkinin kendi BERZAH haritası kurulur."""
    try:
        locked_model = ai_mod.kilitli_model(inp.a.model)
    except ai_mod.AIHatasi as e:
        raise HTTPException(status_code=422, detail=str(e))
    ca, cb = _chart(inp.a), _chart(inp.b)
    ad_a, ad_b = inp.a.name or "A", inp.b.name or "B"
    ortak = {"servis": VERSION,
             "girdi": {"mod": inp.mod, "A": {"ad": ad_a, "an": jd_to_iso(ca.jd_ut),
                                             "tz": ca.tz_offset, "tz_kaynak": ca.tz_source},
                       "B": {"ad": ad_b, "an": jd_to_iso(cb.jd_ut),
                             "tz": cb.tz_offset, "tz_kaynak": cb.tz_source},
                       "an": jd_to_iso(ca.jd_ut), "tz": ca.tz_offset,
                       "tz_kaynak": ca.tz_source, "ev_sistemi": ca.house_system}}
    if inp.mod == "kompozit":
        ortak["kompozit"] = kompozit(ca, cb, ad_a, ad_b)
    else:
        ortak["sinastri"] = sinastri(ca, cb, ad_a, ad_b)
    # Davison: kompozitin tamamlayıcısı — gerçek bir an olduğu için ilişkinin
    # ZAMANLAMASI buradan okunur. Deklinasyon sinastrisi ise boylamda
    # görünmeyen bağları verir.
    try:
        ortak["davison"] = davison(ca, cb, ad_a, ad_b)
    except Exception as e:
        ortak["davison"] = {"hata": str(e)[:150]}
    try:
        ortak["deklinasyon"] = deklinasyon_sinastri(ca, cb, ad_a, ad_b)
    except Exception as e:
        ortak["deklinasyon"] = {"hata": str(e)[:150]}
    ortak["A_berzah"] = full_v2(ca)
    ortak["B_berzah"] = full_v2(cb)   # her iki kişi kendi topolojisini alır
    # Ek katmanlar artık HER İKİ kişi için de uygulanır (v2.7). Önceden yalnız
    # kişisel modda ve yalnız A için hesaplanıyordu; ilişki modunda hiç yoktu.
    if inp.a.isim:
        ortak["A_isim"] = isim_tecellisi(ca, inp.a.isim, inp.a.anne)
    if inp.b.isim:
        ortak["B_isim"] = isim_tecellisi(cb, inp.b.isim, inp.b.anne)
    for etiket, kis, gir in (("A", ca, inp.a), ("B", cb, inp.b)):
        if not gir.sr_year:
            continue
        ortak[f"{etiket}_solar"] = run_kabzbast(
            kis, days=180, sr_year=gir.sr_year).get("solar_return")
        try:
            sjd = solar_return_jd(kis, gir.sr_year)
            sch = chart_at_jd(sjd, kis.lat, kis.lng, f"SR {gir.sr_year}",
                              gir.house_system)
            ortak[f"{etiket}_solar_v2"] = {"yil": gir.sr_year, "an": jd_to_iso(sjd),
                                           "berzah_v2": full_v2(sch, topoloji=False)}
        except Exception:
            pass
    # İlişki modunda da Hüküm/Çatal satırları kişiselleştirilir; v3.2'de yalnız
    # kişisel modda çalışıyordu ve sinastri/kompozit şablon metinle kalıyordu.
    if inp.rol == "misafir":
        mod_ad = "Sinastri" if inp.mod == "sinastri" else "Kompozit"
        try:
            ortak["misafir_kategoriler"] = ai_mod.misafir_yorumlari(
                ortak, mod_ad, locked_model)
        except Exception as e:
            ortak["misafir_kategoriler"] = {"_hata": str(e)[:200]}
        kimlik = oturum_mod.kaydet(ortak, mod_ad, locked_model,
                                    {"a": inp.a.model_dump(), "b": inp.b.model_dump()})
        pay = oturum_mod.misafir_payi(ortak)
        pay["oturum"] = kimlik
        pay["girdi"]["mod"] = inp.mod
        pay["ai"] = {"model": locked_model, "locked": True}
        return pay
    if getattr(inp.a, "yorumla", True):
        try:
            ortak["kisisel"] = ai_mod.kisisellestir(
                ortak, "Sinastri" if inp.mod == "sinastri" else "Kompozit",
                locked_model)
        except Exception:
            ortak["kisisel"] = {}
    ortak["ai"] = {"model": locked_model, "locked": True}
    kimlik = oturum_mod.kaydet(ortak,
        "Sinastri" if inp.mod == "sinastri" else "Kompozit", locked_model,
        {"a": inp.a.model_dump(), "b": inp.b.model_dump()})
    ortak["oturum"] = kimlik
    return ortak


@app.get("/api/v1/ai-health")
def api_ai_health(request: Request):
    _sinir(request, "ai")
    """Gateway ayarlarını doğrular — Render'da kurulum sonrası buraya bakın."""
    return ai_mod.saglik()


ADMIN_SIFRE = os.environ.get("ADMIN_SIFRE", "")
# Siteye erişim anahtarı: tanımlıysa arayüz ve API'nin tamamı kapalı hâle gelir.
# Servis herkese açık bir URL'de duruyor ve her analiz AI kotası harcıyor;
# bu anahtar, bağlantıyı bilen herkesin kotayı yakmasını engeller.
ERISIM_ANAHTARI = os.environ.get("ZIC_ERISIM_ANAHTARI", "")


def _erisim_kontrol(request: "Request") -> None:
    if not ERISIM_ANAHTARI:
        return
    verilen = (request.headers.get("x-zic-anahtar")
               or request.query_params.get("anahtar") or "")
    if not _secrets.compare_digest(str(verilen), ERISIM_ANAHTARI):
        raise HTTPException(status_code=401,
                            detail="Erişim anahtarı gerekli.")


@app.get("/api/v1/rol-bilgi")
def api_rol_bilgi():
    """Yönetici girişinin parola isteyip istemediğini bildirir."""
    return {"parola_gerekli": bool(ADMIN_SIFRE),
            "not": ("ADMIN_SIFRE ortam değişkeni tanımlı değilse yönetici "
                    "girişi korumasızdır; rol yalnız görünüm ayrımı olur.")}


@app.post("/api/v1/rol-dogrula")
def api_rol_dogrula(govde: dict, request: Request):
    if not ADMIN_SIFRE:
        return {"ok": True, "not": "Parola tanımlı değil, giriş serbest."}
    _sinir(request, "auth")            # IP başına: 15 dakikada 5 deneme
    # IP tabanlı sınır ilkece atlatılabilir (vekil başlığı, IPv6 havuzu, botnet).
    # Bu yüzden parola için IP'den BAĞIMSIZ küresel bir tavan da var: kaynağı
    # ne olursa olsun 15 dakikada en fazla 20 başarısız deneme.
    _sinir(request, "auth_kuresel")
    # compare_digest: uzunluk ve içerik farkını sabit sürede karşılaştırır
    if _secrets.compare_digest(str(govde.get("parola", "")), ADMIN_SIFRE):
        limit_mod.sifirla("auth", _ip(request))
        return {"ok": True}
    raise HTTPException(status_code=401, detail="Parola hatalı.")


@app.get("/api/v1/ai-saglayicilar")
def api_saglayicilar():
    """Sağlayıcı zincirinin durumu: hangisi aktif, hangisi soğumada."""
    return ai_mod.saglayici_durumu()


@app.post("/api/v1/saglayici-sina")
def api_saglayici_sina(request: Request):
    """
    Her sağlayıcıyı TEK TEK sınar ve hangisinin neden düştüğünü söyler.

    "Danışmana şu an ulaşılamıyor" hatası, zincirdeki BÜTÜN sağlayıcılar
    düştüğünde çıkar. Bu uç, hangisinin ne sebeple düştüğünü gösterir —
    yoksa körlemesine anahtar denemek gerekir.
    """
    _sinir(request, "agir")
    import time as _t
    out = []
    for sg in ai_mod.SAGLAYICILAR:
        t0 = _t.time()
        try:
            metin, _p = ai_mod._tek_saglayici_dene(
                sg, "Yalnız 'tamam' yaz.", [{"role": "user", "content": "test"}])
            out.append({"ad": sg["ad"], "protokol": sg["protokol"],
                        "base": sg["base"], "durum": "çalışıyor",
                        "sure": round(_t.time() - t0, 2),
                        "yanit": (metin or "")[:60]})
        except Exception as e:
            out.append({"ad": sg["ad"], "protokol": sg["protokol"],
                        "base": sg["base"], "durum": "düştü",
                        "sure": round(_t.time() - t0, 2),
                        "hata": str(e)[:220]})
    calisan = [x for x in out if x["durum"] == "çalışıyor"]
    return {
        "toplam": len(out), "calisan": len(calisan),
        "saglayicilar": out,
        "teshis": ("Hiçbir sağlayıcı yanıt vermiyor — 'Danışmana şu an "
                   "ulaşılamıyor' hatasının sebebi bu. Aşağıdaki hata "
                   "metinlerine bakın."
                   if not calisan else
                   f"{len(calisan)} sağlayıcı çalışıyor; ilki "
                   f"{calisan[0]['ad']}."),
    }


@app.get("/api/v1/ai-models")
def api_ai_models():
    """Gateway'deki modelleri listeler — arayüzdeki danışman seçici bunu kullanır."""
    try:
        return ai_mod.modelleri_getir()
    except ai_mod.OranSiniri as e:
        raise HTTPException(status_code=429, detail=str(e))
    except ai_mod.AIHatasi as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/api/v1/solar-return-bagla")
def api_solar_return_bagla(inp: SolarReturnAttachInput, request: Request):
    """Mevcut kişisel oturuma Solar Return bağlar; Hüküm ve metni yeniden üretir."""
    _sinir(request, "agir")
    o = oturum_mod.getir(inp.oturum)
    if not o:
        raise HTTPException(status_code=410, detail="Oturum süresi doldu.")
    if o.get("mod") != "Kişisel":
        raise HTTPException(status_code=422, detail="Dinamik Solar Return şu an kişisel analizde destekleniyor.")
    dg = dict(o.get("dogum") or {})
    if not dg:
        raise HTTPException(status_code=422, detail="Oturumda doğum verisi bulunamadı.")
    dg["sr_year"] = inp.year
    dg["model"] = o.get("model")
    try:
        bi = BirthInput(**dg)
        ch = _chart(bi)
        ref = referans_ani(ch, inp.year)
        sch = ref["chart"]
        solar = {"yil": ref["yil"], "an": ref["an"],
                 "berzah_v2": full_v2(sch, topoloji=False)}
        analiz = o["analiz"]
        analiz["referans"] = {k: ref.get(k) for k in ("an", "yil", "kaynak", "bugun", "fark_yil", "aktif")}
        analiz["solar_v2"] = solar
        # Sonradan SR bağlamak yalnız harita halkasını değiştirmemeli. v13.4.1'de
        # yaş/duraklama/kayıp zaman eski bugünde kaldığı için Hüküm yeni SR ile
        # eski hayat evresini aynı metinde birleştiriyordu; referansa bağlı tüm
        # hafif katmanlar burada aynı jd ile yenilenir.
        try:
            from .duraklama import duraklama_izi
            analiz["duraklama_izi"] = duraklama_izi(ch, bugun_jd=float(ref["jd"]))
        except Exception as _e:
            analiz["duraklama_izi"] = {"hata": str(_e)[:200]}
        try:
            from .yas import yas_katmani
            analiz["yas_katmani"] = yas_katmani(ch, jd=float(ref["jd"]))
        except Exception as _e:
            analiz["yas_katmani"] = {"hata": str(_e)[:200]}
        try:
            from .omur import kayip_zaman
            analiz["kayip_zaman"] = kayip_zaman(ch, bugun_jd=float(ref["jd"]))
        except Exception as _e:
            analiz["kayip_zaman"] = {"hata": str(_e)[:200]}
        try:
            analiz["sira_cevrimi"] = sira_cevrimi(
                ch, (analiz.get("berzah_v2") or {}).get("alan_topolojisi"),
                bi.isim, bi.anne, simdi_jd=float(ref["jd"]))
        except Exception as _e:
            analiz["sira_cevrimi"] = {"hata": str(_e)[:200]}
        try:
            analiz["kartografi"] = kartografi_katmani(
                ch, sr_jd=float(ref["jd"]), izdusum=False, solar_aktif=True)
        except Exception as _e:
            analiz["kartografi"] = {"hata": str(_e)[:200]}
        try:
            from .lunasyon import lunasyon_takvimi as _lt_f
            from .sukut import sukut_haritasi as _sk_f
            from .hamle import hamle_penceresi as _hp_f
            _lt = _lt_f(ch, sch, jd_bas=float(ref["jd"]), ay_sayisi=6)
            _sk = _sk_f(ch, jd_bas=float(ref["jd"]))
            analiz["hamle_penceresi"] = _hp_f(
                {"berzah_v2": analiz.get("berzah_v2") or {},
                 "yas_katmani": analiz.get("yas_katmani") or {},
                 "kabzbast_v1_m66_74": analiz.get("kabzbast_v1_m66_74") or {},
                 "lunasyon_olaylari": _lt.get("olaylar") or [], "sukut": _sk},
                hafta=12, jd_bas=float(ref["jd"]))
        except Exception as _e:
            analiz["hamle_penceresi"] = {"hata": str(_e)[:200]}
        tr = analiz.get("transit")
        if isinstance(tr, dict) and "hata" not in tr:
            tr["referans_disi"] = True
            tr["referans_fark_yil"] = ref.get("fark_yil")
            tr["referans_an"] = ref.get("an")
        mn = analiz.get("maneviyat")
        if isinstance(mn, dict) and "hata" not in mn:
            mn["referans_disi"] = True
            mn["referans_fark_yil"] = ref.get("fark_yil")
        for _k in ("zaman_seridi", "sukut", "algi_esigi", "donus_noktasi"):
            analiz.pop(_k, None)
        analiz["hukum"] = hukum_baglam(analiz.get("berzah_v2") or {}, solar)
        try:
            analiz["oruntu_omurgasi"] = oruntu_omurgasi(analiz)
        except Exception as _e:
            analiz["oruntu_omurgasi"] = {"hata": str(_e)[:200]}
        # Sahne defteri ve bağlam özeti eski yılın cümlelerini tutmamalı. Aynı
        # oturum kimliği korunur ama içerik önbelleği referans değişince boşalır.
        try:
            from .sahne import oturum_onbellek_sil
            oturum_onbellek_sil(inp.oturum)
        except Exception:
            pass
        if bi.yorumla:
            analiz["kisisel"] = ai_mod.kisisellestir(analiz, "Kişisel", o.get("model"))
        o["dogum"] = bi.model_dump()
        o["revision"] = int(o.get("revision") or 1) + 1
        try:
            from .ayar import kaydet as _ayar_kaydet
            _ayar_kaydet(analiz)
        except Exception:
            pass
        degisen = {k: analiz.get(k) for k in (
            "referans", "solar_v2", "hukum", "duraklama_izi", "yas_katmani",
            "kayip_zaman", "sira_cevrimi", "kartografi", "hamle_penceresi",
            "transit", "maneviyat", "oruntu_omurgasi", "kisisel")}
        return {"solar_v2": solar, "hukum": analiz["hukum"],
                "referans": analiz.get("referans") or {}, "degisen": degisen,
                "oruntu_omurgasi": analiz.get("oruntu_omurgasi") or {},
                "kisisel": analiz.get("kisisel") or {},
                "revision": o["revision"],
                "ai": {"model": o.get("model"), "locked": True}}
    except ai_mod.OranSiniri as e:
        raise HTTPException(status_code=429, detail=str(e))
    except ai_mod.AIHatasi as e:
        raise HTTPException(status_code=503, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Solar Return bağlanamadı: {e}")


@app.post("/api/v1/chat")
def api_chat(inp: SohbetInput, request: Request):
    _sinir(request, "ai")
    """Analiz JSON'u üzerinden astroloji danışmanı yanıtı."""
    analiz, mod, model = _oturum_baglam(inp.oturum, inp.analiz, inp.mod, inp.model)
    if not analiz:
        raise HTTPException(status_code=422, detail="Analiz verisi yok.")
    try:
        baglam = ai_mod.baglam_ozeti(analiz, mod)
        metin, protokol, devam = ai_mod.danisman_yaniti(
            inp.soru, baglam, [m.model_dump() for m in inp.gecmis],
            mod, model, gosterilen=inp.gosterilen)
        # Gerçekten KULLANILAN model bildirilir. Önceden istenen model
        # yansıtılıyordu; izin verilmeyen bir model ikame edilse bile yanıt
        # onu kullanmış gibi görünüyor, kısıtlamanın çalışıp çalışmadığı
        # dışarıdan anlaşılamıyordu.
        return {"yanit": metin, "protokol": protokol,
                "model": model,
                "devam_turu": devam, "baglam_karakter": len(baglam)}
    except ai_mod.OranSiniri as e:
        raise HTTPException(status_code=429, detail=str(e))
    except ai_mod.AIHatasi as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/api/v1/chat-bolum")
def api_chat_bolum(inp: BolumInput, request: Request):
    _sinir(request, "ai")
    """Eski bölüm düğmeleri de v13.3 kapsam/defter/iddia motorunu kullanır."""
    try:
        from .sahne import v1_bolum_yanit
        return v1_bolum_yanit(inp.model_dump())
    except ai_mod.OranSiniri as e:
        raise HTTPException(status_code=429, detail=str(e))
    except ai_mod.AIHatasi as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/api/v1/dinamik")
def api_dinamik(inp: DinamikInput, request: Request):
    _sinir(request, "agir")
    """
    A · YÜRÜYEN BERZAH — eşiğin zaman içindeki yörüngesi ve çatallanma takvimi.
    Ayrı uçta: tarama birkaç yüz efemeris çağrısı ister, ana analizi yavaşlatmaz.
    """
    from .engine_mass import compute_masses
    from .field_dynamics import yuruyen_berzah
    ch = _chart(inp)
    ms = compute_masses(ch)
    try:
        return {"girdi": {"an": jd_to_iso(ch.jd_ut), "yil": inp.yil},
                "yuruyen_berzah": yuruyen_berzah(ch, ms, yil=inp.yil)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dinamik tarama başarısız: {e}")


@app.post("/api/v1/sentez")
def api_sentez(inp: SentezInput, request: Request):
    """Bütün katmanları tek bir okumada birleştirir."""
    _sinir(request, "ai")
    analiz, mod, model = _oturum_baglam(inp.oturum, inp.analiz, inp.mod, inp.model)
    if not analiz:
        raise HTTPException(status_code=422, detail="Analiz verisi yok.")
    try:
        return {"sentez": ai_mod.butunsel_sentez(analiz, mod, inp.rol, model)}
    except ai_mod.OranSiniri as e:
        raise HTTPException(status_code=429, detail=str(e))
    except ai_mod.AIHatasi as e:
        raise HTTPException(status_code=503, detail=str(e))


# ============================================================================
# DANIŞAN DEFTERİ — okumaların birbirinin üstüne binmesi (yalnız yönetici)
# ============================================================================

@app.post("/api/v1/kartografi-cizgi")
def api_kartografi_cizgi(inp: BirthInput, request: Request):
    """
    Tam ASC/DSC eğri noktaları — harita çizimi için. Ana analizden
    çıkarıldı çünkü 102 KB tutuyor ve arayüz özet değerleri kullanıyor.
    """
    _sinir(request, "agir")
    ch = _chart(inp)
    try:
        from .kartografi import astrokartografi
        return astrokartografi(ch.jd_ut)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Çizgi: {e}")


@app.post("/api/v1/onerilen-sorular")
def api_onerilen_sorular(inp: SoruInput, request: Request):
    """
    Bu haritada en olası üç takip sorusunu döner. AI ÇAĞRISI YOK —
    yalnız hangi soruların anlamlı olduğunu hesaplar. İstemci bunları
    arka planda cevaplatır, danışman tıkladığında hazır olur.
    """
    analiz = inp.analiz
    model = inp.model
    if inp.oturum:
        o = oturum_mod.getir(inp.oturum)
        if not o:
            raise HTTPException(status_code=410, detail="Oturum süresi doldu.")
        analiz = o["analiz"]
        model = o.get("model") or model
    if not analiz:
        raise HTTPException(status_code=422, detail="Analiz verisi yok.")
    from . import sorular as SR
    try:
        kodlar = SR.onerilen(analiz, 3)
    except Exception:
        kodlar = ["g6", "k1", "z1"]
    return {"kodlar": kodlar,
            "sorular": [s.sozluk() for s in SR.getir(kodlar)]}


@app.get("/api/v1/sorular")
def api_sorular(kategori: Optional[str] = None):
    """Danışanın seçebileceği soru kataloğu."""
    from . import sorular as SR
    return SR.liste(kategori)


def _zaman_chart_ref(inp: LunasyonInput):
    """Eski ve yeni zaman uçlarını aynı doğum + referans sözleşmesine bağlar.

    Portalın eski sürümleri yalnız ``analiz.girdi`` özetini gönderebiliyordu;
    yeni sürüm tam ``BirthInput`` yollar. İki yol burada birleşir, böylece
    Sükût/Eşik/Dönüş gibi uçlar kendi başına bugüne düşmez.
    """
    g = inp.dogum or (inp.analiz.get("girdi") or {})
    if not g:
        raise HTTPException(status_code=422, detail="Doğum verisi yok.")
    try:
        if g.get("year") is not None:
            bi = BirthInput(**g)
        else:
            an = str(g.get("an", ""))
            sv = inp.analiz.get("solar_v2") or {}
            sy = sv.get("yil") if isinstance(sv, dict) and not sv.get("hata") else None
            bi = BirthInput(
                year=int(an[:4]), month=int(an[5:7]), day=int(an[8:10]),
                hour=int(an[11:13]), minute=int(an[14:16]),
                lat=float(g.get("enlem", g.get("lat", 0)) or 0),
                lng=float(g.get("boylam", g.get("lng", 0)) or 0),
                tz_offset=0.0, house_system=g.get("ev_sistemi", "P"),
                sr_year=int(sy) if sy not in (None, "") else None)
        ch = _chart(bi)
        ref = referans_ani(ch, bi.sr_year)
        return ch, ref, bi
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Doğum verisi okunamadı: {e}")


@app.post("/api/v1/lunasyon")
def api_lunasyon(inp: LunasyonInput, request: Request):
    """
    Bir yıllık lunasyon takvimi: yeni aylar, dolunaylar ve tutulmalar,
    natal ve solar haritaya oturtulmuş, haftalara bölünmüş.

    AI çağrısı YOK — saf hesap, hızlıdır.
    """
    _sinir(request, "agir")
    ch, ref, _bi = _zaman_chart_ref(inp)
    from .lunasyon import lunasyon_takvimi, bu_hafta
    sr = ref.get("chart") if ref.get("aktif") else None
    try:
        tk = lunasyon_takvimi(ch, sr, jd_bas=float(ref["jd"]),
                               ay_sayisi=inp.ay_sayisi)
        tk["solar_var"] = bool(ref.get("aktif"))
        tk["solar_yil"] = ref.get("yil")
        tk["referans"] = {k: ref.get(k) for k in ("an", "yil", "kaynak", "bugun", "fark_yil", "aktif")}
        tk["bu_hafta"] = bu_hafta(tk)
        return tk
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Takvim: {e}")


@app.post("/api/v1/lunasyon-okuma")
def api_lunasyon_okuma(inp: LunasyonInput, request: Request):
    """Seçilen gök olayının bu kişide neyi görünür kıldığı."""
    _sinir(request, "ai")
    analiz, mod, model = _oturum_baglam(inp.oturum, inp.analiz, inp.mod, inp.model)
    if not analiz:
        raise HTTPException(status_code=422, detail="Analiz verisi yok.")
    olay = inp.dogum or {}
    if not olay.get("tur"):
        raise HTTPException(status_code=422, detail="Olay verisi yok.")
    try:
        return {"yanit": ai_mod.haftalik_okuma(analiz, olay, mod,
                                               inp.rol, model)}
    except ai_mod.OranSiniri as e:
        raise HTTPException(status_code=429, detail=str(e))
    except ai_mod.AIHatasi as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/api/v1/donus-noktasi")
def api_donus(inp: LunasyonInput, request: Request):
    """
    Dönüş noktası: yavaş gezegenlerin bir daha gelmeyecek kapıları.

    Ayrı uçta çünkü PAHALI (~3.5 sn): dört yavaş gezegen × on iki nokta ×
    dört açı, doğumdan kırk yıl ileriye taranıyor. Ana analizi ikiye
    katlardı. Kartografi'nin arz izdüşümüyle aynı kalıp.
    """
    _sinir(request, "agir")
    ch, ref, _bi = _zaman_chart_ref(inp)
    from .omur import donus_noktasi
    try:
        out = donus_noktasi(ch, bugun_jd=float(ref["jd"]))
        out["referans"] = {k: ref.get(k) for k in ("an", "yil", "kaynak", "bugun", "fark_yil", "aktif")}
        return out
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dönüş: {e}")


@app.post("/api/v1/sukut")
def api_sukut(inp: LunasyonInput, request: Request):
    """
    Sükût haritası: gökyüzünün sustuğu aralıklar. AI çağrısı yok.
    Ayrıca `soru` alanına bir tarih verilirse yanlışlama sorgusu çalışır.
    """
    _sinir(request, "agir")
    ch, ref, _bi = _zaman_chart_ref(inp)
    from .sukut import sukut_haritasi, sukut_sorgusu
    try:
        h = sukut_haritasi(ch, jd_bas=float(ref["jd"]))
        h["referans"] = {k: ref.get(k) for k in ("an", "yil", "kaynak", "bugun", "fark_yil", "aktif")}
        t = (inp.soru or "").strip()
        if len(t) == 10 and t[4] == "-":
            h["sorgu"] = sukut_sorgusu(h, t)
        return h
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sükût: {e}")


@app.post("/api/v1/esik")
def api_esik(inp: LunasyonInput, request: Request):
    """Algı eşiği ve türetilmiş orb. AI çağrısı yok."""
    _sinir(request, "agir")
    ch, ref, _bi = _zaman_chart_ref(inp)
    from .esik import algi_esigi, orb_karsilastirma
    from .sukut import sukut_haritasi
    try:
        h = sukut_haritasi(ch, jd_bas=float(ref["jd"]))
        e = algi_esigi(ch, h)
        if "hata" in e:
            raise HTTPException(status_code=500, detail=e["hata"])
        e["orb_karsilastirma"] = orb_karsilastirma(ch, e)
        e["referans"] = {k: ref.get(k) for k in ("an", "yil", "kaynak", "bugun", "fark_yil", "aktif")}
        return e
    except HTTPException:
        raise
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Eşik: {ex}")


@app.post("/api/v1/esik-okuma")
def api_esik_okuma(inp: LunasyonInput, request: Request):
    """Algı eşiğinin bu kişide ne anlama geldiği."""
    _sinir(request, "ai")
    analiz, mod, model = _oturum_baglam(inp.oturum, inp.analiz, inp.mod, inp.model)
    if not analiz or not inp.dogum:
        raise HTTPException(status_code=422, detail="Veri eksik.")
    try:
        return {"yanit": ai_mod.esik_okuma(
            analiz, inp.dogum, (inp.dogum or {}).get("orb_karsilastirma"),
            mod, inp.rol, model)}
    except ai_mod.OranSiniri as e:
        raise HTTPException(status_code=429, detail=str(e))
    except ai_mod.AIHatasi as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/api/v1/sukut-okuma")
def api_sukut_okuma(inp: LunasyonInput, request: Request):
    """Sükût haritasının bu kişide ne anlama geldiği."""
    _sinir(request, "ai")
    analiz, mod, model = _oturum_baglam(inp.oturum, inp.analiz, inp.mod, inp.model)
    if not analiz:
        raise HTTPException(status_code=422, detail="Analiz verisi yok.")
    if not inp.dogum:
        raise HTTPException(status_code=422, detail="Sükût haritası yok.")
    try:
        return {"yanit": ai_mod.sukut_okuma(analiz, inp.dogum, mod,
                                            inp.rol, model)}
    except ai_mod.OranSiniri as e:
        raise HTTPException(status_code=429, detail=str(e))
    except ai_mod.AIHatasi as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/api/v1/lunasyon-sohbet")
def api_lunasyon_sohbet(inp: LunasyonInput, request: Request):
    """Seçili gök olayı üzerine karşılıklı sohbet."""
    _sinir(request, "ai")
    analiz, mod, model = _oturum_baglam(inp.oturum, inp.analiz, inp.mod, inp.model)
    if not analiz:
        raise HTTPException(status_code=422, detail="Analiz verisi yok.")
    olay = inp.dogum or {}
    if not olay.get("tur"):
        raise HTTPException(status_code=422, detail="Olay verisi yok.")
    if not inp.soru.strip():
        raise HTTPException(status_code=422, detail="Soru boş.")
    try:
        return {"yanit": ai_mod.lunasyon_sohbet(analiz, olay, inp.soru,
                                                inp.gecmis, mod, inp.rol,
                                                model)}
    except ai_mod.OranSiniri as e:
        raise HTTPException(status_code=429, detail=str(e))
    except ai_mod.AIHatasi as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/api/v1/rapor-bolum")
def api_rapor_bolum(inp: RaporInput, request: Request):
    """
    Raporun TEK bölümünü üretir.

    On bölümü tek istekte üretmek mümkün değil: gerçek modelde bölüm
    başına ~40 saniye, toplam ~400 saniye eder ve hiçbir vekil buna izin
    vermez. Bölümler istemciden tek tek istenir; her istek rahatça
    sınırın altında kalır ve kullanıcı ilerlemeyi görür.
    """
    _sinir(request, "ai")
    analiz, mod, model = _oturum_baglam(inp.oturum, inp.analiz, inp.mod, inp.model)
    if not analiz:
        raise HTTPException(status_code=422, detail="Analiz verisi yok.")
    from .rapor import BOLUMLER
    i = max(0, min(int(inp.sira or 0), len(BOLUMLER) - 1))
    kod, baslik, katmanlar, aranacak = BOLUMLER[i]
    try:
        metin = ai_mod.rapor_bolumu(analiz, baslik, katmanlar, aranacak,
                                    inp.onceki, mod, model, inp.tur)
        return {"sira": i, "toplam": len(BOLUMLER), "kod": kod,
                "baslik": baslik, "metin": metin,
                "son": i == len(BOLUMLER) - 1}
    except ai_mod.OranSiniri as e:
        raise HTTPException(status_code=429, detail=str(e))
    except ai_mod.AIHatasi as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/api/v1/rapor-pdf")
def api_rapor_pdf(govde: dict, request: Request):
    """Toplanan bölümlerden PDF kurar. AI çağrısı yok, hızlıdır."""
    _sinir(request, "agir")
    bolumler = [(str(b.get("baslik", "")), str(b.get("metin", "")))
                for b in (govde.get("bolumler") or []) if b.get("metin")]
    if not bolumler:
        raise HTTPException(status_code=422, detail="Bölüm yok.")
    ad = (str(govde.get("ad") or "Danışan")).strip()[:60] or "Danışan"
    alt = str(govde.get("alt") or "")
    tur = "anlatim" if str(govde.get("tur")) == "anlatim" else "danisan"
    uyari = ("Bu rapor bir gözlem aracıdır; kesin hüküm değildir. Sağlık, "
             "hukuk ve para konularında karar vermeden önce o alanın "
             "uzmanına danışın. Ömür, ölüm tarihi ya da tıbbî teşhis "
             "üretilmez.")
    if tur == "anlatim":
        uyari = ("DANIŞMAN NÜSHASI — danışana verilmez. Köşeli parantezli "
                 "satırlar sesli OKUNMAZ; onlar sana yönerge. " + uyari)
    from .rapor import pdf_uret
    baslik_ = (f"{ad} · Anlatım metni" if tur == "anlatim"
               else f"{ad} · Doğum Haritası Okuması")
    # Kapağa natal çark ve danışman adı. Doğum haritası raporunda haritanın
    # kendisi yoktu; kişi "haritam nerede" diye sorar ve haklıdır.
    ch_ = None
    g_ = govde.get("dogum") or {}
    if g_:
        try:
            ch_ = _chart(BirthInput(**{k: g_[k] for k in
                                       ("year", "month", "day", "hour",
                                        "minute", "lat", "lng") if k in g_},
                                    tz_offset=float(g_.get("tz_offset", 0)),
                                    house_system=g_.get("ev_sistemi", "P")))
        except Exception:
            ch_ = None
    danisman_ = str(govde.get("danisman") or
                    os.environ.get("ZIC_DANISMAN", ""))[:80]
    try:
        veri = pdf_uret(baslik_, alt, bolumler, uyari, tur,
                        chart=ch_, danisman=danisman_)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF üretilemedi: {e}")
    from fastapi.responses import Response
    dosya = re.sub(r"[^A-Za-z0-9_-]", "_", ad)[:40] or "rapor"
    ek = "_anlatim" if tur == "anlatim" else "_okuma"
    return Response(content=veri, media_type="application/pdf",
                    headers={"Content-Disposition":
                             f'attachment; filename="{dosya}{ek}.pdf"'})


@app.post("/api/v1/rapor")
def api_rapor(inp: RaporInput, request: Request):
    """
    Kişiyi baştan sona anlatan uzun rapor. On bölüm ayrı ayrı üretilip
    birleştirilir; PDF ya da düz metin döner.
    """
    _sinir(request, "agir")
    analiz, mod, model = _oturum_baglam(inp.oturum, inp.analiz, inp.mod, inp.model)
    if not analiz:
        raise HTTPException(status_code=422, detail="Analiz verisi yok.")
    g = analiz.get("girdi", {})
    ad = (g.get("ad") or g.get("isim") or "Danışan").strip() or "Danışan"
    try:
        bolumler = ai_mod.tam_rapor(analiz, mod, model)
    except ai_mod.OranSiniri as e:
        raise HTTPException(status_code=429, detail=str(e))
    except ai_mod.AIHatasi as e:
        raise HTTPException(status_code=503, detail=str(e))
    alt = f"{g.get('an', '')}"
    if g.get("ev_sistemi"):
        alt += f" · ev sistemi {g['ev_sistemi']}"
    uyari = ("Bu rapor bir gözlem aracıdır; kesin hüküm değildir. Sağlık, "
             "hukuk ve para konularında karar vermeden önce o alanın "
             "uzmanına danışın. Ömür, ölüm tarihi ya da tıbbî teşhis "
             "üretilmez.")
    if inp.bicim == "metin":
        return {"bolumler": [{"baslik": b, "metin": m} for b, m in bolumler]}
    from .rapor import pdf_uret
    try:
        veri = pdf_uret(f"{ad} · Doğum Haritası Okuması", alt, bolumler, uyari)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF üretilemedi: {e}")
    from fastapi.responses import Response
    dosya = re.sub(r"[^A-Za-z0-9_-]", "_", ad)[:40] or "rapor"
    return Response(content=veri, media_type="application/pdf",
                    headers={"Content-Disposition":
                             f'attachment; filename="{dosya}_okuma.pdf"'})


@app.post("/api/v1/soru-cevap")
def api_soru_cevap(inp: SoruInput, request: Request):
    """Seçilen sorulara, her sorunun bağlı olduğu katmanlardan cevap."""
    _sinir(request, "ai")
    analiz, mod, model = _oturum_baglam(inp.oturum, inp.analiz, inp.mod, inp.model)
    if not analiz:
        raise HTTPException(status_code=422, detail="Analiz verisi yok.")
    try:
        metin, kodlar = ai_mod.soru_cevapla(analiz, inp.kodlar, inp.ek_soru,
                                            mod, inp.rol, model)
        return {"yanit": metin, "sorular": kodlar}
    except ai_mod.OranSiniri as e:
        raise HTTPException(status_code=429, detail=str(e))
    except ai_mod.AIHatasi as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/api/v1/manevi")
def api_manevi(inp: ManeviInput, request: Request):
    """Spiritüel çalışma okuması; soru verilirse o katmana özel sohbet."""
    _sinir(request, "ai")
    analiz = inp.analiz
    model = inp.model
    if inp.oturum:
        o = oturum_mod.getir(inp.oturum)
        if not o:
            raise HTTPException(status_code=410, detail="Oturum süresi doldu.")
        analiz = o["analiz"]
        model = o.get("model") or model
    if not analiz:
        raise HTTPException(status_code=422, detail="Analiz verisi yok.")
    try:
        metin, protokol = ai_mod.manevi_yorum(analiz, inp.soru,
                                              inp.gecmis, model)
        return {"yanit": metin, "protokol": protokol}
    except ai_mod.OranSiniri as e:
        raise HTTPException(status_code=429, detail=str(e))
    except ai_mod.AIHatasi as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/api/v1/sehir")
def api_sehir(inp: SehirInput, request: Request):
    """
    Bir yer için çözümleme ve AI yorumu. Soru verilirse o yere özel
    sohbet olarak çalışır.
    """
    _sinir(request, "ai")
    analiz = inp.analiz
    model = inp.model
    if inp.oturum:
        o = oturum_mod.getir(inp.oturum)
        if not o:
            raise HTTPException(status_code=410, detail="Oturum süresi doldu.")
        analiz = o["analiz"]
        model = o.get("model") or model
    if not analiz:
        raise HTTPException(status_code=422, detail="Analiz verisi yok.")
    g = analiz.get("girdi", {})
    try:
        ch = _chart(BirthInput(
            year=int(str(g.get("an", "1990"))[:4]),
            month=int(str(g.get("an", "1990-01"))[5:7]),
            day=int(str(g.get("an", "1990-01-01"))[8:10]),
            hour=int(str(g.get("an", "1990-01-01 00:00"))[11:13]),
            minute=int(str(g.get("an", "1990-01-01 00:00"))[14:16]),
            lat=0.0, lng=0.0, tz_offset=0.0,
            house_system=g.get("ev_sistemi", "P")))
        coz = sehir_cozumle(ch, inp.enlem, inp.boylam, inp.ad)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Yer çözümlenemedi: {e}")
    try:
        metin, protokol = ai_mod.sehir_yorumu(analiz, coz, inp.soru,
                                              inp.gecmis, inp.rol, model)
        return {"cozumleme": coz, "yanit": metin, "protokol": protokol}
    except ai_mod.OranSiniri as e:
        raise HTTPException(status_code=429, detail=str(e))
    except ai_mod.AIHatasi as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/api/v1/arz-izdusumu")
def api_arz_izdusumu(inp: BirthInput, request: Request):
    """
    Modelin karar eşiğinin yeryüzünde nasıl değiştiği. Izgara taraması
    pahalıdır (330 nokta ≈ 3.6 sn), bu yüzden ayrı uçta ve istek üzerine.
    """
    _sinir(request, "agir")
    ch = _chart(inp)
    try:
        from .kartografi import arz_izdusumu
        return arz_izdusumu(ch.jd_ut, house_system=inp.house_system)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"İzdüşüm: {e}")


@app.get("/api/v1/formul-katmanlar")
def api_formul_katmanlar():
    """Formülasyonda seçilebilecek katmanlar."""
    return {"katmanlar": [{"kod": k, "ad": v}
                          for k, v in ai_mod.FORMUL_KATMAN.items()]}


@app.post("/api/v1/formul")
def api_formul(inp: FormulInput, request: Request):
    """Seçilen katmanlar ARASINDA bağ kurar — tek tek özetlemez."""
    _sinir(request, "ai")
    analiz, mod, model = _oturum_baglam(inp.oturum, inp.analiz, inp.mod, inp.model)
    if not analiz:
        raise HTTPException(status_code=422, detail="Analiz verisi yok.")
    try:
        return {"formul": ai_mod.formulasyon(analiz, inp.katmanlar, mod,
                                             inp.rol, model),
                "katmanlar": inp.katmanlar}
    except ai_mod.OranSiniri as e:
        raise HTTPException(status_code=429, detail=str(e))
    except ai_mod.AIHatasi as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/api/v1/kisisellestir")
def api_kisisellestir(inp: KisiselInput, request: Request):
    _sinir(request, "ai")
    """Hüküm ve Çatal satırlarını haritaya özgü hâle getirir (arka planda)."""
    analiz, mod, model = _oturum_baglam(inp.oturum, inp.analiz, inp.mod, inp.model)
    try:
        return {"alanlar": ai_mod.kisisellestir(analiz, mod, model)}
    except ai_mod.OranSiniri as e:
        raise HTTPException(status_code=429, detail=str(e))
    except ai_mod.AIHatasi as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/api/v1/ai-context")
def api_ai_context(inp: BirthInput):
    """Mevcut Astro Pro AI sohbet katmanına verilecek kompakt kanıt kartları."""
    ch = _chart(inp)
    # v13.4.1 yalnız bazı yıllık modülleri seçili SR yılına bağlamıştı; aynı
    # payload içinde yaş/duraklama bugünü, lunasyon ise geçmiş yılı okuyordu.
    # Tek referans nesnesi bu parçalı zaman çapalarını aynı ana toplar.
    ref = referans_ani(ch, inp.sr_year)
    v2 = full_v2(ch)
    kb = run_kabzbast(ch, days=inp.days, sr_year=inp.sr_year)
    cards = []

    def add(cid, baslik, satirlar):
        cards.append({"id": f"BERZAH-{cid}", "family": "İcat · BERZAH Modeli",
                      "baslik": baslik, "kanit": satirlar})

    b = v2.get("berzah")
    if b:
        add("V2-CEKIRDEK", "Kütle Motoru — KD/AD/Berzah",
            [f"KD {v2['KD']['konum']} (ev {v2['KD']['ev']}) · AD {v2['AD']['konum']}",
             f"Berzah {b['konum']} ev {b['ev']} · {b['tur']} · asimetri {b['asimetri']}",
             f"İki deniz: {b['iki_deniz']['a']} ↔ {b['iki_deniz']['b']}",
             f"Çatalın cümlesi: {b['catalin_cumlesi']}",
             f"Berzah hamlesi: {b['berzah_hamlesi']}"])
    if v2.get("kurtarici"):
        k = v2["kurtarici"][0]
        add("KURTARICI", "Altın Açı Kapısı (137.508°)",
            [f"{k['gezegen']} KD'ye {k['aci']}° — talimat bu gezegenden yazılır"])
    add("KABZBAST", "Kabz/Bast Ekseni (m66-67)",
        [kb["m66_67_kabz_bast"]["eksen"]["kutup"],
         f"Σκ·m = {kb['m66_67_kabz_bast']['eksen']['net_egrilik']}"])
    if kb["m68_einstein_rosen"]:
        br = kb["m68_einstein_rosen"][0]
        add("KOPRU", "Birincil Einstein–Rosen Köprüsü (m68)", [br["cumle"]])
    add("GECIT", "Tayy-i Mekân Pencereleri (m74)",
        [f"{w['tarih']} S={w['gecit_skoru']} C={w['C']} ρ/ρc={w['rho_orani']}"
         for w in kb["m74_gecit"]["pencereler"][:5]] or ["pencere yok"])
    add("528HZ", "528 Hz Harmonik İmza (m71)",
        [f"Kök ton {kb['m71_528hz']['kok_ton']} = {kb['m71_528hz']['kok_hz']} Hz"])
    return {"kartlar": cards,
            "sistem_notu": ("Model dili semboliktir; 'kara delik/LQC/528Hz' "
                            "fiziksel nedensellik iddiası değildir. Kartları "
                            "danışan diline çevirirken ölçülü konuş.")}

