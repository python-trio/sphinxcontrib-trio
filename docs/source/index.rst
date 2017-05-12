sphinxcontrib-trio
==================

sphinxcontrib-trio is a sphinx extension that makes sphinx's
directives for documenting Python functions and methods smarter and
more powerful. The name is because it was originally written for the
`Trio <https://trio.readthedocs.io>`__ project, and I'm not very
creative. Don't be put off – while it's especially useful for projects
using async/await, there's nothing Trio- or async-specific about it;
any project can benefit.

**Requirements:** This extension currently assumes you're using Python
3.5+ to build your docs. This could be relaxed if anyone wants to send
a patch.

**Documentation:** https://sphinxcontrib-trio.readthedocs.io

**Bug tracker and source code:**
https://github.com/python-trio/sphinxcontrib-trio

**License:** XX


Idea
----

Sphinx provides a number of convenient directives for `documenting
Python code
<http://www.sphinx-doc.org/en/stable/domains.html#the-python-domain>`__:
you can use the ``.. method::`` directive to document an ordinary
method, the ``.. classmethod::`` directive to document a classmethod,
the ``.. decoratormethod::`` directive to document a decorator method,
and so on. But what if you have a classmethod that's also a decorator?
And what if you want to document a project that uses some of Python's
many interesting function types that Sphinx *doesn't* support, like
async functions, abstract methods, or generators?

It would be possible to keep adding directive after directive for
every possible type – ``.. asyncmethod::``, ``.. abstractmethod::``,
``.. classmethoddecorator::``, ``.. abstractasyncstaticmethod::``, but
this quickly becomes silly. This package takes a different approach:

but we take a different approach, based on the
observation that "classmethod" ,"async", "abstractmethod" are
*attributes* of a function, not *types* of function: in particular,
they can be mixed and matched!


When I was documenting the `trio <https://trio.readthedocs.io>`__
package,

I realized I had a problem. I was using `sphinx
<http://www.sphinx-doc.org/>`__, of course. And sphinx provides some
`convenient directives for documenting Python code
<http://www.sphinx-doc.org/en/stable/domains.html#the-python-domain>`__:
you can use the ``.. method::`` directive to document an ordinary
method, the ``.. classmethod::`` directive to document a classmethod,
the ``.. decoratormethod::`` directive to document a decorator method,
and so on. But I realized that I had a lots of async methods that I
wanted to document. And abstract methods. And context managers. And
sphinx doesn't have directives for any of these. So maybe I needed to
add them? That's annoying but not *so* bad, so I studiously started
doing that, one by one...

\...until I realized that I also had an abstract async classmethod,
started to type ``.. abstractasyncclassmethod::``, and realized that
something had gone very wrong. It doesn't make sense to have a totally
new and unique directive for every possible combination of attributes
that a function or method might have! This just doesn't scale.

That's where ``sphinxcontrib-trio`` comes in: instead of having a
different top-level directive for every *combination* of attributes,
it makes it so the basic ``.. function::`` and ``.. method::``
directives now accept options describing each *individual* attribute
that your function/method has, so you can mix and match like:

.. code-block:: rst

   .. method:: overachiever(arg1, ...)
      :abstractmethod:
      :async:
      :classmethod:

This renders like:

.. method:: overachiever(arg1, ...)
   :abstractmethod:
   :async:
   :classmethod:

And while I was at it, I also replaced the ``sphinx.ext.autodoc``
directives ``.. autofunction::`` and ``.. automethod::`` with new
versions that know how to automatically detect many of these
attributes, so you could just as easily have written the above as:

.. code-block:: rst

   .. automethod:: my_method

and it would automatically figure out that this was an abstract async
classmethod by looking at your code.

And finally, I made the legacy ``.. classmethod::`` directive into an
alias for:

.. code-block:: rst

   .. method::
      :classmethod:

and similarly ``staticmethod``, ``decorator``, and
``decoratormethod``, so dropping this extension into an existing
sphinx project should be 100% backwards compatible while giving you
new superpowers.

Basically, this is how sphinx ought to work in the first
place. Perhaps in the future it will. But until then, this extension
is pretty handy.


Details on supported options
----------------------------

The enhanced ``.. function::`` directive supports the following
options, some of which can be automatically detected by
``.. autofunction::``:

====================  ========================== ======================
Spelling              Renders like               Detected by autodoc?
====================  ========================== ======================
``:async:``           await fn()                  yes!
``:decorator:``       @fn                         no
``:with:``            with fn()                   no
``:with: foo``        with fn() as foo            no
``:async-with:``      async with fn()             no
``:async-with: foo``  async with fn() as foo      no
``:for:``             for ... in fn()             generators only
``:for: foo``         with foo in fn()            generators only
``:async-for:``       async for ... in fn()       async generators only
``:async-for: foo``   async for foo in fn()       async generators only
====================  ========================== ======================

The enhanced ``.. method::`` and ``.. automethod::`` directives
support all of the same options as the ``.. function::`` and
``.. autofunction::`` directives, and also add the following:

====================  ========================== ====================
Spelling              Renders like               Detected by autodoc?
====================  ========================== ====================
``:abstractmethod:``  abstractmethod fn()        yes!
``:staticmethod:``    staticmethod fn()          yes!
``:classmethod:``     classmethod fn()           yes!
====================  ========================== ====================


Examples
--------

A regular async function:

.. code-block:: rst

   .. function:: example_async_fn(...)
      :async:

Renders as:

.. function:: example_async_fn(...)
   :async:

A context manager with a hint as to what's returned:

.. code-block:: rst

   .. function:: open(fname)
      :with: file_handle

Renders as:

.. function:: open(fname)
   :with: file_handle


.. what happens if we autodetect a generator then someone adds ':for:
   x', so we have :for: and then :for x:?

The auto versions of the directives also accept explicit options,
which are appended to the automatically detected options. So if
``some_method`` is defined as a ``classmethod`` in the source, and you
want to document that it should be used as a context manager, you can
write:

.. code-block:: rst

   .. automethod:: some_method
      :with:

then it will render like:

.. method:: some_method(arg1, ...)
   :classmethod:
   :with:

   This method is very interesting because ... [docstring pulled from source]


Bugs and limitations
--------------------

Currently there are no tests, because I don't know how to test a
sphinx extension. If you do, please let me know.

Python supports defining abstract properties like::

  @abstractmethod
  @property
  def some_property(...):
      ...

But this extension currently doesn't help you document them. The
difficulty is that for Sphinx, properties are attributes, not methods,
and we don't currently hook the code for handling ``.. attribute::``
and ``.. autoattribute::``. Maybe we should?

When multiple options are combined, then we try to render them in a
sensible way, but this does assume that you're giving us a sensible
combination to start with. If you give sphinxcontrib-trio nonsense,
then it will happily render nonsense. For example, this ReST:

.. code-block:: rst

   .. function:: all_things_to_all_people(a, b)
      :with: x
      :async-with: y
      :for: z
      :decorator:

renders as:

.. function:: all_things_to_all_people(a, b)
   :with: x
   :async-with: y
   :for: z
   :decorator:


Acknowledgements
----------------

Inspiration and hints on sphinx hackery were drawn from:
* `sphinxcontrib-asyncio
  <https://pythonhosted.org/sphinxcontrib-asyncio/>`__
* `Curio's local customization
  <https://github.com/dabeaz/curio/blob/master/docs/customization.py>`__
* `CPython's local customization
  <https://github.com/python/cpython/blob/master/Doc/tools/extensions/pyspecific.py>`__
