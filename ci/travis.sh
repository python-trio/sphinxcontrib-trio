#!/bin/bash

set -exu -o pipefail

pip install -U pip setuptools wheel

python setup.py sdist --formats=zip
pip install dist/*.zip

# Make sure that the docs build without warnings. And this also acts as a
# basic smoke test on the code, since the docs use the code.
pushd docs
# -n (nit-picky): warn on missing references
# -W: turn warnings into errors
sphinx-build -nW  -b html source build
popd

pip install -Ur test-requirements.txt
pytest tests --cov=sphinxcontrib_trio
pip install codecov
codecov
