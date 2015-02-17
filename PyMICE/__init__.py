#!/usr/bin/env python
# encoding: utf-8
"""
PyMICE package

A collection of tools to access IntelliCage data.

Copyright (c) 2012-2015 Laboratory of Neuroinformatics. All rights reserved.
"""

from .Data import Loader, Merger
from ._Tools import hTime, convertTime
from ._Metadata import Phase, ExperimentConfigFile
from ._Results import ResultsCSV
__ID__ = 'nlx_158570'
__version__ = __ID__ + ' 0'
__all__ = []

