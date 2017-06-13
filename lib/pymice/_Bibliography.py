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

from . import __version__ # WARNING: circular import possible!!!

class _Reference(object):
    META = {'1.1.1': {'doi': '10.5281/zenodo.557087',
                     'year': 2017,
                     'month': 'April',
                      },
            '1.1.0': {'doi': '10.5281/zenodo.200648',
                      'year': 2016,
                      'month': 'December',
                     },
            '1.0.0': {'doi': '10.5281/zenodo.51092',
                      'year': 2016,
                      'month': 'May',
                      },
            '0.2.5': {'doi': '10.5281/zenodo.49550',
                      'year': 2016,
                      'month': 'April',
                      },
            '0.2.4': {'doi': '10.5281/zenodo.47305',
                      'year': 2016,
                      'month': 'January',
                      },
            '0.2.3': {'doi': '10.5281/zenodo.47259',
                      'year': 2016,
                      'month': 'January',
                      },
            }


    PATTERNS = {'apa6': (u"Dzik, J. M., Łęski, S., & Puścian, A. ({date}). PyMICE (v. {version}) [computer software; RRID:nlx_158570]{doi}",
                         [('date', '{year}, {month}'),
                          ('date', 'n.d.'),
                          ('doi', '. doi: {doi}'),
                          ('doi', ''),
                          ]),
                'bibtex': (u"pymice{version}{{Title = {{{{PyMICE (v.~{version})}}}}, Note = {{computer software; RRID:nlx\\_158570}}, {basic}{extended}}}",
                           [('basic', "Author = {{Dzik, Jakub Mateusz and Łęski, Szymon and Puścian, Alicja}}"),
                            ('extended', ", Year = {{{year}}}, Month = {{{month}}}, Doi = {{{doi}}}"),
                            ('extended', ""),
                            ]),
                'latex': (u"\\emph{{PyMICE}} v.~{version}~\\cite{{pymice{version}}}",
                          [
                          ]),
                }

    def software(self, version=__version__, style='apa6'):
        pattern, sections = self.PATTERNS[style]
        return pattern.format(**self._getSections(version, sections))

    def _getSections(self, version, sectionsPattern):
        meta = self.META.get(version, {})
        sections = {'version': version}
        sections.update(self._sections(meta,
                                       reversed(sectionsPattern)))
        return sections

    def _sections(self, meta, patterns):
        for key, pattern in patterns:
            try:
                yield key, pattern.format(**meta)
            except KeyError:
                pass

reference = _Reference()