#!/usr/bin/env python
# encoding: utf-8
"""
_test.py

Copyright (c) 2012-2014 Laboratory of Neuroinformatics. All rights reserved.
"""

import os

try:
  from .Loader import MiceLoader

except ValueError:
  print 'from .Loader import ... failed'
  try:
    from Loader import MiceLoader

  except ImportError:
    print 'from Loader import ... failed'
    from Mice.Loader import MiceLoader

testDir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../test'))
TEST_GLOBALS = {
  'ml_l1': MiceLoader(os.path.join(testDir, 'legacy_data.zip')),
  #'ml_a1': MiceLoader(os.path.join(testDir, 'analyzer_data.txt')),
  'ml_empty': MiceLoader(os.path.join(testDir, 'empty_data.zip')),
  'ml_icp3': MiceLoader(os.path.join(testDir, 'icp3_data.zip')),
  }
