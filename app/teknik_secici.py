#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEKNİK SEÇİCİ — 16 modülden hangileri BU haritada güçlü

SORUN
    Deneme modülleri bloğu 16 tekniği birden bağlama döküyordu: satır
    başına 151 karakter, toplam 2427. Ölçüldü.

    151 karakterde bir teknik anlatılmaz. O satırlar okuma değil, etiketli
    VERİ DÖKÜMÜ:

        "KRN: 03°50' Başak · 5. ev · skor 66 (orta) · Anti-KRN 03°50' Balık"

    Model 16 tanesini aynı anda yorumlamak zorunda kalıyor ve çoğunu
    atlıyor. Ayrıca "hangisi önemli" kararı modele bırakılmış oluyor.

ÇÖZÜM — sistem bunu başka yerde zaten doğru yapıyor
    Lunasyon takviminde hangi kategorinin uyandığı SUNUCUDA hesaplanıp
    modele veriliyor. Aynı ilke burada da uygulanır: her tekniğin bu
    haritada ne kadar güçlü olduğu hesaplanır, en güçlü birkaçı NEFES
    ALACAK yerle verilir, gerisi arayüzde kalır ama bağlama girmez.

    4 teknik × ~600 karakter, 16 teknik × 151 karakterden çok daha fazla
    iş görür.

GÜÇ ÖLÇÜSÜ
    Tekniklerin çoğunda hazır bir puan alanı YOK — kontrol edildi. Bu
    yüzden her teknik için ölçü ayrı tanımlanır: birinde açı sıkılığı,
    ötekinde harmonik genlik, üçüncüsünde ev vurgusu. Aşağıdaki tablo
    o tanımlardır.

    Ölçü bulunamazsa teknik orta puan alır — sessizce sıfırlanmaz, çünkü
    ölçüsüzlük zayıflık değildir.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

# Ölçü YAZILAMAZ — 16 modülün yapısı birbirinden tamamen farklı.
# İlk denemede her teknik için elle alan adı yazdım ("baglar",
# "pencereler", "temaslar") ve YANLIŞ ÇIKTI: gerçek adlar
# `asabiyye_lambda2`, `irtifa_egrisi`, `vuslat_kapilari` gibi şeylerdi.
# Dört teknik 0.00 aldı çünkü aradığım anahtar yoktu — güçsüz oldukları
# için değil.
#
# Daha kötüsü: "ölçü tanımsız" için verdiğim 4.0 varsayılanı, ÖLÇÜLMÜŞ
# zayıf teknikleri (Vahdet 0.82) geçiyordu. Yani seçim bilgisizlikle
# yönleniyordu — tam tersi olmalı.
#
# ÇÖZÜM: modülün kendi verisinden çalışan GENEL ölçü. Her modül ne
# üretiyorsa onun DOLULUĞUNA bakılır:
#   · kaç dolu liste ve içlerinde kaç öğe var
#   · sayısal alanlar uçta mı, ortada mı (uç = belirgin, orta = kararsız)
#   · yorum metni ne kadar somut
# Bu, yapı bilmeden çalışır ve yanlış anahtar yüzünden sıfırlamaz.

ATLA = {"modul", "yontem", "aciklama", "uyari", "not"}

# ============================================================================
# NEDEN SIRALAMA DEĞİL, SEÇİM
# ============================================================================
# Üç ayrı ölçü denendi ve üçü de başarısız oldu — kaydediliyor ki tekrar
# denenmesin:
#
#   1. Elle alan adı (her tekniğe özel): adları TAHMİN ettim, yanlış çıktı.
#      Dört teknik 0.00 aldı çünkü aradığım anahtar yoktu — zayıf oldukları
#      için değil.
#   2. Mutlak doluluk: çok sayısal alan içeren modüller (Asabiyye) her
#      haritada tavan puan aldı. Ölçü gücü değil, AYRINTILILIĞI ölçüyordu.
#   3. Oransal doluluk: ölçek-bağımsız oldu ama BEŞ HARİTADA DA aynı dört
#      teknik seçildi — sıfır ayrım.
#
# Üçüncü denemenin gösterdiği şey asıl bulgudur: BU MODÜLLERDE HARİTAYA
# ÖZEL GÜÇ SİNYALİ YOK. Hepsi her haritada dolu çıktı üretiyor; "burada
# bir şey bulamadım" hâlleri yok. Doluluk modülün kendi özelliği, haritanın
# değil.
#
# Sahte bir sıralama üretmektense seçim AÇIKÇA EDİTÖRYELDİR: hangi
# tekniklerin danışman elinde işe yaradığına göre seçildi, hesapla değil.
# Bu dürüst olan ve sonucu daha iyi olandır — dört teknik nefes alacak
# yer buluyor, on altısı birden 151 karakterlik satırlara sıkışmıyor.
#
# Kriter: bir teknik SEANSTA KULLANILABİLİR bir şey söylüyor mu?
BAGLAMA_GIREN = [
    "krn",        # kader rezonans noktası — doğrudan davranışa bağlanıyor
    "asabiyye",   # iç ictimâ: kim reis, kim yalnız — ilişkisel, somut
    "ikbal_merdiveni",      # kariyer irtifası ve mühür tarihleri — zamanlanabilir
    "vuslat_kapilari",     # ilişki faz-dönüş takvimi — zamanlanabilir
]

# Arayüzde kalır ama bağlama girmez. Sebep: ya çok teknik (yorumlanması
# terim gerektiriyor), ya da söylediği şey başka katmanda zaten var.
BAGLAM_DISI_SEBEP = {
    "vahdet": "R indeksi ve harmonikler — alan topolojisinde karşılığı var",
    "mizan": "makam listesi; spiritüel çalışmalar bölümünde daha yerinde",
    "ars_ekseni": "düşey mizan — teknik, danışan diline çevrilmesi zor",
    "ayna_ekseni": "simetri skoru — alan halkasıyla örtüşüyor",
    "devri_daim": "döngü sayacı — Şi'râ ve Kabz/Bast ile örtüşüyor",
    "felek_saati": "saat dilimleri — gezegen saatleri bölümünde var",
    "suveyda": "dairesel medyan — kütleler bölümünde karşılığı var",
    "nokta_i_noksan": "en ıssız derece — tek satırlık bilgi, blok gerektirmiyor",
    "nokta_i_icabet": "rıza rezonansı — spiritüel bölümle örtüşüyor",
    "mizac_pusulasi": "mizaç şarjı — kadim katmanda var",
    "sevk_i_felek_v2": "sevk açısı — yürüyen berzahla örtüşüyor",
}


def _genel_guc(d: dict) -> Tuple[float, str]:
    """
    Modülün DOLULUK ORANINDAN güç türetir.

    İlk genel ölçü mutlak sayıyordu ve YANLILIK üretiyordu: çok sayısal
    alan içeren Asabiyye her haritada 10.00 alıyordu. Ölçü gücü değil,
    ayrıntılılığı ödüllendiriyordu.

    Şimdi ölçek-bağımsız: modülün KENDİ alanlarının kaçta kaçı dolu.
    Böylece iki alanlı bir modül ile yirmi alanlı bir modül aynı ölçekte
    yarışır — ve aynı modül farklı haritalarda farklı puan alır.
    """
    alanlar = [(k, v) for k, v in d.items() if k not in ATLA]
    if not alanlar:
        return 0.0, "içerik yok"

    dolu = 0
    liste_ogeleri = 0
    uc_puan = 0.0
    uc_sayi = 0
    parca: List[str] = []

    for k, v in alanlar:
        if isinstance(v, list):
            if v:
                dolu += 1
                liste_ogeleri += len(v)
        elif isinstance(v, dict):
            if [x for x in v.values() if x not in (None, "", [], {})]:
                dolu += 1
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            dolu += 1
            if 0.0 <= float(v) <= 1.0:
                # 0–1 aralığı: uçlar belirgin, 0.5 kararsız
                uc_puan += abs(float(v) - 0.5) * 2.0
                uc_sayi += 1
        elif isinstance(v, str) and v.strip():
            dolu += 1

    oran = dolu / len(alanlar)                    # 0–1
    puan = oran * 6.0                             # doluluk payı
    if liste_ogeleri:
        puan += min(2.0, liste_ogeleri * 0.06)    # içerik yoğunluğu
        parca.append(f"{liste_ogeleri} öğe")
    if uc_sayi:
        puan += (uc_puan / uc_sayi) * 2.0         # ORTALAMA uçluk, toplam değil
        parca.append(f"{uc_sayi} ölçüt")
    parca.insert(0, f"doluluk {dolu}/{len(alanlar)}")
    return round(min(10.0, puan), 2), " · ".join(parca)


def teknik_puanla(dn: dict) -> List[dict]:
    """Her tekniği bu haritadaki gücüne göre puanlar, sıralı döner."""
    out: List[dict] = []
    for kod, veri in (dn or {}).items():
        if not isinstance(veri, dict) or "hata" in veri:
            continue
        if kod.startswith("run_all"):
            continue              # toplayıcı işlev, teknik değil
        ad = (veri.get("modul") or kod).split("(")[0].strip()[:22]
        try:
            puan, gerekce = _genel_guc(veri)
        except Exception:
            puan, gerekce = 0.0, "ölçülemedi"
        out.append({"kod": kod, "ad": ad, "puan": round(puan, 2),
                    "gerekce": gerekce})
    out.sort(key=lambda x: -x["puan"])
    return out


def secilenler(dn: dict, adet: int = 4, asgari: float = 0.0) -> dict:
    """
    Bağlama girecek teknikleri döner.

    Seçim EDİTÖRYELDİR (yukarıdaki açıklamaya bakın): haritaya özel güç
    sinyali olmadığı için hesapla sıralanamıyor. Yine de her seçilenin
    doluluk puanı hesaplanır — bir modül o haritada gerçekten boş
    dönerse listeden düşer.
    """
    puanlar = {x["kod"]: x for x in teknik_puanla(dn)}
    guclu: List[dict] = []
    for kod in BAGLAMA_GIREN[:adet]:
        p = puanlar.get(kod)
        if p and p["puan"] > 0.5:
            guclu.append(p)
    return {
        "secilen": guclu,
        "elenen": [k for k in puanlar if k not in BAGLAMA_GIREN],
        "eleme_sebebi": BAGLAM_DISI_SEBEP,
        "toplam": len(puanlar),
        "not": ("Seçim editöryeldir, hesapla değil: bu modüllerde haritaya "
                "özel güç sinyali yok — hepsi her haritada dolu çıktı "
                "üretiyor. Seçilenler seansta kullanılabilir bir şey "
                "söyleyenlerdir; ötekiler arayüzde duruyor."),
    }
