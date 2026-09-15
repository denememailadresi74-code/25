#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TAM RAPOR — bütün katmanlardan tek bir uzun okuma, PDF olarak

NEDEN AYRI BİR MODÜL
    Bütünsel okuma (sentez) kısa bir toparlamadır: 5-7 paragraf. Danışan
    soruları belirli sorulara cevap verir. Bu modül üçüncü bir şey yapar:
    kişiyi BAŞTAN SONA anlatan, elde kalan bir belge üretir.

    Tek çağrıyla yazılamaz. Uzun metin çok jeton ister, çok jeton uzun
    sürer, uzun süre zaman aşımına girer — soru bölümünde bunu yaşadık.
    Bu yüzden rapor BÖLÜM BÖLÜM üretilir; her bölüm kendi katmanlarından
    beslenir ve sonunda birleştirilir.

BÖLÜMLERİN DÜZENİ
    Katmana göre değil, KİŞİYE göre. Danışan "alan topolojisi" okumak
    istemez; "ben kimim, ne iyi yapıyorum, neyi geliştirmeliyim" okumak
    ister. Bölümler bu soruların sırasıyla dizilir.

PDF
    ReportLab + DejaVu. Türkçe karakterler için gömülü font şart:
    varsayılan fontlarda ş, ğ, İ, ı düzgün çıkmaz.
"""
from __future__ import annotations

import io
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple

# ============================================================================
# RAPOR BÖLÜMLERİ — kişiye göre dizilmiş
# ============================================================================
# (kod, başlık, hangi katmanlar, ne aranacak)
BOLUMLER: List[Tuple[str, str, str, str]] = [
    ("portre", "Bu kişi kim",
     "çekirdek, kütleler, kadim katman, Human Design",
     "Kişinin temel işleyişi: neye göre hareket ediyor, dünyayla nasıl "
     "temas kuruyor, ilk izlenimi ile gerçekte olanı arasındaki fark ne. "
     "Sıfat listesi değil — bir insanı tanıyan birinin anlatacağı gibi."),

    ("dongu", "Tekrar eden döngü",
     "çekirdek, karar eşiği, alan topolojisi",
     "Hayatında dönüp dolaşıp geldiği yer. Şikâyet ettiği şey ile asıl "
     "sebep arasındaki fark. Bu döngüyü kendi eliyle nasıl kuruyor — "
     "suçlama olmadan, ama yumuşatmadan."),

    ("guc", "Ne iyi yapıyor",
     "kütleler, alan topolojisi, Human Design, deneme modülleri",
     "Gerçek gücü. Özellikle HAFİFE ALDIĞI yanı: zayıflık sandığı ama "
     "aslında işleyen şey. Bu gücün hangi ortamda ortaya çıktığını, "
     "hangisinde körelttiğini söyle."),

    ("gelisim", "Neyi geliştirmeli",
     "çekirdek, hudûd, kapılar, kadim katman",
     "Eksik değil, ÇALIŞILMAMIŞ olan. Kişinin hiç el atmadığı yan. "
     "Nereden başlanacağını somut söyle; 'kendini geliştir' gibi boş "
     "cümle kurma."),

    ("kendini", "Kendini nasıl ortaya koyar",
     "Human Design, kütleler, alan topolojisi, yer",
     "Bu kişi görünür olmak istediğinde ne yapmalı: hangi ortamda, hangi "
     "rolde, hangi davranışla. Ne zaman öne çıkmalı, ne zaman beklemeli. "
     "Kendini yanlış yerde konumlandırdığında ne oluyor."),

    ("iliski", "İlişkilerde",
     "çekirdek, hudûd, kütleler",
     "Yakınlaşma ve uzaklaşma anındaki tekrar eden hamlesi. Bu hamleye "
     "kendisi ne ad veriyor, gerçekte ne işe yarıyor. Kimseyi suçlama; "
     "elindeki tek düğmeyi göster."),

    ("is", "İş ve rızık",
     "kütleler, Human Design, alan topolojisi, kadim katman",
     "Emeğinin değere döndüğü ve dağıldığı yer. Hangi koşulda üretken "
     "oluyor. Görünürlükle ilişkisi. Bu biçime uyan iki üç alan söyle — "
     "sektör değil, işin türü."),

    ("ic", "İç dünyası",
     "kadim katman, deneme modülleri, çekirdek, kapılar",
     "Kendini anlattığı hikâye ile fiilen yaptığı arasındaki açıklık. "
     "İçindeki gerilimin nereden geldiği. Yara dilini abartma, kırılgan "
     "konumlama."),

    ("zaman", "Önündeki dönem",
     "alan topolojisi, bugünkü gök, yılın haritası, Şi'râ çevrimi",
     "Hangi kapı aralanıyor ve o aralıkta tam olarak ne mümkün oluyor. "
     "Ay adı ver, gün verme. Garanti verme; 'kapı aralık' dili kullan."),

    ("kapanis", "Kapanış",
     "çekirdek, alan topolojisi",
     "İki şey: bu yıl neye çalışacak, bu hafta ne yapacak. Bu hafta "
     "yapılacak şey BİTİNCE 'yaptım' denebilecek kadar somut olsun. "
     "Motivasyon cümlesi kurma."),
]


# ============================================================================
# İKİ RAPOR TÜRÜ
# ============================================================================
# DANIŞAN raporu sessiz okunmak için yazılır: tam cümleler, kendi kendine
# yeten paragraflar, elde kalacak bir belge.
#
# ANLATIM metni SESLİ OKUNMAK için yazılır ve bambaşka bir şeydir. Yazılı
# iyi olan cümle, okunduğunda kötü olabilir: uzun cümlede nefes biter,
# yan cümlecikte dinleyen kaybolur. Ayrıca danışmanın seansta ihtiyaç
# duyduğu şey yalnız metin değildir — nerede duracağını, ne soracağını,
# neye dikkat edeceğini ve arkadaki dayanağı da bilmesi gerekir.
#
# Bu yüzden anlatım metninde SAHNE YÖNERGELERİ vardır ve bunlar PDF'te
# gövde metninden görsel olarak ayrılır.

ANLATIM_ISARET = {
    "[DUR]": ("dur", "Burada durup soru sor"),
    "[İZLE]": ("izle", "Danışanın tepkisini gözle"),
    "[DİKKAT]": ("dikkat", "Burada dikkatli ol"),
    "[ARKA PLAN]": ("arka", "Sen bil, söyleme"),
}


def _pdf_font() -> str:
    """
    Türkçe karakter için gömülü font. Varsayılan ReportLab fontlarında
    ş, ğ, İ, ı düzgün çıkmaz — DejaVu gömülür.
    """
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    # DÖRT KESİM DE GEREKLİ. Önceden yalnız düz ve kalın kaydediliyordu;
    # <i> etiketi sessizce düz yazıya düşüyordu ve VURGU GÖRÜNMÜYORDU.
    # Sesli anlatım metninde vurgu işlevseldir: danışman hangi kelimeyi
    # vurgulayacağını oradan okur.
    kokler = ("/usr/share/fonts/truetype/dejavu/",
              "/usr/share/fonts/dejavu/",
              "/usr/share/fonts/TTF/")
    for kok in kokler:
        duz = kok + "DejaVuSans.ttf"
        if not os.path.isfile(duz):
            continue
        try:
            from reportlab.lib.fonts import addMapping
            pdfmetrics.registerFont(TTFont("Gövde", duz))
            addMapping("Gövde", 0, 0, "Gövde")
            for dosya, ad, kalin_mi, egik_mi in (
                    ("DejaVuSans-Bold.ttf", "Gövde-K", 1, 0),
                    ("DejaVuSans-Oblique.ttf", "Gövde-E", 0, 1),
                    ("DejaVuSans-BoldOblique.ttf", "Gövde-KE", 1, 1)):
                yol = kok + dosya
                if os.path.isfile(yol):
                    pdfmetrics.registerFont(TTFont(ad, yol))
                    addMapping("Gövde", kalin_mi, egik_mi, ad)
            return "Gövde"
        except Exception:
            continue
    return "Helvetica"          # son çare: Türkçe bozulabilir


def _xml_kacis(m: str) -> str:
    return (m.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _md_to_rl(m: str) -> str:
    """**kalın** ve *italik* işaretlerini ReportLab etiketine çevirir."""
    m = _xml_kacis(m)
    m = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", m)
    m = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", m)
    return m


def pdf_uret(baslik: str, altbaslik: str,
             bolumler: List[Tuple[str, str]], uyari: str = "",
             tur: str = "danisan", chart=None, danisman: str = "") -> bytes:
    """
    Bölümleri PDF'e döker.

    tur="danisan"  → sessiz okuma için sade dizgi
    tur="anlatim"  → sesli anlatım için: sahne yönergeleri kutulanır,
                     satır aralığı açılır (gözün satır kaçırmaması için),
                     yazı biraz büyür.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    PageBreak, HRFlowable, Table, TableStyle)

    font = _pdf_font()
    kalin = "Gövde-K" if font == "Gövde" else "Helvetica-Bold"
    tampon = io.BytesIO()
    doc = SimpleDocTemplate(
        tampon, pagesize=A4,
        # Satır uzunluğu okunabilirliği belirler: A4 genişliğinde dar
        # kenarlıkla satır 100+ karaktere çıkar ve göz satır kaçırır.
        # 26 mm kenarlık satırı ~78 karaktere indirir.
        leftMargin=26 * mm, rightMargin=26 * mm,
        topMargin=22 * mm, bottomMargin=22 * mm,
        title=baslik, author="ZÎC")

    s_baslik = ParagraphStyle("b", fontName=kalin, fontSize=22, leading=27,
                              spaceAfter=4)
    s_alt = ParagraphStyle("a", fontName=font, fontSize=10.5, leading=15,
                           textColor=colors.HexColor("#666666"), spaceAfter=18)
    s_bol = ParagraphStyle("bl", fontName=kalin, fontSize=14, leading=19,
                           spaceBefore=16, spaceAfter=7,
                           textColor=colors.HexColor("#14110F"))
    anlatim = (tur == "anlatim")
    # Sesli okunan metinde satır aralığı AÇIK olmalı: göz satır kaçırırsa
    # danışman duraklar. Ayrıca iki yana yaslama yapılmaz — düzensiz
    # kelime aralığı sesli okumada takılmaya yol açar.
    s_govde = ParagraphStyle("g", fontName=font,
                             fontSize=12.2 if anlatim else 10.7,
                             leading=20 if anlatim else 16.4,
                             spaceAfter=11 if anlatim else 9,
                             alignment=0 if anlatim else 4)
    s_dur = ParagraphStyle("d", fontName=kalin, fontSize=9.4, leading=13.4,
                           leftIndent=0, spaceBefore=2, spaceAfter=6,
                           textColor=colors.HexColor("#1B4FA0"),
                           borderPadding=6, backColor=colors.HexColor("#EEF3FB"))
    s_izle = ParagraphStyle("i", fontName=font, fontSize=9.2, leading=13,
                            leftIndent=0, spaceBefore=2, spaceAfter=6,
                            textColor=colors.HexColor("#1F6F5C"),
                            borderPadding=6, backColor=colors.HexColor("#EAF5F1"))
    s_dikkat = ParagraphStyle("dk", fontName=kalin, fontSize=9.2, leading=13,
                              leftIndent=0, spaceBefore=2, spaceAfter=6,
                              textColor=colors.HexColor("#A32A1C"),
                              borderPadding=6, backColor=colors.HexColor("#FBEEEC"))
    s_arka = ParagraphStyle("ar", fontName=font, fontSize=8.6, leading=12.4,
                            leftIndent=0, spaceBefore=2, spaceAfter=6,
                            textColor=colors.HexColor("#666666"),
                            borderPadding=6, backColor=colors.HexColor("#F2F2F0"))
    s_not = ParagraphStyle("n", fontName=font, fontSize=8.6, leading=12.6,
                           textColor=colors.HexColor("#777777"),
                           spaceBefore=14)

    # --- KAPAK ---
    # Öncesinde başlık gövdenin üstüne yapışıyordu; belge "çıktı" gibi
    # duruyordu. Ayrı bir kapak, elde tutulacak bir şeye dönüştürür.
    s_kapak = ParagraphStyle("kp", fontName=kalin, fontSize=30, leading=36,
                             spaceAfter=10, alignment=0)
    s_kapak_alt = ParagraphStyle("kpa", fontName=font, fontSize=11.5,
                                 leading=17, spaceAfter=6,
                                 textColor=colors.HexColor("#555555"))
    s_kapak_not = ParagraphStyle("kpn", fontName=font, fontSize=9.2,
                                 leading=14, textColor=colors.HexColor("#888888"))
    s_no = ParagraphStyle("no", fontName=font, fontSize=9.5, leading=13,
                          textColor=colors.HexColor("#AAAAAA"),
                          spaceBefore=14, spaceAfter=1)
    s_ilk = ParagraphStyle("ilk", parent=s_govde, spaceBefore=2)

    akis: List[Any] = [
        Spacer(1, 26 * mm if chart is not None else 58 * mm),
        Paragraph(_xml_kacis(baslik), s_kapak),
        HRFlowable(width="34%", thickness=2.2, color=colors.HexColor("#14110F"),
                   spaceBefore=6, spaceAfter=14, hAlign="LEFT"),
        Paragraph(_xml_kacis(altbaslik), s_kapak_alt),
    ]
    if danisman:
        akis.append(Paragraph(_xml_kacis(danisman), ParagraphStyle(
            "dn", fontName=font, fontSize=10, leading=15,
            textColor=colors.HexColor("#888888"), spaceAfter=2)))
    if chart is not None:
        try:
            akis.append(Spacer(1, 6 * mm))
            akis.append(cark_cizimi(chart, 74, font))
            akis.append(Spacer(1, 4 * mm))
        except Exception:
            pass                    # çark çizilemezse belge yine üretilir
    akis += [
        Spacer(1, 6 * mm),
        Paragraph("İÇİNDEKİLER", ParagraphStyle(
            "ib", fontName=font, fontSize=8.6, leading=12,
            textColor=colors.HexColor("#999999"))),
        Spacer(1, 3 * mm),
    ]
    for i, (bas, _m) in enumerate(bolumler, 1):
        akis.append(Paragraph(
            f'<font color="#AAAAAA">{i:02d}</font>&nbsp;&nbsp;{_xml_kacis(bas)}',
            ParagraphStyle("ic", fontName=font, fontSize=10.4, leading=17.5)))
    akis.append(PageBreak())

    for i, (bas, metin) in enumerate(bolumler):
        if i:
            akis.append(PageBreak())
        akis.append(Paragraph(f"{i + 1:02d}", s_no))
        akis.append(Paragraph(_xml_kacis(bas), s_bol))
        akis.append(HRFlowable(width="100%", thickness=0.6,
                               color=colors.HexColor("#DDDDDD"),
                               spaceAfter=9))
        parlar = [p.strip() for p in (metin or "").split("\n") if p.strip()]

        if not anlatim:
            for _pn, par in enumerate(parlar):
                akis.append(Paragraph(_md_to_rl(par),
                                      s_ilk if _pn == 0 else s_govde))
            continue

        # --- ANLATIM: KENAR NOTU DÜZENİ ---
        # Yönergeler önceden metnin AKIŞINI KESİYORDU: sesli okurken göz
        # konuşma metninden kopuyor, sonra yerini arıyordu. Artık yönerge
        # sağ kenarda, konuşma metni solda kesintisiz akıyor.
        govde_g = (doc.width * 0.62)
        kenar_g = (doc.width * 0.36)
        satirlar: List[List[Any]] = []
        bekleyen: List[Any] = []          # o ana kadarki konuşma metni

        def bosalt(yonerge=None):
            if not bekleyen and yonerge is None:
                return
            satirlar.append([bekleyen[:] if bekleyen else "",
                             yonerge if yonerge is not None else ""])
            bekleyen.clear()

        for _pn, par in enumerate(parlar):
            if par.startswith(("[DUR]", "[İZLE]", "[DİKKAT]", "[ARKA PLAN]")):
                bicem = (s_dur if par.startswith("[DUR]") else
                         s_izle if par.startswith("[İZLE]") else
                         s_dikkat if par.startswith("[DİKKAT]") else s_arka)
                bosalt(Paragraph(_md_to_rl(par), bicem))
            else:
                bekleyen.append(Paragraph(_md_to_rl(par),
                                          s_ilk if not satirlar and not bekleyen
                                          else s_govde))
        bosalt()

        if satirlar:
            t = Table(satirlar, colWidths=[govde_g, kenar_g], hAlign="LEFT")
            t.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (0, -1), 0),
                ("RIGHTPADDING", (0, 0), (0, -1), 10),
                ("LEFTPADDING", (1, 0), (1, -1), 8),
                ("RIGHTPADDING", (1, 0), (1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                # Kenar sütununu ayıran ince dikey çizgi
                ("LINEBEFORE", (1, 0), (1, -1), 0.6,
                 colors.HexColor("#DDDDDD")),
            ]))
            akis.append(t)
    if uyari:
        akis.append(Spacer(1, 8))
        akis.append(HRFlowable(width="100%", thickness=0.7,
                               color=colors.HexColor("#DDDDDD")))
        akis.append(Paragraph(_xml_kacis(uyari), s_not))

    def sayfa(kanvas, belge):
        kanvas.saveState()
        kanvas.setFont(font, 8)
        kanvas.setFillColor(colors.HexColor("#AAAAAA"))
        kanvas.drawRightString(A4[0] - 22 * mm, 12 * mm, str(belge.page))
        kanvas.drawString(22 * mm, 12 * mm, baslik)
        kanvas.setStrokeColor(colors.HexColor("#EEEEEE"))
        kanvas.setLineWidth(0.5)
        kanvas.line(22 * mm, 16 * mm, A4[0] - 22 * mm, 16 * mm)
        kanvas.restoreState()

    def kapak(kanvas, belge):
        """Kapakta sayfa numarası ve çizgi olmaz."""
        kanvas.saveState()
        kanvas.setStrokeColor(colors.HexColor("#14110F"))
        kanvas.setLineWidth(3)
        kanvas.line(0, A4[1] - 6, A4[0], A4[1] - 6)
        kanvas.restoreState()

    doc.build(akis, onFirstPage=kapak, onLaterPages=sayfa)
    return tampon.getvalue()


# ============================================================================
# ÇARK ÇİZİMİ — PDF için
# ============================================================================
# Doğum haritası raporunda haritanın kendisi yoktu. Belge eksik duruyordu:
# kişi "haritam nerede" diye sorar ve haklıdır.
#
# SVG gömmek yerine doğrudan ReportLab ile çiziliyor. Sebep: SVG dönüşümü
# ek bağımsızlık ister (svglib) ve font gömme sorunları çıkarır. Doğrudan
# çizim tam denetim verir ve baskıda temiz çıkar.

BURC_KISA = ["Koç", "Boğ", "İki", "Yen", "Asl", "Bşk",
             "Ter", "Akr", "Yay", "Oğl", "Kov", "Bal"]


def cark_cizimi(chart, boyut: float = 150.0, font: str = "Helvetica"):
    """
    Natal çarkı ReportLab Drawing olarak döner.

    Baskı için tasarlandı: renk yerine çizgi kalınlığı ve gri tonu ayrım
    yapar, siyah-beyaz yazıcıda da okunur.
    """
    import math
    from reportlab.graphics.shapes import (Drawing, Circle, Line, String,
                                           Group)
    from reportlab.lib import colors

    from .astro import CORE10, TR_NAME

    d = Drawing(boyut * 2, boyut * 2)
    m = boyut                       # merkez
    dis, ic, gez = boyut * 0.94, boyut * 0.76, boyut * 0.60

    def nokta(derece, yaricap):
        """
        ASC solda (180°), burçlar SAAT YÖNÜNÜN TERSİNE ilerler.

        İlk denemede işaret tersti: Boğa'dan sonra Koç geliyordu, oysa
        İkizler gelmeli. Çarkta yön yanlış olunca ev sıraları da ters
        okunur — sessiz ama ciddi bir hata.
        """
        a = math.radians(180 + (derece - chart.asc))
        return m + yaricap * math.cos(a), m + yaricap * math.sin(a)

    gri = colors.HexColor("#BBBBBB")
    koyu = colors.HexColor("#333333")

    d.add(Circle(m, m, dis, fillColor=None, strokeColor=koyu, strokeWidth=1))
    d.add(Circle(m, m, ic, fillColor=None, strokeColor=gri, strokeWidth=0.7))
    d.add(Circle(m, m, gez * 0.55, fillColor=None, strokeColor=gri,
                 strokeWidth=0.5))

    # Burç bölmeleri ve kısaltmaları
    for i in range(12):
        x1, y1 = nokta(i * 30, ic)
        x2, y2 = nokta(i * 30, dis)
        d.add(Line(x1, y1, x2, y2, strokeColor=gri, strokeWidth=0.6))
        tx, ty = nokta(i * 30 + 15, (ic + dis) / 2)
        s = String(tx, ty - 3, BURC_KISA[i], fontName=font, fontSize=7,
                   fillColor=koyu, textAnchor="middle")
        d.add(s)

    # Ev sınırları
    cusps = list(getattr(chart, "cusps", []) or [])
    for i, c in enumerate(cusps[:12]):
        x1, y1 = nokta(c, gez * 0.55)
        x2, y2 = nokta(c, ic)
        kalin = 1.4 if i in (0, 3, 6, 9) else 0.5
        d.add(Line(x1, y1, x2, y2, strokeColor=koyu if kalin > 1 else gri,
                   strokeWidth=kalin))
        ex, ey = nokta(c + 4, gez * 0.62)
        d.add(String(ex, ey - 2.5, str(i + 1), fontName=font, fontSize=5.6,
                     fillColor=gri, textAnchor="middle"))

    # Cisimler — üst üste binmeyi azaltmak için yarıçap kaydırılır
    # Üst üste binmeyi azaltmak: yakın cisimler farklı yarıçapa alınır.
    # İlk eşik (7°, 11 px) yetmiyordu — dört cisim aynı bölgede üst üste
    # biniyordu. Eşik genişletildi, adım büyütüldü.
    yerlesim: List[float] = []
    sirali = sorted((k for k in CORE10 if chart.bodies.get(k)),
                    key=lambda k: chart.bodies[k].lon)
    for k in sirali:
        b = chart.bodies[k]
        lon = b.lon
        kayma = 0
        for onceki in yerlesim:
            if abs(((lon - onceki + 180) % 360) - 180) < 13:
                kayma += 1
        yerlesim.append(lon)
        r = gez - (kayma % 4) * 14
        x, y = nokta(lon, r)
        ad = TR_NAME.get(k, k)[:3]
        d.add(String(x, y - 2.6, ad, fontName=font, fontSize=6.6,
                     fillColor=colors.black, textAnchor="middle"))
        # cisimden çembere ince işaret
        ux, uy = nokta(lon, ic - 3)
        vx, vy = nokta(lon, ic)
        d.add(Line(ux, uy, vx, vy, strokeColor=koyu, strokeWidth=0.7))

    # ASC ve MC vurgusu
    for derece, etiket in ((chart.asc, "ASC"), (chart.mc, "MC")):
        x1, y1 = nokta(derece, ic)
        x2, y2 = nokta(derece, dis)
        d.add(Line(x1, y1, x2, y2, strokeColor=colors.black, strokeWidth=1.6))
        tx, ty = nokta(derece, dis + 7)
        d.add(String(tx, ty - 2.5, etiket, fontName=font, fontSize=6.4,
                     fillColor=colors.black, textAnchor="middle"))
    return d
