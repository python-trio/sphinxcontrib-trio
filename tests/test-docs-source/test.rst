=====================================
 sphinxcontrib-trio end-to-end tests
=====================================

Each ``note`` in this file is a test case. The ``test_end_to_end``
function in ``test_sphinxcontrib_trio.py`` loops through the rendered
output of each ``note``, and for eacn one it finds all the "none"
code-blocks, and it makes sure that the contents of that code-block
appears in the html source for the rest of the note.

It also runs all ``warning``\s as tests in the same way, but for these
it checks that they fail. This acts as a check that the test harness
is actually working, and can be used for negative tests.

Currently there is no normalization applied to the HTML. We can add
it later if it turns out to be a problem...

Basic smoke tests
=================

.. note::

   .. function:: foo(bar)
      :async:

   .. code-block:: none

      <em class="property">await </em><code class="descname">foo</code>


.. warning::

   .. function:: foo(bar)

   .. code-block:: none

      <em class="property">await </em><code class="descname">foo</code>


Check all the formatting logic
==============================

.. note::

   .. method:: foo(bar)
      :abstractmethod:
      :staticmethod:
      :async:

   .. code-block:: none

      <em class="property">abstractmethod staticmethod await </em><code class="descname">foo</code>


.. note::

   .. method:: foo(bar)
      :classmethod:

   .. code-block:: none

      <em class="property">classmethod </em><code class="descname">foo</code>


.. note::

   .. function:: foo(bar)
      :with:

   .. code-block:: none

      <em class="property">with </em><code class="descname">foo</code>


.. note::

   .. method:: foo(bar)
      :with: baz

   .. code-block:: none

      <em class="property">with </em><code class="descname">foo</code><span class="sig-paren">(</span><em>bar</em><span class="sig-paren">)</span><em class="property">&nbsp;as baz</em>

.. note::

   .. method:: foo(bar)
      :async-with:

   .. code-block:: none

      <em class="property">async with </em><code class="descname">foo</code>


.. note::

   .. method:: foo(bar)
      :async-with: baz

   .. code-block:: none

      <em class="property">async with </em><code class="descname">foo</code><span class="sig-paren">(</span><em>bar</em><span class="sig-paren">)</span><em class="property">&nbsp;as baz</em>


This one checks that there's no parentheses:

.. note::

   .. decorator:: foo

   .. code-block:: none

      <code class="descclassname">@</code><code class="descname">foo</code></dt>


But if you do have arguments, they're displayed

.. note::

   .. decorator:: foo(bar)

   .. code-block:: none

      <code class="descclassname">@</code><code class="descname">foo</code><span class="sig-paren">(</span><em>bar</em>


.. note::

   .. method:: foo(bar)
      :for:

   .. code-block:: none

      <em class="property">for ... in </em><code class="descname">foo</code>


.. note::

   .. method:: foo(bar)
      :for: baz

   .. code-block:: none

      <em class="property">for baz in </em><code class="descname">foo</code>

.. note::

   .. method:: foo(bar)
      :async-for:

   .. code-block:: none

      <em class="property">async for ... in </em><code class="descname">foo</code>


.. note::

   .. method:: foo(bar)
      :async-for: baz

   .. code-block:: none

      <em class="property">async for baz in </em><code class="descname">foo</code>


Backwards compatibility directives
==================================

.. note::

   .. decorator:: foo

   .. code-block:: none

      <code class="descclassname">@</code><code class="descname">foo</code>

.. note::

   .. decoratormethod:: foo

   .. code-block:: none

      <code class="descclassname">@</code><code class="descname">foo</code>

.. note::

   .. classmethod:: foo(bar)

   .. code-block:: none

      <em class="property">classmethod </em><code class="descname">foo</code>

.. note::

   .. staticmethod:: foo(bar)

   .. code-block:: none

      <em class="property">staticmethod </em><code class="descname">foo</code>


Autodoc
=======

.. module:: autodoc_examples

Autodoc smoke tests:

.. note::

   .. autofunction:: basic

   .. code-block:: none

      <code class="descclassname">autodoc_examples.</code><code class="descname">basic</code>

.. warning::

   .. autofunction:: basic

   .. code-block:: none

      </em><code class="descname">basic</code>

.. note::

   .. autofunction:: asyncfn

   .. code-block:: none

      <em class="property">await </em><code class="descclassname">autodoc_examples.</code><code class="descname">asyncfn</code>

We don't bother testing every bizarro combination here, because we
have unit tests for that.

But classes in particular are tricky, because (a) you have to look up
members the right way or ``classmethod`` and ``staticmethod`` hide
from you, and (b) you have to integrate correctly with autodoc for
``:members:`` to automatically use your custom directives.

.. note::

   .. autoclass:: ExampleClass
      :members:
      :undoc-members:

   .. code-block:: none

      <em class="property">abstractmethod </em><code class="descname">abstractmethod_</code>

   .. code-block:: none

      <em class="property">abstractmethod classmethod </em><code class="descname">classabstract</code>

   .. code-block:: none

      <em class="property">classmethod </em><code class="descname">classmethod_</code>

   .. code-block:: none

      <em class="property">await </em><code class="descname">asyncmethod</code>


Autodoc + order by source:

.. autoclass:: ExampleClassForOrder
   :members:
   :undoc-members:


Autodoc + explicit options:

.. note::

   .. autofunction:: basic
      :for:
      :async:

   .. code-block:: none

      <em class="property">for ... in await </em><code class="descclassname">autodoc_examples.</code><code class="descname">basic</code>

Overriding sniffed ``:for:`` with ``:for: arg``:

.. note::

   .. autofunction:: gen

   .. code-block:: none

      <em class="property">for ... in </em><code class="descclassname">autodoc_examples.</code><code class="descname">gen</code>

.. note::

   .. autofunction:: gen
      :for: arg

   .. code-block:: none

      <em class="property">for arg in </em><code class="descclassname">autodoc_examples.</code><code class="descname">gen</code>

Testing ``:no-auto-options:``:

.. note::

   .. autofunction:: gen
      :no-auto-options:

   .. code-block:: none

      <dt>
      <code class="descclassname">autodoc_examples.</code><code class="descname">gen</code>

.. warning::

   .. autofunction:: gen
      :no-auto-options:

   .. code-block:: none

      for

.. note::

   .. autofunction:: gen
      :no-auto-options:
      :for:

   .. code-block:: none

      <em class="property">for ... in </em><code class="descclassname">autodoc_examples.</code><code class="descname">gen</code>

.. note::

   .. autofunction:: gen
      :no-auto-options:
      :async:

   .. code-block:: none

      <em class="property">await </em><code class="descclassname">autodoc_examples.</code><code class="descname">gen</code>


Autodoc + Autosummary
---------------------

See: https://github.com/python-trio/sphinxcontrib-trio/issues/8

Previously the presence of this code in the file (when combined with
``autosummary_generate = True`` in ``conf.py``) would cause all the
*other* ``autofunction`` tests to fail...

.. autosummary::
   :toctree:

   autosummary_me
