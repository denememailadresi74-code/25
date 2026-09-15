#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TANIMSIZ AD TARAYICI

Python derlemesi NameError'ı YAKALAYAMAZ: ad çözümlemesi çalışma anında
yapılır. v4.5'te promptlar yeniden yapılandırılırken `_girdi_temizle` işlevi
yanlışlıkla silindi; py_compile temiz geçti, 96 doğrulama geçti, ama SOHBET
her istekte 500 verdi ve iki sürüm boyunca fark edilmedi.

Bu tarayıcı kapsam zincirini izler: iç içe fonksiyonlar dış fonksiyonun
yerellerini görebilir, o yüzden yalnız HİÇBİR kapsamda bulunmayan adlar
bildirilir.
"""
import ast
import builtins
import glob
import importlib
import sys

sys.path.insert(0, ".")


def yereller(d: ast.AST) -> set:
    """Bir fonksiyon gövdesinde bağlanan adlar (iç fonksiyonlara inmeden)."""
    ad = set()
    if isinstance(d, (ast.FunctionDef, ast.AsyncFunctionDef)):
        a = d.args
        ad |= {x.arg for x in a.args} | {x.arg for x in a.kwonlyargs}
        ad |= {x.arg for x in getattr(a, "posonlyargs", [])}
        if a.vararg:
            ad.add(a.vararg.arg)
        if a.kwarg:
            ad.add(a.kwarg.arg)

    def gez(n, kok=False):
        for c in ast.iter_child_nodes(n):
            if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                ad.add(c.name)
                continue                      # iç kapsama inme
            if isinstance(c, ast.Lambda):
                continue
            if isinstance(c, ast.Assign):
                for t in c.targets:
                    ad.update(x.id for x in ast.walk(t) if isinstance(x, ast.Name))
            elif isinstance(c, (ast.AnnAssign, ast.AugAssign)) and isinstance(c.target, ast.Name):
                ad.add(c.target.id)
            elif isinstance(c, (ast.For, ast.AsyncFor)):
                ad.update(x.id for x in ast.walk(c.target) if isinstance(x, ast.Name))
            elif isinstance(c, ast.ExceptHandler) and c.name:
                ad.add(c.name)
            elif isinstance(c, (ast.Import, ast.ImportFrom)):
                ad.update((x.asname or x.name).split(".")[0] for x in c.names)
            elif isinstance(c, (ast.Global, ast.Nonlocal)):
                ad.update(c.names)
            elif isinstance(c, ast.NamedExpr) and isinstance(c.target, ast.Name):
                ad.add(c.target.id)
            for w in ast.walk(c):
                if isinstance(w, ast.withitem) and w.optional_vars is not None:
                    ad.update(x.id for x in ast.walk(w.optional_vars)
                              if isinstance(x, ast.Name))
                if isinstance(w, ast.comprehension):
                    ad.update(x.id for x in ast.walk(w.target)
                              if isinstance(x, ast.Name))
            gez(c)
    gez(d, True)
    return ad


def kendi_govdesi(d):
    """Fonksiyonun KENDİ gövdesindeki düğümler — iç fonksiyon ve lambda
    gövdelerine inmez. Onlar kendi kapsamlarıyla ayrıca denetlenir."""
    yigin = list(ast.iter_child_nodes(d))
    while yigin:
        n = yigin.pop()
        yield n
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(n, ast.Lambda):
            continue
        yigin.extend(ast.iter_child_nodes(n))


def denetle(dugum, kapsam: set, rapor: list, yol: str):
    for c in ast.iter_child_nodes(dugum):
        if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef)):
            ic = kapsam | yereller(c)
            # Lambda değişkenleri de bu kapsamda sayılır.
            for n in kendi_govdesi(c):
                if isinstance(n, ast.Lambda):
                    ic |= {a.arg for a in n.args.args}
                    ic |= {a.arg for a in n.args.kwonlyargs}
            # YALNIZ bu fonksiyonun kendi gövdesindeki adlar; iç içe
            # fonksiyonlar özyinelemeli çağrıda kendi kapsamlarıyla bakılır.
            for n in kendi_govdesi(c):
                if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) \
                        and n.id not in ic:
                    rapor.append(f"{yol}{c.name}() satır {n.lineno} → {n.id}")
            denetle(c, ic, rapor, f"{yol}{c.name}.")
        elif isinstance(c, ast.ClassDef):
            denetle(c, kapsam | {c.name}, rapor, f"{yol}{c.name}.")


toplam = 0
for dosya in sorted(glob.glob("app/*.py")):
    ad = "app." + dosya.split("/")[-1][:-3]
    if ad.endswith("__init__"):
        continue
    try:
        mod = importlib.import_module(ad)
    except Exception as ex:
        print(f"  ✗ {ad}: import edilemedi — {type(ex).__name__}: {ex}")
        toplam += 1
        continue
    kapsam = set(dir(mod)) | set(dir(builtins))
    rapor: list = []
    denetle(ast.parse(open(dosya, encoding="utf-8").read()), kapsam, rapor, "")
    # aynı ad birden çok satırda geçebilir; benzersizleştir
    benzersiz = sorted(set(rapor))
    if benzersiz:
        toplam += len(benzersiz)
        print(f"  ✗ {ad}:")
        for x in benzersiz:
            print(f"      {x}")

print(f"\n  TANIMSIZ AD: {toplam}")
sys.exit(1 if toplam else 0)
