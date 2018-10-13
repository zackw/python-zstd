# -*- coding: utf-8 -*-

import logging
import os
import sys
import unittest
import zstd

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("ZSTD")
log.info("Python version: %s" % sys.version)
log.info("python-zstd version: %s" % zstd.VERSION)
log.info("built with libzstd version: %s" % zstd.LIBRARY_VERSION)
log.info("running with libzstd version: %s" % zstd.library_version())


###
# The assertWarns[Regex]() context managers were added to unittest in
# 3.2.  If necessary, shim them.  The msg= argument (added in 3.3) is
# not shimmed, and usage as a context manager is mandatory.
#
# Some of this code was copied almost verbatim from 3.6 unittest/case.py.

if hasattr(unittest.TestCase, 'assertWarns'):
    TestCaseWithWarns = unittest.TestCase

else:
    import re
    import warnings

    def _is_subtype(expected, basetype):
        if isinstance(expected, tuple):
            return all(_is_subtype(e, basetype) for e in expected)
        return isinstance(expected, type) and issubclass(expected, basetype)

    class _AssertWarnsContext(object):
        """A context manager used to implement TestCase.assertWarns* methods."""

        def __init__(self, expected, test_case, expected_regex=None):
            if not _is_subtype(expected, Warning):
                raise TypeError('arg 1 must be a warning type or '
                                'tuple of warning types')

            self.test_case = test_case
            self.expected = expected
            if expected_regex is not None:
                expected_regex = re.compile(expected_regex)
            self.expected_regex = expected_regex

        def _raiseFailure(self, standardMsg):
            msg = self.test_case._formatMessage(None, standardMsg)
            raise self.test_case.failureException(msg)

        def __enter__(self):
            # The __warningregistry__'s need to be in a pristine state for tests
            # to work properly.
            for v in sys.modules.values():
                if getattr(v, '__warningregistry__', None):
                    v.__warningregistry__ = {}
            self.warnings_manager = warnings.catch_warnings(record=True)
            self.warnings = self.warnings_manager.__enter__()
            warnings.simplefilter("always", self.expected)
            return self

        def __exit__(self, exc_type, exc_value, tb):
            self.warnings_manager.__exit__(exc_type, exc_value, tb)
            if exc_type is not None:
                # let unexpected exceptions pass through
                return
            try:
                exc_name = self.expected.__name__
            except AttributeError:
                exc_name = str(self.expected)
            first_matching = None
            for m in self.warnings:
                w = m.message
                if not isinstance(w, self.expected):
                    continue
                if first_matching is None:
                    first_matching = w
                if (self.expected_regex is not None and
                    not self.expected_regex.search(str(w))):
                    continue
                # store warning for later retrieval
                self.warning = w
                self.filename = m.filename
                self.lineno = m.lineno
                return
            # Now we simply try to choose a helpful failure message
            if first_matching is not None:
                self._raiseFailure('"{}" does not match "{}"'.format(
                         self.expected_regex.pattern, str(first_matching)))
            self._raiseFailure("{} not triggered".format(exc_name))

    class TestCaseWithWarns(unittest.TestCase):

        def assertWarns(self, expected_warning):
            return _AssertWarnsContext(expected_warning, self)

        def assertWarnsRegex(self, expected_warning, expected_regex):
            return _AssertWarnsContext(expected_warning, self, expected_regex)

###
# zstd-specific TestCase subclass

class BaseTestZSTD(TestCaseWithWarns):

    # Shorthand.  Use as: with self._testingDeprecated("THING"): ...
    def _testingDeprecated(self, name):
        return self.assertWarnsRegex(DeprecationWarning,
                                     "\\b" + name + "\\b")


__all__ = ['BaseTestZSTD']
