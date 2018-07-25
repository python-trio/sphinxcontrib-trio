"""A sphinx extension to help documenting Python code that uses async/await
(or context managers, or abstract methods, or generators, or ...).

This extension takes a somewhat non-traditional approach, though, based on
the observation that function properties like "classmethod", "async",
"abstractmethod" can be mixed and matched, so the the classic sphinx
approach of defining different directives for all of these quickly becomes
cumbersome. Instead, we override the ordinary function & method directives
to add options corresponding to these different properties, and override the
autofunction and automethod directives to sniff for these
properties. Examples:

A function that returns a context manager:

   .. function:: foo(x, y)
      :with: bar

renders in the docs like:

   with foo(x, y) as bar

The 'bar' part is optional. Use :async-with: for an async context
manager. These are also accepted on method, autofunction, and automethod.

An abstract async classmethod:

   .. method:: foo
      :abstractmethod:
      :classmethod:
      :async:

renders like:

   abstractmethod classmethod await foo()

Or since all of these attributes are introspectable, we can get the same
result with:

   .. automethod:: foo

An abstract static decorator:

   .. method:: foo
      :abstractmethod:
      :staticmethod:
      :decorator:

The :decorator: attribute isn't introspectable, but the others
are, so this also works:

   .. automethod:: foo
      :decorator:

and renders like

   abstractmethod staticmethod @foo

"""

from ._version import __version__

from docutils.parsers.rst import directives
from sphinx import addnodes
from sphinx.domains.python import PyModulelevel, PyClassmember
from sphinx.ext.autodoc import (
    FunctionDocumenter, MethodDocumenter, ClassLevelDocumenter, Options,
)
# In Sphinx versions prior to 1.7, this module would blow away some of the
# regular autodoc configuration as a side-effect when it's first imported, and
# normally this import would happen after we had set up our autodoc
# configuration. So our configuration was getting lost. See:
#
#   https://github.com/python-trio/sphinxcontrib-trio/issues/8
#
# By importing it ourselves up front before we set up our configuration, we
# get those side-effects out of the way early.
import sphinx.ext.autosummary.generate

import inspect
try:
    from async_generator import isasyncgenfunction
except ImportError:
    try:
        from inspect import isasyncgenfunction
    except ImportError:
        # This python install has no way to make async generators
        def isasyncgenfunction(fn):
            return False

CM_CODES = set()

from contextlib import contextmanager
CM_CODES.add(contextmanager(None).__code__)

try:
    from contextlib2 import contextmanager as contextmanager2
except ImportError:
    pass
else:
    CM_CODES.add(contextmanager2(None).__code__)

extended_function_option_spec = {
    "async": directives.flag,
    "decorator": directives.flag,
    "with": directives.unchanged,
    "async-with": directives.unchanged,
    "for": directives.unchanged,
    "async-for": directives.unchanged,
}

extended_method_option_spec = {
    **extended_function_option_spec,
    "abstractmethod": directives.flag,
    "staticmethod": directives.flag,
    "classmethod": directives.flag,
    #"property": directives.flag,
}

autodoc_option_spec = {
    "no-auto-options": directives.flag,
}

################################################################
# Extending the basic function and method directives
################################################################

class ExtendedCallableMixin:
    def needs_arglist(self):
        # if "property" in self.options:
        #     return False
        if ("decorator" in self.options
                or self.objtype in ["decorator", "decoratormethod"]):
            return False
        return True

    # This does *not* override the superclass get_signature_prefix(), because
    # that gets called by the superclass handle_signature(), which then
    # may-or-may-not insert it into the signode (depending on whether or not
    # it returns an empty string). We want to insert the decorator @ after the
    # prefix but before the regular name. If we let the superclass
    # handle_signature() insert the prefix or maybe not, then we can't tell
    # where the @ goes.
    def _get_signature_prefix(self):
        ret = ""
        if "abstractmethod" in self.options:
            ret += "abstractmethod "
        # objtype checks are for backwards compatibility, to support
        #
        #   .. staticmethod::
        #
        # in addition to
        #
        #   .. method::
        #      :staticmethod:
        #
        # it would be nice if there were a central place we could normalize
        # the directive name into the options dict instead of having to check
        # both here at time-of-use, but I don't understand sphinx well enough
        # to do that.
        #
        # Note that this is the code that determines the ordering of the
        # different prefixes.
        if "staticmethod" in self.options or self.objtype == "staticmethod":
            ret += "staticmethod "
        if "classmethod" in self.options or self.objtype == "classmethod":
            ret += "classmethod "
        # if "property" in self.options:
        #     ret += "property "
        if "with" in self.options:
            ret += "with "
        if "async-with" in self.options:
            ret += "async with "
        for for_type, render in [("for", "for"), ("async-for", "async for")]:
            if for_type in self.options:
                name = self.options.get(for_type, "")
                if not name.strip():
                    name = "..."
                ret += "{} {} in ".format(render, name)
        if "async" in self.options:
            ret += "await "
        return ret

    # But we do want to override the superclass get_signature_prefix to stop
    # it from trying to do its own handling of staticmethod and classmethod
    # directives (the legacy ones)
    def get_signature_prefix(self, sig):
        return ""

    def handle_signature(self, sig, signode):
        ret = super().handle_signature(sig, signode)

        # Add the "@" prefix
        if ("decorator" in self.options
                or self.objtype in ["decorator", "decoratormethod"]):
            signode.insert(0, addnodes.desc_addname("@", "@"))

        # Now that the "@" has been taken care of, we can add in the regular
        # prefix.
        prefix = self._get_signature_prefix()
        if prefix:
            signode.insert(0, addnodes.desc_annotation(prefix, prefix))

        # And here's the suffix:
        for optname in ["with", "async-with"]:
            if self.options.get(optname, "").strip():
                # for some reason a regular space here gets stripped, so we
                # use U+00A0 NO-BREAK SPACE
                s = "\u00A0as {}".format(self.options[optname])
                signode += addnodes.desc_annotation(s, s)

        return ret

class ExtendedPyFunction(ExtendedCallableMixin, PyModulelevel):
    option_spec = {
        **PyModulelevel.option_spec,
        **extended_function_option_spec,
    }

class ExtendedPyMethod(ExtendedCallableMixin, PyClassmember):
    option_spec = {
        **PyClassmember.option_spec,
        **extended_method_option_spec,
    }


################################################################
# Autodoc
################################################################

# Our sniffer never reports more than one item from this set. In principle
# it's possible for something to be, say, an async function that returns
# a context manager ("with await foo(): ..."), but it's extremely unusual, and
# OTOH it's very easy for these to get confused when walking the __wrapped__
# chain (e.g. because async_generator converts an async into an async-for, and
# maybe that then gets converted into an async-with by an async version of
# contextlib.contextmanager). So once we see one of these, we stop looking for
# the others.
EXCLUSIVE_OPTIONS = {"async", "for", "async-for", "with", "async-with"}

def sniff_options(obj):
    options = set()
    # We walk the __wrapped__ chain to collect properties.
    while True:
        if getattr(obj, "__isabstractmethod__", False):
            options.add("abstractmethod")
        if isinstance(obj, classmethod):
            options.add("classmethod")
        if isinstance(obj, staticmethod):
            options.add("staticmethod")
        # if isinstance(obj, property):
        #     options.add("property")
        # Only check for these if we haven't seen any of them yet:
        if not (options & EXCLUSIVE_OPTIONS):
            if inspect.iscoroutinefunction(obj):
                options.add("async")
            # in some versions of Python, isgeneratorfunction returns true for
            # coroutines, so we use elif
            elif inspect.isgeneratorfunction(obj):
                options.add("for")
            if isasyncgenfunction(obj):
                options.add("async-for")
            # Some heuristics to detect when something is a context manager
            if getattr(obj, "__code__", None) in CM_CODES:
                options.add("with")
            if getattr(obj, "__returns_contextmanager__", False):
                options.add("with")
            if getattr(obj, "__returns_acontextmanager__", False):
                options.add("async-with")
        if hasattr(obj, "__wrapped__"):
            obj = obj.__wrapped__
        elif hasattr(obj, "__func__"):  # for staticmethod & classmethod
            obj = obj.__func__
        else:
            break

    return options

def update_with_sniffed_options(obj, option_dict):
    if "no-auto-options" in option_dict:
        return
    sniffed = sniff_options(obj)
    for attr in sniffed:
        # Suppose someone has a generator, and they document it as:
        #
        #   .. autofunction:: my_generator
        #      :for: loop_var
        #
        # We don't want to blow away the existing attr["for"] = "loop_var"
        # with our autodetected attr["for"] = None. So we use setdefault.
        option_dict.setdefault(attr, None)

def passthrough_option_lines(self, option_spec):
    sourcename = self.get_sourcename()
    for option in option_spec:
        if option in self.options:
            if self.options.get(option) is not None:
                line = "   :{}: {}".format(option, self.options[option])
            else:
                line = "   :{}:".format(option)
            self.add_line(line, sourcename)

class ExtendedFunctionDocumenter(FunctionDocumenter):
    priority = FunctionDocumenter.priority + 1
    # You can explicitly set the options in case autodetection fails
    option_spec = {
        **FunctionDocumenter.option_spec,
        **extended_function_option_spec,
        **autodoc_option_spec,
    }

    def add_directive_header(self, sig):
        super().add_directive_header(sig)
        passthrough_option_lines(self, extended_function_option_spec)

    def import_object(self):
        ret = super().import_object()
        # autodoc likes to re-use dicts here for some reason (!?!)
        self.options = Options(self.options)
        update_with_sniffed_options(self.object, self.options)
        return ret

class ExtendedMethodDocumenter(MethodDocumenter):
    priority = MethodDocumenter.priority + 1
    # You can explicitly set the options in case autodetection fails
    option_spec = {
        **MethodDocumenter.option_spec,
        **extended_method_option_spec,
        **autodoc_option_spec,
    }

    def add_directive_header(self, sig):
        super().add_directive_header(sig)
        passthrough_option_lines(self, extended_method_option_spec)

    def import_object(self):
        # MethodDocumenter overrides import_object to do some sniffing in
        # addition to just importing. But we do our own sniffing and just want
        # the import, so we un-override it.
        ret = ClassLevelDocumenter.import_object(self)
        # If you have a classmethod or staticmethod, then
        #
        #   Class.__dict__["name"]
        #
        # returns the classmethod/staticmethod object, but
        #
        #   getattr(Class, "name")
        #
        # returns a regular function. We want to detect
        # classmethod/staticmethod, so we need to go through __dict__.
        obj = self.parent.__dict__.get(self.object_name)
        # autodoc likes to re-use dicts here for some reason (!?!)
        self.options = Options(self.options)
        update_with_sniffed_options(obj, self.options)
        # Replicate the special ordering hacks in
        # MethodDocumenter.import_object
        if "classmethod" in self.options or "staticmethod" in self.options:
            self.member_order -= 1
        return ret

################################################################
# Register everything
################################################################

def setup(app):
    app.add_directive_to_domain('py', 'function', ExtendedPyFunction)
    app.add_directive_to_domain('py', 'method', ExtendedPyMethod)
    app.add_directive_to_domain('py', 'classmethod', ExtendedPyMethod)
    app.add_directive_to_domain('py', 'staticmethod', ExtendedPyMethod)
    app.add_directive_to_domain('py', 'decorator', ExtendedPyFunction)
    app.add_directive_to_domain('py', 'decoratormethod', ExtendedPyMethod)

    # Make sure sphinx.ext.autodoc is loaded before we try to mess with it.
    app.setup_extension("sphinx.ext.autodoc")
    # We're overriding these on purpose, so disable the warning about it
    del directives._directives["autofunction"]
    del directives._directives["automethod"]
    app.add_autodocumenter(ExtendedFunctionDocumenter)
    app.add_autodocumenter(ExtendedMethodDocumenter)

    # A monkey-patch to VariableCommentPicker to make autodoc_member_order = 'bysource' work.
    from sphinx.pycode.parser import VariableCommentPicker

    if not hasattr(VariableCommentPicker, "visit_AsyncFunctionDef"):  # pragma: no cover
        VariableCommentPicker.visit_AsyncFunctionDef = VariableCommentPicker.visit_FunctionDef

    return {'version': __version__, 'parallel_read_safe': True}
