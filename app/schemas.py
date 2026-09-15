#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pydantic şemaları — istek/yanıt doğrulama."""
from __future__ import annotations
import re as _re
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


def _metin_temizle(v):
    """
    Serbest metin alanlarından işaretleme karakterlerini temizler.
    Arayüz zaten esc() ile kaçışlıyor; bu, veriyi başka bir istemci
    işlerse diye eklenen ikinci katman.
    """
    if not isinstance(v, str):
        return v
    return _re.sub(r"[<>]", "", v).strip()


class BirthInput(BaseModel):
    name: str = Field("Danışan", max_length=80, description="Etiket / danışan adı")
    year: int = Field(..., ge=1800, le=2200)
    month: int = Field(..., ge=1, le=12)
    day: int = Field(..., ge=1, le=31)
    hour: int = Field(..., ge=0, le=23)
    minute: int = Field(..., ge=0, le=59)
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    tz_name: Optional[str] = Field(None, description="IANA saat dilimi, ör. Europe/Istanbul")
    tz_offset: Optional[float] = Field(None, description="UTC ofseti saat; verilirse tz_name'i ezer")
    house_system: str = Field("P", description="P=Placidus K=Koch W=WholeSign R=Regiomontanus")
    sr_year: Optional[int] = Field(None, description="Solar Return yılı (kabz/bast köprü testi)")
    months: int = Field(18, ge=6, le=48, description="Takvim modülleri ufku (ay)")
    days: int = Field(365, ge=90, le=730, description="Sıçrama takvimi ufku (gün)")
    rol: str = Field("yonetici", description="yonetici | misafir")
    rektifiye: bool = Field(False, description="Doğum saatini olaylardan çöz")
    olaylar: List[Any] = Field(default_factory=list, max_length=12,
                               description="[{tarih, ad}]")

    @field_validator("name", "isim", "anne", mode="before")
    @classmethod
    def _metin_alanlari(cls, v):
        return _metin_temizle(v)
    yorumla: bool = Field(True, description="Hüküm/Çatal satırlarını AI ile "
                                            "arka planda kişiselleştir")
    model: Optional[str] = Field(None, max_length=120, description="Danışman modeli")
    isim: Optional[str] = Field(None, max_length=120,
                                description="İsim Tecellîsi için nüfus imlâsıyla tam ad")
    anne: Optional[str] = Field(None, max_length=80,
                                description="Anne adı (ebced'e eklenir)")


class SolarReturnAttachInput(BaseModel):
    """Mevcut analiz oturumuna Solar Return bağlar ve Hüküm'ü yeniden üretir."""
    oturum: str = Field(..., min_length=8, max_length=160)
    year: int = Field(..., ge=1800, le=2200)

class Olay(BaseModel):
    tarih: str = Field(..., description="YYYY-MM-DD")
    ad: str = Field("", max_length=120)


class RektifikasyonInput(BirthInput):
    olaylar: List[Olay] = Field(default_factory=list)
    pencere_dk: int = Field(120, ge=15, le=360)
    adim_dk: int = Field(2, ge=1, le=10)


class IliskiInput(BaseModel):
    """Sinastri ve kompozit için iki doğum verisi."""
    rol: str = Field("yonetici", description="yonetici | misafir")
    mod: Literal["sinastri", "kompozit"] = "sinastri"
    a: BirthInput
    b: BirthInput


class SohbetMesaji(BaseModel):
    rol: str = Field(..., description="'danisan' | 'danisman'")
    metin: str


class SohbetInput(BaseModel):
    soru: str = Field(..., min_length=1, max_length=2000)
    analiz: Dict[str, Any] = Field(default_factory=dict,
                                   description="Tam analiz JSON'u (yönetici)")
    oturum: Optional[str] = Field(None, description="Misafir oturum kimliği")
    gosterilen: Optional[str] = Field(None, max_length=6000,
                                      description="Ekranda zaten okunanlar")
    mod: str = Field("Kişisel", description="Kişisel | Sinastri | Kompozit")
    gecmis: List[SohbetMesaji] = Field(default_factory=list)
    model: Optional[str] = Field(None, description="Danışman modeli; boşsa AI_MODEL")


class BolumInput(BaseModel):
    """Tek bir bölüm için odaklı AI analizi."""
    oturum: Optional[str] = None
    bolum: str = Field(..., description="hukum | halka | catal | kutleler | kenarlar | "
                                        "kabzbast | deneme | kadim | hd | hamveri | "
                                        "sinastri | alanbukmesi | kompozit | kisi_a | kisi_b")
    analiz: Dict[str, Any] = Field(default_factory=dict)
    mod: str = "Kişisel"
    model: Optional[str] = None


class KisiselInput(BaseModel):
    """Hüküm ve Çatal satırlarının haritaya özgü yeniden yazımı."""
    oturum: Optional[str] = None
    analiz: Dict[str, Any] = Field(default_factory=dict)
    mod: str = "Kişisel"
    model: Optional[str] = None


class DinamikInput(BirthInput):
    """Yürüyen Berzah taraması."""
    yil: int = Field(24, ge=4, le=60, description="Tarama ufku (yıl)")


class SentezInput(BaseModel):
    """Bütün katmanları tek okumada birleştiren sentez."""
    oturum: Optional[str] = None
    analiz: Dict[str, Any] = Field(default_factory=dict)
    mod: str = "Kişisel"
    rol: str = "yonetici"
    model: Optional[str] = None


class FormulInput(BaseModel):
    """Seçilen katmanlar arasında bağ kurma."""
    oturum: Optional[str] = None
    analiz: Dict[str, Any] = Field(default_factory=dict)
    katmanlar: List[str] = Field(..., min_length=2, max_length=6)
    mod: str = "Kişisel"
    rol: str = "yonetici"
    model: Optional[str] = None


class SehirInput(BaseModel):
    """Bir yer için okuma ya da soru."""
    oturum: Optional[str] = None
    analiz: Dict[str, Any] = Field(default_factory=dict)
    ad: str = Field("", max_length=80)
    enlem: float = Field(..., ge=-90, le=90)
    boylam: float = Field(..., ge=-180, le=180)
    soru: str = Field("", max_length=2000)
    gecmis: List[Dict[str, Any]] = Field(default_factory=list, max_length=8)
    rol: str = "yonetici"
    model: Optional[str] = None


class ManeviInput(BaseModel):
    """Spiritüel çalışma katmanı."""
    oturum: Optional[str] = None
    analiz: Dict[str, Any] = Field(default_factory=dict)
    soru: str = Field("", max_length=2000)
    gecmis: List[Dict[str, Any]] = Field(default_factory=list, max_length=8)
    model: Optional[str] = None


class SoruInput(BaseModel):
    """Katalogdan seçilmiş sorulara cevap."""
    oturum: Optional[str] = None
    analiz: Dict[str, Any] = Field(default_factory=dict)
    kodlar: List[str] = Field(default_factory=list, max_length=6)
    ek_soru: str = Field("", max_length=1500)
    mod: str = "Kişisel"
    rol: str = "yonetici"
    model: Optional[str] = None


class RaporInput(BaseModel):
    """Tam rapor — bütün katmanlardan uzun okuma."""
    oturum: Optional[str] = None
    analiz: Dict[str, Any] = Field(default_factory=dict)
    mod: str = "Kişisel"
    model: Optional[str] = None
    bicim: Literal["pdf", "metin"] = "pdf"
    sira: int = Field(0, ge=0, le=20)
    tur: Literal["danisan", "anlatim"] = "danisan"
    onceki: str = Field("", max_length=4000)


class LunasyonInput(BaseModel):
    """Lunasyon takvimi ve haftalık okuma."""
    oturum: Optional[str] = None
    analiz: Dict[str, Any] = Field(default_factory=dict)
    dogum: Dict[str, Any] = Field(default_factory=dict)
    ay_sayisi: int = Field(12, ge=1, le=24)
    olay_sirasi: Optional[int] = Field(None, ge=0, le=60)
    soru: str = Field("", max_length=1500)
    gecmis: List[Dict[str, Any]] = Field(default_factory=list, max_length=10)
    mod: str = "Kişisel"
    rol: str = "yonetici"
    model: Optional[str] = None
