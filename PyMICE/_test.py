#!/usr/bin/env python
# encoding: utf-8
"""
_test.py

Copyright (c) 2012-2014 Laboratory of Neuroinformatics. All rights reserved.
"""

import os

try:
  from ._Loader import Loader

except ValueError:
  print 'from ._Loader import ... failed'
  try:
    from _Loader import Loader

  except ImportError:
    print 'from _Loader import ... failed'
    from PyMICE._Loader import Loader

testDir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../test'))
TEST_GLOBALS = {
  'ml_l1': Loader(os.path.join(testDir, 'legacy_data.zip'), getNpokes=True),
  #'ml_a1': Loader(os.path.join(testDir, 'analyzer_data.txt'), getNpokes=True),
  'ml_icp3': Loader(os.path.join(testDir, 'icp3_data.zip'), getNpokes=True,
                    getLogs=True, getEnv=True),
  'ml_empty': Loader(os.path.join(testDir, 'empty_data.zip'), getNpokes=True),
  'ml_retagged': Loader(os.path.join(testDir, 'retagged_data.zip'), getNpokes=True),
  }
