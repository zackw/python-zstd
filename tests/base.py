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
# zstd-specific TestCase subclass
# currently doesn't need to do anything, but preserved as a hook point

class BaseTestZSTD(unittest.TestCase):
    pass

__all__ = ['BaseTestZSTD']
