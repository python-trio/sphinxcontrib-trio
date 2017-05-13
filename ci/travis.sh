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
mkdir empty
pushd empty
INSTALLDIR=$(python -c "import os, sphinxcontrib_trio; print(os.path.dirname(sphinxcontrib_trio.__file__))")
pytest ../tests --cov="$INSTALLDIR" --cov-config="../.coveragerc
pip install codecov
codecov
