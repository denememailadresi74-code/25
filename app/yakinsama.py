#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YAKINSAMA ÇEKİRDEĞİ — kaç katman aynı şeyi söylüyor

NEYİN YERİNE GELDİ
    Bağlamın en başında "ÖNCE BUNLARI OKU — en belirleyici beş bulgu"
    diye bir blok var. Model onu ilk okuyor ve en çok ona yaslanıyor.

    O beş bulgu ELLE SEÇİLİYOR: kodda sabit bir liste var — şikâyet,
    sebep, eşik türü, kaçış refleksi, yaşanan havza. Hangi haritada
    olursa olsun aynı beşi.

    Sorun şu: bir haritada en belirleyici şey kaçış refleksi olabilir,
    başkasında hiç önemli olmayabilir. Sabit liste bunu göremez.

İCAT
    Bulguyu ELLE seçmek yerine YAKINSAMAYI ÖLÇ.

    Her katman kişi hakkında bir DAVRANIŞ ifadesi üretir. Bu ifadeler
    birbirinden bağımsız kaynaklardan gelir: çekirdek üçlü, alan
    topolojisi, karar biçimi, duraklama izi, yaş katmanı, çelişkiler,
    direnç haritası, kadim katman.

    Bunlar arasında ÖRTÜŞENLER var. Yedi katman "bu kişi karar anında
    geri çekilir" diyorsa, bu o haritanın çekirdeğidir — beş sabit
    bulgudan daha güvenilirdir, çünkü bağımsız yollardan doğrulanmıştır.

    Modül davranış ekseni başına kaç katmanın söz söylediğini sayar ve
    en çok yakınsayanı öne çıkarır.

NEDEN DAHA DOĞRU
    Sabit liste her haritada aynı şeyi vurgular. Yakınsama, HER HARİTADA
    kendi ağırlık merkezini bulur. Ve kaç kaynaktan geldiği söylenince
    model neye yaslanacağını bilir.

SINIR
    Yakınsama doğruluk garantisi değildir — sekiz katman aynı temel
    veriden türüyorsa hepsi aynı hatayı tekrarlayabilir. Bu yüzden
    KAYNAK TÜRÜ sayılır, kaynak sayısı değil.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

# Davranış eksenleri — kişinin ne yaptığına dair temel ayrımlar.
# Her eksen, farklı katmanların aynı şeye işaret edip etmediğini
# yakalayacak biçimde tanımlandı.
EKSENLER: Dict[str, Tuple[str, str]] = {
    "geri_cekilme": (
        "karar anında geri çekilme",
        "Karar vermek yerine konuyu kapatma, uzaklaşma, erteleme."),
    "bekleme": (
        "beklemenin yöntem olması",
        "Çağrılmadan hareket etmeme; bu tembellik değil çalışma biçimi."),
    "ilke_tutunma": (
        "ilkeye tutunup insanı bırakma",
        "Anlaşmazlıkta soyut bir doğruya sığınma."),
    "gorunurluk": (
        "görünürlükle gerilimli ilişki",
        "Görülmek isteme ile kendini gösterememe arasında sıkışma."),
    "yalnizlasma": (
        "kendi içinde bir yanı dışlama",
        "İç bütünlükte bağı zayıf kalan bir taraf."),
    "yogunluk": (
        "aynı anda çok kapıdan geçme",
        "Birden çok eşiğin çakışması; yükün yapısal olması."),
    "sinir_gecirgenligi": (
        "sınırların belirsizliği",
        "Nerede bittiğini bilememe, karışma."),
}


def _ek(kanit: Dict[str, List[dict]], eksen: str, kaynak: str,
        tur: str, metin: str, agirlik: float = 1.0) -> None:
    kanit.setdefault(eksen, []).append(
        {"kaynak": kaynak, "tur": tur, "metin": metin[:180],
         "agirlik": agirlik})


def yakinsama(veri: Dict[str, Any]) -> dict:
    """
    Katmanların hangi davranış ekseninde birleştiğini hesaplar.

    Kaynak TÜRÜ sayılır (çekirdek, topoloji, zaman, meta...), tek tür
    içindeki tekrar bir kez sayılır — yoksa aynı hesaptan türeyen beş
    alt bulgu yapay bir yakınsama üretir.
    """
    v2 = veri.get("berzah_v2") or {}
    ber = v2.get("berzah") or {}
    top = v2.get("alan_topolojisi") or {}
    hd = veri.get("human_design") or {}
    kanit: Dict[str, List[dict]] = {}

    # --- ÇEKİRDEK ---
    tur = str(ber.get("tur") or "")
    if "itici" in tur:
        _ek(kanit, "geri_cekilme", "karar eşiği", "çekirdek",
            f"Eşik türü '{tur}': karar verilmiyor, konu terk ediliyor.", 1.4)
    ref = ber.get("yanlis_refleks") or ""
    if "ilke" in ref.lower():
        _ek(kanit, "ilke_tutunma", "yanlış refleks", "çekirdek", ref, 1.3)
    ad, kd = v2.get("AD") or {}, v2.get("KD") or {}
    if ad.get("ev") in (1, 10) or kd.get("ev") in (1, 10):
        _ek(kanit, "gorunurluk", "çekirdek üçlü", "çekirdek",
            f"Şikâyet ya da sebep görünürlük alanında "
            f"({ad.get('ev')}./{kd.get('ev')}. ev).", 1.2)

    # --- TOPOLOJİ ---
    bar = top.get("cikis_bariyeri") or {}
    day = bar.get("dayaniklilik") if isinstance(bar, dict) else None
    if isinstance(day, (int, float)) and day > 7:
        _ek(kanit, "geri_cekilme", "çıkış bariyeri", "topoloji",
            f"Kalıp dirençli ({day:.1f}); denenmiş ve olmamış.", 1.0)
    asim = ber.get("asimetri")
    if isinstance(asim, (int, float)) and asim > 1.4:
        _ek(kanit, "sinir_gecirgenligi", "alan asimetrisi", "topoloji",
            f"Alan belirgin asimetrik ({asim:.2f}×).", 0.9)

    # --- KARAR BİÇİMİ ---
    strat = str(hd.get("strateji") or "")
    if "bekle" in strat.lower():
        _ek(kanit, "bekleme", "karar biçimi", "yapı",
            f"Doğal strateji: {strat}.", 1.3)
    ot = hd.get("otorite")
    ot = ot.get("tr") if isinstance(ot, dict) else (ot or "")
    if "dalga" in str(ot).lower() or "duygusal" in str(ot).lower():
        _ek(kanit, "bekleme", "otorite", "yapı",
            f"Netlik anda değil dalgada: {ot}.", 1.0)

    # --- DENEME: ASABİYYE ---
    asb = (veri.get("deneme_modulleri") or {}).get("asabiyye") or {}
    if asb.get("yalniz"):
        _ek(kanit, "yalnizlasma", "iç ictimâ", "deneme",
            f"İç düzende bağı zayıf kalan yan: {asb.get('yalniz')}.", 1.0)

    # --- YAŞ KATMANI ---
    yk = veri.get("yas_katmani") or {}
    if (yk.get("esik_sayisi") or 0) >= 3:
        _ek(kanit, "yogunluk", "yaş katmanı", "zaman",
            f"{yk['esik_sayisi']} gelişim eşiği aynı anda açık.", 1.2)

    # --- ÇELİŞKİLER ---
    for c in (veri.get("celiskiler") or []):
        b = str(c.get("baslik", "")).lower()
        if "bekle" in b or "bırak" in b:
            _ek(kanit, "geri_cekilme", "çelişki", "meta",
                c.get("baslik", ""), 1.1)
        if "yer" in b:
            _ek(kanit, "gorunurluk", "çelişki", "meta", c.get("baslik", ""), 0.8)

    # --- DİRENÇ ---
    for r in (veri.get("direnc") or []):
        nz = str(r.get("ne_zaman", "")).lower()
        if "kaçış" in nz or "refleks" in nz:
            _ek(kanit, "ilke_tutunma", "direnç haritası", "meta",
                r.get("ne_zaman", ""), 0.9)
        if "karar" in nz:
            _ek(kanit, "geri_cekilme", "direnç haritası", "meta",
                r.get("ne_zaman", ""), 0.9)

    # --- DURAKLAMA ---
    drk = veri.get("duraklama_izi") or {}
    ham = drk.get("el_degmemis") or []
    if ham:
        _ek(kanit, "yalnizlasma", "duraklama izi", "zaman",
            "Hiç işlenmemiş yan: " + ", ".join(r["nokta"] for r in ham[:2]),
            0.8)

    # --- PUANLAMA: kaynak TÜRÜ sayılır ---
    sonuc: List[dict] = []
    for eksen, kayitlar in kanit.items():
        turler = {k["tur"] for k in kayitlar}
        agirlik = sum(k["agirlik"] for k in kayitlar)
        # Tür çeşitliliği ana ölçü; toplam ağırlık ikincil
        puan = len(turler) * 2.0 + agirlik * 0.6
        ad_, aciklama = EKSENLER.get(eksen, (eksen, ""))
        sonuc.append({
            "eksen": eksen, "ad": ad_, "aciklama": aciklama,
            "kaynak_turu": len(turler), "kanit_sayisi": len(kayitlar),
            "puan": round(puan, 2),
            "kaynaklar": sorted({k["kaynak"] for k in kayitlar}),
            "kanitlar": [k["metin"] for k in kayitlar[:4]],
        })
    sonuc.sort(key=lambda x: -x["puan"])

    cekirdek = [s for s in sonuc if s["kaynak_turu"] >= 2][:3]
    tekil = [s for s in sonuc if s["kaynak_turu"] < 2][:3]

    return {
        "modul": "YAKINSAMA ÇEKİRDEĞİ — kaç katman aynı şeyi söylüyor",
        "eksenler": sonuc,
        "cekirdek": cekirdek,
        "tekil": tekil,
        "okuma": _okuma(cekirdek, tekil),
        "talimat": _talimat(cekirdek, tekil),
        "yontem": ("Her katmanın ürettiği davranış ifadeleri yedi eksende "
                   "toplanır. Puan, KAYNAK TÜRÜ sayısına dayanır (çekirdek, "
                   "topoloji, yapı, zaman, meta, deneme) — tek tür içindeki "
                   "tekrar bir kez sayılır, yoksa aynı hesaptan türeyen alt "
                   "bulgular yapay yakınsama üretir."),
        "sinir": ("Yakınsama doğruluk garantisi DEĞİLDİR. Katmanlar aynı "
                  "temel veriden türüyorsa hepsi aynı hatayı tekrarlayabilir. "
                  "Ölçülen şey doğruluk değil, bağımsız doğrulama sayısı."),
    }


def _okuma(cekirdek: List[dict], tekil: List[dict]) -> str:
    if not cekirdek:
        return ("Katmanlar tek bir davranış ekseninde birleşmiyor. Bu "
                "haritada baskın bir örüntü yok; okumayı tek bir temaya "
                "indirgeme.")
    e = cekirdek[0]
    p = [f"Bu haritanın ağırlık merkezi: {e['ad']} — "
         f"{e['kaynak_turu']} bağımsız katman aynı yeri gösteriyor "
         f"({', '.join(e['kaynaklar'][:3])})."]
    if len(cekirdek) > 1:
        p.append("Ardından " + ", ".join(
            f"{x['ad']} ({x['kaynak_turu']} katman)" for x in cekirdek[1:]) + ".")
    if tekil:
        p.append("Tek kaynaktan gelenler: "
                 + ", ".join(x["ad"] for x in tekil[:2])
                 + " — bunlara az yaslan.")
    return " ".join(p)


def _talimat(cekirdek: List[dict], tekil: List[dict]) -> List[str]:
    t: List[str] = []
    if cekirdek:
        e = cekirdek[0]
        t.append(f"BU HARİTANIN ÇEKİRDEĞİ: {e['ad']}. {e['kaynak_turu']} "
                 f"bağımsız katman ({', '.join(e['kaynaklar'][:4])}) aynı "
                 f"yeri gösteriyor. Okumanın omurgası budur; hangi bölümü "
                 f"yazıyor olursan ol buraya bağlan.")
        for x in cekirdek[1:]:
            t.append(f"İkincil: {x['ad']} ({x['kaynak_turu']} katman).")
    if tekil:
        t.append("TEK KAYNAKLI (az yaslan): "
                 + ", ".join(x["ad"] for x in tekil[:3])
                 + ". Bunlar doğru olabilir ama bağımsız doğrulaması yok.")
    return t
