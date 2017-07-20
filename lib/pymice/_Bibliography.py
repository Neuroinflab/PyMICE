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
"""
.. versionadded:: 1.2.0
"""
from ._Version import __version__, __RRID__
import sys

import functools

if sys.version_info.major == 3:
    from functools import reduce

def _authorsBibliographyAPA6(authors, **kwargs):
    formatted = [_authorBibliographyAPA6(*a) for a in authors]
    return u', '.join(formatted[:-1] + [u'&\xa0' + formatted[-1]])

def _authorBibliographyAPA6(familyName, *names):
    return u'{},\u00a0{}'.format(familyName, u'\xa0'.join(n[0] + '.' for n in names))


def _determineStyle(f):
    @functools.wraps(f)
    def wrapper(self, style=None, **kwargs):
        return f(self,
                 style=self._getStyle(style).lower(),
                 **kwargs)

    return wrapper

def _determineMarkdown(f):
    @functools.wraps(f)
    def wrapper(self, style, markdown=None, **kwargs):
        return f(self,
                 style=style,
                 markdown=self._getMarkdown(style,
                                            markdown).lower(),
                 **kwargs)

    return wrapper

def _applyMarkdown(f):
    @functools.wraps(f)
    def wrapper(self, markdown, **kwargs):
        return self._applyMarkdown(f(self,
                                     markdown=markdown,
                                     **kwargs),
                                   markdown)

    return wrapper

def _fold(f):
    @functools.wraps(f)
    def wrapper(self, *args, **kwargs):
        return self._fold(f(self,
                            *args,
                            **kwargs))

    return wrapper

def _formatDostring(*args, **kwargs):
    def decorator(o):
        o.__doc__ = o.__doc__.format(*args, **kwargs)
        return o

    return decorator

class Citation(object):
    """
    A class of objects facilitating referencing the PyMICE library.

    Example::

      >>> citation = Citation(version='1.1.1')
      >>> print('''{reference}
      ... had no Citation class.
      ...
      ... Bibliography
      ...
      ... {reference.PAPER}
      ...
      ... {reference.SOFTWARE}
      ... '''.format(reference=citation))
      PyMICE (Dzik, Puścian, et al. 2017) v. 1.1.1 (Dzik, Łęski, & Puścian 2017)
      had no Citation class.

      Bibliography

      Dzik J. M., Puścian A., Mijakowska Z., Radwanska K., Łęski S. (June 22, 2017)
          "PyMICE: A Python library for analysis of IntelliCage data" Behavior
          Research Methods doi: 10.3758/s13428-017-0907-5

      Dzik J. M., Łęski S., Puścian A. (April 24, 2017) "PyMICE" computer software
          (v. 1.1.1; RRID:nlx_158570) doi: 10.5281/zenodo.557087

    .. versionadded:: 1.2.0
    """
    _DEFAULT_META = {'rrid': __RRID__,
                     'authors': [('Dzik', 'Jakub', 'Mateusz'),
                                 (u'Łęski', 'Szymon'),
                                 (u'Puścian', 'Alicja'),
                                 ],
                     }
    _META = {'1.2.0': {'doi': '10.5281/zenodo.832982',
                       'year': 2017,
                       'month': 'July',
                       'day': 21,
                       },
             '1.1.1': {'doi': '10.5281/zenodo.557087',
                       'year': 2017,
                       'month': 'April',
                       'day': 24,
                       },
             '1.1.0': {'doi': '10.5281/zenodo.200648',
                       'year': 2016,
                       'month': 'December',
                       'day': 13,
                       },
             '1.0.0': {'doi': '10.5281/zenodo.51092',
                       'year': 2016,
                       'month': 'May',
                       'day': 6,
                       },
             '0.2.5': {'doi': '10.5281/zenodo.49550',
                       'year': 2016,
                       'month': 'April',
                       'day': 11,
                       },
             '0.2.4': {'doi': '10.5281/zenodo.47305',
                       'year': 2016,
                       'month': 'January',
                       'day': 30,
                       },
             '0.2.3': {'doi': '10.5281/zenodo.47259',
                       'year': 2016,
                       'month': 'January',
                       'day': 30,
                       },
             }

    _PAPER_META = {
        'authors': [('Dzik', 'Jakub', 'Mateusz'),
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
        'journalAbbreviationNLM': 'Behav Res Methods',
        'doi': '10.3758/s13428-017-0907-5',
        'issn': '1554-3528',
        'abstract': '{IntelliCage} is an automated system for recording the '
                    'behavior of a group of mice housed together. It produces '
                    'rich, detailed behavioral data calling for new methods '
                    'and software for their analysis. Here we present {PyMICE},'
                    ' a free and open-source library for analysis of '
                    '{IntelliCage} data in the {Python} programming language. '
                    'We describe the design and demonstrate the use of the '
                    'library through a series of examples. {PyMICE} provides '
                    'easy and intuitive access to {IntelliCage} data, and thus '
                    'facilitates the possibility of using numerous other '
                    '{Python} scientific libraries to form a complete data '
                    'analysis workflow.'
        }

    _DEFAULT_STYLE = 'pymice'
    _DEFAULT_MARKDOWN = {'apa6': 'txt',
                         'bibtex': 'latex',
                         'pymice': 'txt',
                         'vancouver': 'txt',
                         }
    _SOFTWARE_PATTERNS = {
        'apa6': ({'txt': u"{authors} ({date}). {title} [{note}]{doi}",
                  'latex': u"\\bibitem{{{key}}} {authors} ({date}). {title} [{note}]{doi}",
                  },
                 [('authors', _authorsBibliographyAPA6),
                  ('title', u"PyMICE (v.\xa0{__version__})".format),
                  ('title', u"PyMICE".format),
                  ('date', u'{year},\xa0{month}'.format),
                  ('date', 'n.d.'.format),
                  ('doi', u'. doi:\xa0{doi}'.format),
                  ('doi', ''.format),
                  ('note', 'computer software; {rrid}'.format),
                  ('key', '{__software__}'.format),
                  ]),
        'bibtex': (u"@Misc{{{key},\nTitle = {{{{{title}}}}}{note},\nAuthor = {{{authors}}}{date}{doi}\n}}\n",
                   [('authors', lambda **kwargs: ' and '.join(u'{}, {}'.format(a[0], ' '.join(a[1:])) for a in kwargs['authors'])),
                    ('title', u"PyMICE (v.\xa0{__version__})".format),
                    ('title', u"PyMICE".format),
                    ('date', ",\nYear = {{{year}}},\nMonth = {{{month}}},\nDay = {{{day}}}".format),
                    ('date', "".format),
                    ('doi', ",\nDoi = {{{doi}}}".format),
                    ('doi', "".format),
                    ('note', ',\nNote = {{computer software; {rrid}}}'.format),
                    ('key', '{__software__}'.format),
                    ]),
        'pymice': ({'txt': u"{authors} {date}\"PyMICE\" computer software ({versionString}{doi}",
                    'latex': u"\\bibitem{{{key}}} {authors} {date}``PyMICE'' computer software ({versionString}{doi}",
                    },
                   [('authors', lambda **kwargs: ', '.join(u'\xa0'.join([a[0]] + [x[0] + '.' for x in a[1:]]) for a in kwargs['authors'])),
                    ('date', u'({month}\xa0{day},\xa0{year}) '.format),
                    ('date', ''.format),
                    ('versionString', u'v.\xa0{__version__}; {rrid})'.format),
                    ('versionString', u'{rrid})'.format),
                    ('doi', u' doi:\xa0{doi}'.format),
                    ('doi', ''.format),
                    ('key', '{__software__}'.format),
                    ]),
        'vancouver': ({'txt': u"{key}. {authors}. PyMICE [computer software].{versionString} Warsaw: Nencki Institute - PAS{date}.{doi}",
                       'latex': u"\\bibitem{{{key}}} {authors}. PyMICE [computer software].{versionString} Warsaw: Nencki Institute - PAS{date}.{doi}",
                       },
                      [('authors', lambda **kwargs: ', '.join(a[0] + u'\xa0' + ''.join(x[0] for x in a[1:]) for a in kwargs['authors'])),
                       ('versionString', u' Version {__version__}.'.format),
                       ('versionString', u''.format),
                       ('date', '; {year}'.format),
                       ('date', ''.format),
                       ('doi', u' DOI:\xa0{doi}'.format),
                       ('doi', ''.format),
                       ('key', '{__software__}'.format),
                       ]),
    }

    _CITE_PAPER_SOFTWARE_PATTERNS = {
        'apa6': ({'txt': u"PyMICE\xa0({paper}{version}{software})",
                  'latex': u"\\emph{{PyMICE}}~\\cite{{{paper}{versionLaTeX}{software}}}",
                  },
                 [('version', u') v.\xa0{__version__}\xa0('.format),
                  ('version', '; '.format),
                  ('versionLaTeX', '}} v.~{__version__}~\\cite{{'.format),
                  ('versionLaTeX', ','.format),
                  ('paper', u'{__cite_paper__}'.format),
                  ('software', u'{__cite_software__}'.format),
                  ]),
        'bibtex': (u"\\emph{{PyMICE}}~\\cite{{{paper}{version}{software}}}",
                   [('version', '}} v.~{__version__}~\\cite{{'.format),
                    ('version', ','.format),
                    ('paper', u'{__cite_paper__}'.format),
                    ('software', u'{__cite_software__}'.format),
                    ]),
        'pymice': ({'txt': u"PyMICE\xa0({paper}{version}{software})",
                    'latex': u"\\emph{{PyMICE}}~\\cite{{{paper}{versionLaTeX}{software}}}",
                    },
                   [('version', u') v.\xa0{__version__}\xa0('.format),
                    ('version', '; '.format),
                    ('versionLaTeX', '}} v.~{__version__}~\\cite{{'.format),
                    ('versionLaTeX', ','.format),
                    ('paper', u'{__cite_paper__}'.format),
                    ('software', u'{__cite_software__}'.format),
                    ]),
        'vancouver': ({'txt': u"PyMICE\xa0({rrid})\xa0[{paper}{version}{software}]",
                       'latex': u"\\emph{{PyMICE}}\xa0({rrid})\xa0\\cite{{{paper}{versionLaTeX}{software}}}",
                       },
                      [('rrid', '{rrid}'.format),
                       ('version', u'] v.\xa0{__version__}\xa0['.format),
                       ('version', ','.format),
                       ('versionLaTeX', u'}} v.\xa0{__version__}\xa0\\cite{{'.format),
                       ('versionLaTeX', ','.format),
                       ('paper', u'{__cite_paper__}'.format),
                       ('software', u'{__cite_software__}'.format),
                       ]),
    }
    _CITE_SOFTWARE_PATTERNS = {
        'apa6': ({'txt': u"{authors}, {date}",
                  'latex': u"{softwareKey}",
                  },
                 [('authors', lambda **x: ', '.join([a[0] for a in x['authors'][:-1]] + [u'&\xa0' + x['authors'][-1][0]])),
                  ('date', '{year}'.format),
                  ('date', 'n.d.'.format),
                  ('softwareKey', '{__software__}'.format),
                  ]),
        'bibtex': (u"{softwareKey}",
                   [('softwareKey', '{__software__}'.format),
                   ]),
        'pymice': ({'txt': u"Dzik, Łęski, &\xa0Puścian{date}",
                    'latex': u"{softwareKey}",
                    },
                   [('softwareKey', '{__software__}'.format),
                    ('date', ' {year}'.format),
                    ('date', ''.format),
                    ]),
        'vancouver': (u"{softwareKey}",
                      [('softwareKey', '{__software__}'.format),
                       ]),
    }
    _CITE_PAPER_PATTERNS = {
        'apa6': ({'txt': u"{authors}, {date}",
                  'latex': u"{paperKey}",
                  },
                 [('authors', lambda **x: ', '.join([a[0] for a in x['authors'][:-1]] + [u'&\xa0' + x['authors'][-1][0]])),
                  ('date', '{year}'.format),
                  ('date', 'n.d.'.format),
                  ('paperKey', '{__paper__}'.format),
                  ]),
        'bibtex': (u"{paperKey}",
                   [('paperKey', '{__paper__}'.format),
                   ]),
        'pymice': ({'txt': u"Dzik, Puścian, et\xa0al.{date}",
                    'latex': u"{paperKey}",
                    },
                   [('date', ' {year}'.format),
                    ('date', ''.format),
                    ('paperKey', '{__paper__}'.format),
                    ]),
        'vancouver': (u"{paperKey}",
                      [('paperKey', '{__paper__}'.format),
                       ]),
    }
    _PAPER_PATTERNS = {'apa6': ({'txt': u"{authors} ({date}). {title}. {journal}{doi}",
                                 'latex': u"\\bibitem{{{key}}} {authors} ({date}). {title}. {journal}{doi}",
                                 },
                                [('authors', _authorsBibliographyAPA6),
                                 ('date', u'{year}'.format),
                                 ('title', u'{title}'.format),
                                 ('journal', '<em>{journal}</em>'.format),
                                 ('doi', u'. doi:\xa0{doi}'.format),
                                 ('key', '{__paper__}'.format),
                                ]),
                       'bibtex': (u"@Article{{{key}{title},\nAuthor = {{{authors}}}{date}{journal}{doi}{issn}{url}{abstract}\n}}\n",
                                 [('authors', lambda **kwargs: ' and '.join(u'{}, {}'.format(a[0], ' '.join(a[1:])) for a in kwargs['authors'])),
                                  ('title', u",\nTitle = {{{title}}}".format),
                                  ('date', ",\nYear = {{{year}}},\nMonth = {{{month}}},\nDay = {{{day}}}".format),
                                  ('journal', ",\nJournal = {{{journal}}}".format),
                                  ('doi', ",\nDoi = {{{doi}}}".format),
                                  ('issn', ",\nIssn = {{{issn}}}".format),
                                  ('url', ",\nUrl = {{http://dx.doi.org/{doi}}}".format),
                                  ('abstract', ",\nAbstract = {{{abstract}}}".format),
                                  ('key', '{__paper__}'.format),
                                  ]),
                       'pymice': ({'txt': u"{authors} ({date}) \"{title}\" {journal} {doi}",
                                   'latex': u"\\bibitem{{{key}}} {authors} ({date}) ``{title}'' {journal} {doi}",
                                   },
                                 [('authors', lambda **kwargs: ', '.join(u'\xa0'.join([a[0]] + [x[0] + '.' for x in a[1:]]) for a in kwargs['authors'])),
                                  ('date', u'{month}\xa0{day},\xa0{year}'.format),
                                  ('title', u'{title}'.format),
                                  ('journal', '{journal}'.format),
                                  ('doi', u'doi:\xa0{doi}'.format),
                                  ('key', '{__paper__}'.format),
                                  ]),
                       'vancouver': ({'txt': u"{key}. {authors}. {title}. {journal}. {date}. {doi}",
                                      'latex': u"\\bibitem{{{key}}} {authors}. {title}. {journal}. {date}. {doi}",
                                      },
                                     [('authors', lambda **kwargs: ', '.join(a[0] + u'\xa0' + ''.join(x[0] for x in a[1:]) for a in kwargs['authors'])),
                                      ('date', u'{year}'.format),
                                      ('title', u'{title}'.format),
                                      ('journal', '{journalAbbreviationNLM}'.format),
                                      ('doi', u'DOI:\xa0{doi}'.format),
                                      ('key', '{__paper__}'.format),
                                      ]),
    }

    _MARKDOWN_ESCAPE = {
                       'latex': [('_', '\\_'),
                                 (u'\xa0', '~'),
                                 ('<em>', '\\emph{'),
                                 ('</em>', '}'),
                                 ],
                       'html': [('{', ''),
                                ('}', ''),
                                ('&', '&amp;'),
                                (u'\xa0', '&nbsp;'),
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

    def __init__(self, style=None, markdown=None, version=__version__,
                       paperKey=None, softwareKey=None,
                       **kwargs):
        """
        :keyword style: reference style; must be one of 'PyMICE', 'APA6', 'Vancouver',
                        'BibTeX'; defaults to 'PyMICE'
        :type style: str

        :keyword markdown: markdown language to be used; must be one of 'txt', 'rst',
                           'md', 'html', 'LaTeX'; default value depends on the reference
                           style
        :type markdown: str

        :keyword version: version of the PyMICE library to be referenced; None if no
                          version shall be referenced; omit to reference the current
                          version
        :type version: str or None

        :keyword paperKey: a key (e.g. LaTeX label or entry number) for the bibliography
                           entry referencing the paper introducing the PyMICE library
        :type paperKey: str or int

        :keyword softwareKey: a key (e.g. LaTeX label or entry number) for the
                              bibliography entry referencing the PyMICE library
        :type softwareKey: str or int

        .. warning::

          All constructor parameters shall be given as keyword arguments.

          No undocumented parameter shall be used.
        """
        self._version = version
        self._style = style
        self._markdown = markdown
        self._maxLineWidth = kwargs.get('maxLineWidth', 80)
        self._paperKey = paperKey
        self._softwareKey = softwareKey

    def _getPaperKey(self, markdown):
        return self._paperKey if self._paperKey is not None else 'dzik2017pm' if markdown == 'latex' else 1

    def _getSoftwareKey(self, meta, markdown):
        if self._softwareKey is not None: return self._softwareKey
        if markdown == 'latex':
            try:
                return 'pymice{__version__}'.format(**meta)
            except KeyError:
                return 'pymice'
        return 2

    @_determineStyle
    @_determineMarkdown
    @_fold
    @_applyMarkdown
    @_formatDostring(unicode='unicode' if sys.version_info.major < 3 else 'str')
    def referencePaper(self, style, markdown):
        """
        Generete a bibliography entry for the paper introducing the PyMICE library.
        Keyword attributes override parameters set in the object constructor.

        :keyword style: reference style; must be one of 'PyMICE', 'APA6', 'Vancouver',
                        'BibTeX'
        :type style: str

        :keyword markdown: markdown language to be used; must be one of 'txt', 'rst',
                           'md', 'html', 'LaTeX'
        :type markdown: str

        :returns: the bibliography entry
        :rtype: {unicode}

        Example::

          >>> citation = Citation()
          >>> print('''Bibliography:
          ...
          ... {{reference}}
          ... '''.format(reference=citation.referencePaper(style='Vancouver',
          ...                                              markdown='HTML')))
          Bibliography:

          1. Dzik&nbsp;JM, Puścian&nbsp;A, Mijakowska&nbsp;Z, Radwanska&nbsp;K,
              Łęski&nbsp;S. PyMICE: A Python library for analysis of IntelliCage data.
              Behav Res Methods. 2017. DOI:&nbsp;10.3758/s13428-017-0907-5

        .. warning::

          All constructor parameters shall be given as keyword arguments.
        """
        return self._applyTemplate(self._PAPER_PATTERNS,
                                   self._PAPER_META, #.copy(),
                                   style,
                                   markdown)

    @_determineStyle
    @_determineMarkdown
    @_fold
    @_applyMarkdown
    @_formatDostring(unicode='unicode' if sys.version_info.major < 3 else 'str')
    def referenceSoftware(self, style, markdown, **kwargs):
        """
        Generete a bibliography entry for the PyMICE library.
        Keyword attributes override parameters set in the object constructor.

        :keyword style: reference style; must be one of 'PyMICE', 'APA6', 'Vancouver',
                        'BibTeX'
        :type style: str

        :keyword markdown: markdown language to be used; must be one of 'txt', 'rst',
                           'md', 'html', 'LaTeX'; if default value depends on the reference
                           style (if not set in the constructor)
        :type markdown: str

        :keyword version: version of the PyMICE library to be referenced; None if no
                          version shall be referenced
        :type version: str or None

        :returns: the bibliography entry
        :rtype: {unicode}

        Example::

          >>> citation = Citation()
          >>> print(citation.referenceSoftware(style='BibTeX',
          ...                                  version='1.0.0'))
          @Misc{{pymice1.0.0,
          Title = {{{{PyMICE (v.~1.0.0)}}}},
          Note = {{computer software; RRID:nlx\_158570}},
          Author = {{Dzik, Jakub Mateusz and Łęski, Szymon and Puścian, Alicja}},
          Year = {{2016}},
          Month = {{May}},
          Day = {{6}},
          Doi = {{10.5281/zenodo.51092}}
          }}

        .. warning::

          All constructor parameters shall be given as keyword arguments.
        """
        return self._applyTemplate(self._SOFTWARE_PATTERNS,
                                   self._getSoftwareReleaseMeta(kwargs),
                                   style,
                                   markdown)

    def _getSoftwareReleaseMeta(self, kwargs):
        return self._getSoftwareMeta(self._getVersion(kwargs))

    def _getVersion(self, kwargs):
        return kwargs.get('version',
                          self._version)

    @_determineStyle
    @_determineMarkdown
    @_applyMarkdown
    @_formatDostring(unicode='unicode' if sys.version_info.major < 3 else 'str')
    def cite(self, style, markdown, **kwargs):
        """
        Generete an in-text reference to the PyMICE library in the recommended format.
        Keyword attributes override parameters set in the object constructor.

        :keyword style: reference style; must be one of 'PyMICE', 'APA6', 'Vancouver',
                        'BibTeX'
        :type style: str

        :keyword markdown: markdown language to be used; must be one of 'txt', 'rst',
                           'md', 'html', 'LaTeX'; if default value depends on the reference
                           style (if not set in the constructor)
        :type markdown: str

        :keyword version: version of the PyMICE library to be referenced; None if no
                          version shall be referenced
        :type version: str or None

        :returns: the in-text reference
        :rtype: {unicode}

        Example::

          >>> citation = Citation()
          >>> print(reference.cite(version='0.2.3'))
          PyMICE (Dzik, Puścian, et al. 2017) v. 0.2.3 (Dzik, Łęski, & Puścian 2016)

        .. warning::

          All constructor parameters shall be given as keyword arguments.
        """
        return self._applyTemplate(self._CITE_PAPER_SOFTWARE_PATTERNS,
                                   self._getCiteMeta(style, markdown,
                                                     **kwargs),
                                   style,
                                   markdown)

    def _getCiteMeta(self, style, markdown, **kwargs):
        meta = self._DEFAULT_META.copy()
        meta.update({'__cite_paper__': self._citePaper(style,
                                                       markdown),
                     '__cite_software__': self._citeSoftware(style,
                                                             markdown,
                                                             kwargs)})
        version = self._getVersion(kwargs)
        if version is not None:
            meta['__version__'] = version

        return meta

    @_determineStyle
    @_determineMarkdown
    @_applyMarkdown
    @_formatDostring(unicode='unicode' if sys.version_info.major < 3 else 'str')
    def citeSoftware(self, style, markdown, **kwargs):
        """
        Prefabricate the stem of an in-text reference to the PyMICE library.
        Keyword attributes override parameters set in the object constructor.

        :keyword style: reference style; must be one of 'PyMICE', 'APA6', 'Vancouver',
                        'BibTeX'
        :type style: str

        :keyword markdown: markdown language to be used; must be one of 'txt', 'rst',
                           'md', 'html', 'LaTeX'; if default value depends on the reference
                           style (if not set in the constructor)
        :type markdown: str

        :keyword version: version of the PyMICE library to be referenced; None if no
                          version shall be referenced
        :type version: str or None

        :returns: the prefabricated reference stem
        :rtype: {unicode}

        Example::

          >>> citation = Citation()
          >>> print(reference.citeSoftware(version='1.1.1', style='APA6'))
          Dzik, Łęski, & Puścian, 2017

        .. warning::

          All constructor parameters shall be given as keyword arguments.
        """
        return self._citeSoftware(style, markdown, kwargs)

    def _citeSoftware(self, style, markdown, kwargs):
        return self._applyTemplate(self._CITE_SOFTWARE_PATTERNS,
                                   self._getSoftwareReleaseMeta(kwargs),
                                   style,
                                   markdown)
    @_determineStyle
    @_determineMarkdown
    @_applyMarkdown
    @_formatDostring(unicode='unicode' if sys.version_info.major < 3 else 'str')
    def citePaper(self, style, markdown):
        """
        Prefabricate the stem of an in-text reference to the publication introducing the
        PyMICE library.
        Keyword attributes override parameters set in the object constructor.

        :keyword style: reference style; must be one of 'PyMICE', 'APA6', 'Vancouver',
                        'BibTeX'
        :type style: str

        :keyword markdown: markdown language to be used; must be one of 'txt', 'rst',
                           'md', 'html', 'LaTeX'; if default value depends on the reference
                           style (if not set in the constructor)
        :type markdown: str

        :returns: the prefabricated reference stem
        :rtype: {unicode}

        Example::

          >>> citation = Citation()
          >>> print('''The library has been introduced in our paper~\\\\cite{{{{{{}}}}}},
          ... so we ask that reference to the paper is provided in any published
          ... research making use of PyMICE.
          ... '''.format(reference.citePaper(markdown='LaTeX')))
          The library has been introduced in our paper~\\cite{{dzik2017pm}},
          so we ask that reference to the paper is provided in any published
          research making use of PyMICE.


        .. warning::

          All constructor parameters shall be given as keyword arguments.
        """
        return self._citePaper(style, markdown)

    def _citePaper(self, style, markdown):
        return self._applyTemplate(self._CITE_PAPER_PATTERNS,
                                   self._PAPER_META,
                                   style,
                                   markdown)

    def _getStyle(self, style):
        if style is not None: return style
        if self._style is not None: return self._style
        return self._DEFAULT_STYLE

    def _applyTemplate(self, template, meta, style, markdown):
        meta.update(__paper__ = self._getPaperKey(markdown),
                    __software__ = self._getSoftwareKey(meta, markdown))
        pattern, sections = self._getFormatters(template,
                                                style,
                                                markdown)
        formatted = self._formatMeta(pattern, sections, meta)
        return formatted

    def _fold(self, string):
        maxWidth = self._maxLineWidth
        if maxWidth is None:
            return string

        indentWidth = 4

        words = [w for l in string.splitlines(True) for w in l.split(' ') if w != '' ]
        lines = [words[0]]

        for w in words[1:]:
            if lines[-1][-1] == '\n':
                lines.append(w)

            elif len(w.rstrip('\n')) + len(lines[-1]) >= maxWidth:
                lines.append(' ' * indentWidth + w)

            else:
                lines[-1] += ' ' + w

        if lines[-1][-1] == '\n':
            lines.append('')

        return '\n'.join(l.rstrip('\n') for l in lines)

    def _formatMeta(self, template, sections, meta):
        return self._format(template,
                            self._sections(meta,
                                           reversed(sections)))

    def _format(self, pattern, sections):
        return pattern.format(**dict(sections))

    def _applyMarkdown(self, string, markdown):
        return reduce(lambda s, substitution: s.replace(*substitution),
                      self._MARKDOWN_ESCAPE[markdown],
                      string)

    def _getMarkdown(self, style, markdown):
        if markdown is not None: return markdown
        if self._markdown is not None: return self._markdown

        try:
            return self._DEFAULT_MARKDOWN[style]
        except KeyError:
            pass #return self._DEFAULT_MARKDOWN[self._DEFAULT_STYLE]

    def _getFormatters(self, formatters, style, markdown):
        pattern, sections = formatters[style]
        try:
            pattern = pattern[markdown]
        except TypeError:
            pass
        except KeyError:
            pattern = pattern[self._DEFAULT_MARKDOWN[style]]

        return pattern, sections

    def _getSoftwareMeta(self, version):
        meta = self._DEFAULT_META.copy()
        if version is not None:
            meta['__version__'] = version

        try:
            meta.update(self._META[version])
        except KeyError:
            pass

        return meta

    def _sections(self, meta, formatters):
        for key, formatter in formatters:
            try:
                yield key, formatter(**meta)
            except KeyError:
                pass

    def _str(self):
        return self.cite()

    if sys.version_info.major < 3:
        def __unicode__(self):
            """
            Example::

              >>> citation = Citation(version='1.1.1')
              >>> print(unicode(citation))
              PyMICE (Dzik, Puścian, et al. 2017) v. 1.1.1 (Dzik, Łęski, & Puścian 2017)

            :return: recommended in-text reference
            :rtype: unicode
            """
            return self._str()

        def __str__(self):
            """
            Example::

              >>> citation = Citation(version='1.1.1')
              >>> print(str(citation))
              PyMICE (Dzik, Puścian, et al. 2017) v. 1.1.1 (Dzik, Łęski, & Puścian 2017)

            :return: UTF-8 encoded recommended in-text reference
            :rtype: str
            """
            return self._str().encode('utf-8')

    else:
        def __str__(self):
            """
            Example::

              >>> citation = Citation(version='1.1.1')
              >>> print(str(citation))
              PyMICE (Dzik, Puścian, et al. 2017) v. 1.1.1 (Dzik, Łęski, & Puścian 2017)


            :return: recommended in-text reference
            :rtype: str
            """
            return self._str()

    @property
    @_formatDostring(unicode='unicode' if sys.version_info.major < 3 else 'str')
    def SOFTWARE(self):
        """
        A bibliography entry for the PyMICE library.

        Example::

          >>> citation = Citation(version='1.1.1')
          >>> print('''Bibliography:
          ...
          ... {{reference.SOFTWARE}}
          ... '''.format(reference=citation))
          Bibliography:

          Dzik J. M., Łęski S., Puścian A. (April 24, 2017) "PyMICE" computer software
              (v. 1.1.1; RRID:nlx_158570) doi: 10.5281/zenodo.557087

        :type: {unicode}
        """
        return self.referenceSoftware()

    @property
    @_formatDostring(unicode='unicode' if sys.version_info.major < 3 else 'str')
    def PAPER(self):
        """
        A bibliography entry for the paper introducing the PyMICE library.

        Example::

          >>> citation = Citation()
          >>> print('''Bibliography:
          ...
          ... {{reference.PAPER}}
          ... '''.format(reference=citation))
          Bibliography:

          Dzik J. M., Puścian A., Mijakowska Z., Radwanska K., Łęski S. (June 22, 2017)
              "PyMICE: A Python library for analysis of IntelliCage data" Behavior
              Research Methods doi: 10.3758/s13428-017-0907-5

        :type: {unicode}
        """
        return self.referencePaper()

    @property
    @_formatDostring(unicode='unicode' if sys.version_info.major < 3 else 'str')
    def CITE_SOFTWARE(self):
        """
        A prefabricated stem of an in-text reference of the PyMICE library.

        :type: {unicode}
        """
        return self.citeSoftware()

    @property
    @_formatDostring(unicode='unicode' if sys.version_info.major < 3 else 'str')
    def CITE_PAPER(self):
        """
        A prefabricated stem of an in-text reference of the paper introducing the PyMICE
        library.

        :type: {unicode}
        """
        return self.citePaper()


reference = Citation()