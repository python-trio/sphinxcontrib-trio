# So autodoc can find our test code
import sys
import os
import os.path
sys.path.insert(0, os.path.abspath("."))

extensions = [
    # Don't include sphinx.ext.autodoc, to test for gh-9
    "sphinxcontrib_trio",
    # Needed to test for gh-8
    "sphinx.ext.autosummary",
]

autosummary_generate = True

source_suffix = ".rst"
master_doc = "test"

html_theme = "alabaster"
