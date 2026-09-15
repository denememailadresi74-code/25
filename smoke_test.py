#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Duman testi — servis fonksiyonlarını API katmanı olmadan uçtan uca çalıştırır."""
import json
import sys
import time

from app.astro import build_chart, jd_to_iso
from app.engine_mass import full_v2
from app.engine_kabzbast import run_kabzbast
from app.modules_deneme import run_all_deneme
from app.modules_kadim import isim_tecellisi, kadim_lab, huviyet_muhru
from app.module_hd import human_design


def main():
    t0 = time.time()
    ch = build_chart(1990, 6, 21, 14, 30, 40.80, 29.43,
                     tz_offset=3.0, label="Duman Testi")
    print(f"[1] Harita OK  {jd_to_iso(ch.jd_ut)}  ASC {ch.asc:.2f}  MC {ch.mc:.2f}")

    v2 = full_v2(ch)
    assert v2["KD"] and v2["oz_modul_spektrumu"], "v2 eksik"
    b = v2.get("berzah")
    print(f"[2] BERZAH v2 OK  KD={v2['KD']['konum']}  "
          f"B={b['konum'] if b else '—'} ({b['tur'] if b else ''})")

    kb = run_kabzbast(ch, days=200, sr_year=2026)
    assert kb["m68_einstein_rosen"] is not None
    print(f"[3] Kabz/Bast v1 OK  eksen={kb['m66_67_kabz_bast']['eksen']['kutup'][:4]}  "
          f"köprü={len(kb['m68_einstein_rosen'])}  "
          f"geçit={len(kb['m74_gecit']['pencereler'])}  "
          f"SR köprü yılı={kb['solar_return']['kopru_yili']}")

    den = run_all_deneme(ch, months=12)
    assert len(den) == 16, f"deneme modül sayısı {len(den)} != 16"
    print(f"[4] 16 deneme modülü OK  "
          f"KRN={den['krn']['KRN']['konum']}  "
          f"R={den['vahdet']['R_indeksi']}  "
          f"λ2={den['asabiyye']['asabiyye_lambda2']}  "
          f"Süveyda={den['suveyda']['suveyda']['konum']}")
    print(f"    Sahib-Kırân pencereleri: {len(den['sahib_kiran']['pencereler'])}  "
          f"İcâbet={den['nokta_i_icabet']['icabet']['konum']}  "
          f"Noksan={den['nokta_i_noksan']['noksan']['konum']}")

    kad = kadim_lab(ch)
    hv = huviyet_muhru(ch, den, v2)
    it = isim_tecellisi(ch, "İsa", "Fatma")
    print(f"[5] Kadim OK  Hyleg={kad['hyleg']['aday']}  "
          f"Kırân-ı Ekber={kad['kiran_i_ekber'].get('siradaki_kavusum', '?')}/"
          f"{kad['kiran_i_ekber']['siradaki_kavusum_burcu']}  "
          f"Hüviyet: B={hv['butunluk_endeksi']} G={hv['gerilim_endeksi']} → {hv['muhur_kimligi'][:9]}")
    print(f"    İsim Tecellîsi: ebced={it['ebced']['ebced']} → {it['isim_derecesi']['konum']}")

    hd = human_design(ch)
    print(f"[6] Human Design OK  {hd['tip']['tr']} · {hd['otorite']['tr'][:16]} · "
          f"profil {hd['profil']} · {hd['tanim']} · kanal={len(hd['kanallar'])}")

    full = {"berzah_v2": v2, "kabzbast": kb, "deneme": den,
            "kadim": {"lab": kad, "huviyet": hv, "isim": it}, "hd": hd}
    js = json.dumps(full, ensure_ascii=False)
    print(f"[7] JSON serileştirme OK  ({len(js)/1024:.0f} KB)")
    print(f"\n✓ TÜM SİSTEM AYAKTA — toplam süre {time.time()-t0:.1f} sn")


if __name__ == "__main__":
    sys.exit(main())
