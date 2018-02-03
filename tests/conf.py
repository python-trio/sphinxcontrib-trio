# So autodoc can find our test code
import sys
import os.path
sys.path.insert(0, os.path.abspath("."))

extensions = [
    "sphinxcontrib_trio",
]

source_suffix = ".rst"
master_doc = "test"

html_theme = "alabaster"
