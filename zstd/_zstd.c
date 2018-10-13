/*
 * ZSTD Library Python bindings
 * Copyright (c) 2015-2018, Sergey Dryabzhinsky
 * All rights reserved.
 *
 * BSD License
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 *
 * * Redistributions of source code must retain the above copyright
 *   notice, this list of conditions and the following disclaimer.
 *
 * * Redistributions in binary form must reproduce the above copyright
 *   notice, this list of conditions and the following disclaimer in
 *   the documentation and/or other materials provided with the
 *   distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
 * FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
 * COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
 * INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
 * STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
 * OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <zstd.h>

#if ZSTD_VERSION_NUMBER < 10304
# error "python-zstd must be built using libzstd >= 1.3.4"
#endif

#if (PY_MAJOR_VERSION == 2 && PY_MINOR_VERSION < 6) \
 || (PY_MAJOR_VERSION == 3 && PY_MINOR_VERSION < 4)
# error "python-zstd must be built using Python 2.(>=6) or 3.(>=4)"
#endif

/*
 * Portability headaches.
 */

/* Not all supported compilers understand the C99 'inline' keyword.  */

#if !defined __STDC_VERSION__ || __STDC_VERSION < 199901L
# if defined __SUNPRO_C || defined __hpux || defined _AIX
#  define inline
# elif defined _MSC_VER || defined __GNUC__
#  define inline __inline
# endif
#endif

#ifndef ZSTD_CLEVEL_MIN
# define ZSTD_CLEVEL_MIN -5
#endif

#ifndef ZSTD_CLEVEL_MAX
# define ZSTD_CLEVEL_MAX 22
#endif

#ifndef ZSTD_CLEVEL_DEFAULT
# define ZSTD_CLEVEL_DEFAULT 3
#endif

/* Python 2/3 differences.  */
#if PY_MAJOR_VERSION >= 3

/* Module data was added in Python 3.  */
static struct PyModuleDef ZstdModuleDef;
struct module_state {
    PyObject *error;
};
#define GETSTATE(m) ((struct module_state*)PyModule_GetState(m))
#define ZstdError   (GETSTATE(PyState_FindModule(&ZstdModuleDef))->error)

/* This is used in a few places where we specifically want the
   "normal" string type: bytes for Py2, unicode for Py3.  */
#define PlainString_FromString(s) PyUnicode_FromString(s)

#else

static PyObject *ZstdError;
#define PlainString_FromString(s) PyString_FromString(s)

#endif


/* This does what 3.x's "y*" argument tuple code would do, in a 2.x/3.x-
   agnostic way.  Returns 0 on success, -1 on failure (in which case an
   exception has been set).  As with "y*", caller is responsible for
   calling PyBuffer_Release.  */
static inline int
obj_AsByteBuffer(PyObject *obj, Py_buffer *view)
{
    if (PyObject_GetBuffer(obj, view, PyBUF_SIMPLE) != 0) {
        PyErr_SetString(PyExc_TypeError, "a bytes-like object is required");
        return -1;
    }
    if (!PyBuffer_IsContiguous(view, 'C')) {
        PyBuffer_Release(view);
        PyErr_SetString(PyExc_TypeError, "a contiguous buffer is required");
        return -1;
    }
    return 0;
}

/* Check for a pre-1.0.0.99 frame header; if detected, update src_ptr,
   src_size, and raw_frame_size to skip over it.  */
static inline int
skip_old_frame_header(const unsigned char **src_ptr, size_t *src_size,
                      unsigned long long *raw_frame_size)
{
    /* An old frame header is a 4-byte little-endian integer giving
       the uncompressed length, followed by normal compressed data,
       which always begins with a four-byte magic number (even when
       legacy compressed formats are in use).  Therefore, if we don't
       have at least 8 bytes of data, it's not an old frame header.  */
    if (*src_size < 8)
        return 0;

    const unsigned char *p = *src_ptr;
    unsigned long long old_frame_size =
        (((unsigned long long) p[0]) <<  0) |
        (((unsigned long long) p[1]) <<  8) |
        (((unsigned long long) p[2]) << 16) |
        (((unsigned long long) p[3]) << 24);

    /* Old frames were limited to 0x7fff_ffff bytes of uncompressed data.
       Conveniently, this means we can't confuse an old frame header with
       any version of the Zstandard magic number, because all of those
       numbers have high (fourth) byte 0xFD.  */
    if (old_frame_size > 0x80000000ull)
        return 0;

    unsigned long long check_frame_size =
        ZSTD_getFrameContentSize(*src_ptr + 4, *src_size - 4);

    if (check_frame_size != old_frame_size &&
        check_frame_size != ZSTD_CONTENTSIZE_UNKNOWN)
        return 0;

    *src_ptr += 4;
    *src_size -= 4;
    *raw_frame_size = old_frame_size;
    return 1;
}

/* For use in docstrings.  */
#define S_(x) #x
#define S(x) S_(x)
#define SZL S(ZSTD_CLEVEL_MIN)
#define SZD S(ZSTD_CLEVEL_DEFAULT)
#define SZH S(ZSTD_CLEVEL_MAX)


PyDoc_STRVAR(compress_doc,
    "compress(data, level="SZD")\n"
    "--\n\n"
    "Compress data and return the compressed form.\n"
    "The compression level may be from "SZL" (fastest) to "SZH" (slowest).\n"
    "The default is "SZD".  level=0 is the same as level="SZD".\n"
    "\n"
    "Raises a zstd.Error exception if any error occurs.");

static PyObject *compress(PyObject* self, PyObject *args, PyObject *kwds)
{
    PyObject *src;
    Py_buffer srcbuf;
    PyObject *dst;
    char *dst_ptr;
    size_t dst_size;
    size_t c_size;
    int level = ZSTD_CLEVEL_DEFAULT;

    static char *kwlist[] = {"data", "level", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|i:compress", kwlist,
                                     &src, &level))
        return NULL;

    if (level == 0)
        level = ZSTD_CLEVEL_DEFAULT;
    if (level < ZSTD_CLEVEL_MIN) {
        PyErr_Format(PyExc_ValueError, "Bad compression level - less than %d: %d",
                     ZSTD_CLEVEL_MIN, level);
        return NULL;
    }
    if (level > ZSTD_CLEVEL_MAX) {
        PyErr_Format(PyExc_ValueError, "Bad compression level - more than %d: %d",
                     ZSTD_CLEVEL_MAX, level);
        return NULL;
    }

    if (obj_AsByteBuffer(src, &srcbuf))
        return NULL;

    dst_size = ZSTD_compressBound(srcbuf.len);
    dst = PyBytes_FromStringAndSize(NULL, dst_size);
    if (dst == NULL) {
        PyBuffer_Release(&srcbuf);
        return NULL;
    }

    dst_ptr = PyBytes_AS_STRING(dst);

    Py_BEGIN_ALLOW_THREADS;
    c_size = ZSTD_compress(dst_ptr, dst_size, srcbuf.buf, srcbuf.len,
                           level);
    Py_END_ALLOW_THREADS;

    if (ZSTD_isError(c_size)) {
        PyErr_Format(ZstdError, "Compression error: %s",
                     ZSTD_getErrorName(c_size));
        Py_CLEAR(dst);
    } else {
        _PyBytes_Resize(&dst, c_size);
    }

    PyBuffer_Release(&srcbuf);
    return dst;
}

static PyObject *decompress_fixed(const unsigned char *src_ptr,
                                  size_t src_size,
                                  unsigned long long raw_frame_size)
{
    PyObject *dst;
    char *dst_ptr;
    size_t dst_size;
    size_t d_size;

    if (raw_frame_size > (unsigned long long)PY_SSIZE_T_MAX) {
        PyErr_SetString(ZstdError,
                        "Decompressed data is too large for a bytes object");
        return NULL;
    }

    dst_size = (size_t) raw_frame_size;
    dst = PyBytes_FromStringAndSize(NULL, dst_size);

    if (dst != NULL) {
        dst_ptr = PyBytes_AS_STRING(dst);

        Py_BEGIN_ALLOW_THREADS;
        d_size = ZSTD_decompress(dst_ptr, dst_size, src_ptr, src_size);
        Py_END_ALLOW_THREADS;

        if (ZSTD_isError(d_size)) {
            PyErr_Format(ZstdError, "Decompression error: %s",
                         ZSTD_getErrorName(d_size));
            Py_CLEAR(dst);

        } else if (d_size != dst_size) {
            PyErr_Format(ZstdError, "Decompression error: length mismatch "
                         "(expected %zu, got %zu bytes)", dst_size, d_size);
            Py_CLEAR(dst);
        }
    }
    return dst;
}

static PyObject *decompress_stream(const unsigned char *src_ptr, size_t src_size)
{
    PyObject *dst;
    size_t dst_size;
    size_t d_size;
    ZSTD_DStream *zds;
    ZSTD_outBuffer obuf;
    ZSTD_inBuffer ibuf;

    zds = ZSTD_createDStream();
    if (zds == NULL)
        return PyErr_NoMemory();

    dst_size = ZSTD_DStreamOutSize();
    dst = PyBytes_FromStringAndSize(NULL, dst_size);
    if (dst == NULL) {
        ZSTD_freeDStream(zds);
        return NULL; /* error already set */
    }

    ibuf.pos = 0;
    ibuf.src = src_ptr;
    ibuf.size = src_size;
    obuf.pos = 0;
    for (;;) {
        obuf.dst = PyBytes_AS_STRING(dst);
        obuf.size = dst_size;

        Py_BEGIN_ALLOW_THREADS;
        d_size = ZSTD_decompressStream(zds, &obuf, &ibuf);
        Py_END_ALLOW_THREADS;

        if (ZSTD_isError(d_size)) {
            PyErr_Format(ZstdError, "Decompression error: %s",
                         ZSTD_getErrorName(d_size));
            Py_CLEAR(dst);
            break;
        }
        if (ibuf.pos == ibuf.size) {
            _PyBytes_Resize(&dst, obuf.pos);
            break;
        }
        /* need more space */
        dst_size *= 2;
        _PyBytes_Resize(&dst, dst_size);
        if (dst == NULL) break;
    }
    ZSTD_freeDStream(zds);
    return dst;
}


PyDoc_STRVAR(decompress_doc,
    "decompress(data)\n"
    "--\n\n"
    "Decompress data and return the uncompressed form.\n"
    "Raises a zstd.Error exception if any error occurs.");

static PyObject *decompress(PyObject* self, PyObject *args, PyObject *kwds)
{
    PyObject *dst;
    PyObject *src;
    Py_buffer srcbuf;
    const unsigned char *src_ptr;
    size_t src_size;
    unsigned long long raw_frame_size;

    static char *kwlist[] = {"data", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:decompress", kwlist,
                                     &src))
        return NULL;

    if (obj_AsByteBuffer(src, &srcbuf))
        return NULL;
    src_ptr = (const unsigned char *)srcbuf.buf;
    src_size = srcbuf.len;

    raw_frame_size = ZSTD_getFrameContentSize(src_ptr, src_size);
    if (raw_frame_size == ZSTD_CONTENTSIZE_ERROR
        && !skip_old_frame_header(&src_ptr, &src_size, &raw_frame_size))
    {
        PyErr_SetString(ZstdError, "Compressed data is invalid");
        PyBuffer_Release(&srcbuf);
        return NULL;
    }

    if (raw_frame_size == ZSTD_CONTENTSIZE_UNKNOWN)
        dst = decompress_stream(src_ptr, src_size);
    else
        dst = decompress_fixed(src_ptr, src_size, raw_frame_size);

    PyBuffer_Release(&srcbuf);
    return dst;
}

PyDoc_STRVAR(library_version_doc,
    "library_version()\n"
    "--\n\n"
    "Return the version of the zstd library as a string.\n"
    "The value returned will be different from the LIBRARY_VERSION\n"
    "constant when the library in use at runtime is a different version\n"
    "from the library this module was compiled against.");

static PyObject *library_version(PyObject* self)
{
    return PlainString_FromString(ZSTD_versionString());
}


PyDoc_STRVAR(library_version_number_doc,
    "library_version_number()\n"
    "--\n\n"
    "Return the version of the zstd library as a number.\n"
    "The format of the number is: major*100*100 + minor*100 + release.\n"
    "The value returned will be different from the LIBRARY_VERSION_NUMBER\n"
    "constant when the library in use at runtime is a different version\n"
    "from the library this module was compiled against.");

static PyObject *library_version_number(PyObject* self)
{
#if PY_MAJOR_VERSION >= 3
    return PyLong_FromLong(ZSTD_versionNumber());
#else
    return PyInt_FromLong(ZSTD_versionNumber());
#endif
}


/* There is no official way to query which legacy formats libzstd supports.
   These strings are the compression of zero bytes of data with versions 0.1
   through 0.8 of libzstd, and we see which ones ZSTD_getFrameContentSize will
   admit to understanding.  */
static int
detect_zstd_legacy_format_support(void)
{
    static const unsigned char legacy_compressions[][13] = {
        "\xfd\x2f\xb5\x1e\xc0\x00\x00\x00\x00\x00\x00\x00\x00",
        "\x22\xb5\x2f\xfd\xc0\x00\x00\x00\x00\x00\x00\x00\x00",
        "\x23\xb5\x2f\xfd\xc0\x00\x00\x00\x00\x00\x00\x00\x00",
        "\x24\xb5\x2f\xfd\x08\xc0\x00\x00\x00\x00\x00\x00\x00",
        "\x25\xb5\x2f\xfd\x08\xc0\x00\x00\x00\x00\x00\x00\x00",
        "\x26\xb5\x2f\xfd\x07\xc0\x00\x00\x00\x00\x00\x00\x00",
        "\x27\xb5\x2f\xfd\x04\x50\xea\x3b\x1d\x00\x00\x00\x00",
        "\x28\xb5\x2f\xfd\x04\x50\x01\x00\x00\x99\xe9\xd8\x51",
    };
    int i;
    for (i = 0; i < 8; i++) {
        if (ZSTD_getFrameContentSize(legacy_compressions[i], 13)
            != ZSTD_CONTENTSIZE_ERROR)
            return i + 1;
    }
    abort();
}

static void zstd_add_constants(PyObject *module)
{
    PyModule_AddStringConstant(module, "VERSION", PKG_VERSION_STR);
    PyModule_AddStringConstant(module, "LIBRARY_VERSION", ZSTD_VERSION_STRING);
    PyModule_AddIntConstant(module, "LIBRARY_VERSION_NUMBER",
                            ZSTD_VERSION_NUMBER);

    PyModule_AddIntConstant(module, "CLEVEL_MIN", ZSTD_CLEVEL_MIN);
    PyModule_AddIntConstant(module, "CLEVEL_MAX", ZSTD_CLEVEL_MAX);
    PyModule_AddIntConstant(module, "CLEVEL_DEFAULT", ZSTD_CLEVEL_DEFAULT);

    PyModule_AddIntConstant(module, "MIN_LEGACY_FORMAT",
                            detect_zstd_legacy_format_support());
}

static PyMethodDef ZstdMethods[] = {
    {"compress", (PyCFunction)compress, METH_VARARGS|METH_KEYWORDS,
     compress_doc},
    {"decompress", (PyCFunction)decompress, METH_VARARGS|METH_KEYWORDS,
     decompress_doc},
    {"library_version", (PyCFunction)library_version, METH_NOARGS,
     library_version_doc},
    {"library_version_number", (PyCFunction)library_version_number,
     METH_NOARGS, library_version_number_doc},
    {NULL, NULL, 0, NULL}
};

PyDoc_STRVAR(zstd_module_doc,
    "C extension wrapping libzstd.  Not meant to be used directly;\n"
    "use the parent module instead.");

#if PY_MAJOR_VERSION >= 3

static int zstd_traverse(PyObject *m, visitproc visit, void *arg)
{
    Py_VISIT(GETSTATE(m)->error);
    return 0;
}

static int zstd_clear(PyObject *m)
{
    Py_CLEAR(GETSTATE(m)->error);
    return 0;
}

static struct PyModuleDef ZstdModuleDef = {
        PyModuleDef_HEAD_INIT,
        "_zstd",
        zstd_module_doc,
        sizeof(struct module_state),
        ZstdMethods,
        NULL,
        zstd_traverse,
        zstd_clear,
        NULL
};

PyMODINIT_FUNC PyInit__zstd(void)
{
    PyObject *module = PyModule_Create(&ZstdModuleDef);
    if (module == NULL)
        return NULL;

    PyDoc_STRVAR(zstd_error_doc,
                 "Zstd compression or decompression error.");

    PyObject *zstd_error = PyErr_NewExceptionWithDoc(
        "_zstd.Error", zstd_error_doc, NULL, NULL);
    if (zstd_error == NULL) {
        Py_DECREF(module);
        return NULL;
    }
    GETSTATE(module)->error = zstd_error;
    Py_INCREF(zstd_error);
    PyModule_AddObject(module, "Error", zstd_error);

    zstd_add_constants(module);
    return module;
}

#else

PyMODINIT_FUNC init_zstd(void)
{
    PyObject *module = Py_InitModule3("_zstd", ZstdMethods,
                                      zstd_module_doc);
    if (module == NULL)
        return;

    ZstdError = PyErr_NewException("_zstd.Error", NULL, NULL);
    if (ZstdError == NULL) {
        Py_DECREF(module);
        return;
    }
    Py_INCREF(ZstdError);
    PyModule_AddObject(module, "Error", ZstdError);

    zstd_add_constants(module);
}

#endif
