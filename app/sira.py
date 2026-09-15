#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ŞİRÂ ÇEVRİMİ — TARIK NEFESİ  (ZÎC v3.1 icadı)

NEDEN ŞİRÂ?
    BERZAH modelinin çekirdeği bir İKİLİ yapıdır: görünen ağız (Ak Delik) ile
    görünmeyen yoğun merkez (Kara Delik) ve aralarındaki eşik. Gökyüzünde bu
    yapının birebir karşılığı vardır: Şi'râ (Sirius) gerçek bir ikili yıldızdır.
      • Şi'râ A — gökyüzünün en parlak yıldızı; görünen hayat.
      • Şi'râ B — çıplak gözle görülmez bir beyaz cüce; Güneş kütlesinde ama
        Dünya büyüklüğünde. Yoğun, sessiz, görünmeyen taşıyıcı.
    İkisi 50.13 yılda bir birbirinin çevresinde döner. Bu, insan ömrüne oturan
    tek gökcismi çevrimidir: 50 yaş civarında kişi doğduğu faza geri döner.

    Kur'an'da Necm 49: "Şüphesiz Şi'râ'nın Rabbi O'dur." Târık sûresi (86:1-3)
    "gece gelen, delip geçen yıldız"dan söz eder; müfessirlerin bir kısmı bunu
    Şi'râ ile ilişkilendirmiştir. Osmanlı yıldıznâmelerinde Şi'râ, "ışığı keskin
    olan" anlamında el-Şi'râ el-Yemâniyye adıyla geçer.

YÖNTEM — hepsi hesaplanır, hiçbiri tabloya bakılarak atanmaz:
    1. Şi'râ A'nın ekliptik boylamı, özdevinim ve presesyon dahil (Swiss
       Ephemeris sabit yıldız kataloğu). 1900'de 12°43' Yengeç, 2050'de
       14°47' Yengeç — 150 yılda 2.07° kayar.
    2. Şi'râ B'nin yörünge fazı Kepler denklemi ile çözülür:
           P = 50.1284 yıl · e = 0.59142 · T(perigeon) = 1994.5715
       (Bond ve ark. 2017, HST astrometrisi.)
       Çıktı: AYRIKLIK r/a ∈ [0.409, 1.591] ve AÇISAL HIZ dν/dt.
       Yörünge çok basıktır: perigeonda çift hızla süpürür, apogeonda sürünür.
       Bu, çevrimi tekdüze bir saat olmaktan çıkarır — nefes gibi yapar.
    3. Doğumdaki faz = mizaç tohumu. Bugünkü faz = mevsim. İkisinin FARKI
       öneriyi belirler.
    4. Osmanlı yıldıznâmesi: ebced(ad + anne adı) mod 12 → yıldız burcu.
    5. Menâzil-i kamer: Şi'râ'nın 28 ay menzilindeki yeri.

SEKİZ ALAN — her biri AYRI bir hesaplanmış büyüklükten türer, aynı sayı farklı
adlarla tekrarlanmaz:
    Fikir        ← ayrıklık r/a (geniş = paralel fikirler, dar = tek fikir)
    Düşünce      ← açısal hız dν/dt (hızlı = sıçrayan, yavaş = tek iz sürücü)
    Duygu        ← doğum fazı çeyreği + Ay'ın Şi'râ'ya açısı
    Plan         ← Tarık dönüşüne kalan süre (doğum fazına geri dönüş)
    Alışkanlıklar← alan topolojisinden dayanıklılık (v3.0 ile bağ)
    Kararlılık   ← havza tayini + bariyer asimetrisi (v3.0 ile bağ)
    Yaşam tarzı  ← Şi'râ A'nın evi ve natal temasları
    Değişim      ← ayrıklığın türevi dr/dt (yaklaşıyor mu uzaklaşıyor mu)
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence, Tuple

import swisseph as swe

from .astro import NatalChart, CORE10, TR_NAME, EPHFLAG, ensure_ephe, jd_to_iso
from .circular import (norm360, sep, signed_sep, fmt_lon, sign_of, ebced_detail,
                       SIGNS, ELEMENT)

# --- Şi'râ ikilisinin yörünge ögeleri (Bond ve ark. 2017, HST) ---------------
SIRA_P = 50.1284          # yıl — yörünge dönemi
SIRA_E = 0.59142          # dışmerkezlik
SIRA_T = 1994.5715        # son perigeon (kesirli yıl)
# Not: eski literatürde 49.9 yıl geçer; AI_/parametre ile değiştirilebilir.

MENZIL = [
    "Şeretân", "Butayn", "Süreyyâ", "Debarân", "Hak'a", "Han'a", "Zirâ'",
    "Nesre", "Tarf", "Cebhe", "Zübre", "Sarfe", "Avvâ", "Simâk", "Gafr",
    "Zübânâ", "İklîl", "Kalb", "Şevle", "Neâim", "Belde", "Sa'dü'z-zâbih",
    "Sa'dü bula'", "Sa'dü's-suûd", "Sa'dü'l-ahbiye", "Fer'u'd-delvi'l-mukaddem",
    "Fer'u'd-delvi'l-muahhar", "Batnü'l-hût",
]

# Osmanlı yıldıznâmesi: ebced mod 12 → burç ve tabiat
YILDIZNAME = {
    "Koç": ("Ateş · atılgan", "Kararı önce verir, sonra düşünür; hızı hem sermayesi hem borcu."),
    "Boğa": ("Toprak · sabit", "Yavaş ısınır, geç bırakır; biriktirdiği şey onu hem taşır hem yorar."),
    "İkizler": ("Hava · devingen", "İki işi aynı anda yürütür; derinlik ancak birini bırakınca gelir."),
    "Yengeç": ("Su · koruyucu", "Hafızası uzun; geçmişi bugüne taşımadan yol alamaz."),
    "Aslan": ("Ateş · sabit", "Görülmeden yapılan işi eksik sayar; tanıksız karar onu zorlar."),
    "Başak": ("Toprak · devingen", "Ayrıntıyı görür, bütünü geç toplar; bitirme eşiği yüksektir."),
    "Terazi": ("Hava · atılgan", "Karşı tarafın ağırlığını kendi ağırlığı sanır; tek başına tartmalı."),
    "Akrep": ("Su · sabit", "Yüzeyde durmaz; bulduğu şeyi söylemeden önce uzun süre taşır."),
    "Yay": ("Ateş · devingen", "Ufuk açıldıkça rahatlar; kapalı alanda hızla anlam kaybeder."),
    "Oğlak": ("Toprak · atılgan", "Yükü görev sanır; taşıdığı şeyin bedelini sonradan sorar."),
    "Kova": ("Hava · sabit", "İlkeye insandan önce bakar; istisnayı tanımayı öğrenmesi gerekir."),
    "Balık": ("Su · devingen", "Sınırı geç fark eder; karara takvim koymadan karar veremez."),
}


# ============================================================================
# 1. ŞİRÂ B — YÖRÜNGE FAZI (Kepler)
# ============================================================================
def _kesirli_yil(jd: float) -> float:
    y, mo, d, h = swe.revjul(jd)
    j0 = swe.julday(y, 1, 1, 0.0)
    j1 = swe.julday(y + 1, 1, 1, 0.0)
    return y + (jd - j0) / (j1 - j0)


def sira_fazi(jd: float, P: float = SIRA_P, e: float = SIRA_E,
              T: float = SIRA_T) -> dict:
    """
    Şi'râ B'nin yörünge durumu. Kepler denklemi Newton yinelemesiyle çözülür.

        M = 2π·((t−T)/P mod 1)          ortalama anomali
        E − e·sinE = M                  eksantrik anomali
        r/a = 1 − e·cosE                ayrıklık
        ν = 2·atan2(√(1+e)·sin(E/2), √(1−e)·cos(E/2))
        dν/dt ∝ √(1−e²)/(r/a)²          açısal hız (alan hızı sabiti)
    """
    t = _kesirli_yil(jd)
    faz = ((t - T) / P) % 1.0
    M = 2 * math.pi * faz
    E = M if e < 0.8 else math.pi
    for _ in range(80):
        d = (E - e * math.sin(E) - M) / (1 - e * math.cos(E))
        E -= d
        if abs(d) < 1e-13:
            break
    r = 1 - e * math.cos(E)
    nu = math.degrees(2 * math.atan2(math.sqrt(1 + e) * math.sin(E / 2),
                                     math.sqrt(1 - e) * math.cos(E / 2))) % 360
    # açısal hız, ortalama hıza göre normalize
    hiz = math.sqrt(1 - e * e) / (r * r)
    # ayrıklığın türevi: yaklaşıyor mu uzaklaşıyor mu
    dr = e * math.sin(E) / (1 - e * math.cos(E))     # işaret yeterli
    ceyrek = ("perigeon çeyreği — en yoğun temas" if faz < 0.125 or faz >= 0.875 else
              "açılma çeyreği — bağ gevşiyor" if faz < 0.375 else
              "apogeon çeyreği — en uzak, en yavaş" if faz < 0.625 else
              "kapanma çeyreği — yeniden yaklaşıyor")
    # Hassasiyet: bu değerler aşağıya (öneri üretimine) akar. 4 haneye
    # yuvarlamak Kepler tutarlılığını 3.9e-4'e kadar bozuyordu; 6 hane
    # makine hassasiyetini korur, ekranda yine kısaltılır.
    return {"yil": round(t, 4), "faz": round(faz, 6),
            "ayriklik": round(r, 6), "ayriklik_min": round(1 - e, 4),
            "ayriklik_max": round(1 + e, 4),
            "acisal_hiz": round(hiz, 6),
            "yaklasiyor": dr < 0, "ceyrek": ceyrek,
            "gercek_anomali": round(nu, 2),
            "perigeon_yili": round(T + P * round((t - T) / P), 2),
            "sonraki_perigeon": round(T + P * (math.floor((t - T) / P) + 1), 2),
            "sonraki_apogeon": round(T + P * (math.floor((t - T) / P) + 0.5)
                                     + (P if faz >= 0.5 else 0), 2)}


# ============================================================================
# 2. ŞİRÂ A — SABİT YILDIZ KONUMU VE TEMASLARI
# ============================================================================
def sira_yildizi(jd: float) -> dict:
    """Şi'râ A'nın ekliptik konumu — özdevinim ve presesyon dahil."""
    ensure_ephe()
    try:
        r = swe.fixstar_ut("Sirius", jd, EPHFLAG)
        lon = norm360(r[0][0])
        lat = r[0][1]
        kaynak = "Swiss Ephemeris sabit yıldız kataloğu"
    except Exception:
        # katalog yoksa: J2000 boylamı + presesyon yaklaşımı
        lon = norm360(104.0885 + (_kesirli_yil(jd) - 2000.0) * (360.0 / 25772.0) * 1.0)
        lat = -39.605
        kaynak = "katalog yok — presesyon yaklaşımı"
    m = int(lon / (360.0 / 28)) % 28
    return {"konum": fmt_lon(lon), "lon": round(lon, 4), "enlem": round(lat, 3),
            "menzil_no": m + 1, "menzil": MENZIL[m], "kaynak": kaynak}


def sira_temaslari(chart: NatalChart, sira_lon: float, orb: float = 3.0) -> List[dict]:
    """
    Şi'râ A'nın natal cisimlerle teması. Sabit yıldız geleneğinde yalnız
    kavuşum ve karşıtlık sayılır; orb dardır çünkü yıldız noktasal kabul edilir.
    """
    hedef = {**{k: chart.bodies[k].lon for k in CORE10},
             "Asc": chart.asc, "MC": chart.mc}
    out = []
    for k, lon in hedef.items():
        d = sep(lon, sira_lon)
        for ang, ad in ((0.0, "kavuşum"), (180.0, "karşıtlık")):
            o = abs(d - ang)
            if o <= orb:
                out.append({"cisim": TR_NAME.get(k, k), "tur": ad,
                            "orb": round(o, 2), "konum": fmt_lon(lon),
                            "guc": round(1 - o / orb, 3)})
                break
    out.sort(key=lambda x: -x["guc"])
    return out


# ============================================================================
# 3. SEKİZ ALAN ÖNERİSİ
# ============================================================================
def _oneriler(dogum: dict, simdi: dict, temaslar: List[dict],
              chart: NatalChart, topoloji: Optional[dict],
              yildizname: Optional[dict], sira_lon: float) -> Dict[str, dict]:
    """
    Her alan AYRI bir hesaplanmış büyüklükten türer. Aynı sayının farklı
    adlarla tekrarlanmaması, önerinin gerçekten ayrışması için şarttır.
    """
    o: Dict[str, dict] = {}
    ay_d, ay_s = dogum["ayriklik"], simdi["ayriklik"]
    hz_d, hz_s = dogum["acisal_hiz"], simdi["acisal_hiz"]

    # --- FİKİR ← ayrıklık --------------------------------------------------
    if ay_s < 0.7:
        o["fikir"] = {"olcum": f"ayrıklık {ay_s} (dar)",
                      "durum": "Fikirler tek eksende toplanıyor.",
                      "oneri": "Şu dönem yeni bir alan açma; elindeki tek fikri "
                               "sonuna kadar götür. Dağıtırsan hiçbiri olgunlaşmaz."}
    elif ay_s > 1.3:
        o["fikir"] = {"olcum": f"ayrıklık {ay_s} (geniş)",
                      "durum": "Paralel fikirler aynı anda canlı.",
                      "oneri": "Üçten fazla iş yürütme. Haftada bir gün yalnız "
                               "birini seç ve o gün ötekilere hiç bakma."}
    else:
        o["fikir"] = {"olcum": f"ayrıklık {ay_s} (orta)",
                      "durum": "Fikir üretimi dengeli.",
                      "oneri": "Bu ara yeni fikir aramak yerine mevcut olanı "
                               "yazıya dök; ölçülebilir hâle getir."}

    # --- DÜŞÜNCE ← açısal hız ---------------------------------------------
    if hz_s > 1.6:
        o["dusunce"] = {"olcum": f"açısal hız {hz_s} (yüksek)",
                        "durum": "Zihin sıçrayarak çalışıyor; bağlantılar hızlı, derinlik zayıf.",
                        "oneri": "Karar vermeden önce yirmi dört saat bekle. "
                                 "İlk çözüm genelde en hızlı olan, en doğru olan değil."}
    elif hz_s < 0.7:
        o["dusunce"] = {"olcum": f"açısal hız {hz_s} (düşük)",
                        "durum": "Zihin tek iz sürüyor; derin ama yavaş.",
                        "oneri": "Bir konuyu üç günden fazla tek başına düşünme. "
                                 "Dışarıdan bir ses almak tıkanmayı açar."}
    else:
        o["dusunce"] = {"olcum": f"açısal hız {hz_s} (orta)",
                        "durum": "Düşünce hızı iş görür durumda.",
                        "oneri": "Düşündüğünü yazmayı alışkanlık yap; hız ile "
                                 "derinlik ancak yazıyla birlikte tutulur."}

    # --- DUYGU ← doğum çeyreği + Ay–Şi'râ açısı ---------------------------
    ay_temas = next((t for t in temaslar if t["cisim"] == "Ay"), None)
    if ay_temas:
        o["duygu"] = {"olcum": f"Ay–Şi'râ {ay_temas['tur']} ({ay_temas['orb']}°)",
                      "durum": "Duygular yüksek görünürlükte; hissettiğin şey "
                               "hemen dışarı yansıyor.",
                      "oneri": "Tepkiyi söylemeden önce adını koy. "
                               "'Kızgınım' demek, kızgın davranmaktan hafiftir."}
    elif dogum["ceyrek"].startswith("perigeon"):
        o["duygu"] = {"olcum": f"doğum çeyreği: {dogum['ceyrek']}",
                      "durum": "Duygu yoğun ve sıkışık yaşanır; az kişiye çok bağlanırsın.",
                      "oneri": "Bağlandığın kişi sayısını artırmaya çalışma; "
                               "mevcut iki üç bağın bakımını takvime bağla."}
    elif dogum["ceyrek"].startswith("apogeon"):
        o["duygu"] = {"olcum": f"doğum çeyreği: {dogum['ceyrek']}",
                      "durum": "Duygu mesafeli işlenir; yakınlık geç kurulur ama uzun sürer.",
                      "oneri": "Yakınlığı beklemek yerine küçük ve düzenli temas "
                               "kur: haftada bir kısa mesaj, aylık bir görüşme."}
    else:
        o["duygu"] = {"olcum": f"doğum çeyreği: {dogum['ceyrek']}",
                      "durum": "Duygu geçiş halinde; bağlar kuruluyor ya da çözülüyor.",
                      "oneri": "Bu dönemde kalıcı duygusal karar verme; "
                               "üç ay sonra aynı şeyi hâlâ istiyor musun diye bak."}

    # --- PLAN ← Tarık dönüşüne kalan süre ---------------------------------
    fark = (simdi["faz"] - dogum["faz"]) % 1.0
    kalan = (1.0 - fark) * SIRA_P
    yas_donus = SIRA_P
    o["plan"] = {"olcum": f"faz farkı {round(fark,3)} · dönüşe {round(kalan,1)} yıl",
                 "durum": (f"Tarık dönüşüne {round(kalan,1)} yıl var; "
                           f"doğduğun faza {round(yas_donus,1)} yaşında dönüyorsun."),
                 "oneri": ("Dönüşe iki yıldan az kaldı: yeni bir devir başlatmak "
                           "için beklemeye değer, şimdi kapanış yap."
                           if kalan < 2 else
                           "Dönüş uzak: uzun vadeli planı şimdi kur, çünkü "
                           f"önümüzdeki {min(round(kalan,0),10):.0f} yıl aynı "
                           "çevrim içinde geçecek."
                           if kalan > 10 else
                           f"Orta vadedesin: planı {round(kalan,0):.0f} yıllık "
                           "ufka göre böl, daha uzağa taşıma.")}

    # --- ALIŞKANLIKLAR ← dayanıklılık (v3.0 alan topolojisi) --------------
    hi = ((topoloji or {}).get("himmet") or {})
    day = hi.get("dayaniklilik")
    if day is None:
        o["aliskanliklar"] = {"olcum": "topoloji yok",
                              "durum": "Alışkanlık direnci ölçülemedi.",
                              "oneri": "Bir alışkanlığı değiştirmeden önce iki hafta "
                                       "sadece kaydet; ölçmeden değiştirme."}
    elif day < 3:
        o["aliskanliklar"] = {"olcum": f"dayanıklılık {day} (düşük)",
                              "durum": "Alışkanlıklar kolay kurulur, kolay bozulur.",
                              "oneri": "Yeni alışkanlığı iradeyle değil ORTAMLA "
                                       "tut: nesneyi göz önüne koy, engeli fiziken kaldır."}
    elif day < 10:
        o["aliskanliklar"] = {"olcum": f"dayanıklılık {day} (orta)",
                              "durum": "Alışkanlık belirli pencerelerde değişiyor.",
                              "oneri": "Değişimi geçirgenlik penceresine denk getir; "
                                       "rastgele bir pazartesi seçme."}
    else:
        o["aliskanliklar"] = {"olcum": f"dayanıklılık {day} (yüksek)",
                              "durum": "Alışkanlıklar çok sağlam; iyi de olsa kötü de olsa kalıcı.",
                              "oneri": "Tek seferde tek alışkanlık değiştir ve en az "
                                       "üç ay ver. Çoklu deneme bu yapıda hep başarısız olur."}

    # --- KARARLILIK ← havza + bariyer asimetrisi --------------------------
    hv = ((topoloji or {}).get("havza") or {})
    ey = ((topoloji or {}).get("esik_yuksekligi") or {})
    if hv.get("bolunmus_mu"):
        o["kararlilik"] = {"olcum": f"göstergeler {len(hv.get('oy_dagilimi') or {})} havzada",
                           "durum": "Kimlik göstergelerin farklı havzalara dağılmış; "
                                    "kararlılık eksikliği karakter değil, yapısal bölünme.",
                           "oneri": "Kendini kararsızlıkla suçlama. Bunun yerine "
                                    "hangi kararı hangi 'ben'in verdiğini yaz — "
                                    "iki hafta sonra desen görünür olur."}
    elif ey and ey.get("sol", {}).get("bariyer") is not None:
        asim = ey.get("asimetri", 0)
        o["kararlilik"] = {"olcum": f"bariyer asimetrisi {asim} · kolay yön {ey.get('kolay_yon')}",
                           "durum": f"Çıkışı kolay olan yön {ey.get('kolay_yon')}; "
                                    "kararların farkında olmadan o yöne kayıyor.",
                           "oneri": f"Karar verirken kendine sor: bunu seçtim mi, "
                                    f"yoksa {ey.get('kolay_yon')} tarafı daha ucuz "
                                    "olduğu için mi oraya kaydım?"}
    else:
        o["kararlilik"] = {"olcum": f"yaşanan havza {hv.get('yasanan_havza')}",
                           "durum": "Kararlar tek havzadan veriliyor.",
                           "oneri": "Kararlarını bir yere yaz ve üç ay sonra "
                                    "geri dön; tutarlılığın kanıtı hafıza değil kayıttır."}

    # --- YAŞAM TARZI ← Şi'râ A'nın evi ve temasları -----------------------
    ev = chart.house(sira_lon)
    ev_metin = {
        1: "kendini ortaya koyma biçimin", 2: "kazanç ve değer alanın",
        3: "gündelik iletişim ve yakın çevren", 4: "ev, kök ve aile düzenin",
        5: "üretim, oyun ve risk alanın", 6: "günlük rutinin ve işin",
        7: "ortaklıkların", 8: "ortak kaynaklar ve krizlerin",
        9: "öğrenme, inanç ve uzak yolculukların", 10: "mesleğin ve görünürlüğün",
        11: "çevren ve gelecek tasavvurun", 12: "yalnız kaldığın alan",
    }.get(ev or 0, "hayatın genel akışı")
    ana = temaslar[0] if temaslar else None
    o["yasam_tarzi"] = {
        "olcum": f"Şi'râ {ev}. evde" + (f" · {ana['cisim']} {ana['tur']}" if ana else ""),
        "durum": f"Şi'râ'nın keskin ışığı {ev_metin} üzerine düşüyor; "
                 "hayatın burada görünür ve yüksek sesli.",
        "oneri": (f"Enerjini {ev_metin} etrafında topla — dağıttığında "
                  "yorulursun. Haftada bir günü buraya ayır ve o gün "
                  "başka alana geçme.")}

    # --- DEĞİŞİM ← ayrıklığın türevi --------------------------------------
    if simdi["yaklasiyor"]:
        o["degisim"] = {"olcum": f"ayrıklık {ay_s}, kapanıyor",
                        "durum": "Çevrim kapanma yönünde; dağınık olan toplanıyor.",
                        "oneri": "Yeni başlatma zamanı değil, TOPLAMA zamanı. "
                                 "Yarım kalanları bitir, açık dosyaları kapat."}
    else:
        o["degisim"] = {"olcum": f"ayrıklık {ay_s}, açılıyor",
                        "durum": "Çevrim açılma yönünde; alan genişliyor.",
                        "oneri": "Şimdi genişleme penceresi. Denemek istediğin "
                                 "şeyi küçük ölçekte başlat; bu faz onu taşır."}

    if yildizname:
        for k in o:
            o[k]["yildizname_notu"] = yildizname["tabiat"]
    return o


# ============================================================================
# TOPLU ÇALIŞTIRICI
# ============================================================================
def sira_cevrimi(chart: NatalChart, topoloji: Optional[dict] = None,
                 isim: Optional[str] = None, anne: Optional[str] = None,
                 simdi_jd: Optional[float] = None) -> dict:
    """ŞİRÂ ÇEVRİMİ — Tarık nefesi ve sekiz alan önerisi."""
    import datetime as dt
    j_now = simdi_jd if simdi_jd is not None else \
        swe.julday(*dt.datetime.utcnow().timetuple()[:3], 0.0)

    yildiz_d = sira_yildizi(chart.jd_ut)
    yildiz_s = sira_yildizi(j_now)
    dogum = sira_fazi(chart.jd_ut)
    simdi = sira_fazi(j_now)
    temaslar = sira_temaslari(chart, yildiz_d["lon"])

    # Osmanlı yıldıznâmesi
    yn = None
    if isim:
        eb = ebced_detail(isim + ((" " + anne) if anne else ""))
        burc = SIGNS[eb["ebced"] % 12]
        tab, aciklama = YILDIZNAME[burc]
        yn = {"ebced": eb["ebced"], "burc": burc, "tabiat": tab,
              "aciklama": aciklama,
              "yontem": "Osmanlı yıldıznâmesi: ebced(ad + anne adı) mod 12."}

    oneriler = _oneriler(dogum, simdi, temaslar, chart, topoloji, yn,
                         yildiz_d["lon"])

    # Tarık dönüşü tarihleri
    dogum_yil = dogum["yil"]
    donusler = [round(dogum_yil + SIRA_P * k, 2) for k in (1, 2)]
    yari = round(dogum_yil + SIRA_P / 2, 2)

    return {
        "modul": "ŞİRÂ ÇEVRİMİ — Tarık Nefesi",
        "aciklama": ("Şi'râ gerçek bir ikili yıldızdır: parlak Şi'râ A ile "
                     "görünmeyen beyaz cüce Şi'râ B, 50.13 yılda bir birbirinin "
                     "çevresinde döner. BERZAH'ın görünen ağız / görünmeyen "
                     "merkez yapısının gökteki karşılığıdır."),
        "sira_a": {"dogumda": yildiz_d, "bugun": yildiz_s,
                   "presesyon_kaymasi": round(
                       signed_sep(yildiz_s["lon"], yildiz_d["lon"]), 3)},
        "sira_b": {"dogumda": dogum, "bugun": simdi,
                   "yorunge": {"P_yil": SIRA_P, "e": SIRA_E,
                               "perigeon_epok": SIRA_T,
                               "kaynak": "Bond ve ark. 2017, HST astrometrisi"}},
        "temaslar": temaslar,
        "menzil": {"no": yildiz_d["menzil_no"], "ad": yildiz_d["menzil"],
                   "not": "28 menâzil-i kamer, tropikal boylamla ölçüldü."},
        "yildizname": yn,
        "tarik_donusu": {"tam_donus_yillari": donusler, "yari_donus": yari,
                         "not": ("Tam dönüşte kişi doğduğu faza geri döner "
                                 f"(~{SIRA_P:.0f} yaş). Yarı dönüşte "
                                 "(~25 yaş) faz tam karşıttır: en büyük "
                                 "karşıtlık dönemi.")},
        "oneriler": oneriler,
        "uyari": ("Yörünge mekaniği ve yıldız konumu gerçektir; bunlardan "
                  "karakter ve öneri türetmek modelin BENZETMESİDİR, fiziksel "
                  "nedensellik iddiası değildir."),
    }
