import pytest

import subprocess
import os.path
import sys
import textwrap
import abc
from contextlib import contextmanager

from contextlib2 import contextmanager as contextmanager2
from async_generator import async_generator, yield_
import lxml.html

from sphinxcontrib_trio import sniff_options

if sys.version_info >= (3, 6):
    exec(textwrap.dedent("""
        async def agen_native():
            yield
    """))

def test_sniff_options():
    def check(obj, *expected):
        __tracebackhide__ = True
        assert sniff_options(obj) == set(expected)

    def boring():  # pragma: no cover
        pass
    check(boring)

    class Basic:  # pragma: no cover
        def a(self):
            pass

        @classmethod
        def b(self):
            pass

        @staticmethod
        def c(self):
            pass

        @classmethod
        async def classasync(self):
            pass

    check(Basic.__dict__["a"])
    check(Basic.__dict__["b"], "classmethod")
    check(Basic.__dict__["c"], "staticmethod")
    check(Basic.__dict__["classasync"], "classmethod", "async")

    class Abstract(abc.ABC):  # pragma: no cover
        @abc.abstractmethod
        def abmeth(self):
            pass

        @staticmethod
        @abc.abstractmethod
        def abstatic(self):
            pass

        @staticmethod
        @abc.abstractmethod
        async def abstaticasync(self):
            pass

    check(Abstract.__dict__["abmeth"], "abstractmethod")
    check(Abstract.__dict__["abstatic"], "abstractmethod", "staticmethod")
    check(Abstract.__dict__["abstaticasync"],
          "abstractmethod", "staticmethod", "async")

    async def async_fn():  # pragma: no cover
        pass
    check(async_fn, "async")

    def gen():  # pragma: no cover
        yield
    check(gen, "for")

    @async_generator
    async def agen():  # pragma: no cover
        await yield_()
    check(agen, "async-for")

    if "agen_native" in globals():
        check(agen_native, "async-for")

    @contextmanager
    def cm():  # pragma: no cover
        yield

    check(cm, "with")

    @contextmanager2
    def cm2():  # pragma: no cover
        yield
    check(cm2, "with")

    def manual_cm():  # pragma: no cover
        pass
    manual_cm.__returns_contextmanager__ = True
    check(manual_cm, "with")

    def manual_acm():  # pragma: no cover
        pass
    manual_acm.__returns_acontextmanager__ = True
    check(manual_acm, "async-with")

    # A chain with complex overrides. We ignore the intermediate generator and
    # async function, because the outermost one is a contextmanager -- but we
    # still pick up the staticmethod at the end of the chain.
    @staticmethod
    def messy0():
        pass
    async def messy1():
        pass
    messy1.__wrapped__ = messy0
    def messy2():
        yield
    messy2.__wrapped__ = messy1
    def messy3():
        pass
    messy3.__wrapped__ = messy2
    messy3.__returns_contextmanager__ = True
    check(messy3, "with", "staticmethod")

# Hopefully the next sphinx release will have dedicated pytest-based testing
# utilities:
#
#   https://github.com/sphinx-doc/sphinx/issues/3458
#   https://github.com/sphinx-doc/sphinx/pull/3718
#
# Until then...
def test_end_to_end(tmpdir):
    subprocess.run(
        ["sphinx-build", "-v", "-nW", "-nb", "html",
         os.path.dirname(__file__), str(tmpdir)])

    tree = lxml.html.parse(str(tmpdir / "test.html")).getroot()

    def do_html_test(node):
        original_content = node.text_content()
        print("-- test case --\n", lxml.html.tostring(node, encoding="unicode"))

        check_tags = node.cssselect(".highlight-none")
        checks = []
        for tag in check_tags:
            # lxml normalizes &nbsp to the unicode \xa0, so we do the same
            checks.append(tag.text_content().strip().replace("&nbsp;", "\xa0"))
            tag.drop_tree()

        # make sure we removed the tests from the top-level node, to avoid
        # potential false positives matching on the tests themselves!
        assert len(node.text_content()) < len(original_content)
        assert checks

        test_content = lxml.html.tostring(node, encoding="unicode")
        for check in checks:
            assert check in test_content

    print("\n-- NEGATIVE (WARNING) TESTS --\n")

    for warning in tree.cssselect(".warning"):
        with pytest.raises(AssertionError):
            do_html_test(warning)

    print("\n-- POSITIVE (NOTE) TESTS --\n")

    for note in tree.cssselect(".note"):
        do_html_test(note)
