#!/usr/bin/env python
# encoding: utf-8
###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) 2017 Jakub M. Dzik a.k.a. Kowalski (Laboratory of          #
#    Neuroinformatics; Nencki Institute of Experimental Biology of Polish     #
#    Academy of Sciences)                                                     #
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
import sys
import unittest
from unittest import TestCase
import functools

import pymice as pm
from pymice._Bibliography import Citation


def requireMarkdown(f):
    @functools.wraps(f)
    def wrapper(self):
        try:
            markdown = self.MARKDOWN
        except AttributeError:
            self.skipTest('no markdown given')
        else:
            return f(self, markdown)

    return wrapper


class TestCitationBase(TestCase):
    MAX_LINE_WIDTH = None

    if sys.version_info.major < 3:
        def checkUnicodeEqual(self, expected, observed):
            self.maxDiff = None
            try:
                self.assertEqual(expected, observed)
            except AssertionError:
                for i, (a, b) in enumerate(zip(expected, observed)):
                    if a != b:
                        print(u'\n{} ({} != {})'.format(expected[:i], ord(a), ord(b)))
                        break
                raise
            self.assertIsInstance(observed, unicode)

        def checkStrEqual(self, expected, observed):
            self.assertEqual(expected.encode('utf-8'), observed)
            self.assertIsInstance(observed, str)

        def checkToString(self, expected, observed):
            self.checkStrEqual(expected, str(observed))
            self.checkUnicodeEqual(expected, unicode(observed))

    else:
        def checkUnicodeEqual(self, expected, observed):
            self.assertEqual(expected, observed)
            self.assertIsInstance(observed, str)

        def checkToString(self, expected, observed):
            self.checkUnicodeEqual(expected, str(observed))

    def setUp(self):
        self.maxDiff = None
        try:
            style = self.STYLE
        except AttributeError:
            self.skipTest('generic test called')
        else:
            self.reference = self.Citation(style)

    def Citation(self, style, _noMaxLineWidth=False, **kwargs):
        if 'markdown' not in kwargs:
            try:
                kwargs['markdown'] = self.MARKDOWN

            except AttributeError:
                pass

        try:
            kwargs['paperKey'] = self.PAPER_KEY

        except AttributeError:
            pass

        try:
            kwargs['softwareKey'] = self.SOFTWARE_KEY

        except AttributeError:
            pass

        if _noMaxLineWidth:
            return Citation(style, **kwargs)

        return Citation(style,
                        maxLineWidth=self.MAX_LINE_WIDTH,
                        **kwargs)

    def testSoftwareReferenceCurrentVersionIsDefault(self):
        self.checkUnicodeEqual(self.SOFTWARE[pm.__version__],
                               self.reference.referenceSoftware(style=self.STYLE))

    def testSoftwareReferenceDefaultStyleIsGivenInConstructor(self):
        self.checkUnicodeEqual(self.SOFTWARE[pm.__version__],
                               self.reference.referenceSoftware())

    def testSoftwareReferenceDefaultVersionIsGivenInConstructor(self):
        for version, expected in self.SOFTWARE.items():
            self.checkUnicodeEqual(expected,
                                   self.Citation(self.STYLE,
                                                 version=version).referenceSoftware())

    def testSoftwareReferenceArgumentOverridesConstructorVersion(self):
        for version, expected in self.SOFTWARE.items():
            self.checkUnicodeEqual(expected,
                                   self.reference.referenceSoftware(version=version))

    def testSoftwareReferenceArgumentOverridesConstructorVersionAndStyle(self):
        for version, expected in self.SOFTWARE.items():
            self.checkUnicodeEqual(expected,
                                   self.Citation('__unknown__').referenceSoftware(version=version,
                                                                                  style=self.STYLE))

    @requireMarkdown
    def testSoftwareReferenceArgumentOverridesConstructorMarkdown(self, markdown):
        for version, expected in self.SOFTWARE.items():
            self.checkUnicodeEqual(expected,
                                   self.Citation(markdown='__unknown__',
                                                 style=self.STYLE,
                                                 version=version).referenceSoftware(markdown=markdown))

    def testSoftwareReferenceProperty(self):
        for version, expected in self.SOFTWARE.items():
            self.checkUnicodeEqual(expected,
                                   self.Citation(self.STYLE,
                                                 version=version).SOFTWARE)

    def testDefaultToString(self):
        self.checkToString(self.CITE_PYMICE[pm.__version__],
                           self.reference)

    def testToString(self):
        for version, expected in self.CITE_PYMICE.items():
            self.checkToString(expected,
                               self.Citation(self.STYLE,
                                             version=version))

    def testCitePymiceCurrentVersionIsDefault(self):
        self.checkUnicodeEqual(self.CITE_PYMICE[pm.__version__],
                               self.reference.cite(style=self.STYLE))

    def testCitePymiceDefaultVersionAndStyleGivenInConstructor(self):
        for version, expected in self.CITE_PYMICE.items():
            self.checkUnicodeEqual(expected,
                                   self.Citation(style=self.STYLE,
                                                 version=version).cite())

    def testCitePymiceArgumentOverridesVersion(self):
        for version, expected in self.CITE_PYMICE.items():
            self.checkUnicodeEqual(expected,
                                   self.reference.cite(version=version))

    def testCitePymiceArgumentOverridesConstructorVersionAndStyle(self):
        for version, expected in self.CITE_PYMICE.items():
            self.checkUnicodeEqual(expected,
                                   self.Citation('__unknown__').cite(version=version,
                                                                     style=self.STYLE))

    @requireMarkdown
    def testCitePymiceArgumentOverridesConstructorMarkdown(self, markdown):
        for version, expected in self.CITE_PYMICE.items():
            self.checkUnicodeEqual(expected,
                                   self.Citation(markdown='__unknown__',
                                                 style=self.STYLE,
                                                 version=version).cite(markdown=markdown))

    def testCiteSoftwarePropertyDefault(self):
        self.checkUnicodeEqual(self.CITE_SOFTWARE[pm.__version__],
                               self.reference.CITE_SOFTWARE)

    def testCiteSoftwareProperty(self):
        for version, expected in self.CITE_SOFTWARE.items():
            self.checkUnicodeEqual(expected,
                                   self.Citation(self.STYLE,
                                                 version=version).CITE_SOFTWARE)

    def testCiteSoftwareCurrentVersionIsDefault(self):
        self.checkUnicodeEqual(self.CITE_SOFTWARE[pm.__version__],
                               self.reference.citeSoftware(style=self.STYLE))

    def testCiteSoftwareDefaultVersionAndStyleGivenInConstructor(self):
        for version, expected in self.CITE_SOFTWARE.items():
            self.checkUnicodeEqual(expected,
                                   self.Citation(style=self.STYLE,
                                                 version=version).citeSoftware())

    def testCiteSoftwareArgumentOverridesVersion(self):
        for version, expected in self.CITE_SOFTWARE.items():
            self.checkUnicodeEqual(expected,
                                   self.reference.citeSoftware(version=version))

    def testCiteSoftwareArgumentOverridesConstructorVersionAndStyle(self):
        for version, expected in self.CITE_SOFTWARE.items():
            self.checkUnicodeEqual(expected,
                                   self.Citation('__unknown__').citeSoftware(version=version,
                                                                     style=self.STYLE))

    @requireMarkdown
    def testCiteSoftwareArgumentOverridesConstructorMarkdown(self, markdown):
        for version, expected in self.CITE_SOFTWARE.items():
            self.checkUnicodeEqual(expected,
                                   self.Citation(markdown='__unknown__',
                                                 style=self.STYLE,
                                                 version=version).citeSoftware(markdown=markdown))


    def testCitePaperProperty(self):
        self.checkUnicodeEqual(self.CITE_PAPER,
                               self.reference.CITE_PAPER)

    def testCitePaper(self):
        self.checkUnicodeEqual(self.CITE_PAPER,
                               self.reference.citePaper())

    def testCitePaperArgumentOverridesConstructorStyle(self):
        self.checkUnicodeEqual(self.CITE_PAPER,
                               self.Citation('__unknown__').citePaper(style=self.STYLE))

    @requireMarkdown
    def testCitePaperArgumentOverridesConstructorMarkdown(self, markdown):
        self.checkUnicodeEqual(self.CITE_PAPER,
                               self.Citation(markdown='__unknown__',
                                             style=self.STYLE).citePaper(markdown=markdown))


    def testPaperReferenceDefaultStyleAndMarkdownSetInConstructor(self):
        self.checkUnicodeEqual(self.PAPER,
                               self.reference.referencePaper())

    def testPaperReferenceProperty(self):
        self.checkUnicodeEqual(self.PAPER,
                               self.reference.PAPER)

    def testPaperReferenceArgumentOverridesConstructorStyle(self):
        self.checkUnicodeEqual(self.PAPER,
                               self.Citation('__unknown__').referencePaper(style=self.STYLE))

    @requireMarkdown
    def testPaperReferenceArgumentOverridesConstructorMarkdown(self, markdown):
        self.checkUnicodeEqual(self.PAPER,
                               self.Citation(self.STYLE,
                                             markdown='__unknown__').referencePaper(markdown=markdown))


class TestCitationGivenStyleAPA6(TestCitationBase):
    STYLE = 'apa6'
    SOFTWARE = {'1.2.0': u"Dzik,\xa0J.\xa0M., Łęski,\xa0S., &\xa0Puścian,\xa0A. (2017,\xa0July). PyMICE (v.\xa01.2.0) [computer software; RRID:nlx_158570]. doi:\xa010.5281/zenodo.832982",
                '1.1.1': u"Dzik,\xa0J.\xa0M., Łęski,\xa0S., &\xa0Puścian,\xa0A. (2017,\xa0April). PyMICE (v.\xa01.1.1) [computer software; RRID:nlx_158570]. doi:\xa010.5281/zenodo.557087",
                '1.1.0': u"Dzik,\xa0J.\xa0M., Łęski,\xa0S., &\xa0Puścian,\xa0A. (2016,\xa0December). PyMICE (v.\xa01.1.0) [computer software; RRID:nlx_158570]. doi:\xa010.5281/zenodo.200648",
                '1.0.0': u"Dzik,\xa0J.\xa0M., Łęski,\xa0S., &\xa0Puścian,\xa0A. (2016,\xa0May). PyMICE (v.\xa01.0.0) [computer software; RRID:nlx_158570]. doi:\xa010.5281/zenodo.51092",
                '0.2.5': u"Dzik,\xa0J.\xa0M., Łęski,\xa0S., &\xa0Puścian,\xa0A. (2016,\xa0April). PyMICE (v.\xa00.2.5) [computer software; RRID:nlx_158570]. doi:\xa010.5281/zenodo.49550",
                '0.2.4': u"Dzik,\xa0J.\xa0M., Łęski,\xa0S., &\xa0Puścian,\xa0A. (2016,\xa0January). PyMICE (v.\xa00.2.4) [computer software; RRID:nlx_158570]. doi:\xa010.5281/zenodo.47305",
                '0.2.3': u"Dzik,\xa0J.\xa0M., Łęski,\xa0S., &\xa0Puścian,\xa0A. (2016,\xa0January). PyMICE (v.\xa00.2.3) [computer software; RRID:nlx_158570]. doi:\xa010.5281/zenodo.47259",
                'unknown': u"Dzik,\xa0J.\xa0M., Łęski,\xa0S., &\xa0Puścian,\xa0A. (n.d.). PyMICE (v.\xa0unknown) [computer software; RRID:nlx_158570]",
                }
    CITE_PYMICE = {'1.2.0': u"PyMICE\xa0(Dzik, Puścian, Mijakowska, Radwanska, &\xa0Łęski, 2017) v.\xa01.2.0\xa0(Dzik, Łęski, &\xa0Puścian, 2017)",
                   '1.1.1': u"PyMICE\xa0(Dzik, Puścian, Mijakowska, Radwanska, &\xa0Łęski, 2017) v.\xa01.1.1\xa0(Dzik, Łęski, &\xa0Puścian, 2017)",
                   '1.1.0': u"PyMICE\xa0(Dzik, Puścian, Mijakowska, Radwanska, &\xa0Łęski, 2017) v.\xa01.1.0\xa0(Dzik, Łęski, &\xa0Puścian, 2016)",
                   'unknown': u"PyMICE\xa0(Dzik, Puścian, Mijakowska, Radwanska, &\xa0Łęski, 2017) v.\xa0unknown\xa0(Dzik, Łęski, &\xa0Puścian, n.d.)",
                   None: u"PyMICE\xa0(Dzik, Puścian, Mijakowska, Radwanska, &\xa0Łęski, 2017; Dzik, Łęski, &\xa0Puścian, n.d.)",
                   }
    CITE_PAPER = u"Dzik, Puścian, Mijakowska, Radwanska, &\xa0Łęski, 2017"
    CITE_SOFTWARE = {'1.2.0': u"Dzik, Łęski, &\xa0Puścian, 2017",
                     '1.1.1': u"Dzik, Łęski, &\xa0Puścian, 2017",
                     '1.1.0': u"Dzik, Łęski, &\xa0Puścian, 2016",
                     'unknown': u"Dzik, Łęski, &\xa0Puścian, n.d.",
                     None: u"Dzik, Łęski, &\xa0Puścian, n.d.",
                     }
    PAPER = u"Dzik,\xa0J.\xa0M., Puścian,\xa0A., Mijakowska,\xa0Z., Radwanska,\xa0K., &\xa0Łęski,\xa0S. (2017). PyMICE: A Python library for analysis of IntelliCage data. Behavior Research Methods. doi:\xa010.3758/s13428-017-0907-5"


class TestDefaultLineWidthLimitIs80_GivenStyleAPA6(TestCitationGivenStyleAPA6):
    def Citation(self, style, **kwargs):
        return super(TestDefaultLineWidthLimitIs80_GivenStyleAPA6,
                     self).Citation(style,
                                    _noMaxLineWidth=True,
                                    **kwargs)

    SOFTWARE = {'1.2.0': u"Dzik,\xa0J.\xa0M., Łęski,\xa0S., &\xa0Puścian,\xa0A. (2017,\xa0July). PyMICE (v.\xa01.2.0) [computer\n    software; RRID:nlx_158570]. doi:\xa010.5281/zenodo.832982",
                '1.1.1': u"Dzik,\xa0J.\xa0M., Łęski,\xa0S., &\xa0Puścian,\xa0A. (2017,\xa0April). PyMICE (v.\xa01.1.1) [computer\n    software; RRID:nlx_158570]. doi:\xa010.5281/zenodo.557087",
                '1.1.0': u"Dzik,\xa0J.\xa0M., Łęski,\xa0S., &\xa0Puścian,\xa0A. (2016,\xa0December). PyMICE (v.\xa01.1.0)\n    [computer software; RRID:nlx_158570]. doi:\xa010.5281/zenodo.200648",
                '1.0.0': u"Dzik,\xa0J.\xa0M., Łęski,\xa0S., &\xa0Puścian,\xa0A. (2016,\xa0May). PyMICE (v.\xa01.0.0) [computer\n    software; RRID:nlx_158570]. doi:\xa010.5281/zenodo.51092",
                '0.2.5': u"Dzik,\xa0J.\xa0M., Łęski,\xa0S., &\xa0Puścian,\xa0A. (2016,\xa0April). PyMICE (v.\xa00.2.5) [computer\n    software; RRID:nlx_158570]. doi:\xa010.5281/zenodo.49550",
                '0.2.4': u"Dzik,\xa0J.\xa0M., Łęski,\xa0S., &\xa0Puścian,\xa0A. (2016,\xa0January). PyMICE (v.\xa00.2.4)\n    [computer software; RRID:nlx_158570]. doi:\xa010.5281/zenodo.47305",
                '0.2.3': u"Dzik,\xa0J.\xa0M., Łęski,\xa0S., &\xa0Puścian,\xa0A. (2016,\xa0January). PyMICE (v.\xa00.2.3)\n    [computer software; RRID:nlx_158570]. doi:\xa010.5281/zenodo.47259",
                'unknown': u"Dzik,\xa0J.\xa0M., Łęski,\xa0S., &\xa0Puścian,\xa0A. (n.d.). PyMICE (v.\xa0unknown) [computer\n    software; RRID:nlx_158570]",
                }
    PAPER = u"Dzik,\xa0J.\xa0M., Puścian,\xa0A., Mijakowska,\xa0Z., Radwanska,\xa0K., &\xa0Łęski,\xa0S. (2017).\n    PyMICE: A Python library for analysis of IntelliCage data. Behavior Research\n    Methods. doi:\xa010.3758/s13428-017-0907-5"


class TestCitationGivenStyleAPA6markdownTXT(TestCitationGivenStyleAPA6):
    MARKDOWN = 'txt'


class TestCitationGivenStyleAPA6markdownLaTeX(TestCitationGivenStyleAPA6):
    MARKDOWN = 'latex'
    SOFTWARE = {'1.2.0': u"\\bibitem{pymice1.2.0} Dzik,~J.~M., Łęski,~S., &~Puścian,~A. (2017,~July). PyMICE (v.~1.2.0) [computer software; RRID:nlx\_158570]. doi:~10.5281/zenodo.832982",
                '1.1.1': u"\\bibitem{pymice1.1.1} Dzik,~J.~M., Łęski,~S., &~Puścian,~A. (2017,~April). PyMICE (v.~1.1.1) [computer software; RRID:nlx\_158570]. doi:~10.5281/zenodo.557087",
                '1.1.0': u"\\bibitem{pymice1.1.0} Dzik,~J.~M., Łęski,~S., &~Puścian,~A. (2016,~December). PyMICE (v.~1.1.0) [computer software; RRID:nlx\_158570]. doi:~10.5281/zenodo.200648",
                '1.0.0': u"\\bibitem{pymice1.0.0} Dzik,~J.~M., Łęski,~S., &~Puścian,~A. (2016,~May). PyMICE (v.~1.0.0) [computer software; RRID:nlx\_158570]. doi:~10.5281/zenodo.51092",
                '0.2.5': u"\\bibitem{pymice0.2.5} Dzik,~J.~M., Łęski,~S., &~Puścian,~A. (2016,~April). PyMICE (v.~0.2.5) [computer software; RRID:nlx\_158570]. doi:~10.5281/zenodo.49550",
                '0.2.4': u"\\bibitem{pymice0.2.4} Dzik,~J.~M., Łęski,~S., &~Puścian,~A. (2016,~January). PyMICE (v.~0.2.4) [computer software; RRID:nlx\_158570]. doi:~10.5281/zenodo.47305",
                '0.2.3': u"\\bibitem{pymice0.2.3} Dzik,~J.~M., Łęski,~S., &~Puścian,~A. (2016,~January). PyMICE (v.~0.2.3) [computer software; RRID:nlx\_158570]. doi:~10.5281/zenodo.47259",
                'unknown': u"\\bibitem{pymiceunknown} Dzik,~J.~M., Łęski,~S., &~Puścian,~A. (n.d.). PyMICE (v.~unknown) [computer software; RRID:nlx\_158570]",
                None: u"\\bibitem{pymice} Dzik,~J.~M., Łęski,~S., &~Puścian,~A. (n.d.). PyMICE [computer software; RRID:nlx\_158570]",
                }
    CITE_PYMICE = {'1.2.0': u"\\emph{PyMICE}~\\cite{dzik2017pm} v.~1.2.0~\\cite{pymice1.2.0}",
                   '1.1.1': u"\\emph{PyMICE}~\\cite{dzik2017pm} v.~1.1.1~\\cite{pymice1.1.1}",
                   'unknown': u"\\emph{PyMICE}~\\cite{dzik2017pm} v.~unknown~\\cite{pymiceunknown}",
                   None: u"\\emph{PyMICE}~\\cite{dzik2017pm,pymice}",
                   }
    CITE_PAPER = u"dzik2017pm"
    CITE_SOFTWARE = {'1.2.0': u"pymice1.2.0",
                     '1.1.1': u"pymice1.1.1",
                     'unknown': u"pymiceunknown",
                     None: u"pymice",
                     }
    PAPER = u"\\bibitem{dzik2017pm} Dzik,~J.~M., Puścian,~A., Mijakowska,~Z., Radwanska,~K., &~Łęski,~S. (2017). {PyMICE}: A {Python} library for analysis of {IntelliCage} data. \emph{Behavior Research Methods}. doi:~10.3758/s13428-017-0907-5"


class TestCitationGivenStyleAPA6markdownLaTeXcustomKeys(TestCitationGivenStyleAPA6markdownLaTeX):
    PAPER_KEY = 'dzikPaper'
    SOFTWARE_KEY = 'dzikSoft'

    SOFTWARE = {'1.2.0': u"\\bibitem{dzikSoft} Dzik,~J.~M., Łęski,~S., &~Puścian,~A. (2017,~July). PyMICE (v.~1.2.0) [computer software; RRID:nlx\_158570]. doi:~10.5281/zenodo.832982",
                '1.1.1': u"\\bibitem{dzikSoft} Dzik,~J.~M., Łęski,~S., &~Puścian,~A. (2017,~April). PyMICE (v.~1.1.1) [computer software; RRID:nlx\_158570]. doi:~10.5281/zenodo.557087",
                '1.1.0': u"\\bibitem{dzikSoft} Dzik,~J.~M., Łęski,~S., &~Puścian,~A. (2016,~December). PyMICE (v.~1.1.0) [computer software; RRID:nlx\_158570]. doi:~10.5281/zenodo.200648",
                '1.0.0': u"\\bibitem{dzikSoft} Dzik,~J.~M., Łęski,~S., &~Puścian,~A. (2016,~May). PyMICE (v.~1.0.0) [computer software; RRID:nlx\_158570]. doi:~10.5281/zenodo.51092",
                '0.2.5': u"\\bibitem{dzikSoft} Dzik,~J.~M., Łęski,~S., &~Puścian,~A. (2016,~April). PyMICE (v.~0.2.5) [computer software; RRID:nlx\_158570]. doi:~10.5281/zenodo.49550",
                '0.2.4': u"\\bibitem{dzikSoft} Dzik,~J.~M., Łęski,~S., &~Puścian,~A. (2016,~January). PyMICE (v.~0.2.4) [computer software; RRID:nlx\_158570]. doi:~10.5281/zenodo.47305",
                '0.2.3': u"\\bibitem{dzikSoft} Dzik,~J.~M., Łęski,~S., &~Puścian,~A. (2016,~January). PyMICE (v.~0.2.3) [computer software; RRID:nlx\_158570]. doi:~10.5281/zenodo.47259",
                'unknown': u"\\bibitem{dzikSoft} Dzik,~J.~M., Łęski,~S., &~Puścian,~A. (n.d.). PyMICE (v.~unknown) [computer software; RRID:nlx\_158570]",
                None: u"\\bibitem{dzikSoft} Dzik,~J.~M., Łęski,~S., &~Puścian,~A. (n.d.). PyMICE [computer software; RRID:nlx\_158570]",
                }
    CITE_PYMICE = {'1.2.0': u"\\emph{PyMICE}~\\cite{dzikPaper} v.~1.2.0~\\cite{dzikSoft}",
                   '1.1.1': u"\\emph{PyMICE}~\\cite{dzikPaper} v.~1.1.1~\\cite{dzikSoft}",
                   'unknown': u"\\emph{PyMICE}~\\cite{dzikPaper} v.~unknown~\\cite{dzikSoft}",
                   None: u"\\emph{PyMICE}~\\cite{dzikPaper,dzikSoft}",
                   }
    CITE_PAPER = u"dzikPaper"
    CITE_SOFTWARE = {k: u"dzikSoft" for k in SOFTWARE}
    PAPER = u"\\bibitem{dzikPaper} Dzik,~J.~M., Puścian,~A., Mijakowska,~Z., Radwanska,~K., &~Łęski,~S. (2017). {PyMICE}: A {Python} library for analysis of {IntelliCage} data. \emph{Behavior Research Methods}. doi:~10.3758/s13428-017-0907-5"


class TestCitationGivenStyleAPA6markdownMD(TestCitationGivenStyleAPA6):
    MARKDOWN = 'md'
    SOFTWARE = {'1.2.0': u"Dzik,\xa0J.\xa0M., Łęski,\xa0S., &\xa0Puścian,\xa0A. (2017,\xa0July). PyMICE (v.\xa01.2.0) [computer software; RRID:nlx\\_158570]. doi:\xa010.5281/zenodo.832982",
                '1.1.1': u"Dzik,\xa0J.\xa0M., Łęski,\xa0S., &\xa0Puścian,\xa0A. (2017,\xa0April). PyMICE (v.\xa01.1.1) [computer software; RRID:nlx\\_158570]. doi:\xa010.5281/zenodo.557087",
                '1.1.0': u"Dzik,\xa0J.\xa0M., Łęski,\xa0S., &\xa0Puścian,\xa0A. (2016,\xa0December). PyMICE (v.\xa01.1.0) [computer software; RRID:nlx\\_158570]. doi:\xa010.5281/zenodo.200648",
                '1.0.0': u"Dzik,\xa0J.\xa0M., Łęski,\xa0S., &\xa0Puścian,\xa0A. (2016,\xa0May). PyMICE (v.\xa01.0.0) [computer software; RRID:nlx\\_158570]. doi:\xa010.5281/zenodo.51092",
                '0.2.5': u"Dzik,\xa0J.\xa0M., Łęski,\xa0S., &\xa0Puścian,\xa0A. (2016,\xa0April). PyMICE (v.\xa00.2.5) [computer software; RRID:nlx\\_158570]. doi:\xa010.5281/zenodo.49550",
                '0.2.4': u"Dzik,\xa0J.\xa0M., Łęski,\xa0S., &\xa0Puścian,\xa0A. (2016,\xa0January). PyMICE (v.\xa00.2.4) [computer software; RRID:nlx\\_158570]. doi:\xa010.5281/zenodo.47305",
                '0.2.3': u"Dzik,\xa0J.\xa0M., Łęski,\xa0S., &\xa0Puścian,\xa0A. (2016,\xa0January). PyMICE (v.\xa00.2.3) [computer software; RRID:nlx\\_158570]. doi:\xa010.5281/zenodo.47259",
                'unknown': u"Dzik,\xa0J.\xa0M., Łęski,\xa0S., &\xa0Puścian,\xa0A. (n.d.). PyMICE (v.\xa0unknown) [computer software; RRID:nlx\\_158570]",
                }
    PAPER = u"Dzik,\xa0J.\xa0M., Puścian,\xa0A., Mijakowska,\xa0Z., Radwanska,\xa0K., &\xa0Łęski,\xa0S. (2017). PyMICE: A Python library for analysis of IntelliCage data. _Behavior Research Methods_. doi:\xa010.3758/s13428-017-0907-5"


class TestCitationGivenStyleAPA6markdownRST(TestCitationGivenStyleAPA6):
    MARKDOWN = 'rst'
    SOFTWARE = {'1.2.0': u"Dzik,\xa0J.\xa0M., Łęski,\xa0S., &\xa0Puścian,\xa0A. (2017,\xa0July). PyMICE (v.\xa01.2.0) [computer software; RRID:nlx\\_158570]. doi:\xa010.5281/zenodo.832982",
                '1.1.1': u"Dzik,\xa0J.\xa0M., Łęski,\xa0S., &\xa0Puścian,\xa0A. (2017,\xa0April). PyMICE (v.\xa01.1.1) [computer software; RRID:nlx\\_158570]. doi:\xa010.5281/zenodo.557087",
                '1.1.0': u"Dzik,\xa0J.\xa0M., Łęski,\xa0S., &\xa0Puścian,\xa0A. (2016,\xa0December). PyMICE (v.\xa01.1.0) [computer software; RRID:nlx\\_158570]. doi:\xa010.5281/zenodo.200648",
                '1.0.0': u"Dzik,\xa0J.\xa0M., Łęski,\xa0S., &\xa0Puścian,\xa0A. (2016,\xa0May). PyMICE (v.\xa01.0.0) [computer software; RRID:nlx\\_158570]. doi:\xa010.5281/zenodo.51092",
                '0.2.5': u"Dzik,\xa0J.\xa0M., Łęski,\xa0S., &\xa0Puścian,\xa0A. (2016,\xa0April). PyMICE (v.\xa00.2.5) [computer software; RRID:nlx\\_158570]. doi:\xa010.5281/zenodo.49550",
                '0.2.4': u"Dzik,\xa0J.\xa0M., Łęski,\xa0S., &\xa0Puścian,\xa0A. (2016,\xa0January). PyMICE (v.\xa00.2.4) [computer software; RRID:nlx\\_158570]. doi:\xa010.5281/zenodo.47305",
                '0.2.3': u"Dzik,\xa0J.\xa0M., Łęski,\xa0S., &\xa0Puścian,\xa0A. (2016,\xa0January). PyMICE (v.\xa00.2.3) [computer software; RRID:nlx\\_158570]. doi:\xa010.5281/zenodo.47259",
                'unknown': u"Dzik,\xa0J.\xa0M., Łęski,\xa0S., &\xa0Puścian,\xa0A. (n.d.). PyMICE (v.\xa0unknown) [computer software; RRID:nlx\\_158570]",
                }
    PAPER = u"Dzik,\xa0J.\xa0M., Puścian,\xa0A., Mijakowska,\xa0Z., Radwanska,\xa0K., &\xa0Łęski,\xa0S. (2017). PyMICE: A Python library for analysis of IntelliCage data. *Behavior Research Methods*. doi:\xa010.3758/s13428-017-0907-5"


class TestCitationGivenStyleAPA6markdownHTML(TestCitationGivenStyleAPA6):
    MARKDOWN = 'html'
    SOFTWARE = {'1.2.0': u"Dzik,&nbsp;J.&nbsp;M., Łęski,&nbsp;S., &amp;&nbsp;Puścian,&nbsp;A. (2017,&nbsp;July). PyMICE (v.&nbsp;1.2.0) [computer software; RRID:nlx_158570]. doi:&nbsp;10.5281/zenodo.832982",
                '1.1.1': u"Dzik,&nbsp;J.&nbsp;M., Łęski,&nbsp;S., &amp;&nbsp;Puścian,&nbsp;A. (2017,&nbsp;April). PyMICE (v.&nbsp;1.1.1) [computer software; RRID:nlx_158570]. doi:&nbsp;10.5281/zenodo.557087",
                '1.1.0': u"Dzik,&nbsp;J.&nbsp;M., Łęski,&nbsp;S., &amp;&nbsp;Puścian,&nbsp;A. (2016,&nbsp;December). PyMICE (v.&nbsp;1.1.0) [computer software; RRID:nlx_158570]. doi:&nbsp;10.5281/zenodo.200648",
                '1.0.0': u"Dzik,&nbsp;J.&nbsp;M., Łęski,&nbsp;S., &amp;&nbsp;Puścian,&nbsp;A. (2016,&nbsp;May). PyMICE (v.&nbsp;1.0.0) [computer software; RRID:nlx_158570]. doi:&nbsp;10.5281/zenodo.51092",
                '0.2.5': u"Dzik,&nbsp;J.&nbsp;M., Łęski,&nbsp;S., &amp;&nbsp;Puścian,&nbsp;A. (2016,&nbsp;April). PyMICE (v.&nbsp;0.2.5) [computer software; RRID:nlx_158570]. doi:&nbsp;10.5281/zenodo.49550",
                '0.2.4': u"Dzik,&nbsp;J.&nbsp;M., Łęski,&nbsp;S., &amp;&nbsp;Puścian,&nbsp;A. (2016,&nbsp;January). PyMICE (v.&nbsp;0.2.4) [computer software; RRID:nlx_158570]. doi:&nbsp;10.5281/zenodo.47305",
                '0.2.3': u"Dzik,&nbsp;J.&nbsp;M., Łęski,&nbsp;S., &amp;&nbsp;Puścian,&nbsp;A. (2016,&nbsp;January). PyMICE (v.&nbsp;0.2.3) [computer software; RRID:nlx_158570]. doi:&nbsp;10.5281/zenodo.47259",
                'unknown': u"Dzik,&nbsp;J.&nbsp;M., Łęski,&nbsp;S., &amp;&nbsp;Puścian,&nbsp;A. (n.d.). PyMICE (v.&nbsp;unknown) [computer software; RRID:nlx_158570]",
                }
    CITE_PYMICE = {'1.2.0': u"PyMICE&nbsp;(Dzik, Puścian, Mijakowska, Radwanska, &amp;&nbsp;Łęski, 2017) v.&nbsp;1.2.0&nbsp;(Dzik, Łęski, &amp;&nbsp;Puścian, 2017)",
                   '1.1.1': u"PyMICE&nbsp;(Dzik, Puścian, Mijakowska, Radwanska, &amp;&nbsp;Łęski, 2017) v.&nbsp;1.1.1&nbsp;(Dzik, Łęski, &amp;&nbsp;Puścian, 2017)",
                   '1.1.0': u"PyMICE&nbsp;(Dzik, Puścian, Mijakowska, Radwanska, &amp;&nbsp;Łęski, 2017) v.&nbsp;1.1.0&nbsp;(Dzik, Łęski, &amp;&nbsp;Puścian, 2016)",
                   'unknown': u"PyMICE&nbsp;(Dzik, Puścian, Mijakowska, Radwanska, &amp;&nbsp;Łęski, 2017) v.&nbsp;unknown&nbsp;(Dzik, Łęski, &amp;&nbsp;Puścian, n.d.)",
                   None: u"PyMICE&nbsp;(Dzik, Puścian, Mijakowska, Radwanska, &amp;&nbsp;Łęski, 2017; Dzik, Łęski, &amp;&nbsp;Puścian, n.d.)",
                   }
    CITE_PAPER = u"Dzik, Puścian, Mijakowska, Radwanska, &amp;&nbsp;Łęski, 2017"
    CITE_SOFTWARE = {'1.2.0': u"Dzik, Łęski, &amp;&nbsp;Puścian, 2017",
                     '1.1.1': u"Dzik, Łęski, &amp;&nbsp;Puścian, 2017",
                     '1.1.0': u"Dzik, Łęski, &amp;&nbsp;Puścian, 2016",
                     'unknown': u"Dzik, Łęski, &amp;&nbsp;Puścian, n.d.",
                     None: u"Dzik, Łęski, &amp;&nbsp;Puścian, n.d.",
                     }
    PAPER = u"Dzik,&nbsp;J.&nbsp;M., Puścian,&nbsp;A., Mijakowska,&nbsp;Z., Radwanska,&nbsp;K., &amp;&nbsp;Łęski,&nbsp;S. (2017). PyMICE: A Python library for analysis of IntelliCage data. <em>Behavior Research Methods</em>. doi:&nbsp;10.3758/s13428-017-0907-5"


class TestCitationGivenStyleBibTeX(TestCitationBase):
    STYLE = 'bibtex'
    SOFTWARE = {'1.2.0': u"@Misc{pymice1.2.0,\nTitle = {{PyMICE (v.~1.2.0)}},\nNote = {computer software; RRID:nlx\\_158570},\nAuthor = {Dzik, Jakub Mateusz and Łęski, Szymon and Puścian, Alicja},\nYear = {2017},\nMonth = {July},\nDay = {21},\nDoi = {10.5281/zenodo.832982}\n}\n",
                '1.1.1': u"@Misc{pymice1.1.1,\nTitle = {{PyMICE (v.~1.1.1)}},\nNote = {computer software; RRID:nlx\\_158570},\nAuthor = {Dzik, Jakub Mateusz and Łęski, Szymon and Puścian, Alicja},\nYear = {2017},\nMonth = {April},\nDay = {24},\nDoi = {10.5281/zenodo.557087}\n}\n",
                '1.1.0': u"@Misc{pymice1.1.0,\nTitle = {{PyMICE (v.~1.1.0)}},\nNote = {computer software; RRID:nlx\\_158570},\nAuthor = {Dzik, Jakub Mateusz and Łęski, Szymon and Puścian, Alicja},\nYear = {2016},\nMonth = {December},\nDay = {13},\nDoi = {10.5281/zenodo.200648}\n}\n",
                '1.0.0': u"@Misc{pymice1.0.0,\nTitle = {{PyMICE (v.~1.0.0)}},\nNote = {computer software; RRID:nlx\\_158570},\nAuthor = {Dzik, Jakub Mateusz and Łęski, Szymon and Puścian, Alicja},\nYear = {2016},\nMonth = {May},\nDay = {6},\nDoi = {10.5281/zenodo.51092}\n}\n",
                '0.2.5': u"@Misc{pymice0.2.5,\nTitle = {{PyMICE (v.~0.2.5)}},\nNote = {computer software; RRID:nlx\\_158570},\nAuthor = {Dzik, Jakub Mateusz and Łęski, Szymon and Puścian, Alicja},\nYear = {2016},\nMonth = {April},\nDay = {11},\nDoi = {10.5281/zenodo.49550}\n}\n",
                '0.2.4': u"@Misc{pymice0.2.4,\nTitle = {{PyMICE (v.~0.2.4)}},\nNote = {computer software; RRID:nlx\\_158570},\nAuthor = {Dzik, Jakub Mateusz and Łęski, Szymon and Puścian, Alicja},\nYear = {2016},\nMonth = {January},\nDay = {30},\nDoi = {10.5281/zenodo.47305}\n}\n",
                '0.2.3': u"@Misc{pymice0.2.3,\nTitle = {{PyMICE (v.~0.2.3)}},\nNote = {computer software; RRID:nlx\\_158570},\nAuthor = {Dzik, Jakub Mateusz and Łęski, Szymon and Puścian, Alicja},\nYear = {2016},\nMonth = {January},\nDay = {30},\nDoi = {10.5281/zenodo.47259}\n}\n",
                'unknown': u"@Misc{pymiceunknown,\nTitle = {{PyMICE (v.~unknown)}},\nNote = {computer software; RRID:nlx\\_158570},\nAuthor = {Dzik, Jakub Mateusz and Łęski, Szymon and Puścian, Alicja}\n}\n",
                None: u"@Misc{pymice,\nTitle = {{PyMICE}},\nNote = {computer software; RRID:nlx\\_158570},\nAuthor = {Dzik, Jakub Mateusz and Łęski, Szymon and Puścian, Alicja}\n}\n",
                }
    CITE_PYMICE = {'1.2.0': u"\\emph{PyMICE}~\\cite{dzik2017pm} v.~1.2.0~\\cite{pymice1.2.0}",
                   '1.1.1': u"\\emph{PyMICE}~\\cite{dzik2017pm} v.~1.1.1~\\cite{pymice1.1.1}",
                   'unknown': u"\\emph{PyMICE}~\\cite{dzik2017pm} v.~unknown~\\cite{pymiceunknown}",
                   None: u"\\emph{PyMICE}~\\cite{dzik2017pm,pymice}",
                   }
    CITE_PAPER = u"dzik2017pm"
    CITE_SOFTWARE = {'1.2.0': u"pymice1.2.0",
                     '1.1.1': u"pymice1.1.1",
                     'unknown': u"pymiceunknown",
                     None: u"pymice",
                     }
    PAPER = u"@Article{dzik2017pm,\nTitle = {{PyMICE}: A {Python} library for analysis of {IntelliCage} data},\nAuthor = {Dzik, Jakub Mateusz and Puścian, Alicja and Mijakowska, Zofia and Radwanska, Kasia and Łęski, Szymon},\nYear = {2017},\nMonth = {June},\nDay = {22},\nJournal = {Behavior Research Methods},\nDoi = {10.3758/s13428-017-0907-5},\nIssn = {1554-3528},\nUrl = {http://dx.doi.org/10.3758/s13428-017-0907-5},\nAbstract = {{IntelliCage} is an automated system for recording the behavior of a group of mice housed together. It produces rich, detailed behavioral data calling for new methods and software for their analysis. Here we present {PyMICE}, a free and open-source library for analysis of {IntelliCage} data in the {Python} programming language. We describe the design and demonstrate the use of the library through a series of examples. {PyMICE} provides easy and intuitive access to {IntelliCage} data, and thus facilitates the possibility of using numerous other {Python} scientific libraries to form a complete data analysis workflow.}\n}\n"


class TestDefaultLineWidthLimitIs80_GivenStyleBibTeX(TestCitationGivenStyleBibTeX):
    def Citation(self, style, **kwargs):
        return super(TestDefaultLineWidthLimitIs80_GivenStyleBibTeX,
                     self).Citation(style,
                                    _noMaxLineWidth=True,
                                    **kwargs)

    PAPER = u"""@Article{dzik2017pm,
Title = {{PyMICE}: A {Python} library for analysis of {IntelliCage} data},
Author = {Dzik, Jakub Mateusz and Puścian, Alicja and Mijakowska, Zofia and
    Radwanska, Kasia and Łęski, Szymon},
Year = {2017},
Month = {June},
Day = {22},
Journal = {Behavior Research Methods},
Doi = {10.3758/s13428-017-0907-5},
Issn = {1554-3528},
Url = {http://dx.doi.org/10.3758/s13428-017-0907-5},
Abstract = {{IntelliCage} is an automated system for recording the behavior of a
    group of mice housed together. It produces rich, detailed behavioral data
    calling for new methods and software for their analysis. Here we present
    {PyMICE}, a free and open-source library for analysis of {IntelliCage} data
    in the {Python} programming language. We describe the design and demonstrate
    the use of the library through a series of examples. {PyMICE} provides easy
    and intuitive access to {IntelliCage} data, and thus facilitates the
    possibility of using numerous other {Python} scientific libraries to form a
    complete data analysis workflow.}
}
"""


class TestCitationGivenStyleBibTeXcustomKeys(TestCitationGivenStyleBibTeX):
    PAPER_KEY = 'dzikPaper'
    SOFTWARE_KEY = 'dzikSoft'

    SOFTWARE = {'1.2.0': u"@Misc{dzikSoft,\nTitle = {{PyMICE (v.~1.2.0)}},\nNote = {computer software; RRID:nlx\\_158570},\nAuthor = {Dzik, Jakub Mateusz and Łęski, Szymon and Puścian, Alicja},\nYear = {2017},\nMonth = {July},\nDay = {21},\nDoi = {10.5281/zenodo.832982}\n}\n",
                '1.1.1': u"@Misc{dzikSoft,\nTitle = {{PyMICE (v.~1.1.1)}},\nNote = {computer software; RRID:nlx\\_158570},\nAuthor = {Dzik, Jakub Mateusz and Łęski, Szymon and Puścian, Alicja},\nYear = {2017},\nMonth = {April},\nDay = {24},\nDoi = {10.5281/zenodo.557087}\n}\n",
                '1.1.0': u"@Misc{dzikSoft,\nTitle = {{PyMICE (v.~1.1.0)}},\nNote = {computer software; RRID:nlx\\_158570},\nAuthor = {Dzik, Jakub Mateusz and Łęski, Szymon and Puścian, Alicja},\nYear = {2016},\nMonth = {December},\nDay = {13},\nDoi = {10.5281/zenodo.200648}\n}\n",
                '1.0.0': u"@Misc{dzikSoft,\nTitle = {{PyMICE (v.~1.0.0)}},\nNote = {computer software; RRID:nlx\\_158570},\nAuthor = {Dzik, Jakub Mateusz and Łęski, Szymon and Puścian, Alicja},\nYear = {2016},\nMonth = {May},\nDay = {6},\nDoi = {10.5281/zenodo.51092}\n}\n",
                '0.2.5': u"@Misc{dzikSoft,\nTitle = {{PyMICE (v.~0.2.5)}},\nNote = {computer software; RRID:nlx\\_158570},\nAuthor = {Dzik, Jakub Mateusz and Łęski, Szymon and Puścian, Alicja},\nYear = {2016},\nMonth = {April},\nDay = {11},\nDoi = {10.5281/zenodo.49550}\n}\n",
                '0.2.4': u"@Misc{dzikSoft,\nTitle = {{PyMICE (v.~0.2.4)}},\nNote = {computer software; RRID:nlx\\_158570},\nAuthor = {Dzik, Jakub Mateusz and Łęski, Szymon and Puścian, Alicja},\nYear = {2016},\nMonth = {January},\nDay = {30},\nDoi = {10.5281/zenodo.47305}\n}\n",
                '0.2.3': u"@Misc{dzikSoft,\nTitle = {{PyMICE (v.~0.2.3)}},\nNote = {computer software; RRID:nlx\\_158570},\nAuthor = {Dzik, Jakub Mateusz and Łęski, Szymon and Puścian, Alicja},\nYear = {2016},\nMonth = {January},\nDay = {30},\nDoi = {10.5281/zenodo.47259}\n}\n",
                'unknown': u"@Misc{dzikSoft,\nTitle = {{PyMICE (v.~unknown)}},\nNote = {computer software; RRID:nlx\\_158570},\nAuthor = {Dzik, Jakub Mateusz and Łęski, Szymon and Puścian, Alicja}\n}\n",
                None: u"@Misc{dzikSoft,\nTitle = {{PyMICE}},\nNote = {computer software; RRID:nlx\\_158570},\nAuthor = {Dzik, Jakub Mateusz and Łęski, Szymon and Puścian, Alicja}\n}\n",
                }
    CITE_PYMICE = {'1.2.0': u"\\emph{PyMICE}~\\cite{dzikPaper} v.~1.2.0~\\cite{dzikSoft}",
                   '1.1.1': u"\\emph{PyMICE}~\\cite{dzikPaper} v.~1.1.1~\\cite{dzikSoft}",
                   'unknown': u"\\emph{PyMICE}~\\cite{dzikPaper} v.~unknown~\\cite{dzikSoft}",
                   None: u"\\emph{PyMICE}~\\cite{dzikPaper,dzikSoft}",
                   }
    CITE_PAPER = u"dzikPaper"
    CITE_SOFTWARE = {k: u"dzikSoft" for k in SOFTWARE}
    PAPER = u"@Article{dzikPaper,\nTitle = {{PyMICE}: A {Python} library for analysis of {IntelliCage} data},\nAuthor = {Dzik, Jakub Mateusz and Puścian, Alicja and Mijakowska, Zofia and Radwanska, Kasia and Łęski, Szymon},\nYear = {2017},\nMonth = {June},\nDay = {22},\nJournal = {Behavior Research Methods},\nDoi = {10.3758/s13428-017-0907-5},\nIssn = {1554-3528},\nUrl = {http://dx.doi.org/10.3758/s13428-017-0907-5},\nAbstract = {{IntelliCage} is an automated system for recording the behavior of a group of mice housed together. It produces rich, detailed behavioral data calling for new methods and software for their analysis. Here we present {PyMICE}, a free and open-source library for analysis of {IntelliCage} data in the {Python} programming language. We describe the design and demonstrate the use of the library through a series of examples. {PyMICE} provides easy and intuitive access to {IntelliCage} data, and thus facilitates the possibility of using numerous other {Python} scientific libraries to form a complete data analysis workflow.}\n}\n"



class TestCitationGivenStylePymice(TestCitationBase):
    STYLE = 'pymice'
    SOFTWARE = {'1.2.0': u"Dzik\xa0J.\xa0M., Łęski\xa0S., Puścian\xa0A. (July\xa021,\xa02017) \"PyMICE\" computer software (v.\xa01.2.0; RRID:nlx_158570) doi:\xa010.5281/zenodo.832982",
                '1.1.1': u"Dzik\xa0J.\xa0M., Łęski\xa0S., Puścian\xa0A. (April\xa024,\xa02017) \"PyMICE\" computer software (v.\xa01.1.1; RRID:nlx_158570) doi:\xa010.5281/zenodo.557087",
                '1.1.0': u"Dzik\xa0J.\xa0M., Łęski\xa0S., Puścian\xa0A. (December\xa013,\xa02016) \"PyMICE\" computer software (v.\xa01.1.0; RRID:nlx_158570) doi:\xa010.5281/zenodo.200648",
                '1.0.0': u"Dzik\xa0J.\xa0M., Łęski\xa0S., Puścian\xa0A. (May\xa06,\xa02016) \"PyMICE\" computer software (v.\xa01.0.0; RRID:nlx_158570) doi:\xa010.5281/zenodo.51092",
                '0.2.5': u"Dzik\xa0J.\xa0M., Łęski\xa0S., Puścian\xa0A. (April\xa011,\xa02016) \"PyMICE\" computer software (v.\xa00.2.5; RRID:nlx_158570) doi:\xa010.5281/zenodo.49550",
                '0.2.4': u"Dzik\xa0J.\xa0M., Łęski\xa0S., Puścian\xa0A. (January\xa030,\xa02016) \"PyMICE\" computer software (v.\xa00.2.4; RRID:nlx_158570) doi:\xa010.5281/zenodo.47305",
                '0.2.3': u"Dzik\xa0J.\xa0M., Łęski\xa0S., Puścian\xa0A. (January\xa030,\xa02016) \"PyMICE\" computer software (v.\xa00.2.3; RRID:nlx_158570) doi:\xa010.5281/zenodo.47259",
                'unknown': u"Dzik\xa0J.\xa0M., Łęski\xa0S., Puścian\xa0A. \"PyMICE\" computer software (v.\xa0unknown; RRID:nlx_158570)",
                None: u"Dzik\xa0J.\xa0M., Łęski\xa0S., Puścian\xa0A. \"PyMICE\" computer software (RRID:nlx_158570)",
                }
    CITE_PYMICE = {'1.2.0': u"PyMICE\xa0(Dzik, Puścian, et\xa0al. 2017) v.\xa01.2.0\xa0(Dzik, Łęski, &\xa0Puścian 2017)",
                   '1.1.1': u"PyMICE\xa0(Dzik, Puścian, et\xa0al. 2017) v.\xa01.1.1\xa0(Dzik, Łęski, &\xa0Puścian 2017)",
                   '1.1.0': u"PyMICE\xa0(Dzik, Puścian, et\xa0al. 2017) v.\xa01.1.0\xa0(Dzik, Łęski, &\xa0Puścian 2016)",
                   'unknown': u"PyMICE\xa0(Dzik, Puścian, et\xa0al. 2017) v.\xa0unknown\xa0(Dzik, Łęski, &\xa0Puścian)",
                   None: u"PyMICE\xa0(Dzik, Puścian, et\xa0al. 2017; Dzik, Łęski, &\xa0Puścian)",
                   }
    CITE_PAPER = u"Dzik, Puścian, et\xa0al. 2017"
    CITE_SOFTWARE = {'1.2.0': u"Dzik, Łęski, &\xa0Puścian 2017",
                     '1.1.1': u"Dzik, Łęski, &\xa0Puścian 2017",
                     '1.1.0': u"Dzik, Łęski, &\xa0Puścian 2016",
                     'unknown': u"Dzik, Łęski, &\xa0Puścian",
                     None: u"Dzik, Łęski, &\xa0Puścian",
                     }
    PAPER = u"Dzik\xa0J.\xa0M., Puścian\xa0A., Mijakowska\xa0Z., Radwanska\xa0K., Łęski\xa0S. (June\xa022,\xa02017) \"PyMICE: A Python library for analysis of IntelliCage data\" Behavior Research Methods doi:\xa010.3758/s13428-017-0907-5"


class TestCitationGivenStylePymiceMarkdownLaTeX(TestCitationGivenStylePymice):
    MARKDOWN = 'latex'
    SOFTWARE = {'1.2.0': u"\\bibitem{pymice1.2.0} Dzik~J.~M., Łęski~S., Puścian~A. (July~21,~2017) ``PyMICE'' computer software (v.~1.2.0; RRID:nlx\_158570) doi:~10.5281/zenodo.832982",
                '1.1.1': u"\\bibitem{pymice1.1.1} Dzik~J.~M., Łęski~S., Puścian~A. (April~24,~2017) ``PyMICE'' computer software (v.~1.1.1; RRID:nlx\_158570) doi:~10.5281/zenodo.557087",
                '1.1.0': u"\\bibitem{pymice1.1.0} Dzik~J.~M., Łęski~S., Puścian~A. (December~13,~2016) ``PyMICE'' computer software (v.~1.1.0; RRID:nlx\_158570) doi:~10.5281/zenodo.200648",
                '1.0.0': u"\\bibitem{pymice1.0.0} Dzik~J.~M., Łęski~S., Puścian~A. (May~6,~2016) ``PyMICE'' computer software (v.~1.0.0; RRID:nlx\_158570) doi:~10.5281/zenodo.51092",
                '0.2.5': u"\\bibitem{pymice0.2.5} Dzik~J.~M., Łęski~S., Puścian~A. (April~11,~2016) ``PyMICE'' computer software (v.~0.2.5; RRID:nlx\_158570) doi:~10.5281/zenodo.49550",
                '0.2.4': u"\\bibitem{pymice0.2.4} Dzik~J.~M., Łęski~S., Puścian~A. (January~30,~2016) ``PyMICE'' computer software (v.~0.2.4; RRID:nlx\_158570) doi:~10.5281/zenodo.47305",
                '0.2.3': u"\\bibitem{pymice0.2.3} Dzik~J.~M., Łęski~S., Puścian~A. (January~30,~2016) ``PyMICE'' computer software (v.~0.2.3; RRID:nlx\_158570) doi:~10.5281/zenodo.47259",
                'unknown': u"\\bibitem{pymiceunknown} Dzik~J.~M., Łęski~S., Puścian~A. ``PyMICE'' computer software (v.~unknown; RRID:nlx\_158570)",
                None: u"\\bibitem{pymice} Dzik~J.~M., Łęski~S., Puścian~A. ``PyMICE'' computer software (RRID:nlx\_158570)",
                }
    CITE_PYMICE = {'1.2.0': u"\\emph{PyMICE}~\\cite{dzik2017pm} v.~1.2.0~\\cite{pymice1.2.0}",
                   '1.1.1': u"\\emph{PyMICE}~\\cite{dzik2017pm} v.~1.1.1~\\cite{pymice1.1.1}",
                   'unknown': u"\\emph{PyMICE}~\\cite{dzik2017pm} v.~unknown~\\cite{pymiceunknown}",
                   None: u"\\emph{PyMICE}~\\cite{dzik2017pm,pymice}",
                   }
    CITE_PAPER = u"dzik2017pm"
    CITE_SOFTWARE = {'1.2.0': u"pymice1.2.0",
                     '1.1.1': u"pymice1.1.1",
                     'unknown': u"pymiceunknown",
                     None: u"pymice",
                     }
    PAPER = u"\\bibitem{dzik2017pm} Dzik~J.~M., Puścian~A., Mijakowska~Z., Radwanska~K., Łęski~S. (June~22,~2017) ``{PyMICE}: A {Python} library for analysis of {IntelliCage} data'' Behavior Research Methods doi:~10.3758/s13428-017-0907-5"


class TestCitationGivenStylePymiceMarkdownLaTeXcustomKeys(TestCitationGivenStylePymiceMarkdownLaTeX):
    MARKDOWN = 'latex'
    PAPER_KEY = 'dzikPaper'
    SOFTWARE_KEY = 'dzikSoft'

    SOFTWARE = {'1.2.0': u"\\bibitem{dzikSoft} Dzik~J.~M., Łęski~S., Puścian~A. (July~21,~2017) ``PyMICE'' computer software (v.~1.2.0; RRID:nlx\_158570) doi:~10.5281/zenodo.832982",
                '1.1.1': u"\\bibitem{dzikSoft} Dzik~J.~M., Łęski~S., Puścian~A. (April~24,~2017) ``PyMICE'' computer software (v.~1.1.1; RRID:nlx\_158570) doi:~10.5281/zenodo.557087",
                '1.1.0': u"\\bibitem{dzikSoft} Dzik~J.~M., Łęski~S., Puścian~A. (December~13,~2016) ``PyMICE'' computer software (v.~1.1.0; RRID:nlx\_158570) doi:~10.5281/zenodo.200648",
                '1.0.0': u"\\bibitem{dzikSoft} Dzik~J.~M., Łęski~S., Puścian~A. (May~6,~2016) ``PyMICE'' computer software (v.~1.0.0; RRID:nlx\_158570) doi:~10.5281/zenodo.51092",
                '0.2.5': u"\\bibitem{dzikSoft} Dzik~J.~M., Łęski~S., Puścian~A. (April~11,~2016) ``PyMICE'' computer software (v.~0.2.5; RRID:nlx\_158570) doi:~10.5281/zenodo.49550",
                '0.2.4': u"\\bibitem{dzikSoft} Dzik~J.~M., Łęski~S., Puścian~A. (January~30,~2016) ``PyMICE'' computer software (v.~0.2.4; RRID:nlx\_158570) doi:~10.5281/zenodo.47305",
                '0.2.3': u"\\bibitem{dzikSoft} Dzik~J.~M., Łęski~S., Puścian~A. (January~30,~2016) ``PyMICE'' computer software (v.~0.2.3; RRID:nlx\_158570) doi:~10.5281/zenodo.47259",
                'unknown': u"\\bibitem{dzikSoft} Dzik~J.~M., Łęski~S., Puścian~A. ``PyMICE'' computer software (v.~unknown; RRID:nlx\_158570)",
                None: u"\\bibitem{dzikSoft} Dzik~J.~M., Łęski~S., Puścian~A. ``PyMICE'' computer software (RRID:nlx\_158570)",
                }
    CITE_PYMICE = {'1.2.0': u"\\emph{PyMICE}~\\cite{dzikPaper} v.~1.2.0~\\cite{dzikSoft}",
                   '1.1.1': u"\\emph{PyMICE}~\\cite{dzikPaper} v.~1.1.1~\\cite{dzikSoft}",
                   'unknown': u"\\emph{PyMICE}~\\cite{dzikPaper} v.~unknown~\\cite{dzikSoft}",
                   None: u"\\emph{PyMICE}~\\cite{dzikPaper,dzikSoft}",
                   }
    CITE_PAPER = u"dzikPaper"
    CITE_SOFTWARE = {k: u"dzikSoft" for k in SOFTWARE}
    PAPER = u"\\bibitem{dzikPaper} Dzik~J.~M., Puścian~A., Mijakowska~Z., Radwanska~K., Łęski~S. (June~22,~2017) ``{PyMICE}: A {Python} library for analysis of {IntelliCage} data'' Behavior Research Methods doi:~10.3758/s13428-017-0907-5"


class TestDefaultLineWidthLimitIs80(TestCitationGivenStylePymice):
    def Citation(self, style, **kwargs):
        return super(TestDefaultLineWidthLimitIs80,
                     self).Citation(style,
                                    _noMaxLineWidth=True,
                                    **kwargs)

    SOFTWARE = {'1.2.0': u"Dzik\xa0J.\xa0M., Łęski\xa0S., Puścian\xa0A. (July\xa021,\xa02017) \"PyMICE\" computer software\n    (v.\xa01.2.0; RRID:nlx_158570) doi:\xa010.5281/zenodo.832982",
                '1.1.1': u"Dzik\xa0J.\xa0M., Łęski\xa0S., Puścian\xa0A. (April\xa024,\xa02017) \"PyMICE\" computer software\n    (v.\xa01.1.1; RRID:nlx_158570) doi:\xa010.5281/zenodo.557087",
                '1.1.0': u"Dzik\xa0J.\xa0M., Łęski\xa0S., Puścian\xa0A. (December\xa013,\xa02016) \"PyMICE\" computer software\n    (v.\xa01.1.0; RRID:nlx_158570) doi:\xa010.5281/zenodo.200648",
                '1.0.0': u"Dzik\xa0J.\xa0M., Łęski\xa0S., Puścian\xa0A. (May\xa06,\xa02016) \"PyMICE\" computer software\n    (v.\xa01.0.0; RRID:nlx_158570) doi:\xa010.5281/zenodo.51092",
                '0.2.5': u"Dzik\xa0J.\xa0M., Łęski\xa0S., Puścian\xa0A. (April\xa011,\xa02016) \"PyMICE\" computer software\n    (v.\xa00.2.5; RRID:nlx_158570) doi:\xa010.5281/zenodo.49550",
                '0.2.4': u"Dzik\xa0J.\xa0M., Łęski\xa0S., Puścian\xa0A. (January\xa030,\xa02016) \"PyMICE\" computer software\n    (v.\xa00.2.4; RRID:nlx_158570) doi:\xa010.5281/zenodo.47305",
                '0.2.3': u"Dzik\xa0J.\xa0M., Łęski\xa0S., Puścian\xa0A. (January\xa030,\xa02016) \"PyMICE\" computer software\n    (v.\xa00.2.3; RRID:nlx_158570) doi:\xa010.5281/zenodo.47259",
                'unknown': u"Dzik\xa0J.\xa0M., Łęski\xa0S., Puścian\xa0A. \"PyMICE\" computer software (v.\xa0unknown;\n    RRID:nlx_158570)",
                None: u"Dzik\xa0J.\xa0M., Łęski\xa0S., Puścian\xa0A. \"PyMICE\" computer software (RRID:nlx_158570)",
                }
    PAPER = u"Dzik\xa0J.\xa0M., Puścian\xa0A., Mijakowska\xa0Z., Radwanska\xa0K., Łęski\xa0S. (June\xa022,\xa02017)\n    \"PyMICE: A Python library for analysis of IntelliCage data\" Behavior\n    Research Methods doi:\xa010.3758/s13428-017-0907-5"


class TestCitationGivenStyleVancouver(TestCitationBase):
    STYLE = 'vancouver'

    SOFTWARE = {'1.2.0': u"2. Dzik\xa0JM, Łęski\xa0S, Puścian\xa0A. PyMICE [computer software]. Version 1.2.0. Warsaw: Nencki Institute - PAS; 2017. DOI:\xa010.5281/zenodo.832982",
                '1.1.1': u"2. Dzik\xa0JM, Łęski\xa0S, Puścian\xa0A. PyMICE [computer software]. Version 1.1.1. Warsaw: Nencki Institute - PAS; 2017. DOI:\xa010.5281/zenodo.557087",
                '1.1.0': u"2. Dzik\xa0JM, Łęski\xa0S, Puścian\xa0A. PyMICE [computer software]. Version 1.1.0. Warsaw: Nencki Institute - PAS; 2016. DOI:\xa010.5281/zenodo.200648",
                '1.0.0': u"2. Dzik\xa0JM, Łęski\xa0S, Puścian\xa0A. PyMICE [computer software]. Version 1.0.0. Warsaw: Nencki Institute - PAS; 2016. DOI:\xa010.5281/zenodo.51092",
                '0.2.5': u"2. Dzik\xa0JM, Łęski\xa0S, Puścian\xa0A. PyMICE [computer software]. Version 0.2.5. Warsaw: Nencki Institute - PAS; 2016. DOI:\xa010.5281/zenodo.49550",
                '0.2.4': u"2. Dzik\xa0JM, Łęski\xa0S, Puścian\xa0A. PyMICE [computer software]. Version 0.2.4. Warsaw: Nencki Institute - PAS; 2016. DOI:\xa010.5281/zenodo.47305",
                '0.2.3': u"2. Dzik\xa0JM, Łęski\xa0S, Puścian\xa0A. PyMICE [computer software]. Version 0.2.3. Warsaw: Nencki Institute - PAS; 2016. DOI:\xa010.5281/zenodo.47259",
                'unknown': u"2. Dzik\xa0JM, Łęski\xa0S, Puścian\xa0A. PyMICE [computer software]. Version unknown. Warsaw: Nencki Institute - PAS.",
                None: u"2. Dzik\xa0JM, Łęski\xa0S, Puścian\xa0A. PyMICE [computer software]. Warsaw: Nencki Institute - PAS.",
                }
    CITE_PYMICE = {'1.2.0': u"PyMICE\xa0(RRID:nlx_158570)\xa0[1] v.\xa01.2.0\xa0[2]",
                   '1.1.1': u"PyMICE\xa0(RRID:nlx_158570)\xa0[1] v.\xa01.1.1\xa0[2]",
                   '1.1.0': u"PyMICE\xa0(RRID:nlx_158570)\xa0[1] v.\xa01.1.0\xa0[2]",
                   'unknown': u"PyMICE\xa0(RRID:nlx_158570)\xa0[1] v.\xa0unknown\xa0[2]",
                   None: u"PyMICE\xa0(RRID:nlx_158570)\xa0[1,2]",
                   }
    CITE_PAPER = u"1"
    CITE_SOFTWARE = {k: u"2" for k in SOFTWARE}
    PAPER = u"1. Dzik\xa0JM, Puścian\xa0A, Mijakowska\xa0Z, Radwanska\xa0K, Łęski\xa0S. PyMICE: A Python library for analysis of IntelliCage data. Behav Res Methods. 2017. DOI:\xa010.3758/s13428-017-0907-5"


class TestCitationGivenStyleVancouverMarkdownLaTeX(TestCitationGivenStyleVancouver):
    MARKDOWN = 'latex'
    SOFTWARE = {'1.2.0': u"\\bibitem{pymice1.2.0} Dzik~JM, Łęski~S, Puścian~A. PyMICE [computer software]. Version 1.2.0. Warsaw: Nencki Institute - PAS; 2017. DOI:~10.5281/zenodo.832982",
                '1.1.1': u"\\bibitem{pymice1.1.1} Dzik~JM, Łęski~S, Puścian~A. PyMICE [computer software]. Version 1.1.1. Warsaw: Nencki Institute - PAS; 2017. DOI:~10.5281/zenodo.557087",
                '1.1.0': u"\\bibitem{pymice1.1.0} Dzik~JM, Łęski~S, Puścian~A. PyMICE [computer software]. Version 1.1.0. Warsaw: Nencki Institute - PAS; 2016. DOI:~10.5281/zenodo.200648",
                '1.0.0': u"\\bibitem{pymice1.0.0} Dzik~JM, Łęski~S, Puścian~A. PyMICE [computer software]. Version 1.0.0. Warsaw: Nencki Institute - PAS; 2016. DOI:~10.5281/zenodo.51092",
                '0.2.5': u"\\bibitem{pymice0.2.5} Dzik~JM, Łęski~S, Puścian~A. PyMICE [computer software]. Version 0.2.5. Warsaw: Nencki Institute - PAS; 2016. DOI:~10.5281/zenodo.49550",
                '0.2.4': u"\\bibitem{pymice0.2.4} Dzik~JM, Łęski~S, Puścian~A. PyMICE [computer software]. Version 0.2.4. Warsaw: Nencki Institute - PAS; 2016. DOI:~10.5281/zenodo.47305",
                '0.2.3': u"\\bibitem{pymice0.2.3} Dzik~JM, Łęski~S, Puścian~A. PyMICE [computer software]. Version 0.2.3. Warsaw: Nencki Institute - PAS; 2016. DOI:~10.5281/zenodo.47259",
                'unknown': u"\\bibitem{pymiceunknown} Dzik~JM, Łęski~S, Puścian~A. PyMICE [computer software]. Version unknown. Warsaw: Nencki Institute - PAS.",
                None: u"\\bibitem{pymice} Dzik~JM, Łęski~S, Puścian~A. PyMICE [computer software]. Warsaw: Nencki Institute - PAS.",
                }
    CITE_PYMICE = {'1.2.0': u"\\emph{PyMICE}~(RRID:nlx\\_158570)~\\cite{dzik2017pm} v.~1.2.0~\\cite{pymice1.2.0}",
                   '1.1.1': u"\\emph{PyMICE}~(RRID:nlx\\_158570)~\\cite{dzik2017pm} v.~1.1.1~\\cite{pymice1.1.1}",
                   'unknown': u"\\emph{PyMICE}~(RRID:nlx\\_158570)~\\cite{dzik2017pm} v.~unknown~\\cite{pymiceunknown}",
                   None: u"\\emph{PyMICE}~(RRID:nlx\\_158570)~\\cite{dzik2017pm,pymice}",
                 }
    CITE_PAPER = u"dzik2017pm"
    CITE_SOFTWARE = {'1.2.0': u"pymice1.2.0",
                     '1.1.1': u"pymice1.1.1",
                     'unknown': u"pymiceunknown",
                     None: u"pymice",
                     }
    PAPER = u"\\bibitem{dzik2017pm} Dzik~JM, Puścian~A, Mijakowska~Z, Radwanska~K, Łęski~S. {PyMICE}: A {Python} library for analysis of {IntelliCage} data. Behav Res Methods. 2017. DOI:~10.3758/s13428-017-0907-5"


class TestCitationGivenStyleVancouverAndCustomKeys(TestCitationGivenStyleVancouver):
    STYLE = 'vancouver'
    PAPER_KEY = 42
    SOFTWARE_KEY = 69

    SOFTWARE = {'1.2.0': u"69. Dzik\xa0JM, Łęski\xa0S, Puścian\xa0A. PyMICE [computer software]. Version 1.2.0. Warsaw: Nencki Institute - PAS; 2017. DOI:\xa010.5281/zenodo.832982",
                '1.1.1': u"69. Dzik\xa0JM, Łęski\xa0S, Puścian\xa0A. PyMICE [computer software]. Version 1.1.1. Warsaw: Nencki Institute - PAS; 2017. DOI:\xa010.5281/zenodo.557087",
                '1.1.0': u"69. Dzik\xa0JM, Łęski\xa0S, Puścian\xa0A. PyMICE [computer software]. Version 1.1.0. Warsaw: Nencki Institute - PAS; 2016. DOI:\xa010.5281/zenodo.200648",
                '1.0.0': u"69. Dzik\xa0JM, Łęski\xa0S, Puścian\xa0A. PyMICE [computer software]. Version 1.0.0. Warsaw: Nencki Institute - PAS; 2016. DOI:\xa010.5281/zenodo.51092",
                '0.2.5': u"69. Dzik\xa0JM, Łęski\xa0S, Puścian\xa0A. PyMICE [computer software]. Version 0.2.5. Warsaw: Nencki Institute - PAS; 2016. DOI:\xa010.5281/zenodo.49550",
                '0.2.4': u"69. Dzik\xa0JM, Łęski\xa0S, Puścian\xa0A. PyMICE [computer software]. Version 0.2.4. Warsaw: Nencki Institute - PAS; 2016. DOI:\xa010.5281/zenodo.47305",
                '0.2.3': u"69. Dzik\xa0JM, Łęski\xa0S, Puścian\xa0A. PyMICE [computer software]. Version 0.2.3. Warsaw: Nencki Institute - PAS; 2016. DOI:\xa010.5281/zenodo.47259",
                'unknown': u"69. Dzik\xa0JM, Łęski\xa0S, Puścian\xa0A. PyMICE [computer software]. Version unknown. Warsaw: Nencki Institute - PAS.",
                None: u"69. Dzik\xa0JM, Łęski\xa0S, Puścian\xa0A. PyMICE [computer software]. Warsaw: Nencki Institute - PAS.",
                }
    CITE_PYMICE = {'1.2.0': u"PyMICE\xa0(RRID:nlx_158570)\xa0[42] v.\xa01.2.0\xa0[69]",
                   '1.1.1': u"PyMICE\xa0(RRID:nlx_158570)\xa0[42] v.\xa01.1.1\xa0[69]",
                   '1.1.0': u"PyMICE\xa0(RRID:nlx_158570)\xa0[42] v.\xa01.1.0\xa0[69]",
                   'unknown': u"PyMICE\xa0(RRID:nlx_158570)\xa0[42] v.\xa0unknown\xa0[69]",
                   None: u"PyMICE\xa0(RRID:nlx_158570)\xa0[42,69]",
                   }
    CITE_PAPER = u"42"
    CITE_SOFTWARE = {k: u"69" for k in SOFTWARE}
    PAPER = u"42. Dzik\xa0JM, Puścian\xa0A, Mijakowska\xa0Z, Radwanska\xa0K, Łęski\xa0S. PyMICE: A Python library for analysis of IntelliCage data. Behav Res Methods. 2017. DOI:\xa010.3758/s13428-017-0907-5"


class TestCitationGivenStyleVancouverMarkdownLaTeXcustomKeys(TestCitationGivenStyleVancouverMarkdownLaTeX):
    MARKDOWN = 'latex'
    PAPER_KEY = 'dzikPaper'
    SOFTWARE_KEY = 'dzikSoft'

    SOFTWARE = {'1.2.0': u"\\bibitem{dzikSoft} Dzik~JM, Łęski~S, Puścian~A. PyMICE [computer software]. Version 1.2.0. Warsaw: Nencki Institute - PAS; 2017. DOI:~10.5281/zenodo.832982",
                '1.1.1': u"\\bibitem{dzikSoft} Dzik~JM, Łęski~S, Puścian~A. PyMICE [computer software]. Version 1.1.1. Warsaw: Nencki Institute - PAS; 2017. DOI:~10.5281/zenodo.557087",
                '1.1.0': u"\\bibitem{dzikSoft} Dzik~JM, Łęski~S, Puścian~A. PyMICE [computer software]. Version 1.1.0. Warsaw: Nencki Institute - PAS; 2016. DOI:~10.5281/zenodo.200648",
                '1.0.0': u"\\bibitem{dzikSoft} Dzik~JM, Łęski~S, Puścian~A. PyMICE [computer software]. Version 1.0.0. Warsaw: Nencki Institute - PAS; 2016. DOI:~10.5281/zenodo.51092",
                '0.2.5': u"\\bibitem{dzikSoft} Dzik~JM, Łęski~S, Puścian~A. PyMICE [computer software]. Version 0.2.5. Warsaw: Nencki Institute - PAS; 2016. DOI:~10.5281/zenodo.49550",
                '0.2.4': u"\\bibitem{dzikSoft} Dzik~JM, Łęski~S, Puścian~A. PyMICE [computer software]. Version 0.2.4. Warsaw: Nencki Institute - PAS; 2016. DOI:~10.5281/zenodo.47305",
                '0.2.3': u"\\bibitem{dzikSoft} Dzik~JM, Łęski~S, Puścian~A. PyMICE [computer software]. Version 0.2.3. Warsaw: Nencki Institute - PAS; 2016. DOI:~10.5281/zenodo.47259",
                'unknown': u"\\bibitem{dzikSoft} Dzik~JM, Łęski~S, Puścian~A. PyMICE [computer software]. Version unknown. Warsaw: Nencki Institute - PAS.",
                None: u"\\bibitem{dzikSoft} Dzik~JM, Łęski~S, Puścian~A. PyMICE [computer software]. Warsaw: Nencki Institute - PAS.",
                }
    CITE_PYMICE = {'1.2.0': u"\\emph{PyMICE}~(RRID:nlx\\_158570)~\\cite{dzikPaper} v.~1.2.0~\\cite{dzikSoft}",
                   '1.1.1': u"\\emph{PyMICE}~(RRID:nlx\\_158570)~\\cite{dzikPaper} v.~1.1.1~\\cite{dzikSoft}",
                   'unknown': u"\\emph{PyMICE}~(RRID:nlx\\_158570)~\\cite{dzikPaper} v.~unknown~\\cite{dzikSoft}",
                   None: u"\\emph{PyMICE}~(RRID:nlx\\_158570)~\\cite{dzikPaper,dzikSoft}",
                   }
    CITE_PAPER = u"dzikPaper"
    CITE_SOFTWARE = {k: u"dzikSoft" for k in SOFTWARE}
    PAPER = u"\\bibitem{dzikPaper} Dzik~JM, Puścian~A, Mijakowska~Z, Radwanska~K, Łęski~S. {PyMICE}: A {Python} library for analysis of {IntelliCage} data. Behav Res Methods. 2017. DOI:~10.3758/s13428-017-0907-5"


class TestCitationGivenNoDefaultStyleNorVersion(TestCitationGivenStylePymice):
    def setUp(self):
        self.reference = Citation(maxLineWidth=None)

    def testSoftwareDefaultStyleIsPymice(self):
        self.checkUnicodeEqual(self.SOFTWARE[pm.__version__],
                               self.reference.referenceSoftware())


class TestCitationGivenCamelCaseMarkdown(TestCitationGivenStyleAPA6markdownLaTeX):
    MARKDOWN = 'LaTeX'

class TestCitationGivenCamelCaseStyle(TestCitationGivenStyleAPA6markdownLaTeX):
    STYLE = 'Apa6'

if __name__ == '__main__':
    unittest.main()