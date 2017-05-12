from pathlib import Path
from setuptools import setup

from sphinxcontrib_trio import __version__

setup(
    name="sphinxcontrib-trio",
    version=__version__,
    description=
      "Make Sphinx better at documenting Python functions and methods",
    # Just in case the cwd is not the root of the source tree, or python is
    # not set to use utf-8 by default:
    long_description=Path(__file__).with_name("README.rst").read_text('utf-8'),
    author="Nathaniel J. Smith",
    author_email="njs@pobox.com",
    license="MIT -or- Apache License 2.0",
    py_modules="sphinxcontrib_trio",
    url="https://github.com/python-trio/sphinxcontrib-trio",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Framework :: Sphinx :: Extension",
        "Topic :: Documentation :: Sphinx",
        "Topic :: Software Development :: Documentation",
    ])
