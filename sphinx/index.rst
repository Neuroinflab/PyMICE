.. PyMICE documentation master file, created by
   sphinx-quickstart on Wed Oct 21 17:18:44 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Introduction
============

.. toctree::
   :maxdepth: 2


.. image:: https://badge.fury.io/py/PyMICE.svg
    :target: https://badge.fury.io/py/PyMICE
    :alt: PyPI badge

.. image:: https://travis-ci.org/Neuroinflab/PyMICE.svg?branch=master
    :target: https://travis-ci.org/Neuroinflab/PyMICE
    :alt: travis build badge

PyMICE is a Python® library for mice behavioural data analysis.

The library can be used for loading and analysing of data obtained
from IntelliCage™ system in an intuitive way in Python programming language.

The library provides user with an object oriented application programming
interface (API) and a data abstraction layer. It also comes with auxiliary
tools supporting development of analysis workflows, like data validators and
a tool for workflow configuration.

For more details please see `The project website
<https://neuroinflab.wordpress.com/research/pymice/>`_.

PyMICE package manual
=====================

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


   .. autoclass:: InspectFailures

      .. automethod:: __init__

      .. automethod:: __call__


   .. autofunction:: getTutorialData

   .. autodata:: __PGP_PUBLIC_KEY__
      :annotation: = < ASCII armored PGP public key >


Module pymice.debug
-------------------

.. automodule:: pymice.debug

   .. autofunction:: plotPhases


..
    Module pymice._Ens
    ------------------

    .. automodule:: pymice._Ens

       .. autoclass:: Ens

          .. autoclass:: ReadOnlyError

          .. autoclass:: AmbiguousInitializationError

          .. automethod:: map


Authors
=======

* The library

  * Jakub Kowalski
  * Szymon Łęski


* Tutorial data

  * Alicja Puścian


Acknowledgement
===============

JK and SŁ supported by Symfonia NCN grant: UMO-2013/08/W/NZ4/00691.

AP supported by a grant from Switzerland through the Swiss Contribution to the
enlarged European Union (PSPB-210/2010 to Ewelina Knapska and Hans-Peter Lipp).


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

