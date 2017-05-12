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

from docutils.parsers.rst import directives
from sphinx import addnodes
from sphinx.domains.python import PyModulelevel, PyClassmember
from sphinx.ext.autodoc import (
    FunctionDocumenter, MethodDocumenter, ClassLevelDocumenter,
)

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


################################################################
# Extending the basic function and method directives
################################################################

class ExtendedCallableMixin:
    def needs_arglist(self):
        # if "property" in self.options:
        #     return False
        if "decorator" in self.options or self.objtype == "decorator":
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

    def handle_signature(self, sig, signode):
        ret = super().handle_signature(sig, signode)

        # Add the "@" prefix
        if "decorator" in self.options or self.objtype == "decorator":
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

def sniff_options(obj):
    options = set()
    async_gen = False
    # We walk the __wrapped__ chain to collect properties.
    #
    # If something sniffs as *both* an async generator *and* a coroutine, then
    # it's probably an async_generator-style async_generator (since they wrap
    # a coroutine, but are not a coroutine).
    while True:
        if getattr(obj, "__isabstractmethod__", False):
            options.add("abstractmethod")
        if isinstance(obj, classmethod):
            options.add("classmethod")
        if isinstance(obj, staticmethod):
            options.add("staticmethod")
        # if isinstance(obj, property):
        #     options.add("property")
        if inspect.iscoroutinefunction(obj):
            options.add("async")
        # in versions of Python, isgeneratorfunction returns true for
        # coroutines, so we use elif
        elif inspect.isgeneratorfunction(obj):
            options.add("for")
        if isasyncgenfunction(obj):
            options.add("async-for")
            async_gen = True
        if hasattr(obj, "__wrapped__"):
            obj = obj.__wrapped__
        else:
            break
    if async_gen:
        options.discard("async")
    return options

def update_with_sniffed_options(obj, option_dict):
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
    }

    def add_directive_header(self, sig):
        super().add_directive_header(sig)
        passthrough_option_lines(self, extended_function_option_spec)

    def import_object(self):
        ret = super().import_object()
        update_with_sniffed_options(self.object, self.options)
        return ret

class ExtendedMethodDocumenter(MethodDocumenter):
    priority = MethodDocumenter.priority + 1
    # You can explicitly set the options in case autodetection fails
    option_spec = {
        **MethodDocumenter.option_spec,
        **extended_method_option_spec,
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

    # We're overriding these on purpose, so disable the warning about it
    del directives._directives["autofunction"]
    del directives._directives["automethod"]
    app.add_autodocumenter(ExtendedFunctionDocumenter)
    app.add_autodocumenter(ExtendedMethodDocumenter)
    return {'version': __version__, 'parallel_read_safe': True}
