#!/usr/bin/env bash
set -o errexit
set -o pipefail

echo "==> [1/5] Python paketleri kuruluyor ($(python --version))"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "==> [2/5] Sözdizimi doğrulanıyor"
# Hedef sürüm Python 3.11 (.python-version). f-string içinde iç içe AYNI tırnak
# (PEP 701) 3.12+ ta gecerli, 3.11 de SyntaxError verir. Bu adim onu yakalar.
python -m py_compile app/*.py smoke_test.py

echo "==> [3/5] Tanimsiz ad taramasi"
python adtarama.py

echo "==> Kenar durum ve performans"
python kenar_test.py

echo "==> [4/5] Duman testi"
python smoke_test.py

echo "==> [5/5] Derin doğrulama (96 kontrol)"
python verify.py

echo "==> BUILD OK — ZÎC v3.2"
