import pytest

import sys
import textwrap
import abc
from contextlib import contextmanager
from contextlib2 import contextmanager as contextmanager2
from async_generator import async_generator, yield_

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
