# -*- encoding: utf-8 -*-

import base64
import hashlib
import os
import struct

###
# 128kB of random data, which presumably won't compress very well.
# Take care to read only a few bytes from the OS-level secure RNG.
def _gen_random_bytes(length):
    m = hashlib.sha256()
    n, r = divmod(length, m.digest_size)
    out = []
    enc = struct.Struct("<l")
    m.update(os.urandom(16))
    for i in range(n):
        m.update(enc.pack(i))
        out.append(m.digest())

    m.update(enc.pack(0))
    out.append(m.digest()[:r])
    return b"".join(out)

RANDOM_128KB = _gen_random_bytes(128 * 1024)


###
# Precompressed test cases used by test_compression.py.
#
# Each array entry is a test case, having three fields: "n" the name
# of the test case, "u" the uncompressed test data, and "c" an array
# of eight base64-coded compressed blobs derived from the uncompressed
# data.  The blobs are in Zstandard data formats 1 through 8, in that
# order (format 8 is the standardized version; the other seven are
# legacy and may or may not be supported by the library).
#
# Test cases are in increasing order of length.

def _pp_test_data(tcases):
    for tc in tcases:
        tc["u"] = tc["u"].encode("utf-8")
        tcc = tc["c"]
        for i in range(len(tcc)):
            tcc[i] = base64.b64decode(tcc[i])
    return tcases

COMPRESSION_TEST_DATA = _pp_test_data([
    { "n": "empty",
      "u": u"",
      "c": [
          '/S+1HsAAAA==',
          'IrUv/cAAAA==',
          'I7Uv/cAAAA==',
          'JLUv/QjAAAA=',
          'JbUv/QjAAAA=',
          'JrUv/QfAAAA=',
          'J7Uv/QRQ6jsd',
          'KLUv/QRQAQAAmenYUQ==',
      ]
    },
    { "n": "pangram",
      "u": u"pack my box with five dozen liquor jugs\n",
      "c": [
          '/S+1HkAAKHBhY2sgbXkgYm94IHdpdGggZml2ZSBkb3plbiBsaXF1b3IganVncwrAAAA=',
          'IrUv/UAAKHBhY2sgbXkgYm94IHdpdGggZml2ZSBkb3plbiBsaXF1b3IganVncwrAAAA=',
          'I7Uv/UAAKHBhY2sgbXkgYm94IHdpdGggZml2ZSBkb3plbiBsaXF1b3IganVncwrAAAA=',
          'JLUv/QBAAChwYWNrIG15IGJveCB3aXRoIGZpdmUgZG96ZW4gbGlxdW9yIGp1Z3MKwAAA',
          'JbUv/QBAAChwYWNrIG15IGJveCB3aXRoIGZpdmUgZG96ZW4gbGlxdW9yIGp1Z3MKwAAA',
          'JrUv/UIoQAAocGFjayBteSBib3ggd2l0aCBmaXZlIGRvemVuIGxpcXVvciBqdWdzCsAAAA==',
          'J7Uv/SQoQAAocGFjayBteSBib3ggd2l0aCBmaXZlIGRvemVuIGxpcXVvciBqdWdzCseDIg==',
          'KLUv/SQoQQEAcGFjayBteSBib3ggd2l0aCBmaXZlIGRvemVuIGxpcXVvciBqdWdzCpwUGTw=',
      ]
    },
    { "n": "lion",
      "u": u"""\
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
""",
      "c": [
  """\
    /S+1HgABDQAA4wEPKKAnDQckyf/5jzqh2RglRuQm75S3IytVFrutEck+wU7Wz///
    //8PriEzAC0AKQCI02QLT5M8C7AMTM5o74TzkiyLlz1O/uHZZgfONairkpokX225
    K1Qerbat3SF+eMxRh8y8oKq5CeI+XqqTCcfTHpOhruN5SAeQtGEablilrmKclZ9q
    qavgOktlIIW2TgqomzLSmXz0oDfWzhMkh9IbtjHa2pGIWFEoH2lYjok+hGsgPwE6
    mmt5gXWu521Rm2Ing/jEP+JlBW0LJD2G96vf/YTtTXFW77h9QNIWHypo8hc/CwBU
    ARgABkDBKlNBnKhRNdIgkVQoFIGwyCgU0DAAwIARUMjyDcofwAAA
  """, """\
    IrUv/QABDjwEQBwAKKAnDQckyf/5jzqh2RglRuQm75S3IytVFrutEck+wU7Wz///
    //8PriEuACoALwCc5mqq2t9iBxBqk3c1NSjwJq+L7yCfsDiE9aBwxqMIsTQVnK+m
    b7EuvoO8QJoB3+RdTVV7kzzCVBeb5BGnyQ2Hyq6mqh0q2+Rl5VU7wlRuOFSWlWfl
    XXwUCHfxm7wJlmDfjufhPC5+k5fg8ZzmQeGMR6GyTd5euIMhjecg2YfzNHkNzA2P
    AqiI02QLT5M8C7AMrIjT7IWvpoxHVTvTeJO3F54kKkN4k5eVf4tFnOZbLAMrCwsA
    VAEYAAZAwSpTQZyoUTXSIJFUKBSBsMgoFNAwAMCAEVDI8g3KH8AAAA==
  """, """\
    I7Uv/QABDRQEgBsAKJCnDbMkyf8yMwvdCcnXSISIURrCrcmr2rXmJP4UMR2+1N3d
    3d1dFcwtACkALgCTNV3tULEDCNXJy5oaFLiT9zkPHZ+geIz1kHAFpCk1NRWes6ZQ
    sc956HgBNQPv5GVNV3uD/LHU5zTIJ1aTFx6XZU1XO3k5+dV+LJUXHpfl5Dn553xi
    FUusDeFMY9o3I2pA0XPeyUvQeFbzkHAFpHFZJ28/zmjHIjpQtgFFTl5DcwOkACuJ
    1WwLUYN8C7BLrInV7MdZUwWkq31p3MnbjyNMbQh38nLyULGJ1YSKDQ0AVAEYAAZA
    wSpT4SQCAYRG1UiDRFKhUATCIqNQQMMAAANGQKFIgATJoPwBwAAA
  """, """\
    JLUv/QAAARDIAiAVACiQhw1vJEl3s0IhvdgnfXtZO7Zqx34GnSWzJqUXsAm/ADPM
    MMMMsKcEIAAdAB8A12haQOBNXgXFGaYeLHgC0pRYRQzOjaZQsS7+8z5ARQFNXob8
    an9LZQpnlmXIM+Rd/MRUZDRd7VCxAgm1yQPQN8IX/C4+xTRQFnpmkzdhTyA9rG/y
    Ose/pbroHAGJqYgbpnM8AzQiARfHjwYqdmEqI3jDDX8vJvRMFwMgAFQAAAIAgHgA
    gJMRALUkAGQ0CPgAhS8CoFqAACAAUAoAsAxQOIlAAOGABhBAZQHoDAJBAMDSAAIc
    AYI8QwEqRWCPUSCLJDjIYQSAgA9QqEUICAMIngECBgAkSAaguAIzBsAAAA==
  """, """\
    JbUv/QAAAQMSyKEokIcNbyRJd7NCIb3YJ317WTu2asd+Bp0lsyalF7AJvwAzzDDD
    DLCnBImpiBumczwDNCIBF8ePBip2YSojeMMNfy8m9EwXB6BvhC/4XXyKaaAs9Mwm
    b8KeQHpY3+R1jn9LddE5mrwM+dX+lsoUzizLkGfIu/iJqchoutqhYgUSapPXaFpA
    4E1eBcUZph4seALSlFhFDM6NplCxLv7zPkBFASAAAAQAOBEgGCeAkGqAAckC4HBB
    KA8ASjUAIAAApQAAYxWSIxCAOAAGBUuBAMORACACAJilAEC4YDhZKAoUMM4WpEIK
    kHMAwCgADheEUgOAEQLAvABgAAnIgVuAwIwBwAAA
  """, """\
    JrUv/YJ0AAAA8hLIoSiQhw16KZO7WaGQXuyTvr2sHVu1Yz+DzpJZk9IL2IRfgBlm
    mGEG2FMCiamIG6ZzPAM0IgEXx48GKnZhKiN4ww1/Lyb0TBcHoG+EL/hdfIppoCz0
    zCZvwp5Aeljf5HWOf0t10TmavAz51f6WyhTOLMuQZ8i7+ImpyGi62qFiBRJqk9do
    WkDgTV4FxRmmHix4AtKUWEUMzo2mULEu/vM+QEUBIABHCEA1cNQGxlmYOgzws1Bo
    BNYczDRAakEWygEDizJhZ/yEw7QMFA3gtAH2MAZP6QnfwqeEE48As2YY9mchVjeK
    GpDqALDHPHPZGBQZwAAA
  """, """\
    J7Uv/WR0AAAA6xK0nCeghwY4KZN7q3pzf2mV+NZ2L3aieEsSGFca+YSUjtzp5P//
    //+XKwpHoaYfavK+AxJQJv4QGLGctxMcaaSfLSqz1KYQMM8afNFOUQ8QZpa6aEa0
    I6AFSL9oTt47eZuSvEWzOj4xd/Iqhc+E1fHq+Kb8UagxmE3MYcQDCnfRbDBrUOCL
    5oXoc14EBk9Ae06jxqG5wSyMuCm/uBdATR8ARwigKoCawbgPU4cBfhYKjcCagxkD
    BS3IcDlgwEXHT4FNC0JRC04bYA9j8BSMeKTwKeHEI8CsGYb9WYjVjaIGpDoA7DHP
    XDYGRQbUMus=
  """, """\
    KLUv/WR0AF0HANIKJyeghwY4KZN7q3pzf2mV+NZ2L3aieEsSGFca+YSUjtzp5P//
    //+XKwpHoaYfavK+AxJQJv4QGLGctxMcaaSfLSqz1KYQMM8afNFOUQ8QZpa6aEa0
    I6AFSL9oTt47eZuSvEWzOj4xd/Iqhc+E1fHq+Kb8UagxmE3MYcQDCnfRbDBrUOCL
    5oXoc14EBk9Ae06jxqG5wSyMuCm/uBdATR8ARwigKoCawbgPU4cBfhYKjcCagxkD
    BS3IcDlgwEXHT4FNC0JRC04bYA9j8BSMeKTwKeHEI8CsGYb9WYjVjaIGpDoA7DHP
    XDYGRQZ3W5eh
  """,
      ]
    },
    { "n": "lipsum",
      "u": u"""\
Lorem ipsum dolor sit amet, consectetuer adipiscing elit, sed diam
nonummy nibh euismod tincidunt ut laoreet dolore magna aliquam erat
volutpat.  Ut wisi enim ad minim veniam, quis nostrud exerci tation
ullamcorper suscipit lobortis nisl ut aliquip ex ea commodo consequat.
Duis autem vel eum iriure dolor in hendrerit in vulputate velit esse
molestie consequat, vel illum dolore eu feugiat nulla facilisis at
vero eros et accumsan et iusto odio dignissim qui blandit praesent
luptatum zzril delenit augue duis dolore te feugait nulla facilisi.

И немного юникода. Далеко-далеко за словесными горами в стране гласных
и согласных живут рыбные тексты. Вдали от всех живут они в буквенных
домах на берегу Семантика большого языкового океана.  Маленький ручеек
Даль журчит по всей стране и обеспечивает ее всеми необходимыми
правилами. Эта парадигматическая страна, в которой жаренные члены
предложения залетают прямо в рот. Даже всемогущая пунктуация не имеет
власти над рыбными текстами, ведущими безорфографичный образ жизни.
""",

      "c": [
  """\
    /S+1HgADjAADOwTMODAHs40AwDpFdCYRdXYnNQHoLkcQegKGJcXpQaQ0ckwM6y5i
    K8JaR4ueG/SiJ9Q+zw8NPX7LnuVCxwC+AL4ACUW19cPVDkdIMzPPryyQRKpYuWpQ
    Ek/186PjunoxROTPYDlQqIg8JYczb/5/PrVCiUiJP78yFVmIoC6IiMxkEBNnVgyO
    cRKZPORPpkj13MqtiKPV1ehnTlmP5lcVWLHhM/JXj0aE0g34/2ywqCYQ6hpzFqh5
    iYixEEiIEJ7CFi0aBD3nCllrTHtt8Z7oKTDGcUuhBbaFTpHwLE9rQplCDAO2BfM8
    qK8JTMFZnGsZD2sca55Cfe41zTUPWw6aY/S1RXvQEjUBCOePhQTSJT1APj/42Hyq
    0qs4WRGZZ/acIhX7nw9q4SGkaTLDhKpig0SK+P8rFYmCy5rKP6+eFhx9akH6BCj+
    0wAUyP8NEmQFFcnf/zrAo0E1T0fVTGROxalVvPqfD08oB8SravCfYAWiQtdcGdMg
    x0Dn9IkeW7znSURMAeZByDAHCY9jWttj9EEG+kCuKbwoAZ2nYQ2yOu9xEfQwDls0
    yIFNc206gDLmNaEMWhrTxT2QAAGcpmUcx+Diee0D+wQP0vV/flU5qFaqn2Ik38rM
    k2FBwyRdkZr5FXVJpMRTsX8knpn/cQFVrGLE+V89xYpqQHr1nHLAJ8TEqkVd14Mh
    j5VVUUB+7FMTyBYVyUqR5wMi5Td+NCg9s+cVi7oaS37Ff10Va9fegvAYBsGDDnvM
    NW5ZXh3YqAp1jClCWwud1hKNaVChrTmmQbC1AoBFbXrAMdA5Am9RiCWeOwAfd+A0
    TZsTwIOJBhlCexqD0FmcgcLEEjmEaGnPOWAR0zgofQirig0JLqrnv8Q6n6hqhgI4
    Jo6eDkfOG0yUh/zfojS/rqsHsbEwVaoYm4o/q0d1QahS/fy/khzyCeXo2f9ncPV8
    B0X1eH1GPqd2mkyfU8ThKn9LalyRGs782IuKlUys/ghQwAZhWxFAxmt12si5x7Vh
    bY1FC+a4AnUKLGrURK4POshxnrqGaRh8bfEsynAvip66iNFA17ZEUV0dc6KneAoQ
    Y5wy73nOolGdxnHtdeGgFrVxTxktFABUCf9yAQBFDxsLBQAzADiQUQOirH6EIxQM
    0NRPgKQNcdFPADLf4pmEwQyKB5OigUtZCH3KCf9YiohpBoZSRctvUBCaIYkSQlr6
    CekPwAAA
  """, """\
    IrUv/QADjDATIGcAODAHs40AwDpFdCYRdXYnNQHoLkcQegKGJcXpQaQ0ckwM6y5i
    K8JaR4ueG/SiJ9Q+zw8NPX7LnuVC0wDFALEArtDDPEsbBB3k2sBWpim0aQ+yRg4C
    IKF4DCa0yHkWfZanaZ5FWeuBVoaDCY5hfbBM5JxG7kEPgYfpcwy3iGBUqDGgZ9Ew
    hoEJ53GPvboF1A60LhB60eM0cjChBw1zTlNo4xzXdGFtnNPqIjeAPgG0iscYDzKP
    QuIxqLVhMMExrMxBYE0b9DDP0tca9DCmD/Y5cHELx70uTxM52GqAgHNKgKaBzuMk
    GuaWLi3qwXNMK4LjFpFjuIUVavC1t2iR8yx68FrD+lxU6GGepQ2MGK5Ng54ABHEp
    p2xkI7e6clzK64ZbXfmR1o2kjnxNuZGNP1zJBlxPpqYcP+Aq4pKvJ1dbN8heN3xt
    XZnaugg4kVA4hgBbgbYXObi0QQTI+pzTmLaUcRACBG3gY48BmcRzWtQYxOhzi8MY
    AnUwoY2LIucguKWPW54+L4Kur9VhUQMXC9bXGj1Q6wM1hcRjjVzkGLdgBcoYBjp9
    zCHAVqCwtTGMK9MUevAYTGiR8yza3Isa8zSJFkWtzzFNoe2xBxkMVKjj+hzUoMVp
    BuoEkeNSRpyorvzIytWSrxUk5Gtq61ZXqKk7JXU8cvVCUkfcSGrI160gvo64U1Yv
    pJSOdLgMknL8gBOTqakX0pFSFuLqyQzSSsCtIm4dp558Hfl68iMfZjBAMkjK15Ab
    n1w9pXW8MrUCriMbppaSGnLj1lWQ8crXEmvqyJMdCbmRW219Td3IyJ3yutUBruKR
    UzZyMvWUpX6kNeRHStkpHRm52uFeN7LVCQX5SOtGxik3XGrrCUW19cPVDvfhuJSQ
    rwvxI60XsjpBxqVs+DpBSnn9MDXkVleuXpCOlEwduQfVlePVFclx61ZP2cg45ciJ
    KampK1eX2roMWV2AjDtyysnWjoy4DBlfkI5s+HKY8lrKRu51ZYaUMuJO2SDjU1JT
    jj9chqy2pnb4mrJkaikjTjzSmpryQpZayrjDhfhayuspryc3cg8iQ8YnN5J6Iaun
    jFduuFpyXMp4xI1PuYCrqK4cp1wdFABUCf9yAQBFDxsLBQAzADiQUQOirH6EIxQM
    0NRPgKQNcdFPADLf4pmEwQyKB5OigUtZCH3KCf9YiohpBoZSRctvUBCaIYkSQlr6
    CekPwAAA
  """, """\
    I7Uv/QADiyATAGcAODAHs40AwDpFdCYRdXYnNQHoLkcQBAG/JcXpQaQ0ckwM6y5i
    K8JaR4ueG/SiJ9Q+zw8NPX7LnuVC0gDFALEAhR7mWdog6CDXBrYyTaFNe5A1chAA
    CcVjMKFFzrPoszxN8yzKWg+0MhxMcAzrg2Ui5zRyD3oIPEyfY7hFBKNCjQE9i4Yx
    DEw4j3vs1S2gdqB1gdCLHqeRgwk9aJhzmkIb57imC2vjnFYXuQH0CaBVPMZ4kHkU
    Eo9BrQ2DCY5hZQ4Ca9qgh3mWvtaghzF9sM+Bi1s47nV5msjBVgMEnFMCNA10HifR
    MLd0aVEPnmNaERy3iBzDLaxQg6+9RYucZ9GD1xrW56JCD/MsbWDEcG0a9AQg1NZx
    KadsZCNxKa8bbnXlR1o3kjryNeVGNv5wJRtwPZmacrzBVcQlX0+utj4ge93wtXVl
    ausi4ERC4RgCbAXaXuTg0gYRIOtzTmPaUsZBCBC0gY89BmQSz2lRYxCjzy0OYwjU
    wYQ2Loqcg+CWPm55+rwIur5Wh0UNXCxYX2v0QK0P1BQSjzVykWPcghUoYxjo9DGH
    AFuBwtbGMK5MU+jBYzChRc6zaHMvaszTJFoUtT7HNIW2xx5kMFChjutzUIMWpxmo
    4wKV45SrI8eljDhRXfmRlaslXytIyNfU1q2uUFN3Sup45OqFpI64kdSQr1tBfB1x
    p6xeSCkd6XAZJOV4gxOTqakX0pFSFuLqyQzSSsCtIm4dp558HXnkwwwGSAZJ+Rpy
    45Orp7SOV6ZWwHVkw9RSUkNu3LoKMl75WmJNHXmyIyE3cqutr6kbGblTXrc6wFU8
    cspGTqaestSPtIb8SCk7pSMjVzvc60a2OqEgH2ndyDjlhhsJRbX1w9UO9+G4lJCv
    C/EjrReyOkHGpWz4OkFKef0wNeRWV65ekI6UTB25B9WV49UVyXHrVk/ZyDjlyIkp
    qakrV5faugxZXYCMO3LKydaOjLgMGV+Qjmz4cjje4CqmvJaykXtdmSGljLhTHpDx
    Kakpxx8uQ1ZbUzt8TVkytZQRJx5pTU15IUstZdzhQnwt5fWU15MbuQeRIeOTG0m9
    kNVTxis3XC05LmU84sanXMBVVAcVAFQI/3IBAEUbEwUAMwA4kFEDoqx+BBr6CZC0
    IS76CUDmWzyTMJhB8WBSNChBwAUUhD7lhH8sRcQ0A0OpopSCgtGgIDRDEiWEtPQT
    0h/AAAA=
  """, """\
    JLUv/QAAA0gcDIBGADhAMdomACCnwC3STShkYtYwJ+YA8wOwYMQzaER0z1mcGDZl
    CmopC8pjC9+teuxYAPJUkYBuNPkAV3oAegB7AJFpTuGC1gbKBGknQvC55qcRwQm2
    tGWCMjvLTFtanxZgSICtgIsB4+MSGLigNFsRQZ/l1RaLOWEm5NZjGA1bdLRpCu04
    9jSmERxoswGMxeYaw5Y6dvI5AfVJL5o2TxnqLEMZYcImX3ONEzDZMtRnyD3OMYuP
    oWYJuQECDGz5ckEMQ3Xaeg7M9D1tC3Xs1HF28EVt67HYNMsw/RyUdlD66dNHm3XA
    zXDpIuYBx3Q+jzqRCl8+jjH5XjrBCReMjCcmQIUScloicFMnFBVSs5h+EsYlAKOA
    KyI4xzHmGq90gjRDn6cQcgfuMVSGNi8+Q8mAXMPW8wSNld5wR6eiW179gTrlkG14
    demOldyPre5JgVsReaylNzyyjfVjISv5dIh7OsNgo1ekU491rCXRG+vplkeWumOl
    S169csc6+uQOQHrl0Re4FdEfXp3y6dQbrKs7vDp1y6VTNwNnGIWuhE7HGRex5ZOO
    H4UUKDCLcEFGfAKMYjr1yafJIxbsgp18erh0SnLmsZZPB2x0yD6WcuqQvURPYCuI
    x9pyhm3spcEy7HSIh0sRhYhXlETEsI51iH55bABuReXTJZczlk8MtuGVJD265NIv
    d1ymK2xjIQtxLywjXWEhEZ9O+cJSlxq4rYikU15dEtnJGRDYha28eiz1CAA3ZB0u
    PX4AAAEtopIaBS1UQhIaUZCWVX7UqrE/ByCCghCDfPCQpACAAB5AaZEWBncUjQzn
    c+VoFXNlISUlvxzRzLRvHshEJWsauDCHLOdNcYA69NqQC3LWO8ugO4LIghG0l4PB
    IMsmgyv1BgP1ZAec2160N/i/O/UYkLcVCPKrAMOOvwYscNsCBOxRfSFDieI8g7h7
    4mgXpl09MWDK26CAQox7xrBPOTTYsJySfhB9t5loUpZEFzugIpHJMHBG1RecVgzD
    QmfzIexILXT7CkcBbFHeEopc944MXih/yYemzzmUVp2jFLTnHz3gvQTGMD96YrRe
    BEgrf7MycmdgbyP6DV1bi+SzHsfdMda0VhK0E/5AXivAAAA=
  """, """\
    JbUv/QAAA0QMHjQ4QDHaJgAgp8At0k0oZGLWMCfmAPMDsGDEM2hEdM9ZnBg2ZQpq
    KQvKYwvfrXrsWADyVJGAbjT5AFd6AHoAewCRaU7hgtYGygRpJ0LwueanEcEJtrRl
    gjI7y0xbWp8WYEiArYCLAePjEhi4oDRbEUGf5dUWizlhJuTWYxgNW3S0aQrtOPY0
    phEcaLMBjMXmGsOWOnbyOQH1SS+aNk8Z6ixDGWHCJl9zjRMw2TLUZ8g9zjGLj6Fm
    CbkBAgxs+XJBDEN12noOzPQ9bQt17NRxdvBFbeux2DTLMP0clHZQ+unTR5t1wM1w
    6SLmAcd0Po86kQpfPo4x+V46wQkXjIwnJkCFEnJaInBTJxQVUrOYfhLGJQCjgCsi
    OMcx5hqvdII0Q5+nEHIH7jFUhjYvPkPJgFzD1vMEjZXecEenolte/YE65ZBteHXp
    jpXcj63uSYFbEXmspTc8so31YyEr+XSIezrDYKNXpFOPdawl0Rvr6ZZHlrpjpUte
    vXLHOvrkDkB65dEXuBXRH16d8unUG6yrO7w6dculUzcDZxiFroROxxkXseWTjh+F
    FCgwi3BBRnwCjGI69cmnySMW7IKdfHq4dEpy5rGWTwdsdMg+lnLqkL1ET2AriMfa
    coZt7KXBMux0iIdLEYWIV5RExLCOdYh+eWwAbkXl0yWXM5ZPDLbhlSQ9uuTSL3dc
    pitsYyELcS8sI11hIRGfTvnCUpcauK2IpFNeXRLZyRkQ2IWtvHos9QgAN2QdLj1+
    /AEtspIYBS1UQhIaUZCWVX7UqrE/ByCCghCDfPCQpACAAA+stKSBQTEKkwnkJ/IP
    KhoFalrJHUfjzaybMMms5JJ2XUiG3OaROPw630TLFhvrhOUed+TJtiLEl3jAEWua
    ZMrnG2R0ewd8ex0ND/O/QH0D2G+hPyQp6GHw3wM8aKgJBDdRvSCLEIV4NvecyJaF
    xXpNopmatiogjNieexhnpTeYv0xcCi06aSPk+BIFl1IAlABhxhrTegZTVmyIQ02G
    v7uIDX17enLYmMwnCVW7m54M8LyGT4zXuemsOHJiFHv+GU2ytzBG9DP6REQ9kKVN
    f3HMtslIWgX9V13nFAf3mnu7GVdFaUPm8JC8VsAAAA==
  """, """\
    JrUv/YKTBAADPwweNDhAMdomANkyt0g3oZCJWcOcmAPMD8CCEc+gEdE9Z3Fi2JQp
    qKUsKI8tfLfqsWMByFNFArrR5ANcAXoAegB7AJFpTuGC1gbKBGknQvC55qcRwQm2
    tGWCMjvLTFtanxZgSICtgIsB4+MSGLigNFsRQZ/l1RaLOWEm5NZjGA1bdLRpCu04
    9jSmERxoswGMxeYaw5Y6dvI5AfVJL5o2TxnqLEMZYcImX3ONEzDZMtRnyD3OMYuP
    oWYJuQECDGz5ckEMQ3Xaeg7M9D1tC3Xs1HF28EVt67HYNMsw/RyUdlD66dNHm3XA
    zXDpIuYBx3Q+jzqRCl8+jjH5XjrBCReMjCcmQIUScloicFMnFBVSs5h+EsYlAKOA
    KyI4xzHmGq90gjRDn6cQcgfuMVSGNi8+Q8mAXMPW8wSNld5wR6eiW179gTrlkG14
    demOldyPre5JgVsReaylNzyyjfVjISv5dIh7OsNgo1ekU491rCXRG+vplkeWumOl
    S169csc6+uQOQHrl0Re4FdEfXp3y6dQbrKs7vDp1y6VTNwNnGIWuhE7HGRex5ZOO
    H4UUKDCLcEFGfAKMYjr1yafJIxbsgp18erh0SnLmsZZPB2x0yD6WcuqQvURPYCuI
    x9pyhm3spcEy7HSIh0sRhYhXlETEsI51iH55bABuReXTJZczlk8MtuGVJD265NIv
    d1ymK2xjIQtxLywjXWEhEZ9O+cJSlxq4rYikU15dEtnJGRDYha28eiz1CAA3ZB0u
    PX78ESVjiqkJByNACgQIIEKAkEI+EHhIUgBAABIDqk7ZhJoVXDPzO/WeLbLGYLae
    tw9vp2l1FjzjKhk2UENmZGHX0BnjyYXOHfmvzaC7R6QwZ77g4RQM5xkBShLP6wjR
    szUQut3XIMMIGvCLQWKvESYjBHfGAi4BOdkAwcHTqnqSqlK8tPruGQkBZJVpOaWw
    LLx6yJGaUpYMpok3hnVSqwYpOcCPYM4VW0zVEFZkzGGpVQAIMa6VeE5hkPAeCm36
    AGQUhcnb/zmsiXNA1xwUlD0TA/jtwq3iFHnj2TuugRyu3Qar+pVFncBAsrUFV8xx
    4ugDCxX243hLjMkt0vOPX/xOlfBTsSTBecAAAA==
  """, """\
    J7Uv/WSTBAADOww6MjJQaRsAKa1IcmlbyNJ60z2NdSPDEFSoAZV2lAhE7f+L3S89
    e2z0lBcWU7L+TRKbXed+znwAfAB7ABAUm8gpZNDqSHkg/UQJPhf5aWTwojGNskGb
    H+amUVqfGjAcYDMgc8AIuYYGMindWGRQiJlFDdacMFNyDDKMhlF81IkU+nHtaUwX
    WNDICFqLkYuaxvTxk88LqFC6Eanz1KEPs5QRJnTyRc7xAmZjhvosOcg9bvE51C0l
    JyDQEaEGRvmSSQ5DfSIGLbjpexo19LHTx9nBFzVir0XHYYbp56S0k9JPn0LqMAKO
    DJk2YhJwTCcEqRep8CXkWpPvpRuckMHogGIDVCmlJ8oCjtQpRZXULaahhJEFaBiQ
    RQb3uNacY5Y+kHYo9BRKbsFBhupQ58VnKR2ScxoL1B9LPeKebk3H/PqEdeqUWy7Z
    iF+nDlnKHdnrriDcjElkTT3ik32sIytZyqtT3NWbBTv9Qt2KLGRNmf5YV8d8stYh
    S53y65dD1tMrNwDql0+PcDOmT/y65dWtP1hfl/h165hTt24JbxqGsoTOxxkbMUoo
    H0MqJUjgFiELDaO69cqryisUrIKtvJo4dYvyJrKYVwx2umQja7l1yWbuYC+KyBpz
    iH1s5sFCbHWKiVMTh4pflsUEsdMth6zE9ExkK9yMy6tTMm8wrxZsxC+K+nTKqWcO
    yVR32MdKluJ+2Ia6w0oqXt3yh7VOTbjNmKhbfp0y2cohGuzDXn5F1vpE4ZasxAN7
    /DElY4ihgWhkFCQFAgQAQoCQQj4QeEhSAEAAEhMqTllChZWscfn5dTotciNA1pzp
    j7fSeDoPzvjKhz1o2I307WS6Ix59011uoFfo0dAdKc45Xzg4JcM4bIOSxPM6wvZa
    GaRu1zVg+AUH/HqQ4DWiJ/bsCBSCyqwFqwf3Vc1JKkoB0vKbMw62kDXWTGnOunDU
    oSO9pCUZTBNrDHBSrgZT8ocb0Zx9bDGNAaoIPAdTO4UAecI3tUtCWyi2qQEYLg4m
    4T/9iByngR7G8HDizI1waRi3nOPLG96+u47u8PQ2SNWtLMoEAoYNL7hkjicHR1iS
    sA+OrMRA3CI9+PDF71QJPRVLErwH6PY+
  """, """\
    KLUv/WSTBMUZAPawjDJQaRsAKa1IcmlbyNJ60z2NdSPDEFSoAZV2lAhE7f+L3S89
    e2z0lBcWU7L+TRKbXed+znwAfAB7ABAUm8gpZNDqSHkg/UQJPhf5aWTwojGNskGb
    H+amUVqfGjAcYDMgc8AIuYYGMindWGRQiJlFDdacMFNyDDKMhlF81IkU+nHtaUwX
    WNDICFqLkYuaxvTxk88LqFC6Eanz1KEPs5QRJnTyRc7xAmZjhvosOcg9bvE51C0l
    JyDQEaEGRvmSSQ5DfSIGLbjpexo19LHTx9nBFzVir0XHYYbp56S0k9JPn0LqMAKO
    DJk2YhJwTCcEqRep8CXkWpPvpRuckMHogGIDVCmlJ8oCjtQpRZXULaahhJEFaBiQ
    RQb3uNacY5Y+kHYo9BRKbsFBhupQ58VnKR2ScxoLfyz1iHu6NR3z6xPWqVNuuWQj
    fp06ZCl3ZK+7gnAzJpE19YhP9rGOrGQpr05xX9WbBTv9Qt2KLGRNmf5YV8d8stYh
    S53y65dD1tMrNwDql0+PcDOmT/y65dWtP1hfl/h165hTt24JbxqGsoTOxxkbMUoo
    H0MqJUjgFiELDaO69cqryisUrIKtvJo4dYvyJrKYVwx2umQja7l1yWbuYC+KyBpz
    iH1s5sFCbHWKiVMTh4pflsUEsdMth6zE9ExkK9yMy6tTMm8wrxZsxC+K+nTKqWcO
    yVR32MdKluJ+2Ia6w0oqXt3yh7VOTbjNmKhbfp0y2cohGuzDXn5F1vpE4ZasxKl5
    qCEpY4ihgWhkFCQFAgQAQoCQQj4QgEhSIIAAEhNap2xC3ZWsUfj5dTotwkYCa8/A
    HyekcToHn1GxExqykX27pqvEk7M6yw31OhQ9P5HGHKMFghMZ2lMeFEFErENrf6sB
    6DqvwYZV8OO3QRCvtTfRZ1NgEVRmC3g96K9aThJRCpCW34hxkI2sWXOlPWvDyQw9
    dJZWZEBNrDHeCVzNpmQPd6U599piGgNWUXgOpnYKAfKEcOqVhLhQbFMFMFwcygQ/
    AowzQAXjeDhx5kW4NuBabvHnDW9fts7j8PQ2CNWlLGICMcOGF1Qdx5ODIhxJ2AcH
    VuIQt0xPPnzxO1VCY8WSBO8Bp/axRw==
  """
      ]
    },
])

__all__ = ['COMPRESSION_TEST_DATA', 'RANDOM_128KB']
