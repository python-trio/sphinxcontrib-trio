.. note that this README gets 'include'ed into the main documentation

sphinxcontrib-trio
==================

This sphinx extension helps you document Python code that uses
async/await, or abstract methods, or context managers, or generators,
or ... you get the idea. It works by making sphinx's regular
directives for documenting Python functions and methods smarter and
more powerful. The name is because it was originally written for the
`Trio <https://trio.readthedocs.io>`__ project, and I'm not very
creative. But don't be put off – there's nothing Trio- or
async-specific about this extension; any Python project can
benefit. (Though projects using async/await probably benefit the most,
since sphinx's built-in tools are especially inadequate in this case.)


Vital statistics
----------------

**Requirements:** This extension currently assumes you're using Python
3.5+ to build your docs. This could be relaxed if anyone wants to send
a patch.

**Documentation:** https://sphinxcontrib-trio.readthedocs.io

**Bug tracker and source code:**
https://github.com/python-trio/sphinxcontrib-trio

**License:** MIT or Apache 2, your choice.

**Usage:** ``pip install -U sphinxcontrib-trio`` in the same
environment where you installed sphinx, and then add
``"sphinxcontrib_trio"`` to the list of ``extensions`` in your
project's ``conf.py``. (Note that it's ``sphinxcontrib_trio`` with an
underscore, NOT a dot. This is because I don't understand namespace
packages, and I fear things that I don't understand.)

**Code of conduct:** Contributors are requested to follow our `code of
conduct
<https://github.com/python-trio/sphinxcontrib-trio/blob/master/CODE_OF_CONDUCT.md>`__
in all project spaces.
