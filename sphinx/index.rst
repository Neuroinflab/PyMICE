.. PyMICE documentation master file, created by
   sphinx-quickstart on Wed Oct 21 17:18:44 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to PyMICE's documentation!
==================================

Contents:

.. toctree::
   :maxdepth: 2

Package pymice
--------------
.. automodule:: pymice

   .. autoclass:: Loader

      .. automethod:: __init__

      .. automethod:: getVisits

      .. automethod:: getLog

      .. automethod:: getEnvironment

      .. automethod:: getHardwareEvents

      .. automethod:: getAnimal

      .. automethod:: getCage

      .. automethod:: getInmates

      .. automethod:: getGroup

      .. automethod:: getStart

      .. automethod:: getEnd


   .. autoclass:: Merger

      .. automethod:: __init__

      .. automethod:: getVisits

      .. automethod:: getLog

      .. automethod:: getEnvironment

      .. automethod:: getHardwareEvents

      .. automethod:: getAnimal

      .. automethod:: getCage

      .. automethod:: getInmates

      .. automethod:: getGroup

      .. automethod:: getStart

      .. automethod:: getEnd


   Auxilary tools
   --------------
   .. autoclass:: ExperimentTimeline

      .. automethod:: __init__

      .. automethod:: getTime

      .. automethod:: sections


   .. autoclass:: DataValidator

      .. automethod:: __init__

      .. automethod:: __call__


   .. autoclass:: LickometerLogAnalyzer

      .. automethod:: __init__


   .. autoclass:: PresenceLogAnalyzer

      .. automethod:: __init__


   .. autoclass:: TestMiceData

      .. automethod:: __init__

      .. automethod:: __call__


   .. autofunction:: getTutorialData

   .. autodata:: __PGP_PUBLIC_KEY__
      :annotation: = < ASCII armored PGP public key >


Module pymice.debug
-------------------

.. automodule:: pymice.debug

   .. autofunction:: plotPhases


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

