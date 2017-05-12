.. include:: ../../README.rst


The big idea
------------

Sphinx provides some convenient directives for `documenting Python
code
<http://www.sphinx-doc.org/en/stable/domains.html#the-python-domain>`__:
you can use the ``method::`` directive to document an ordinary method,
the ``classmethod::`` directive to document a classmethod, the
``decoratormethod::`` directive to document a decorator method, and so
on. But what if you have a classmethod that's also a decorator?  And
what if you want to document a project that uses some of Python's many
interesting function types that Sphinx *doesn't* support, like async
functions, abstract methods, generators, ...?

It would be possible to keep adding directive after directive for
every possible type: ``asyncmethod::``, ``abstractmethod::``,
``classmethoddecorator::``, ``abstractasyncstaticmethod::`` – you get
the idea. But this quickly becomes silly. sphinxcontrib-trio takes a
different approach: it enhances the basic ``function::`` and
``method::`` directives to accept options describing the attributes of
each function/method, so you can write ReST code like:

.. code-block:: rst

   .. method:: overachiever(arg1, ...)
      :abstractmethod:
      :async:
      :classmethod:

      This method is perhaps more complicated than it needs to be.

and you'll get rendered output like:

.. method:: overachiever(arg1, ...)
   :abstractmethod:
   :async:
   :classmethod:

   This method is perhaps more complicated than it needs to be.

While I was at it, I also enhanced the ``sphinx.ext.autodoc``
directives ``autofunction::`` and ``automethod::`` with new versions
that know how to automatically detect many of these attributes, so you
could just as easily have written the above as:

.. code-block:: rst

   .. automethod:: overachiever

and it would automatically figure out that this was an abstract async
classmethod by looking at your code.

And finally, I made the legacy ``classmethod::`` directive into an
alias for:

.. code-block:: rst

   .. method::
      :classmethod:

and similarly ``staticmethod``, ``decorator``, and
``decoratormethod``, so dropping this extension into an existing
sphinx project should be 100% backwards-compatible while giving sphinx
new superpowers.

Basically, this is how sphinx ought to work in the first
place. Perhaps in the future it will. But until then, this extension
is pretty handy.


Details on supported options
----------------------------

The following options are supported by the enhanced ``function::`` and
``method::`` directives, and some of them can be automatically
detected if you use ``autofunction::`` / ``automethod::``:

====================  ===============================  ==========================
Option                Renders like                     Autodetectable?
====================  ===============================  ==========================
``:async:``           *await* **fn**\()                yes!
``:decorator:``       @\ **fn**                        no
``:with:``            *with* **fn**\()                 no
``:with: foo``        *with* **fn**\() *as foo*        no
``:async-with:``      *async with* **fn**\()           no
``:async-with: foo``  *async with* **fn**\() *as foo*  no
``:for:``             *for ... in* **fn**\()           yes! (on generators)
``:for: foo``         *for foo in* **fn**\()           yes! (on generators)
``:async-for:``       *async for ... in* **fn**\()     yes! (on async generators)
``:async-for: foo``   *async for foo in* **fn**\()     yes! (on async generators)
====================  ===============================  ==========================

The ``:async-for:`` autodetection code supports both `native async
generators <https://www.python.org/dev/peps/pep-0525/>`__ (in Python
3.6+) and those created by the `async_generator
<https://github.com/njsmith/async_generator>`__ library (in Python
3.5+).

There are also a few options that are specific to ``method::``:

====================  ==========================  =====================
Option                Renders like                Autodetectable?
====================  ==========================  =====================
``:abstractmethod:``  *abstractmethod* **fn**\()  yes!
``:staticmethod:``    *staticmethod* **fn**\()    yes!
``:classmethod:``     *classmethod* **fn**\()     yes!
====================  ==========================  =====================


Examples
--------

A regular async function:

.. code-block:: rst

   .. function:: example_async_fn(...)
      :async:

      This is an example.

Renders as:

.. function:: example_async_fn(...)
   :async:

   This is an example.

A context manager with a hint as to what's returned:

.. code-block:: rst

   .. function:: open(file_name)
      :with: file_handle

      It's good practice to use :func:`open` as a context manager.

Renders as:

.. function:: open(file_name)
   :with: file_handle

   It's good practice to use :func:`open` as a context manager.

The auto versions of the directives also accept explicit options,
which are appended to the automatically detected options. So if
``some_method`` is defined as a ``abstractmethod`` in the source, and
you want to document that it should be used as a decorator, you can
write:

.. code-block:: rst

   .. automethod:: some_method
      :decorator:

and it will render like:

.. method:: some_method
   :abstractmethod:
   :decorator:

   Here's some text automatically extracted from the method's docstring.


Bugs and limitations
--------------------

* Currently there are no tests, because I don't know how to test a
  sphinx extension. If you do, please let me know.

* Python supports defining abstract properties like::

    @abstractmethod
    @property
    def some_property(...):
        ...

  But currently this extension doesn't help you document them. The
  difficulty is that for Sphinx, properties are "attributes", not
  "methods", and we don't currently hook the code for handling
  ``attribute::`` and ``autoattribute::``. Maybe we should?

* When multiple options are combined, then we try to render them in a
  sensible way, but this does assume that you're giving us a sensible
  combination to start with. If you give sphinxcontrib-trio nonsense,
  then it will happily render nonsense. For example, this ReST:

  .. code-block:: rst

     .. function:: all_things_to_all_people(a, b)
        :with: x
        :async-with: y
        :for: z
        :decorator:

        Something has gone terribly wrong.

  renders as:

  .. function:: all_things_to_all_people(a, b)
     :with: x
     :async-with: y
     :for: z
     :decorator:

     Something has gone terribly wrong.

* There's currently no particular support for asyncio's old-style
  "generator-based coroutines", though they might work if you remember
  to use `asyncio.coroutine
  <https://docs.python.org/3/library/asyncio-task.html#asyncio.coroutine>`__.


Acknowledgements
----------------

Inspiration and hints on sphinx hackery were drawn from:

* `sphinxcontrib-asyncio
  <https://pythonhosted.org/sphinxcontrib-asyncio/>`__
* `Curio's local customization
  <https://github.com/dabeaz/curio/blob/master/docs/customization.py>`__
* `CPython's local customization
  <https://github.com/python/cpython/blob/master/Doc/tools/extensions/pyspecific.py>`__

sphinxcontrib-asyncio was especially helpful. Compared to
sphinxcontrib-asyncio, this package takes the idea of directive
options to its logical conclusion, steals Dave Beazley's idea of
documenting special methods like coroutines by showing how they're
used ("await f()" instead of "coroutine f()"), and avoids the
`forbidden word
<https://trio.readthedocs.io/en/latest/tutorial.html#tutorial>`__
`coroutine
<https://mail.python.org/pipermail/async-sig/2016-October/000141.html>`__.
