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

if sys.version_info.major == 3:
    from functools import reduce

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

    PAPER_META = {'authors': [('Dzik', 'Jakub', 'Mateusz'),
                              (u'Puścian', 'Alicja'),
                              ('Mijakowska', 'Zofia'),
                              ('Radwanska', 'Kasia'),
                              (u'Łęski', 'Szymon'),
                              ],
                  'title': '{PyMICE}: A {Python} library for analysis of {IntelliCage} data',
                  'year': 2017,
                  'day': 22,
                  'month': 'June',
                  'journal': 'Behavior Research Methods',
                  'doi': '10.3758/s13428-017-0907-5',
                  'issn': '1554-3528',
                  'abstract': 'IntelliCage is an automated system for recording the behavior of a group of mice housed together. It produces rich, detailed behavioral data calling for new methods and software for their analysis. Here we present PyMICE, a free and open-source library for analysis of IntelliCage data in the Python programming language. We describe the design and demonstrate the use of the library through a series of examples. PyMICE provides easy and intuitive access to IntelliCage data, and thus facilitates the possibility of using numerous other Python scientific libraries to form a complete data analysis workflow.'
                  }


    DEFAULT_MARKDOWN = {'apa6': 'txt',
                        'bibtex': 'latex',
                        }
    SOFTWARE_PATTERNS = {
        'apa6': ({'txt': u"{authors} ({date}). {title} [{note}]{doi}",
                  'latex': u"\\bibitem{{pymice{version}}} {authors} ({date}). {title} [{note}]{doi}",
                  },
                 [('authors', _authorsBibliographyAPA6),
                  ('title', u"PyMICE (v.\u00A0{__version__})".format),
                  ('title', u"PyMICE".format),
                  ('date', u'{year},\u00A0{month}'.format),
                  ('date', 'n.d.'.format),
                  ('doi', u'. doi:\u00A0{doi}'.format),
                  ('doi', ''.format),
                  ('note', 'computer software; {rrid}'.format),
                  ('version', '{__version__}'.format),
                  ('version', ''.format),
                  ]),
        'bibtex': (u"pymice{version}{{Title = {{{{{title}}}}}, Note = {{{note}}}, Author = {{{authors}}}{date}{doi}}}",
                   [('authors', lambda **kwargs: ' and '.join(u'{}, {}'.format(a[0], ' '.join(a[1:])) for a in kwargs['authors'])),
                    ('title', u"PyMICE (v.\u00A0{__version__})".format),
                    ('title', u"PyMICE".format),
                    ('date', ", Year = {{{year}}}, Month = {{{month}}}".format),
                    ('date', "".format),
                    ('doi', ", Doi = {{{doi}}}".format),
                    ('doi', "".format),
                    ('note', 'computer software; {rrid}'.format),
                    ('version', '{__version__}'.format),
                    ('version', ''.format),
                    ]),
        }
    CITE_SOFTWARE_PATTERNS = {
        'apa6': ({'txt': u"PyMICE (Dzik, Puścian, Mijakowska, Radwanska, & Łęski, 2017{version}{authors}, {date})",
                  'latex': u"\\emph{{PyMICE}}~\\cite{{dzik2017pm{version_latex}}}",
                  },
                 [('authors', lambda **x: ', '.join([a[0] for a in x['authors'][:-1]] + ['& ' + x['authors'][-1][0]])),
                  ('date', '{year}'.format),
                  ('date', 'n.d.'.format),
                  ('version', u') v.\u00A0{__version__} ('.format),
                  ('version', '; '.format),
                  ('version_latex', '}} v.~{__version__}~\\cite{{pymice{__version__}'.format),
                  ('version_latex', ',pymice'.format),
                  ]),
        'bibtex': (u"\\emph{{PyMICE}}~\\cite{{dzik2017pm{version}}}",
                   [('version', '}} v.~{__version__}~\\cite{{pymice{__version__}'.format),
                    ('version', ',pymice'.format),
                   ]),
        }

    STYLE_ESCAPE = {} # XXX may be unnecessary
    MARKDOWN_ESCAPE = {
                       'latex': [('_', '\\_'),
                                 (u'\u00A0', '~'),
                                 ('<em>', '\\emph{'),
                                 ('</em>', '}'),
                                 ],
                       'html': [('{', ''),
                                ('}', ''),
                                ('&', '&amp;'),
                                (u'\u00A0', '&nbsp;'),
                                ],
                       'md': [('{', ''),
                              ('}', ''),
                              ('_', '\\_'),
                              ('<em>', '_'),
                              ('</em>', '_'),
                              ],
                       'rst': [('{', ''),
                               ('}', ''),
                               ('_', '\\_'),
                               ('<em>', '*'),
                               ('</em>', '*'),
                               ],
                       'txt': [('{', ''),
                               ('}', ''),
                               ('<em>', ''),
                               ('</em>', ''),
                               ]
                       }

    PAPER_PATTERNS = {'apa6': ({'txt': u"{authors} ({date}). {title}. {journal}{doi}",
                                'latex': u"\\bibitem{{dzik2017pm}} {authors} ({date}). {title}. {journal}{doi}",
                                },
                               [('authors', _authorsBibliographyAPA6),
                                ('date', u'{year}'.format),
                                ('title', u"{title}".format),
                                ('journal', '<em>{journal}</em>'.format),
                                ('doi', u'. doi:\u00A0{doi}'.format),
                                ]),
                      'bibtex': (u"dzik2017pm{{Title = {{{title}}}, Author = {{{authors}}}{date}{journal}{doi}{issn}{url}{abstract}}}",
                                 [('authors', lambda **kwargs: ' and '.join(u'{}, {}'.format(a[0], ' '.join(a[1:])) for a in kwargs['authors'])),
                                  ('title', u"{title}".format),
                                  ('date', ", Year = {{{year}}}, Month = {{{month}}}, Day = {{{day}}}".format),
                                  ('journal', ", Journal = {{{journal}}}".format),
                                  ('doi', ", Doi = {{{doi}}}".format),
                                  ('issn', ", Issn = {{{issn}}}".format),
                                  ('url', ", Url = {{http://dx.doi.org/{doi}}}".format),
                                  ('abstract', ", Abstract = {{{abstract}}}".format),
                                  ]),
                      }

    def __init__(self, style='apa6', markdown=None, version=__version__):
        self._style = style
        self._version = version
        self._setMarkdown(markdown)

    def _setMarkdown(self, markdown):
        self._markdown = markdown if markdown is not None else self.DEFAULT_MARKDOWN[self._style]

    def paperReference(self, style=None):
        if style is None:
            style = self._style

        pattern, sections = self._getFormatters(self.PAPER_PATTERNS,
                                                style)
        return self._applyMarkdown(self._formatMeta(pattern, sections,
                                                    self.PAPER_META,
                                                    style))

    def _formatMeta(self, template, sections, meta, style):
        return self._format(template,
                            self._sections(meta,
                                           reversed(sections),
                                           style))

    def _format(self, pattern, sections):
        return pattern.format(**dict(sections))

    def softwareReference(self, style=None, **kwargs):
        if style is None:
            style = self._style

        version = kwargs.get('version',
                             self._version)

        pattern, sections = self._getFormatters(self.SOFTWARE_PATTERNS,
                                                style)
        return self._applyMarkdown(self._formatMeta(pattern, sections,
                                                    self._getMeta(version),
                                                    style))

    def cite(self, version, style):
        pattern, sections = self._getFormatters(self.CITE_SOFTWARE_PATTERNS,
                                                style)
        formatted = self._formatMeta(pattern, sections, self._getMeta(version), style)
        return self._applyMarkdown(formatted)

    def _applyMarkdown(self, string):
        return reduce(lambda s, substitution: s.replace(*substitution),
                      self.MARKDOWN_ESCAPE[self._markdown],
                      string)

    def _getFormatters(self, formatters, style):
        pattern, sections = formatters[style]
        try:
            pattern = pattern[self._markdown]
        except TypeError:
            pass
        except KeyError:
            pattern = pattern[self.DEFAULT_MARKDOWN[style]]

        return pattern, sections

    def _getMeta(self, version):
        meta = self.DEFAULT_META.copy()
        if version is not None:
            meta['__version__'] = version

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
                yield key, self._style_escape(text, style)

    # XXX May be unnecessary
    def _style_escape(self, text, style):
        try:
            return self.STYLE_ESCAPE[style](text)
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