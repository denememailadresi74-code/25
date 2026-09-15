#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ZÎC kalıcı ölçüm deposu.

İddia Defteri, AYÂR ve SİCİL aylar boyunca birikmeden anlamlı değildir. Kod
klasörüne yazılan JSON dosyaları tek süreçte çalışsa bile Render'ın geçici dosya
sisteminde dağıtım/uyku sırasında silinebilir; ayrıca ``threading.RLock`` farklı
worker süreçlerini korumaz. Bu nedenle v13.4'te kimliksiz ölçüm kayıtları standart
kütüphanedeki SQLite'a taşınır.

Veri yolu ``ZIC_VERI_DIZINI`` ile seçilir. Ortam değişkeni verilmezse eski
davranışla ``app/`` kullanılır. SQLite işlem kilidi süreçler arası güvenliği
sağlar; kişi adı, doğum tarihi, koordinat veya üretilmiş tam danışman metni bu
depoya yazılmaz.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List


def veri_dizini() -> Path:
    ham = os.environ.get("ZIC_VERI_DIZINI", "").strip()
    yol = Path(ham).expanduser() if ham else Path(__file__).resolve().parent
    yol.mkdir(parents=True, exist_ok=True)
    return yol


def db_yolu() -> Path:
    return veri_dizini() / "defter.db"


def imza_yolu() -> Path:
    return veri_dizini() / "defter.imza.json"


def referans_yolu(ad: str) -> Path:
    if ad not in ("mizan", "sahit"):
        raise ValueError(ad)
    return veri_dizini() / f"{ad}_quantiles_gercek.json"


@contextmanager
def baglan() -> Iterator[sqlite3.Connection]:
    con = sqlite3.connect(str(db_yolu()), timeout=30.0, isolation_level=None)
    try:
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA synchronous=NORMAL")
        con.execute("PRAGMA busy_timeout=30000")
        _sema(con)
        yield con
    finally:
        con.close()


def _sema(con: sqlite3.Connection) -> None:
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS iddia (
            id TEXT PRIMARY KEY,
            ts REAL NOT NULL,
            oturum TEXT NOT NULL,
            bolum TEXT NOT NULL,
            mercek TEXT NOT NULL,
            davranis TEXT NOT NULL,
            alan TEXT NOT NULL,
            yon TEXT NOT NULL,
            zaman TEXT NOT NULL,
            olasilik REAL NOT NULL,
            sonuc TEXT,
            isaret_ts REAL,
            referans_yil INTEGER,
            iddia_metin TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_iddia_bolum ON iddia(bolum);
        CREATE INDEX IF NOT EXISTS idx_iddia_mercek ON iddia(mercek);
        CREATE TABLE IF NOT EXISTS ayar (
            seq INTEGER PRIMARY KEY AUTOINCREMENT,
            ts REAL NOT NULL,
            veri TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sicil (
            seq INTEGER PRIMARY KEY AUTOINCREMENT,
            ts REAL NOT NULL,
            veri TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS meta (
            anahtar TEXT PRIMARY KEY,
            deger TEXT NOT NULL
        );
        """
    )
    # SQLite CREATE TABLE IF NOT EXISTS eski veritabanına yeni sütun eklemez.
    # v13.5 geçmiş Brier kayıtlarını silmeden referans yılını taşımak zorunda;
    # bu yüzden göç yalnız eksik sütunları ekler ve eski satırlar NULL kalır.
    sutunlar = {str(x[1]) for x in con.execute("PRAGMA table_info(iddia)").fetchall()}
    if "referans_yil" not in sutunlar:
        con.execute("ALTER TABLE iddia ADD COLUMN referans_yil INTEGER")
    if "iddia_metin" not in sutunlar:
        con.execute("ALTER TABLE iddia ADD COLUMN iddia_metin TEXT")


def _imza_guncelle(dolu: bool = True) -> None:
    if not dolu:
        return
    yol = imza_yolu()
    try:
        mevcut: Dict[str, Any] = {}
        if yol.exists():
            mevcut = json.loads(yol.read_text(encoding="utf-8"))
        mevcut.update({"daha_once_doluydu": True, "son_yazim": time.time()})
        gecici = yol.with_suffix(".tmp")
        gecici.write_text(json.dumps(mevcut, ensure_ascii=False), encoding="utf-8")
        gecici.replace(yol)
    except Exception:
        pass


def sifirlanmis_olabilir() -> bool:
    """İmza yaşadığı hâlde ölçüm tabloları boşsa kayıp ihtimalini görünür kılar."""
    try:
        imza = json.loads(imza_yolu().read_text(encoding="utf-8"))
        once = bool(imza.get("daha_once_doluydu"))
    except Exception:
        return False
    if not once:
        return False
    with baglan() as con:
        toplam = sum(int(con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]) for t in ("iddia", "ayar", "sicil"))
    return toplam == 0


def iddia_ekle(kayitlar: Iterable[Dict[str, Any]]) -> None:
    satirlar = list(kayitlar)
    if not satirlar:
        return
    with baglan() as con:
        con.execute("BEGIN IMMEDIATE")
        try:
            con.executemany(
                """INSERT OR REPLACE INTO iddia
                (id,ts,oturum,bolum,mercek,davranis,alan,yon,zaman,olasilik,sonuc,isaret_ts,referans_yil,iddia_metin)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                [(
                    x["id"], float(x["ts"]), str(x.get("oturum") or "anon"), str(x.get("bolum") or ""),
                    str(x.get("mercek") or x.get("bolum") or ""), str(x.get("davranis") or "genel"),
                    str(x.get("alan") or "genel"), str(x.get("yon") or "koşullu"), str(x.get("zaman") or "kalıcı"),
                    float(x.get("olasilik", .75)), x.get("sonuc"), x.get("isaret_ts"),
                    int(x["referans_yil"]) if x.get("referans_yil") not in (None, "") else None,
                    str(x.get("iddia_metin") or "")[:500] or None,
                ) for x in satirlar]
            )
            # Defter sınırsız büyümesin; en yeni 5000 yapılandırılmış iddia yeterli.
            con.execute("DELETE FROM iddia WHERE rowid NOT IN (SELECT rowid FROM iddia ORDER BY ts DESC, rowid DESC LIMIT 5000)")
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            raise
    _imza_guncelle(True)


def iddia_liste() -> List[Dict[str, Any]]:
    with baglan() as con:
        con.row_factory = sqlite3.Row
        sat = con.execute("SELECT * FROM iddia ORDER BY ts, rowid").fetchall()
    return [dict(x) for x in sat]


def iddia_isaretle(kimlik: str, sonuc: str | None) -> Dict[str, Any] | None:
    ts = time.time() if sonuc is not None else None
    with baglan() as con:
        con.execute("BEGIN IMMEDIATE")
        try:
            cur = con.execute("UPDATE iddia SET sonuc=?, isaret_ts=? WHERE id=?", (sonuc, ts, kimlik))
            if cur.rowcount == 0:
                con.execute("ROLLBACK")
                return None
            con.row_factory = sqlite3.Row
            row = con.execute("SELECT * FROM iddia WHERE id=?", (kimlik,)).fetchone()
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            raise
    _imza_guncelle(True)
    return dict(row) if row else None


def json_kayit_ekle(tablo: str, kayit: Dict[str, Any], azami: int) -> None:
    if tablo not in ("ayar", "sicil"):
        raise ValueError(tablo)
    with baglan() as con:
        con.execute("BEGIN IMMEDIATE")
        try:
            con.execute(f"INSERT INTO {tablo}(ts,veri) VALUES (?,?)",
                        (float(kayit.get("ts") or time.time()), json.dumps(kayit, ensure_ascii=False, separators=(",", ":"))))
            con.execute(f"DELETE FROM {tablo} WHERE seq NOT IN (SELECT seq FROM {tablo} ORDER BY seq DESC LIMIT ?)", (int(azami),))
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            raise
    _imza_guncelle(True)


def json_kayit_liste(tablo: str, azami: int | None = None) -> List[Dict[str, Any]]:
    if tablo not in ("ayar", "sicil"):
        raise ValueError(tablo)
    sql = f"SELECT veri FROM {tablo} ORDER BY seq"
    param: tuple[Any, ...] = ()
    if azami:
        sql = f"SELECT veri FROM (SELECT seq,veri FROM {tablo} ORDER BY seq DESC LIMIT ?) ORDER BY seq"
        param = (int(azami),)
    with baglan() as con:
        rows = con.execute(sql, param).fetchall()
    out: List[Dict[str, Any]] = []
    for (ham,) in rows:
        try:
            v = json.loads(ham)
            if isinstance(v, dict):
                out.append(v)
        except Exception:
            continue
    return out


def tablo_sil(tablo: str) -> None:
    if tablo not in ("iddia", "ayar", "sicil"):
        raise ValueError(tablo)
    with baglan() as con:
        con.execute("BEGIN IMMEDIATE")
        try:
            con.execute(f"DELETE FROM {tablo}")
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            raise


def meta_yaz(anahtar: str, deger: Any) -> None:
    with baglan() as con:
        con.execute("INSERT INTO meta(anahtar,deger) VALUES (?,?) ON CONFLICT(anahtar) DO UPDATE SET deger=excluded.deger",
                    (anahtar, json.dumps(deger, ensure_ascii=False)))


def meta_oku(anahtar: str, default: Any = None) -> Any:
    with baglan() as con:
        row = con.execute("SELECT deger FROM meta WHERE anahtar=?", (anahtar,)).fetchone()
    if not row:
        return default
    try:
        return json.loads(row[0])
    except Exception:
        return default


def disaria_aktar() -> Dict[str, Any]:
    return {
        "surum": 1,
        "uretim_ts": time.time(),
        "iddialar": iddia_liste(),
        "ayar": json_kayit_liste("ayar"),
        "sicil": json_kayit_liste("sicil"),
        "meta": _meta_tumu(),
    }


def _meta_tumu() -> Dict[str, Any]:
    with baglan() as con:
        rows = con.execute("SELECT anahtar,deger FROM meta").fetchall()
    out: Dict[str, Any] = {}
    for k, v in rows:
        try:
            out[k] = json.loads(v)
        except Exception:
            out[k] = v
    return out


def _json_imza(kayit: Dict[str, Any]) -> str:
    """Birleştirme yedeğinin aynı anonim ölçümü ikinci kez çoğaltmasını önler."""
    return json.dumps(kayit, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sayilar() -> Dict[str, int]:
    with baglan() as con:
        return {t: int(con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
                for t in ("iddia", "ayar", "sicil")}


def defter_ozeti() -> Dict[str, Any]:
    say = sayilar()
    # Yedek hatırlatması yalnız yapılandırılmış İddia Defteri büyüdüğünde görünür.
    # AYÂR/SİCİL otomatik ölçümleri bu sayacı şişirirse danışman daha ilk gününde
    # sürekli yedek uyarısı görür; saha işi açısından anlamlı eşik insan eliyle
    # değerlendirilebilen iddia kaydıdır.
    n = int(say.get("iddia", 0))
    return {
        "sayilar": say,
        "toplam": sum(say.values()),
        "yedek_hatirlat": bool(n > 0 and n % 25 == 0),
        "sonraki_yedek": 25 if n == 0 else ((n // 25) + 1) * 25,
        "sifirlanmis_olabilir": sifirlanmis_olabilir(),
    }


def iceri_aktar(veri: Dict[str, Any], birlestir: bool = False) -> Dict[str, int]:
    if not isinstance(veri, dict):
        raise ValueError("Defter JSON nesnesi olmalı")
    iddialar = [x for x in veri.get("iddialar", []) if isinstance(x, dict)]
    ayar = [x for x in veri.get("ayar", []) if isinstance(x, dict)]
    sicil = [x for x in veri.get("sicil", []) if isinstance(x, dict)]
    if not birlestir:
        for t in ("iddia", "ayar", "sicil"):
            tablo_sil(t)
        ayar_yeni, sicil_yeni = ayar, sicil
    else:
        # v13.4'te iddia kimliği PRIMARY KEY olduğu için iki yedek birleşimi
        # iddialarda zaten güvenliydi; AYÂR/SİCİL autoincrement olduğu için aynı
        # yedek her içe aktarmada çoğalıyordu. İçeri aktarmada kanonik anonim
        # kayıt imzası kullanmak şemayı büyütmeden bu turu idempotent yapar.
        ayar_var = {_json_imza(x) for x in json_kayit_liste("ayar")}
        sicil_var = {_json_imza(x) for x in json_kayit_liste("sicil")}
        ayar_yeni = [x for x in ayar if _json_imza(x) not in ayar_var]
        sicil_yeni = [x for x in sicil if _json_imza(x) not in sicil_var]
    once = sayilar()
    iddia_ekle(iddialar)
    for x in ayar_yeni:
        json_kayit_ekle("ayar", x, 500)
    for x in sicil_yeni:
        json_kayit_ekle("sicil", x, 5000)
    for k, v in (veri.get("meta") or {}).items():
        meta_yaz(str(k), v)
    if iddialar or ayar_yeni or sicil_yeni:
        _imza_guncelle(True)
    sonra = sayilar()
    return {t: max(0, int(sonra[t]) - int(once[t])) for t in ("iddia", "ayar", "sicil")}
