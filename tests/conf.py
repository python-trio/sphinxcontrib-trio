# So autodoc can find our test code
import sys
import os.path
sys.path.insert(0, os.path.abspath("."))

extensions = [
    "sphinx.ext.autodoc",
    "sphinxcontrib_trio",
]

source_suffix = ".rst"
master_doc = "test"

html_theme = "alabaster"
