#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SORU KATALOĞU — danışanın seçtiği soruya cevap

NEDEN VAR
    Sistem şimdiye kadar "genel okuma" üretiyordu: kişiyi bir yol ayrımında
    tarif ediyor ama ne iyi yaptığını, neyi geliştirmesi gerektiğini, kendini
    nasıl ortaya koyacağını söylemiyordu.

    Danışan aslında GENEL OKUMA istemez; belirli bir soru sorar. "Rızkım
    nereden açılır", "eşim nasıl biri olur", "bu yıl neye odaklanayım".
    Bu katalog o soruları sabitler ve her birini HANGİ KATMANDAN
    cevaplanacağına bağlar.

    Böylece iki kazanç olur:
      1. Cevap uydurmaz — adı geçen katmanlardan çıkar.
      2. İki kişi asla aynı cevabı almaz, çünkü katmanlar farklıdır.

HASSAS SORULAR
    Listedeki bazı sorular doğrudan cevaplanamaz: hastalık riski, hamilelik
    penceresi, ameliyat tarihi, boşanma ihtimali, üçüncü kişinin duyguları,
    yatırım kararı, dava sonucu.

    Bunlar REDDEDİLMEZ — ÇERÇEVESİ DEĞİŞTİRİLİR. İyi bir danışman da öyle
    yapar: hastalık adı vermez, bünyeyi ve zorlanma desenini konuşur; boşanma
    kehaneti yapmaz, bağı yıpratanı ve kişinin kendi payını konuşur.
    Her hassas sorunun `cerceve` alanında bunun nasıl yapılacağı yazar.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# Katman kodları — baglam_ozeti'ndeki blok adlarıyla eşleşir
K_CEKIRDEK = "çekirdek (asıl sebep, şikâyet, karar eşiği)"
K_KUTLE = "kütleler (hangi eğilim ağır, hangisi geri çekiyor)"
K_TOPO = "alan topolojisi (yaşanan taraf, eşik yüksekliği, geçiş pencereleri)"
K_HUDUD = "hudûd (görünmeyen bağlar, kural dışına taşan kapasite)"
K_SIRA = "Şi'râ çevrimi (doğum dönemi ile bugünkü dönem farkı)"
K_KABZ = "Kabz/Bast (toparlanma mı yayılma mı, yükün boşaldığı yer)"
K_KADIM = "kadim katman (bütünlük, iç gerilim, hayat çağı, mizaç)"
K_HD = "Human Design (doğal karar biçimi, strateji, otorite)"
K_DENEME = "deneme modülleri (16 teknik: vahdet, asabiyye, süveyda, ikbal…)"
K_YER = "yer katmanı (astrokartografi, hangi konu nerede öne çıkıyor)"
K_TRANSIT = "bugünkü gök"
K_SOLAR = "yılın haritası"
K_KAPI = "kapılar (altı geleneğin ölçümü)"
K_ILISKI = "ilişki katmanı (sinastri/kompozit — yalnız iki harita varsa)"


class Soru:
    __slots__ = ("kod", "kategori", "metin", "katmanlar", "cerceve", "hassas")

    def __init__(self, kod: str, kategori: str, metin: str,
                 katmanlar: List[str], cerceve: str = "",
                 hassas: bool = False):
        self.kod = kod
        self.kategori = kategori
        self.metin = metin
        self.katmanlar = katmanlar
        self.cerceve = cerceve
        self.hassas = hassas

    def sozluk(self) -> dict:
        return {"kod": self.kod, "kategori": self.kategori,
                "metin": self.metin, "hassas": self.hassas}


# ============================================================================
KATEGORILER = {
    "iliski": "Aşk, evlilik ve ilişkiler",
    "kariyer": "Kariyer, finans ve rızık",
    "gelisim": "Kişisel gelişim ve iç yolculuk",
    "aile": "Sağlık, aile ve çocuklar",
    "zaman": "Öngörü, zamanlama ve yer",
}

SORULAR: List[Soru] = [
    # ---------------------------------------------------------------- İLİŞKİ
    Soru("i1", "iliski", "Evlilik potansiyelim ve kalıcı bağ göstergelerim neler?",
         [K_CEKIRDEK, K_KUTLE, K_DENEME, K_KADIM],
         "Kesin tarih ya da 'evleneceksin/evlenmeyeceksin' hükmü YOK. "
         "Bağ kurma biçimini, neyin kolay neyin zor geldiğini anlat."),
    Soru("i2", "iliski",
         "Eşimin karakteri, mesleği ve onunla nasıl bir ortamda tanışacağım?",
         [K_CEKIRDEK, K_KUTLE, K_YER, K_DENEME],
         "Kişiyi tarif etme — TİPİ tarif et: hangi mizaçtaki insanla "
         "tamamlanıyor, hangisiyle yıpranıyor. Meslek yerine 'hangi alandan "
         "biri sana denk düşer' de. Ortam için yer katmanını kullan. "
         "Fiziksel tarif YAPMA; ölçülmez, uydurma olur ve kişiyi yanıltır."),
    Soru("i3", "iliski", "Partnerimle uyumumuz nasıl?",
         [K_ILISKI, K_CEKIRDEK],
         "İki harita yoksa cevaplama: 'İlişki modunda iki kişinin verisiyle "
         "bakalım' de."),
    Soru("i4", "iliski", "Ciddi bir ilişki hayatıma ne zaman girer?",
         [K_TOPO, K_TRANSIT, K_SOLAR, K_DENEME],
         "Tarih vermek yerine 'bu kalıbın gevşediği dönemler' de. Kesinlik "
         "iddia etme.", hassas=True),
    Soru("i5", "iliski",
         "İlişkilerimde tekrar eden krizlerin ve kopuklukların sebebi ne?",
         [K_CEKIRDEK, K_KUTLE, K_KADIM],
         "En güçlü sorulardan biri: kişinin KENDİ payını göster."),
    Soru("i6", "iliski", "Eski bir bağ hâlâ üzerimde mi, o döngü bitti mi?",
         [K_CEKIRDEK, K_HUDUD, K_SIRA],
         "Üçüncü kişi hakkında yargı YOK. Kişinin kendi bağlılığını konuş."),
    Soru("i7", "iliski", "Ayrılık ya da boşanma ihtimalim var mı?",
         [K_CEKIRDEK, K_TOPO, K_KADIM],
         "KEHANET YOK. 'Ayrılırsın' ya da 'ayrılmazsın' ASLA deme. Bunun "
         "yerine: bu bağı yıpratan şey nedir, kişinin elinde ne var, neyi "
         "değiştirirse yıpranma azalır.", hassas=True),
    Soru("i8", "iliski", "Bağlılık ve güven konusunda neredeyim?",
         [K_CEKIRDEK, K_HD, K_DENEME]),
    Soru("i9", "iliski", "Partnerim şu an ne hissediyor?",
         [K_ILISKI],
         "CEVAPLAMA. Üçüncü kişinin duygusunu okumak ne mümkün ne doğru. "
         "Şunu söyle: 'Onun ne hissettiğini buradan okuyamam — ama sen ne "
         "sorduğunu ve neyi merak ettiğini konuşabiliriz.' Sonra kişinin "
         "kendi kaygısına dön.", hassas=True),
    Soru("i10", "iliski",
         "İlişkiyi bir üst aşamaya taşımak için uygun dönem hangisi?",
         [K_TOPO, K_TRANSIT, K_SOLAR],
         "Dönem penceresi ver, garanti verme.", hassas=True),

    # --------------------------------------------------------------- KARİYER
    Soru("k1", "kariyer",
         "Rızkım hangi alandan, sektörden veya iş kolundan açılır?",
         [K_KUTLE, K_CEKIRDEK, K_HD, K_DENEME, K_KADIM],
         "EN ÇOK SORULAN SORU — iyi cevapla. Meslek adı listesi verme; "
         "ÇALIŞMA BİÇİMİNİ tarif et: yalnız mı ekiple mi, uzun soluklu mu "
         "kısa atakla mı, görünür mü perde arkası mı, kendi kuralıyla mı "
         "kurumun kuralıyla mı. Sonra bu biçime uyan 2-3 ALAN söyle "
         "(sektör değil alan: 'insanı çözümleyen işler', 'elle kurulan "
         "işler' gibi). Kişinin şu anki işi buna uymuyorsa onu da söyle."),
    Soru("k2", "kariyer", "Kendi işimi kurmak bana uygun mu?",
         [K_HD, K_KUTLE, K_TOPO, K_KADIM],
         "Karar verme — koşulları söyle: hangi şartla yürür, hangi şartla "
         "zorlanır."),
    Soru("k3", "kariyer",
         "Kurumsal mı, serbest mi, yaratıcı alan mı bana uygun?",
         [K_HD, K_KUTLE, K_DENEME, K_KADIM]),
    Soru("k4", "kariyer", "İş değişikliği için uygun dönem hangisi?",
         [K_TOPO, K_TRANSIT, K_SOLAR],
         "Geçiş pencerelerini kullan; kesinlik verme.", hassas=True),
    Soru("k5", "kariyer", "Ortaklı iş bana yarar mı zarar mı?",
         [K_CEKIRDEK, K_DENEME, K_HD],
         "Finansal tavsiye DEĞİL: ortaklıkta senin davranışın neyi üretir, "
         "onu anlat."),
    Soru("k6", "kariyer", "Dışarıdan kaynak, miras ya da kredi akışı görünüyor mu?",
         [K_KUTLE, K_TOPO],
         "PARA VAADİ YOK. 'Şu tarihte para gelir' ASLA deme. Kişinin "
         "kaynakla ilişkisini, bekleme ve isteme biçimini konuş.",
         hassas=True),
    Soru("k7", "kariyer", "Yatırım ve riskli adımlar için ne zaman dikkatli olmalıyım?",
         [K_TOPO, K_TRANSIT],
         "FİNANSAL TAVSİYE YOK. 'Al/satma' deme. Kişinin acele ettiği ve "
         "acele ettiğinde ne yaptığı üzerine konuş; kararı ona bırak ve "
         "gerekirse mali müşavire yönlendir.", hassas=True),
    Soru("k8", "kariyer",
         "İş yerindeki rekabet ve otoriteyle çatışmalarımı nasıl yönetmeliyim?",
         [K_CEKIRDEK, K_DENEME, K_KUTLE],
         "'Gizli düşman' dilini KULLANMA — şüphe büyütür. Kişinin çatışma "
         "biçimini ve kendi payını konuş."),
    Soru("k9", "kariyer", "Tanınırlığa ve tepe noktama hangi dönemde ulaşırım?",
         [K_TOPO, K_SIRA, K_SOLAR, K_DENEME],
         "Garanti verme; dönem ve koşul söyle.", hassas=True),
    Soru("k10", "kariyer", "Maddi istikrar için hangi dönem destekleyici?",
         [K_TOPO, K_TRANSIT, K_SOLAR],
         "Para vaadi yok; çalışma ve sabır penceresi olarak anlat.",
         hassas=True),

    # --------------------------------------------------------------- GELİŞİM
    Soru("g1", "gelisim", "Bu hayattaki asıl görevim ve aşmam gereken konfor alanım ne?",
         [K_CEKIRDEK, K_KADIM, K_SIRA, K_KAPI]),
    Soru("g2", "gelisim", "Bende hangi denge eksik, nasıl toparlarım?",
         [K_KUTLE, K_KADIM, K_DENEME]),
    Soru("g3", "gelisim", "Şu anki yaş eşiğim bana hangi dersi getiriyor?",
         [K_SIRA, K_KADIM, K_TOPO, K_SOLAR]),
    Soru("g4", "gelisim", "Ana duygusal yaram nerede, nasıl onarırım?",
         [K_CEKIRDEK, K_KADIM, K_DENEME],
         "TERAPİ DEĞİL. Yara dilini abartma; kişiyi kırılgan gibi konumlama. "
         "Gerekirse bir uzmana başvurmasını öner."),
    Soru("g5", "gelisim", "Hangi bilinçaltı korkularım ve sezgisel yanlarım var?",
         [K_HUDUD, K_CEKIRDEK, K_DENEME]),
    Soru("g6", "gelisim",
         "En güçlü yeteneklerim neler ve bunları nasıl parlatırım?",
         [K_KUTLE, K_HD, K_DENEME, K_TOPO],
         "ÖNEMLİ SORU. Övgü değil, KULLANILABİLİR şey söyle: bu yetenek "
         "hangi işte, hangi ortamda, hangi rolde ortaya çıkar. Kişinin "
         "hafife aldığı yanı özellikle işaretle."),
    Soru("g7", "gelisim", "İçimdeki huzursuzluk ve öfkenin kaynağı ne?",
         [K_CEKIRDEK, K_KUTLE, K_KADIM],
         "Tanı koyma. Sürekli ya da ağırsa bir uzmanla konuşmasını öner."),
    Soru("g8", "gelisim", "Tekrar eden başarısızlık kalıplarımın kökeni ne?",
         [K_CEKIRDEK, K_TOPO, K_DENEME]),
    Soru("g9", "gelisim", "Sezgilerimi ve yaratıcılığımı nasıl üretken kılarım?",
         [K_HD, K_KUTLE, K_DENEME, K_KAPI]),
    Soru("g10", "gelisim", "Şu an beni hangi köklü dönüşüm dönemi etkiliyor?",
         [K_TOPO, K_TRANSIT, K_SIRA]),

    # ------------------------------------------------------------------ AİLE
    Soru("a1", "aile", "Bünyem nasıl, neye dikkat etmem iyi olur?",
         [K_KADIM, K_KUTLE],
         "TIBBÎ TEŞHİS YOK. Organ adı, hastalık adı, risk oranı VERME. "
         "Yalnız mizaç ve zorlanma deseni: hangi durumda yoruluyor, neyi "
         "aşırıya kaçırıyor. Cümlenin sonunda hekime yönlendir.",
         hassas=True),
    Soru("a2", "aile", "Çocuk konusunda ne görünüyor?",
         [K_KADIM, K_CEKIRDEK],
         "DOĞURGANLIK YORUMU YOK. Hamilelik penceresi, kısırlık, cinsiyet "
         "ASLA. Yalnız ebeveynlik yaklaşımı: nasıl bir ebeveyn olma "
         "eğilimin var, neyi zor bulursun. Tıbbî soruyu hekime yönlendir.",
         hassas=True),
    Soru("a3", "aile", "Çocuğuma yaklaşırken nelere dikkat etmeliyim?",
         [K_CEKIRDEK, K_HD, K_KADIM],
         "Çocuğun kendi haritası yoksa çocuk hakkında hüküm kurma; "
         "EBEVEYNİN yaklaşımını konuş."),
    Soru("a4", "aile", "Anne–baba ve kök aile dinamiklerim ne gösteriyor?",
         [K_CEKIRDEK, K_KADIM, K_DENEME],
         "Aile bireyleri hakkında yargı YOK; kişinin onlarla kurduğu bağı "
         "konuş."),
    Soru("a5", "aile", "Yorgunluk ve uyku düzenimi ne bozuyor?",
         [K_KADIM, K_HD, K_KUTLE],
         "TIBBÎ TAVSİYE YOK. Ritim ve düzen üzerine konuş; sürüyorsa "
         "hekime yönlendir.", hassas=True),
    Soru("a6", "aile", "Ev ve aile içi gerginliklerin arka planı ne?",
         [K_CEKIRDEK, K_DENEME, K_TOPO]),
    Soru("a8", "aile", "Aile büyüklerimin durumu ve haneyi etkileyen dönemler ne?",
         [K_CEKIRDEK, K_KADIM, K_TOPO],
         "BAŞKASININ SAĞLIĞINI OKUMA. Aile büyüğü hakkında hiçbir sağlık, "
         "ömür veya risk yorumu YAPMA — o kişi burada değil, verisi yok ve "
         "olsa bile bu doğru olmaz. Bunun yerine SORANIN kendi yükünü konuş: "
         "bakım sorumluluğunu nasıl taşıyor, neyi erteliyor, kendine ne kadar "
         "yer bırakıyor. Kaygı varsa yatıştır ve hekime yönlendir.",
         hassas=True),
    Soru("a9", "aile", "Çocuğumun yeteneklerini ve eğitimini nasıl desteklerim?",
         [K_CEKIRDEK, K_HD, K_KADIM],
         "ÇOCUĞU ETİKETLEME. Çocuğun kendi verisi yoksa onun hakkında hüküm "
         "kurma; 'şu meslek ona uygun', 'şu derste başarısız olur' ASLA. "
         "Ebeveynin yaklaşımını konuş: kendi beklentisini nereye koyuyor, "
         "hangi baskıyı farkında olmadan aktarıyor, neyi bırakırsa çocuk "
         "kendi yolunu bulur.", hassas=True),
    Soru("a10", "aile", "Ameliyat ya da estetik işlem için uygun zaman var mı?",
         [K_TOPO, K_TRANSIT],
         "TIBBÎ ZAMANLAMA VERME. 'Şu tarihte ameliyat ol / olma' ASLA. "
         "Bu kararı hekim verir ve gökyüzüne göre ertelemek zarar verebilir. "
         "Şunu söyle: 'Tıbbî zamanlamayı hekimin belirler; ben ancak senin "
         "karar verirken acele mi ettiğini, yoksa çok mu beklettiğini "
         "konuşabilirim.' Sonra kişinin karar biçimine dön.",
         hassas=True),
    Soru("a7", "aile", "Günlük düzenimi enerjimi yükseltecek biçimde nasıl kurarım?",
         [K_HD, K_KADIM, K_KUTLE],
         "Diyet, egzersiz reçetesi VERME. Ritim ve karar biçimi üzerine "
         "konuş."),

    # ----------------------------------------------------------------- ZAMAN
    Soru("z1", "zaman", "Bu yılın ana teması ve odaklanmam gereken alan ne?",
         [K_SOLAR, K_TOPO, K_TRANSIT]),
    Soru("z2", "zaman", "Yurt dışı ya da uzak yer benim için açık mı?",
         [K_YER, K_TOPO, K_KUTLE]),
    Soru("z3", "zaman", "Taşınmak bana ne getirir, nereye?",
         [K_YER],
         "Taşınmayı ÇÖZÜM gibi sunma. Bir konu öne çıkar, başkası geri "
         "çekilir — ikisini birden söyle."),
    Soru("z4", "zaman", "Resmî süreçler ve sözleşmeler için gökyüzü ne diyor?",
         [K_TOPO, K_TRANSIT],
         "HUKUKÎ TAVSİYE YOK. Dava sonucu tahmini ASLA. Kişinin sabrı ve "
         "acelesi üzerine konuş; avukata yönlendir.", hassas=True),
    Soru("z5", "zaman", "Bu yılki tutulmalar hangi alanımı tetikliyor?",
         [K_TRANSIT, K_SOLAR, K_TOPO]),
    Soru("z6", "zaman", "En kolay fırsat yakalayacağım alan neresi?",
         [K_KUTLE, K_TOPO, K_DENEME]),
    Soru("z7", "zaman", "Hangi dönemlerde işleri bekletmeliyim?",
         [K_TRANSIT, K_TOPO]),
    Soru("z8", "zaman", "Şu anki psikolojik dönemimi ne açıklıyor?",
         [K_TRANSIT, K_SIRA, K_TOPO, K_KADIM]),
    Soru("z9", "zaman", "Hangi alanda ani uyanış ve kırılma yaşıyorum?",
         [K_TRANSIT, K_TOPO, K_HUDUD]),
    Soru("z10", "zaman", "Önümüzdeki altın zaman aralığı hangi ayları kapsıyor?",
         [K_TOPO, K_TRANSIT, K_SOLAR, K_DENEME],
         "Geçirgenlik pencerelerini kullan; garanti verme.", hassas=True),
]

# ============================================================================
# KATEGORİ ÇERÇEVELERİ
# ============================================================================
# Hudûd-ı Felek bölümünün talimatı ötekilerden iyiydi çünkü modele NE
# ARAYACAĞINI söylüyordu. Ötekiler yalnız "şunu anlat" diyordu ve genel
# çıkıyordu. Her kategoriye aynı keskinlikte bir arama emri verildi:
# bakılacak şeyin BİÇİMİ tarif ediliyor, içeriği veriden gelecek.

KATEGORI_CERCEVE: Dict[str, str] = {
    "iliski":
        "ARA: Kişinin yakınlaşma ve uzaklaşma ANINDA yaptığı tekrar eden "
        "hamle. İlişkiler hakkında genel şey söyleme; şunları bul: "
        "(1) yakınlık arttığında ne yapıyor — geri mi çekiliyor, hızlanıyor "
        "mu, sınav mı kuruyor; (2) bu hamleye kendisi ne ad veriyor, "
        "gerçekte ne işe yarıyor; (3) karşıdakinin bunu nasıl gördüğü, "
        "yani kişinin göremediği kısım. "
        "Kimseyi suçlama, kimseyi kurtarma; kişinin elindeki tek düğmeyi "
        "göster.",
    "kariyer":
        "ARA: Kişinin emeğinin DEĞERE dönüştüğü ve dağıldığı yer. Meslek "
        "adı sayma; şunları bul: (1) hangi koşulda üretkenleşiyor — yalnız "
        "mı ekiple mi, kendi kuralıyla mı dış çerçeveyle mi, uzun soluklu "
        "mu atakla mı; (2) emeğinin nerede boşa gittiği, genelde fark "
        "etmediği yer; (3) görünürlükle ilişkisi — görülmek mi istiyor, "
        "görülmekten mi kaçıyor, ikisi arasında mı sıkışıyor. "
        "Sonra bu biçime uyan iki üç ALAN söyle: sektör değil, işin türü.",
    "gelisim":
        "ARA: Kişinin kendini anlattığı hikâye ile fiilen yaptığı şey "
        "arasındaki AÇIKLIK. Erdem listesi çıkarma; şunları bul: "
        "(1) kendine dair hangi cümleyi kuruyor ve o cümle nerede tutmuyor; "
        "(2) hangi gücünü zayıflık sanıyor — en değerli bulgu budur; "
        "(3) değişimi neye erteliyor, koşul olarak öne sürdüğü şey ne. "
        "Yara dilini abartma, kişiyi kırılgan konumlama.",
    "aile":
        "ARA: Kişinin taşıdığı YÜKÜN kime ait olduğu. Teşhis koyma, kimseyi "
        "yargılama; şunları bul: (1) kendisine ait olmayan hangi yükü "
        "taşıyor ve kimin adına; (2) kendisine ait olan hangi yükü "
        "taşımıyor; (3) bu evde konuşulmayan şey ne ve kişinin payı ne "
        "kadar. Sağlık ve çocuk konusunda hüküm YOK; ilgili uzmana "
        "yönlendir.",
    "zaman":
        "ARA: Hangi kapının aralandığı ve o aralıkta TAM OLARAK neyin "
        "mümkün olduğu. Tarih listesi verme; şunları bul: (1) hangi dönemde "
        "direnç düşüyor — ay adı ver, gün değil; (2) o aralıkta ne "
        "kolaylaşıyor, ne kolaylaşmıyor; (3) kişi o aralığı kaçırırsa ne "
        "olur — felaket değil, gerçekçi karşılık. "
        "Garanti verme; 'kapı aralık' dili kullan, 'şu olacak' değil.",
}


_INDEKS: Dict[str, Soru] = {s.kod: s for s in SORULAR}


def liste(kategori: Optional[str] = None) -> dict:
    s = [x for x in SORULAR if not kategori or x.kategori == kategori]
    return {"kategoriler": [{"kod": k, "ad": v} for k, v in KATEGORILER.items()],
            "sorular": [x.sozluk() for x in s],
            "toplam": len(s)}


def getir(kodlar: List[str]) -> List[Soru]:
    return [_INDEKS[k] for k in kodlar if k in _INDEKS]


def onerilen(veri: Dict[str, Any], adet: int = 3) -> List[str]:
    """
    Bu haritada EN OLASI takip sorularını seçer.

    Rastgele değil: bulgulara bakar. Şikâyet ile sebep farklı evdeyse
    "tekrar eden kalıp" sorusu öne çıkar; karar biçimi beklemeyi
    gerektiriyorsa "kendi işimi kurmak" sorusu anlamlıdır.

    Amaç seansta beklemeyi bitirmek: bu üç sorunun cevabı analiz biter
    bitmez arka planda yazılır, danışman tıkladığında hazır gelir.
    """
    v2 = veri.get("berzah_v2") or {}
    ad, kd = (v2.get("AD") or {}), (v2.get("KD") or {})
    hd = veri.get("human_design") or {}
    mn = ((veri.get("maneviyat") or {}).get("mizan") or {})
    puan: Dict[str, int] = {}

    def art(kod, n=1):
        puan[kod] = puan.get(kod, 0) + n

    # Şikâyet ile sebep farklı evdeyse: tekrar eden kalıp meselesi
    if ad.get("ev") and kd.get("ev") and ad["ev"] != kd["ev"]:
        art("g8", 3); art("i5", 2)
    # Görünürlük/kariyer evleri
    if ad.get("ev") in (2, 6, 10) or kd.get("ev") in (2, 6, 10):
        art("k1", 3); art("g6", 2)
    # İlişki evleri
    if ad.get("ev") in (5, 7, 8, 11) or kd.get("ev") in (5, 7, 8, 11):
        art("i5", 3); art("i1", 2)
    # Aile/kök evleri
    if ad.get("ev") in (3, 4, 12) or kd.get("ev") in (3, 4, 12):
        art("a4", 2); art("g4", 2)
    # Karar biçimi beklemeyi gerektiriyorsa girişimcilik sorusu anlamlı
    if "bekle" in str(hd.get("strateji", "")).lower():
        art("k2", 2)
    # Gelenekler ayrışıyorsa iç yolculuk sorusu
    if (mn.get("yakinsama") or {}).get("kac_gelenek", 9) <= 2:
        art("g1", 2)
    # Her haritada anlamlı olan taban
    art("g6", 1); art("z1", 1); art("k1", 1)

    sirali = sorted(puan.items(), key=lambda x: -x[1])
    secim = [k for k, _ in sirali if k in _INDEKS][:adet]
    return secim or ["g6", "k1", "z1"][:adet]


def talimat(secilen: List[Soru]) -> str:
    """Seçilen soruları AI talimatına çevirir."""
    p: List[str] = []
    for i, s in enumerate(secilen, 1):
        p.append(f"\nSORU {i}: {s.metin}")
        p.append(f"  Kullanacağın katmanlar: {', '.join(s.katmanlar)}")
        if s.cerceve:
            p.append(f"  ÇERÇEVE: {s.cerceve}")
    return "\n".join(p)
