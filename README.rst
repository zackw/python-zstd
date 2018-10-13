===============
python-zstd 2.0
===============

.. image:: https://travis-ci.org/zackw/python-zstd.svg?branch=zstd2
    :target: https://travis-ci.org/zackw/python-zstd

`Zstandard`_, or Zstd for short, is a new lossless compression algorithm,
intended to provide compression ratios at least as good as zlib while
being significantly faster.  It can also produce compression ratios
competitive with bzip2 and lzma, at the cost of compression speed,
but preserving the same high *decompression* speed.

.. _Zstandard: https://github.com/facebook/zstd

This module, `zstd`_ 2.0, provides a simple API wrapping the reference
C implementation, libzstd, of Zstandard.  It provides functionality
comparable to the various compression modules in the Python standard
library.

.. _zstd: https://github.com/zackw/python-zstd

We do not currently plan to support compression dictionaries, nor any
of the experimental libzstd APIs, in this module.  The `zstandard`_
module, maintained by Gregory Szorc, provides access to these features
at the cost of a much more elaborate API.

.. _zstandard: https://pypi.python.org/pypi/zstandard

zstd 2.0 is a fork of the original python-zstd `maintained by Sergey
Dryabzhinsky`_.  That line of development offers compatibility with
older versions of Python than this fork, and bundles its own copy of
libzstd for your convenience; however, its API lacks support for
streaming compression and decompression.

.. _maintained by Sergey Dryabzhinsky: https://github.com/sergey-dryabzhinsky/python-zstd

zstd 2.0 does **not** bundle a copy of libzstd.  The system must
supply this library.  Version 1.3.4 or later is required.  No
experimental or deprecated features of libzstd are used.


Build and install from PyPI
---------------------------

Source packages are available from PyPI for Python 2.6+::

   $ pip install zstd2

and for Python 3.2+::

   $ pip3 install zstd2

The PyPI package name is “zstd2,” but the module name for ``import``
statements is “zstd.”  Both Sergey Dryabzhinsky’s zstd and Gregory
Szorc’s zstandard also install a module with this name; therefore,
zstd2 cannot be installed in the same environment as either of the
others.

Precompiled packages are not currently available.  Building and
installation requires a C compiler, `setuptools`_, and the development
environments for Python and libzstd. On Debian-like Linux
distributions, to build for Python 2::

   $ sudo apt-get install build-essential python-setuptools \
       python-dev libzstd-dev

or for Python 3::

   $ sudo apt-get install build-essential python3-setuptools \
        python3-dev libzstd-dev

.. _setuptools: https://pypi.org/project/setuptools/


Build from Git
--------------

The same tools are required as for building from PyPI.  The code is
available from Github::

   $ git clone https://github.com/zackw/python-zstd
   $ cd python-zstd

Building uses the standard ``setup.py`` interface::

   $ python setup.py build_ext test

or for Python 3::

   $ python3 setup.py build_ext test

``setup.py`` will attempt to use ``pkg-config`` to locate an external
libzstd; failing that, it will assume that the header file ``zstd.h``
and library file ``-lzstd`` are available without special compile-time
options.  If this is incorrect, you can use the ``--libraries``,
``--include-dirs``, and ``--library-dirs`` options to tell it where to
look::

   $ python setup.py build_ext \
       --include-dirs /opt/zstd/include \
       --library-dirs /opt/zstd/lib \
       --libraries zstd134


Basic usage
-----------

Compression and decompression are the same as with ``zlib``:

   >>> import zstd
   >>> data = b"123456qwert"
   >>> cdata = zstd.compress(data, level=1)
   >>> data == zstd.decompress(cdata)
   True

The ``level`` parameter to ``zstd.compress`` can be any integer from
``zstd.CLEVEL_MIN`` (currently −5) to ``zstd.CLEVEL_MAX``
(currently 22).  Omitting it, or passing zero, is the same as passing
``zstd.CLEVEL_DEFAULT`` (currently 3).  Negative numbers compress
“ultra-fast,” at the expense of compression ratio.  Numbers greater
than or equal to 20 produce “ultra-high” compression ratios, at the
expense of speed and memory usage.

The version of these bindings is exposed as ``zstd.VERSION``.

   >>> zstd.VERSION
   '2.0'

The libzstd version compiled against is ``zstd.LIBRARY_VERSION``, and
the libzstd version in use at runtime is ``zstd.library_version()``.

   >>> zstd.LIBRARY_VERSION
   '1.3.5'
   >>> zstd.library_version()
   '1.3.6'

This is what you would see if the module had been compiled against
version 1.3.5 of an external libzstd, but then the library was updated
to 1.3.6.

Compatibility Notes
-------------------

Support for legacy versions of the Zstandard compressed data format
(those produced by libzstd version 0.7 and earlier) depends only on
how libzstd was configured.  There is no longer any selection to be
made when building this module.  The constant ``zstd.MIN_LEGACY_FORMAT``
indicates the oldest legacy format that can be decompressed; it will
be a number from 1 (all legacy formats supported) to 8 (only the final
format produced by libzstd 0.8 and later is supported).

Old versions of this module (prior to 1.0.0.99.1) produced compressed
data with a custom header that other consumers of Zstandard compressed
data cannot read.  ``zstd.decompress`` can still decompress data in
this format, but ``zstd.compress`` will not produce it.  Note that
this custom header could appear with any of the legacy versions, or
the current version, of the compressed data format.

Old versions of this module (prior to 2.0) had version numbers that
depended on the version number of the bundled libzstd.  This is no
longer the case.

A number of alternative function names present in Sergey
Dryabzhinsky's zstd module have been removed:

+-------------------------+----------------------------------+
| Removed name            | Use instead                      |
+=========================+==================================+
| ``dumps``               | ``compress``                     |
+-------------------------+                                  |
| ``ZSTD_compress``       |                                  |
+-------------------------+----------------------------------+
| ``decompress_old``      | ``decompress``                   |
+-------------------------+                                  |
| ``loads``               |                                  |
+-------------------------+                                  |
| ``uncompress``          |                                  |
+-------------------------+                                  |
| ``ZSTD_uncompress``     |                                  |
+-------------------------+----------------------------------+
| ``version``             | ``VERSION`` (a constant, not a   |
|                         | function)                        |
+-------------------------+----------------------------------+
| ``ZSTD_version``        | ``library_version``              |
+-------------------------+----------------------------------+
| ``ZSTD_version_number`` | ``library_version_number``       |
+-------------------------+----------------------------------+
| ``compress_old``        | No equivalent (produced old,     |
|                         | incompatible compressed format)  |
+-------------------------+----------------------------------+
