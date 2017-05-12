#!/bin/bash

set -exu -o pipefail

pip install -U pip setuptools wheel

python setup.py sdist --formats=zip
pip install dist/*.zip

cd docs
# -n (nit-picky): warn on missing references
# -W: turn warnings into errors
sphinx-build -nW  -b html source build
