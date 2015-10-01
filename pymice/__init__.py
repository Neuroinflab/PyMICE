#!/usr/bin/env python
# encoding: utf-8
###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) 2012-2015 Jakub M. Kowalski, S. Łęski (Laboratory of       #
#    Neuroinformatics; Nencki Institute of Experimental Biology)              #
#                                                                             #
#    This software is free software: you can redistribute it and/or modify    #
#    it under the terms of the GNU General Public License as published by     #
#    the Free Software Foundation, either version 3 of the License, or        #
#    (at your option) any later version.                                      #
#                                                                             #
#    This software is distributed in the hope that it will be useful,         #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of           #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            #
#    GNU General Public License for more details.                             #
#                                                                             #
#    You should have received a copy of the GNU General Public License        #
#    along with this software.  If not, see http://www.gnu.org/licenses/.     #
#                                                                             #
###############################################################################

"""
pymice package

A collection of tools to access IntelliCage data.
"""

from ._ICData import Loader, Merger
from ._Tools import hTime, convertTime, getTutorialData, warn
from ._Metadata import Phase, ExperimentConfigFile, ExperimentTimeline
from ._Results import ResultsCSV
from .LogAnalyser import (LickometerLogAnalyzer, PresenceLogAnalyzer,
                          TestMiceData, DataValidator)
__NeuroLexID__ = 'nlx_158570'
__version__ = '0.2.1'
__ID__ = __NeuroLexID__ + ' ' + __version__
__all__ = []

__PGP_PUBLIC_KEY__ = """
-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: GnuPG v1

mQINBFYM5AsBEACc7h7ArIrrz36HENTdXp65DVvvYoVniG/yBAMERtGjTy47aucL
HjMQ661e4w2u5+6FCGaMN4V3mki696PR1uix/LwXOy+lZFNjGWvNqgsC4ygYRjmg
lLDHtVEwMTWe4hzFQO0MaENo35PSZspZdOduNSow7ywjmwW/auqQloZ78GCLv1S4
zbe3Ck2D4S9lV4mfcpxUqJ+RI+BGMAEcMhrsJlf36pHnn/WNrwADD0Q5G8dJ4RP/
oW2FzrFbmvYLLWQqgiI2r1SAbJOz6+pCBn5kTaK2BxgeaSysA7NIgVFajqDbEgaH
loAeR/fnzPopiu4MQjKgmlOvfjc9ITc6eStvV1Ve+lJHib6pLw/h1G+fIC2SPDM2
ybJU6CSB4XzcpGlIou38RK+aibFc8Z0SpIt4tbH+WTI5CQPxc1gN8G1Wkiu5oKSM
84uLhoEltqjMphZWfp3TENIYnutXDPCQhVa7vq7hIFeoKK1UScqZMwRGb+raF0as
aqfAaau868piOVUJoPvlohRqc9e+9tnyZElKBCJkXBLZUeyKzXO4icp4l4dHpolU
WQ9ilR3RrM4WqpayxR1FA/rwX1x66UPPJDFP187WUqKHmDwBIFf3TQnDSVU6rkv4
YFJItKoV23UKhX+5QPAU87KGXsdI8AHgZRSTN8Iq3ago+0aQfCZ/41LLFwARAQAB
tHRKYWt1YiBLb3dhbHNraSAoTGFib3JhdG9yeSBvZiBOZXVyb2luZm9ybWF0aWNz
OyBOZW5ja2kgSW5zdGl0dXRlIG9mIEV4cGVyaW1lbnRhbCBCaW9sb2d5KSA8ai5r
b3dhbHNraUBuZW5ja2kuZ292LnBsPokCPgQTAQIAKAUCVgzkCwIbAwUJAeEzgAYL
CQgHAwIGFQgCCQoLBBYCAwECHgECF4AACgkQeE7YK3iX8HVvoxAAkJTS8v1NCsuY
pOYdsCxgvbFigX4WKelJAXKBDbghmeWXNrErcH3rGlQh9smj+uvNrXA1seN1EryV
2nKni70qexDWsLzD8nLM4pCYlJQR5Gp/0UVOnZepEDGpz4cb8xfhAAqdtUQXEyhD
kDaMvj9hX0TmgZgzGOEhiMFyYx8lyJO4TjuYVld080pCFsB8wMuO84vRCsT0if8t
i75A9ZnntfZJLrGouZ90nO5gkdHtrjgmFoZgXVDXYTkOYclCT8obyYgy32iMyTqd
8dHEb8jPHykJ30AO+97JwML+wE1Zaoa2bVUsKq1b2q8zRnAD9LSavyMwC84TDO/t
7iwAmeRGHzD3RRQySLxuhegqRHkf4EJzXv0n5ARuJNiRA9AYCVKEgJzFDkGm+c2u
iJ+SVax14vqj2pivj61Z95jIL9J7QwMrz/HDp/DwawsdCdlu4rygfDrJ7Jveb66G
9hH3XAPegwJUvk2mMTTTXbExQOMBLMaK/AwvyV2mQPQT84erXfCTcVRCprP0HoxN
68/+vfDxcQur1Mbq+Tk+ak3ddg9pXz+YnIXE6WFsLW1tkMD7KQbaT9v2V5dMmDQf
1HbTCS9AZC66E8OpXI/q9Rir9JLBk3EECoAlVs0H6zbcW/TFT918fUGKoVh3aojz
kykPZPIyJ61FmAgV+Q/rBkWxsfQll9+5Ag0EVgzkCwEQALX6atw8T73a3JAhDRta
oJ5Fq5ahrnzNToL+cBvuIwNwq7NmxxW3U72GFSrBUBFZH92TDjSmvjTH4eriKzAn
FhmZA2WaeE6+Y+thhPuO8bm1sScxMLJ1qpCYF+2veLKAAC6fMMG3M3mvlu9Mwv1b
OkWyZZvQzIZxdeaj6nJRt+tLbYUCRIJssjQtxcbG3mp4m/MC7i210R3+YPlvoQSE
Ekrao96SK8O0s6GkLsObKyVh2Ar5rkvV2l8bnpEgayXBp2lWk11gJR5IWk5z2wae
Z4xBudMZlPvmKtdUAelQFTER2pb+OOFD7NXH8kha3lRsLSz2kIoxteGVrC2akrn8
sqhFa6iHiInTDKxCPYsF069VrCur7z3joe+gHRs+N8WTokitGZPNqsUe0R2bmlP+
8v5WfARTWXtuqGPGIHN7gk2lQV9pRYr4uX2d6Pdm378Kz8Hj8Kf32XK7rz6176tP
uBtdOToaGUdYfPD3fOgtvEWg+WYl2SXhMBCYrHy8200bh7wH/LZz7SdNelCTkdnE
LVNV3cTXVH8/uKS/RY8qF6vtkaKijANHl2mMvcwF6VPzGSa27c44pxfwOceHDOpl
Q2WwOlCAuDrghTklGAO22PFLav6OrIZi/SIxesO1TrXP/Q8UsMWPnBK/wYKnnwmA
/BMMLxJzbt2mApBOFSTkL3D5ABEBAAGJAiUEGAECAA8FAlYM5AsCGwwFCQHhM4AA
CgkQeE7YK3iX8HXT5BAAhK/TA8ObEI5tjQptpvgNrgsPFVhzHKmpmxxztRLg8t6w
s5/sriKVIrmzIGyhuhbEMOmh51wNEnu2PR4tZLYDEN8vPJbrcSqF5mcq4uUOv7+H
9SMCWtEfme1oX6ZCbE8DMpiEsYxEQk0p/SR7nSXOLmr8bf6d0BqAmBKBH5frjBJg
W9bHE+MVLR5aM/L+smMxlgouSweL6i8EtSJcCag8iqLj8R/90jEhoSNeacRReqGe
3I7x611W6F/hUlTwxMP2r1OU/J4LF+wIZrm2mUp1m8ovDkKFUP1w/rYtq3ijlkNM
/OxKx/3kGuy3gaFVZzloDqRuUuzVGqML44I3+M0MZJQjlZnfcFxsuL+zrXi8KDen
yDY2y9z9Tn29ywDPxYq9LwAedbr6bp+VWZPJI4UNBoiYQCW5TcfUuis4IwijNFCM
KhimVn/jDmMTaFFxy97ZKV2XSB3oVdPfaQ9bcPEPDCnEZ2exv0al1IwI1ptaiRz5
BQ4nlqTYx1jSjHmK2bayU7akT0/RrAipO29gy3f1nfzjn1e8uqzR7Wj+m5iwjX2E
3FQLkoN2+YChYGCNoO0/8PAE7U8bSLwW3AqFDYdTBtulvz1iy+FohRC67G7zbiCd
DT4L7Vi4l+wex6u695AC7tFSLk+9ag9m5yA0gZLV2BolCzU8DFHt5aS86Rp1cYA=
=4J/5
-----END PGP PUBLIC KEY BLOCK-----
"""

__welcomeMessage = """PyMICE library v. %s
(NeuroLex.org ID: %s)

This is a bleeding edge version of the library. It might meet your expectations,
however it might also go to your fridge, drink all the beer it can find there
and then eat your cat. Be warned.
""" % (__version__, __NeuroLexID__)
print(__welcomeMessage)
