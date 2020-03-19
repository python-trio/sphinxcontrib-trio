import re
import abc
import sys
import shutil
import inspect
import textwrap
import subprocess
from pathlib import Path
from functools import wraps
from typing import Callable, cast
from contextlib import contextmanager

import pytest
import lxml.html

try:
    from contextlib2 import contextmanager as contextmanager2
except ImportError:
    have_contextmanager2 = False
else:
    have_contextmanager2 = True

try:
    from async_generator import async_generator, yield_
except ImportError:
    have_async_generator = False
else:
    have_async_generator = True

try:
    from contextlib import asynccontextmanager
except ImportError:
    have_asynccontextmanager = False
else:
    have_asynccontextmanager = True

from sphinxcontrib_trio import sniff_options

if sys.version_info >= (3, 6):
    agen_native = cast(Callable, lambda: None)  # satisfy linter
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
        def b(cls):
            pass

        @staticmethod
        def c(self):
            pass

        @classmethod
        async def classasync(cls):
            pass

    check(inspect.getattr_static(Basic, "a"))
    check(inspect.getattr_static(Basic, "b"), "classmethod")
    check(inspect.getattr_static(Basic, "c"), "staticmethod")
    check(inspect.getattr_static(Basic, "classasync"), "classmethod", "async")

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

    check(inspect.getattr_static(Abstract, "abmeth"), "abstractmethod")
    check(inspect.getattr_static(Abstract, "abstatic"), "abstractmethod", "staticmethod")
    check(
        inspect.getattr_static(Abstract, "abstaticasync"),
        "abstractmethod", "staticmethod", "async",
    )

    async def async_fn():  # pragma: no cover
        pass
    check(async_fn, "async")

    def gen():  # pragma: no cover
        yield
    check(gen, "for")

    if have_async_generator:
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

    if have_contextmanager2:
        @contextmanager2
        def cm2():  # pragma: no cover
            yield
        check(cm2, "with")

    def manual_cm():  # pragma: no cover
        pass
    manual_cm.__returns_contextmanager__ = True  # type: ignore
    check(manual_cm, "with")

    def manual_acm():  # pragma: no cover
        pass
    manual_acm.__returns_acontextmanager__ = True  # type: ignore
    check(manual_acm, "async-with")

    if have_async_generator:
        @async_generator
        async def acm_gen():  # pragma: no cover
            await yield_()

        @wraps(acm_gen)
        def acm_wrapped():  # pragma: no cover
            pass
        acm_wrapped.__returns_acontextmanager__ = True  # type: ignore

        check(acm_wrapped, "async-with")

    if have_asynccontextmanager:
        acm = asynccontextmanager(agen_native)
        check(acm, "async-with")

    # A chain with complex overrides. We ignore the intermediate generator and
    # async function, because the outermost one is a contextmanager -- but we
    # still pick up the staticmethod at the end of the chain.
    @staticmethod  # type: ignore
    def messy0():  # pragma: no cover
        pass

    async def messy1():  # pragma: no cover
        pass

    messy1.__wrapped__ = messy0  # type: ignore

    def messy2():  # pragma: no cover
        yield

    messy2.__wrapped__ = messy1  # type: ignore

    def messy3():  # pragma: no cover
        pass

    messy3.__wrapped__ = messy2  # type: ignore
    messy3.__returns_contextmanager__ = True  # type: ignore
    check(messy3, "with", "staticmethod")


# Hopefully the next sphinx release will have dedicated pytest-based testing
# utilities:
#
#   https://github.com/sphinx-doc/sphinx/issues/3458
#   https://github.com/sphinx-doc/sphinx/pull/3718
#
# Until then...
def test_end_to_end(tmpdir):
    shutil.copytree(str(Path(__file__).parent / "test-docs-source"),
                    str(tmpdir / "test-docs-source"))
    subprocess.run(
        ["sphinx-build", "-v", "-nW", "-nb", "html",
         str(tmpdir / "test-docs-source"), str(tmpdir / "out")])

    tree = lxml.html.parse(str(tmpdir / "out" / "test.html")).getroot()

    def do_html_test(node, *, expect_match):
        original_content = node.text_content()
        print("\n-- test case --\n", lxml.html.tostring(node, encoding="unicode"))

        check_tags = node.cssselect(".highlight-none")
        checks = []
        for tag in check_tags:
            text = tag.text_content().strip()
            # lxml normalizes &nbsp to the unicode \xa0, so we do the same
            text = text.replace("&nbsp;", "\xa0")
            checks.append(text)
            tag.drop_tree()

        # make sure we removed the tests from the top-level node, to avoid
        # potential false positives matching on the tests themselves!
        assert len(node.text_content()) < len(original_content)
        assert checks

        test_content = lxml.html.tostring(node, encoding="unicode")
        # some versions of sphinx (>= 1.6) replace "..." with the ellipsis
        # character \u2026. Normalize back to "..." for comparison
        # purposes.
        test_content = test_content.replace("\u2026", "...")
        for check in checks:
            try:
                if expect_match:
                    assert re.search(check, test_content) is not None
                else:
                    assert re.search(check, test_content) is None
            except AssertionError:
                print("failed check")
                print()
                print(repr(check))
                print()
                print("failed test_content")
                print()
                print(repr(test_content))
                raise

    print("\n-- NEGATIVE (WARNING) TESTS --\n")

    for warning in tree.cssselect(".warning"):
        do_html_test(warning, expect_match=False)

    print("\n-- POSITIVE (NOTE) TESTS --\n")

    for note in tree.cssselect(".note"):
        do_html_test(note, expect_match=True)


def test_member_order(tmpdir):
    shutil.copytree(str(Path(__file__).parent / "test-docs-source"),
                    str(tmpdir / "test-docs-source"))

    subprocess.run(
        ["sphinx-build", "-v", "-nW", "-D", "autodoc_member_order=bysource", "-nb", "html",
         str(tmpdir / "test-docs-source"), str(tmpdir / "out")])

    tree = lxml.html.parse(str(tmpdir / "out" / "test.html")).getroot()

    print("\n-- test case member order by source. --\n")

    methods = (
        tree.cssselect(r"#autodoc_examples\.ExampleClassForOrder")[0].getnext().cssselect("dt")
    )

    names = [method.get("id").split(".")[-1] for method in methods]

    assert names == ["d_asyncmethod", "a_syncmethod", "c_asyncmethod", "b_syncmethod"]
