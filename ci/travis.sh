#!/bin/bash

set -exu -o pipefail

pip install -U pip setuptools wheel

python setup.py sdist --formats=zip
pip install dist/*.zip

# We don't have a test suite, but we can at least make sure that the docs
# build without warnings. And this also acts as a basic smoke test on the
# code, since the docs use the code.
cd docs
# -n (nit-picky): warn on missing references
# -W: turn warnings into errors
sphinx-build -nW  -b html source build
