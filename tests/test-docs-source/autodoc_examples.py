import abc

def basic():
    pass

async def asyncfn(x):
    pass

def gen():
    yield

# Classes are a bit complicated for autodoc, because:
# - there's the :members: option
# - how you access the attributes matters

class ExampleClass(abc.ABC):
    @abc.abstractmethod
    def abstractmethod_(self):
        pass

    @classmethod
    @abc.abstractmethod
    def classabstract(cls):
        pass

    @classmethod
    def classmethod_(cls):
        pass

    async def asyncmethod(self):
        pass

    @property
    def property_(self):
        pass

class ExampleClassForOrder:
    async def d_asyncmethod(self):
        pass

    def a_syncmethod(self):
        pass

    async def c_asyncmethod(self):
        pass

    def b_syncmethod(self):
        pass


async def autosummary_me():
    pass
