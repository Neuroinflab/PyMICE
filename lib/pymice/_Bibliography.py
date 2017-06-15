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

from ._Version import __version__, __RRID__


class _Reference(object):
    META = {'1.1.1': {'doi': '10.5281/zenodo.557087',
                      'year': 2017,
                      'month': 'April',
                      'rrid': __RRID__,
                      },
            '1.1.0': {'doi': '10.5281/zenodo.200648',
                      'year': 2016,
                      'month': 'December',
                      'rrid': __RRID__,
                      },
            '1.0.0': {'doi': '10.5281/zenodo.51092',
                      'year': 2016,
                      'month': 'May',
                      'rrid': __RRID__,
                      },
            '0.2.5': {'doi': '10.5281/zenodo.49550',
                      'year': 2016,
                      'month': 'April',
                      'rrid': __RRID__,
                      },
            '0.2.4': {'doi': '10.5281/zenodo.47305',
                      'year': 2016,
                      'month': 'January',
                      'rrid': __RRID__,
                      },
            '0.2.3': {'doi': '10.5281/zenodo.47259',
                      'year': 2016,
                      'month': 'January',
                      'rrid': __RRID__,
                      },
            }


    SOFTWARE_PATTERNS = {'apa6': (u"Dzik, J. M., Łęski, S., & Puścian, A. ({date}). PyMICE (v. {version}) [{note}]{doi}",
                                  [('date', '{year}, {month}'),
                                   ('date', 'n.d.'),
                                   ('doi', '. doi: {doi}'),
                                   ('doi', ''),
                                   ('note', 'computer software; {rrid}'),
                                   ('note', 'computer software; {}'.format(__RRID__)),
                                   ]),
                         'bibtex': (u"pymice{version}{{Title = {{{{PyMICE (v.~{version})}}}}, Note = {{{note}}}, {basic}{extended}}}",
                                    [('basic', u"Author = {{Dzik, Jakub Mateusz and Łęski, Szymon and Puścian, Alicja}}"),
                                     ('extended', ", Year = {{{year}}}, Month = {{{month}}}, Doi = {{{doi}}}"),
                                     ('extended', ""),
                                     ('note', 'computer software; {rrid}'),
                                     ('note', 'computer software; {}'.format(__RRID__)),
                                     ]),
                         }
    CITE_SOFTWARE_PATTERNS = {'latex': (u"\\emph{{PyMICE}} v.~{version}~\\cite{{pymice{version}}}",
                                        [
                                        ]),
                         }

    ESCAPE = {'bibtex': lambda x: x.replace('_', '\\_')}

    def software(self, version=__version__, style='apa6'):
        pattern, sections = self.SOFTWARE_PATTERNS[style]
        return pattern.format(**self._getSections(version, sections, style))

    def citeSoftware(self, version, style):
        pattern, sections = self.CITE_SOFTWARE_PATTERNS[style]
        return pattern.format(**self._getSections(version, sections, style))

    def _getSections(self, version, sectionsPattern, style):
        meta = self.META.get(version, {})
        sections = {'version': version}
        sections.update(self._sections(meta,
                                       reversed(sectionsPattern),
                                       style))
        return sections

    def _sections(self, meta, patterns, style):
        for key, pattern in patterns:
            try:
                text = pattern.format(**meta)
            except KeyError:
                pass
            else:
                yield key, self._escape(text, style)

    def _escape(self, text, style):
        try:
            return self.ESCAPE[style](text)
        except:
            return text


reference = _Reference()