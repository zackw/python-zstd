# -*- encoding: utf-8 -*-
# Tests

import os
import struct
import sys

import zstd
from tests.base import BaseTestZSTD
from tests.data import COMPRESSION_TEST_DATA, RANDOM_128KB

# Synthesize round-trip tests (compress, decompress, result should equal
# original) for all of the supported compression levels, using each of the
# cases in COMPRESSION_TEST_DATA, and also RANDOM_128KB.

ROUNDTRIP_CASES = [tc["u"] for tc in COMPRESSION_TEST_DATA]
ROUNDTRIP_CASES.append(RANDOM_128KB)

def make_compression_roundtrip_tests():
    tdict = {}
    for level in range(zstd.CLEVEL_MIN, zstd.CLEVEL_MAX + 1):
        # Level 0 is an alias for the default compression level and can
        # be skipped.
        if level == 0: continue

        def test_one(self, level=level):
            for data in ROUNDTRIP_CASES:
                self.assertEqual(
                    data, zstd.decompress(zstd.compress(data, level)))

        fname = "test_roundtrip_%02d" % level
        fname = fname.replace("-", "m")
        test_one.__name__ = fname
        tdict[fname] = test_one

    return tdict

CompressionRoundTrip = type("CompressionRoundTrip", (BaseTestZSTD,),
                            make_compression_roundtrip_tests())

###
# Compression either without a "level" argument or with zero supplied
# for that argument is supposed to produce the same compressed blob as
# compression with level zstd.CLEVEL_DEFAULT.  We repeat this test with
# all of the ROUNDTRIP_CASES, as above.

class CompressionDefaults(BaseTestZSTD):

    def test_no_level(self):
        for data in ROUNDTRIP_CASES:
            cdata1 = zstd.compress(data)
            cdata2 = zstd.compress(data, level=zstd.CLEVEL_DEFAULT)
            self.assertEqual(cdata1, cdata2)

    def test_zero_level(self):
        for data in ROUNDTRIP_CASES:
            cdata1 = zstd.compress(data, 0)
            cdata2 = zstd.compress(data, level=zstd.CLEVEL_DEFAULT)
            self.assertEqual(cdata1, cdata2)

###
# Tests of constants.
#
class CompressionConstants(BaseTestZSTD):
    def test_constant_types(self):
        self.assertTrue(isinstance(zstd.CLEVEL_MIN, int))
        self.assertTrue(isinstance(zstd.CLEVEL_MAX, int))
        self.assertTrue(isinstance(zstd.CLEVEL_DEFAULT, int))
        self.assertTrue(isinstance(zstd.MIN_LEGACY_FORMAT, int))

    def test_constant_relations(self):
        self.assertTrue(zstd.CLEVEL_MIN < zstd.CLEVEL_MAX)
        self.assertTrue(zstd.CLEVEL_MIN < zstd.CLEVEL_DEFAULT)
        self.assertTrue(zstd.CLEVEL_DEFAULT < zstd.CLEVEL_MAX)

        self.assertTrue(zstd.CLEVEL_MIN < 0)
        self.assertTrue(zstd.CLEVEL_MAX > 0)
        self.assertTrue(zstd.CLEVEL_DEFAULT != 0)

        self.assertTrue(1 <= zstd.MIN_LEGACY_FORMAT <= 8)

###
# Tests of error handling.
#
class CompressionErrors(BaseTestZSTD):
    def test_compress_not_bytes(self):
        self.assertRaises(TypeError, zstd.compress, u"ಅಪರಿಚಿತ ವ್ಯಕ್ತಿ")

    def test_compress_level_not_a_number(self):
        self.assertRaises(TypeError, zstd.compress, b"doesn't matter",
                          "CLEVEL_DEFAULT")

    def test_compress_level_too_high(self):
        self.assertRaises(zstd.Error, zstd.compress, b"doesn't matter",
                          zstd.CLEVEL_MAX + 1)

    def test_compress_level_too_low(self):
        self.assertRaises(zstd.Error, zstd.compress, b"doesn't matter",
                          zstd.CLEVEL_MIN - 1)

    def test_decompress_nothing(self):
        self.assertRaises(zstd.Error, zstd.decompress, b"")

    def test_decompress_truncated(self):
        for tc in COMPRESSION_TEST_DATA:
            # Skip this test for the compression of the empty string;
            # libzstd seems not to care whether empty blocks are well-formed.
            if not tc["u"]: continue
            cdata = tc["c"][-1] # current format
            for i in range(1, len(cdata)):
                self.assertRaises(zstd.Error, zstd.decompress, cdata[:i])


###
# Tests of legacy compression formats.
#
# libzstd may or may not support decompression of the seven old
# versions of its own format.  Independently of that, we also want to
# check for continued ability to decompress frames with the custom
# header generated by pre-1.0.0.99 versions of this module.

def make_legacy_compression_format_tests():
    tdict = {}
    prefix_encoder = struct.Struct("<I")
    for v in range(8):
        def test_normal(self, v=v):
            if v+1 < zstd.MIN_LEGACY_FORMAT:
                self.skipTest("no support for legacy format %d" % (v+1))
            for tc in COMPRESSION_TEST_DATA:
                self.assertEqual(zstd.decompress(tc["c"][v]), tc["u"])

        def test_pyzstd(self, v=v):
            if v+1 < zstd.MIN_LEGACY_FORMAT:
                self.skipTest("no support for legacy format %d" % (v+1))
            for tc in COMPRESSION_TEST_DATA:
                prefix = prefix_encoder.pack(len(tc["u"]))
                cdata = prefix + tc["c"][v]
                self.assertEqual(zstd.decompress(cdata), tc["u"])

        tnn = "test_normal_%d" % (v+1)
        test_normal.__name__ = tnn
        tdict[tnn] = test_normal

        tpn = "test_pyzstd_%d" % (v+1)
        test_pyzstd.__name__ = tpn
        tdict[tpn] = test_pyzstd

    return tdict

LegacyCompressionFormats = type("LegacyCompressionFormats", (BaseTestZSTD,),
                                make_legacy_compression_format_tests())
