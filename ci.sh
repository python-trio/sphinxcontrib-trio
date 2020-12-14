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
# https://serverfault.com/questions/7503/how-to-determine-if-a-bash-variable-is-empty
if [ -n "${OLD_SPHINX}" ]; then
    pip install "sphinx == ${OLD_SPHINX}.*"
fi
mkdir empty
pushd empty
INSTALLDIR=$(python -c "import os, sphinxcontrib_trio; print(os.path.dirname(sphinxcontrib_trio.__file__))")
pytest ../tests --cov="$INSTALLDIR" --cov=../tests --cov-config="../.coveragerc"
mv .coverage firstrun

# Run tests again with minimal dependencies installed
pip uninstall -y async_generator contextlib2
pytest ../tests --cov="$INSTALLDIR" --cov=../tests --cov-config="../.coveragerc"

coverage combine -a firstrun

pip install codecov
codecov
