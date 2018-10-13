# -*- encoding: utf-8 -*-
# Tests of deprecated APIs (other than compress_old and decompress_old,
# which are tested in test_compress.py).

import sys
import warnings

import zstd
from tests.base import BaseTestZSTD

class DeprecatedAPI(BaseTestZSTD):

    def call_deprecated(self, fname, *args, **kwargs):
        fn = getattr(zstd, fname, None)
        if fn is None:
            self.skipTest("zstd.%s not present in this build" % fname)
        with self._testingDeprecated(fname):
            return fn(*args, **kwargs)


    def test_version(self):
        ver = self.call_deprecated("version")
        self.assertEqual(ver, zstd.VERSION)

    def test_ZSTD_version(self):
        ver = self.call_deprecated("ZSTD_version")
        self.assertEqual(ver, zstd.library_version())

    def test_ZSTD_version_number(self):
        ver = self.call_deprecated("ZSTD_version_number")
        self.assertEqual(ver, zstd.library_version_number())


    def test_ZSTD_compress(self):
        cdata = self.call_deprecated("ZSTD_compress", tDATA)
        self.assertEqual(cdata[:4], b"\x28\xb5\x2f\xfd")
        self.assertEqual(zstd.decompress(cdata), tDATA)

    def test_dumps(self):
        cdata = self.call_deprecated("dumps", tDATA)
        self.assertEqual(cdata[:4], b"\x28\xb5\x2f\xfd")
        self.assertEqual(zstd.decompress(cdata), tDATA)


    def test_ZSTD_uncompress(self):
        cdata = zstd.compress(tDATA)
        tdata = self.call_deprecated("ZSTD_uncompress", cdata)
        self.assertEqual(tdata, tDATA)

    def test_uncompress(self):
        cdata = zstd.compress(tDATA)
        tdata = self.call_deprecated("uncompress", cdata)
        self.assertEqual(tdata, tDATA)

    def test_ZSTD_loads(self):
        cdata = zstd.compress(tDATA)
        tdata = self.call_deprecated("loads", cdata)
        self.assertEqual(tdata, tDATA)


###
# Test data: Chao Yuen-Ren (趙元任)'s famous Mandarin tongue twister,
# "Lion-Eating Poet in the Stone Den"
tDATA = u"""
《施氏食獅史》

石室詩士施氏，嗜獅，誓食十獅。
氏時時適市視獅。
十時，適十獅適市。
是時，適施氏適市。
氏視是十獅，恃矢勢，使是十獅逝世。
氏拾是十獅屍，適石室。
石室濕，氏使侍拭石室。
石室拭，氏始試食是十獅。
食時，始識是十獅屍，實十石獅屍。
試釋是事。

Lion-Eating Poet in the Stone Den

In a stone den was a poet called Shi Shi, who was a lion addict, and
had resolved to eat ten lions. He often went to the market to look for
lions. At ten o’clock, ten lions had just arrived at the market. At
that time, Shi had just arrived at the market. He saw those ten lions,
and using his trusty arrows, caused the ten lions to die. He brought
the corpses of the ten lions to the stone den. The stone den was
damp. He asked his servants to wipe it. After the stone den was wiped,
he tried to eat those ten lions. When he ate, he realized that these
ten lions were in fact ten stone lion corpses. Try to explain this matter.
""".encode("utf-8")


if __name__ == "__main__":
    unittest.main()
