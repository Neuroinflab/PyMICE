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
import sys

def _authorsBibliographyAPA6(authors, **kwargs):
    formatted = [_authorBibliographyAPA6(*a) for a in authors]
    return u', '.join(formatted[:-1] + ['& ' + formatted[-1]])

def _authorBibliographyAPA6(familyName, *names):
    return u'{},\u00a0{}'.format(familyName, u'\u00A0'.join(n[0] + '.' for n in names))

class Citation(object):
    DEFAULT_META = {'rrid': __RRID__,
                    'authors': [('Dzik', 'Jakub', 'Mateusz'),
                                (u'Łęski', 'Szymon'),
                                (u'Puścian', 'Alicja'),
                                ],
                    }
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


    SOFTWARE_PATTERNS = {'apa6': (u"{authors} ({date}). {title} [{note}]{doi}",
                                  [('authors', _authorsBibliographyAPA6),
                                   ('title', u"PyMICE (v.\u00A0{version})".format),
                                   ('date', u'{year},\u00A0{month}'.format),
                                   ('date', 'n.d.'.format),
                                   ('doi', u'. doi:\u00A0{doi}'.format),
                                   ('doi', ''.format),
                                   ('note', 'computer software; {rrid}'.format),
                                   ]),
                         'bibtex': (u"pymice{version}{{Title = {{{{{title}}}}}, Note = {{{note}}}, Author = {{{authors}}}{date}{doi}}}",
                                    [('authors', lambda **kwargs: ' and '.join(u'{}, {}'.format(a[0], ' '.join(a[1:])) for a in kwargs['authors'])),
                                     ('title', u"PyMICE (v.\u00A0{version})".format),
                                     ('date', ", Year = {{{year}}}, Month = {{{month}}}".format),
                                     ('date', "".format),
                                     ('doi', ", Doi = {{{doi}}}".format),
                                     ('doi', "".format),
                                     ('note', 'computer software; {rrid}'.format),
                                     ]),
                         'latex': (u"\\bibitem{{pymice{version}}} {authors} ({date}). {title} [{note}]{doi}",
                                   [('authors', _authorsBibliographyAPA6),
                                    ('title', u"PyMICE (v.\u00A0{version})".format),
                                    ('date', u'{year},\u00A0{month}'.format),
                                    ('date', 'n.d.'.format),
                                    ('doi', u'. doi:\u00A0{doi}'.format),
                                    ('doi', ''.format),
                                    ('note', 'computer software; {rrid}'.format),
                                    ]),
                         }
    CITE_SOFTWARE_PATTERNS = {'latex': (u"\\emph{{PyMICE}} v.~{version}~\\cite{{pymice{version}}}",
                                        [
                                        ]),
                              'bibtex': (u"\\emph{{PyMICE}} v.~{version}~\\cite{{pymice{version}}}",
                                        [
                                        ]),
                              'apa6':  (u"PyMICE v.\u00A0{version} ({authors}, {date})",
                                        [('authors', lambda **x: ', '.join([a[0] for a in x['authors'][:-1]] + ['& ' + x['authors'][-1][0]])),
                                         ('date', '{year}'.format),
                                         ('date', 'n.d.'.format),
                                         ]),
                              }

    ESCAPE = {'bibtex': lambda x: x.replace('_', '\\_').replace(u'\u00A0', '~'),
              'latex': lambda x: x.replace('_', '\\_').replace(u'\u00A0', '~'),
              }

    def __init__(self, style='apa6', version=__version__):
        self._style = style
        self._version = version

    def softwareReference(self, version=None, style=None):
        if style is None:
            style = self._style

        if version is None:
            version = self._version

        pattern, sections = self.SOFTWARE_PATTERNS[style]
        return pattern.format(**self._getSections(version, sections, style))

    def cite(self, version, style):
        pattern, sections = self.CITE_SOFTWARE_PATTERNS[style]
        return pattern.format(**self._getSections(version, sections, style))

    def _getSections(self, version, sectionsPattern, style):
        sections = {'version': version}
        sections.update(self._sections(self._getMeta(version),
                                       reversed(sectionsPattern),
                                       style))
        return sections

    def _getMeta(self, version):
        meta = self.DEFAULT_META.copy()
        meta['version'] = version

        try:
            meta.update(self.META[version])
        except KeyError:
            pass

        return meta

    def _sections(self, meta, formatters, style):
        for key, formatter in formatters:
            try:
                text = formatter(**meta)
            except KeyError:
                pass
            else:
                yield key, self._escape(text, style)

    def _escape(self, text, style):
        try:
            return self.ESCAPE[style](text)
        except:
            return text

    def _str(self):
        return self.cite(self._version, self._style)

    if sys.version_info.major < 3:
        def __unicode__(self):
            return self._str()

        def __str__(self):
            return self._str().encode('utf-8')

    else:
        def __str__(self):
            return self._str()

reference = Citation()