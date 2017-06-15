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

import pymice as pm
from pymice._Bibliography import Citation


class TestCitationBase(TestCase):
    def checkUnicodeEqual(self, expected, output):
        self.assertEqual(expected, output)
        self.assertIsInstance(output,
                              unicode if sys.version_info.major < 3 else str)

    def setUp(self):
        try:
            style = self.STYLE
        except AttributeError:
            self.skipTest('generic test called')
        else:
            self.reference = Citation(style=style)


    def testSoftware(self):
        for version, expected in self.SOFTWARE.items():
            self.checkUnicodeEqual(expected,
                                   self.reference.software(version, self.STYLE))

    def testSoftwareDefaultStyleIsGivenInConstructor(self):
        self.checkUnicodeEqual(self.SOFTWARE[pm.__version__],
                               self.reference.software())


class TestCitationLaTeX(TestCitationBase):
    STYLE = 'latex'
    SOFTWARE = {'1.1.1': u"\\bibitem{pymice1.1.1} Dzik,~J.~M., Łęski,~S., & Puścian,~A. (2017,~April). PyMICE (v.~1.1.1) [computer software; RRID:nlx\_158570]. doi:~10.5281/zenodo.557087",
                '1.1.0': u"\\bibitem{pymice1.1.0} Dzik,~J.~M., Łęski,~S., & Puścian,~A. (2016,~December). PyMICE (v.~1.1.0) [computer software; RRID:nlx\_158570]. doi:~10.5281/zenodo.200648",
                '1.0.0': u"\\bibitem{pymice1.0.0} Dzik,~J.~M., Łęski,~S., & Puścian,~A. (2016,~May). PyMICE (v.~1.0.0) [computer software; RRID:nlx\_158570]. doi:~10.5281/zenodo.51092",
                '0.2.5': u"\\bibitem{pymice0.2.5} Dzik,~J.~M., Łęski,~S., & Puścian,~A. (2016,~April). PyMICE (v.~0.2.5) [computer software; RRID:nlx\_158570]. doi:~10.5281/zenodo.49550",
                '0.2.4': u"\\bibitem{pymice0.2.4} Dzik,~J.~M., Łęski,~S., & Puścian,~A. (2016,~January). PyMICE (v.~0.2.4) [computer software; RRID:nlx\_158570]. doi:~10.5281/zenodo.47305",
                '0.2.3': u"\\bibitem{pymice0.2.3} Dzik,~J.~M., Łęski,~S., & Puścian,~A. (2016,~January). PyMICE (v.~0.2.3) [computer software; RRID:nlx\_158570]. doi:~10.5281/zenodo.47259",
                'unknown': u"\\bibitem{pymiceunknown} Dzik,~J.~M., Łęski,~S., & Puścian,~A. (n.d.). PyMICE (v.~unknown) [computer software; RRID:nlx\_158570]",
                }
    CITE_SOFTWARE = {
        'latex': {'1.1.1': u"\\emph{PyMICE} v.~1.1.1~\\cite{pymice1.1.1}",
                  },
    }

    def testSoftwareCurrentVersionIsDefault(self):
        self.checkUnicodeEqual(self.SOFTWARE[pm.__version__],
                               self.reference.software(style=self.STYLE))

    def testCiteSoftware(self):
        for style, tests in self.CITE_SOFTWARE.items():
            for version, expected in tests.items():
                self.checkUnicodeEqual(expected,
                                       self.reference.citeSoftware(version, style))


class TestCitationBIBTEX(TestCitationLaTeX):
    STYLE = 'bibtex'
    SOFTWARE = {'1.1.1': u"pymice1.1.1{Title = {{PyMICE (v.~1.1.1)}}, Note = {computer software; RRID:nlx\\_158570}, Author = {Dzik, Jakub Mateusz and Łęski, Szymon and Puścian, Alicja}, Year = {2017}, Month = {April}, Doi = {10.5281/zenodo.557087}}",
                '1.1.0': u"pymice1.1.0{Title = {{PyMICE (v.~1.1.0)}}, Note = {computer software; RRID:nlx\\_158570}, Author = {Dzik, Jakub Mateusz and Łęski, Szymon and Puścian, Alicja}, Year = {2016}, Month = {December}, Doi = {10.5281/zenodo.200648}}",
                '1.0.0': u"pymice1.0.0{Title = {{PyMICE (v.~1.0.0)}}, Note = {computer software; RRID:nlx\\_158570}, Author = {Dzik, Jakub Mateusz and Łęski, Szymon and Puścian, Alicja}, Year = {2016}, Month = {May}, Doi = {10.5281/zenodo.51092}}",
                '0.2.5': u"pymice0.2.5{Title = {{PyMICE (v.~0.2.5)}}, Note = {computer software; RRID:nlx\\_158570}, Author = {Dzik, Jakub Mateusz and Łęski, Szymon and Puścian, Alicja}, Year = {2016}, Month = {April}, Doi = {10.5281/zenodo.49550}}",
                '0.2.4': u"pymice0.2.4{Title = {{PyMICE (v.~0.2.4)}}, Note = {computer software; RRID:nlx\\_158570}, Author = {Dzik, Jakub Mateusz and Łęski, Szymon and Puścian, Alicja}, Year = {2016}, Month = {January}, Doi = {10.5281/zenodo.47305}}",
                '0.2.3': u"pymice0.2.3{Title = {{PyMICE (v.~0.2.3)}}, Note = {computer software; RRID:nlx\\_158570}, Author = {Dzik, Jakub Mateusz and Łęski, Szymon and Puścian, Alicja}, Year = {2016}, Month = {January}, Doi = {10.5281/zenodo.47259}}",
                'unknown': u"pymiceunknown{Title = {{PyMICE (v.~unknown)}}, Note = {computer software; RRID:nlx\\_158570}, Author = {Dzik, Jakub Mateusz and Łęski, Szymon and Puścian, Alicja}}",
                }


class TestCitationAPA6(TestCitationBase):
    STYLE = 'apa6'
    SOFTWARE = {'1.1.1': u"Dzik,\u00A0J.\u00A0M., Łęski,\u00A0S., & Puścian,\u00A0A. (2017,\u00A0April). PyMICE (v.\u00A01.1.1) [computer software; RRID:nlx_158570]. doi:\u00A010.5281/zenodo.557087",
                '1.1.0': u"Dzik,\u00A0J.\u00A0M., Łęski,\u00A0S., & Puścian,\u00A0A. (2016,\u00A0December). PyMICE (v.\u00A01.1.0) [computer software; RRID:nlx_158570]. doi:\u00A010.5281/zenodo.200648",
                '1.0.0': u"Dzik,\u00A0J.\u00A0M., Łęski,\u00A0S., & Puścian,\u00A0A. (2016,\u00A0May). PyMICE (v.\u00A01.0.0) [computer software; RRID:nlx_158570]. doi:\u00A010.5281/zenodo.51092",
                '0.2.5': u"Dzik,\u00A0J.\u00A0M., Łęski,\u00A0S., & Puścian,\u00A0A. (2016,\u00A0April). PyMICE (v.\u00A00.2.5) [computer software; RRID:nlx_158570]. doi:\u00A010.5281/zenodo.49550",
                '0.2.4': u"Dzik,\u00A0J.\u00A0M., Łęski,\u00A0S., & Puścian,\u00A0A. (2016,\u00A0January). PyMICE (v.\u00A00.2.4) [computer software; RRID:nlx_158570]. doi:\u00A010.5281/zenodo.47305",
                '0.2.3': u"Dzik,\u00A0J.\u00A0M., Łęski,\u00A0S., & Puścian,\u00A0A. (2016,\u00A0January). PyMICE (v.\u00A00.2.3) [computer software; RRID:nlx_158570]. doi:\u00A010.5281/zenodo.47259",
                'unknown': u"Dzik,\u00A0J.\u00A0M., Łęski,\u00A0S., & Puścian,\u00A0A. (n.d.). PyMICE (v.\u00A0unknown) [computer software; RRID:nlx_158570]",
                }
    CITE_SOFTWARE = {
        'apa6': {'1.1.1': u"PyMICE v.\u00A01.1.1 (Dzik, Łęski, & Puścian, 2017)",
                 '1.1.0': u"PyMICE v.\u00A01.1.0 (Dzik, Łęski, & Puścian, 2016)",
                 'unknown': u"PyMICE v.\u00A0unknown (Dzik, Łęski, & Puścian, n.d.)",
                  },
        }

    def testSoftwareDefaultStyleIsAPA6(self):
        self.checkUnicodeEqual(self.SOFTWARE[pm.__version__],
                               self.reference.software())

    def testCiteSoftware(self):
        for style, tests in self.CITE_SOFTWARE.items():
            for version, expected in tests.items():
                self.checkUnicodeEqual(expected,
                                       self.reference.citeSoftware(version, style))

class TestCitationDefaultStyle(TestCitationAPA6):
    def setUp(self):
        self.reference = Citation()


if __name__ == '__main__':
    unittest.main()