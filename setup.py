#!/usr/bin/env python

import shlex
import sys
import subprocess

from setuptools import setup, find_packages, Extension

if __name__ != '__main__':
    raise RuntimeError("don't import setup.py")

# Get the package version number from PKG-INFO.
with open("PKG-INFO", "rt") as fp:
    for line in fp:
        k, _, v = line.strip().partition(": ")
        if k == "Version":
            PKG_VERSION_STR = v.strip()
            break
    else:
        sys.stderr.write("setup.py: error: version number not found "
                         "in PKG-INFO")
        sys.exit(1)


ext_defines = [("PKG_VERSION_STR", '"' + PKG_VERSION_STR + '"')]
ext_include_dirs = []
ext_cflags = []
ext_libraries = []
ext_library_dirs = []
ext_ldflags = []

if "--libraries" in sys.argv:
    # If --libraries was set by the user, assume they have taken
    # full responsibility for telling setup() where to find the external
    # libzstd.
    pass
else:

    # Let's see if pkg-config will help us out.
    try:
        libs = subprocess.check_output(
            ["pkg-config", "libzstd", "--libs"])
        if libs:
            if not isinstance(libs, str):
                libs = libs.decode(sys.getdefaultencoding())
            for lib in shlex.split(libs):
                if lib[:2] == "-l":
                    ext_libraries.append(lib[2:])
                elif lib[:3].lower() == "lib":
                    ext_libraries.append(lib)
                elif lib[:2] in ('-L', '/L'):
                    ext_library_dirs.append(lib[:2])
                else:
                    ext_ldflags.append(lib)

        cflags = subprocess.check_output(
            ["pkg-config", "libzstd", "--cflags"])
        if cflags:
            if not isinstance(cflags, str):
                cflags = cflags.decode(sys.getdefaultencoding())
            for cflag in shlex.split(cflags):
                if cflag[:2] == "-D" or cflag[:2] == "/D":
                    k, _, v = cflag[2:].partition('=')
                    if not v: v = "1"
                    ext_defines.append((k, v))
                else:
                    ext_cflags.append(cflag)


    except subprocess.CalledProcessError:
        # pkg-config is not available or does not know about libzstd.
        # Assume we don't need to do anything special.
        pass

    # If we still don't know the name of the external libzstd, guess.
    if not ext_libraries:
        ext_libraries.append("zstd")

with open("README.rst", "r") as readme:
    long_description = readme.read()

setup(
    name="zstd2",
    version=PKG_VERSION_STR,
    description="Simple API for Zstandard compression and decompression",
    long_description=long_description,
    author="Zack Weinberg, Sergey Dryabzhinsky, Anton Stuk",
    author_email="zackw@panix.com",
    maintainer="Zack Weinberg",
    maintainer_email="zackw@panix.com",
    url="https://github.com/zackw/python-zstd",
    keywords=["zstd", "zstandard", "compression"],
    license="BSD",
    packages=find_packages(exclude="tests"),
    ext_modules=[
        Extension("zstd._zstd",
                  sources=["zstd/_zstd.c"],
                  define_macros=ext_defines,
                  include_dirs=ext_include_dirs,
                  extra_compile_args=ext_cflags,
                  libraries=ext_libraries,
                  library_dirs=ext_library_dirs,
                  extra_link_args=ext_ldflags
        )
    ],
    test_suite="tests",
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Intended Audience :: Developers",
        "Development Status :: 5 - Production/Stable",
        "Operating System :: POSIX",
        "Programming Language :: C",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ]
)
