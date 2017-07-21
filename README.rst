PyMICE Python library
=====================

.. image:: https://badge.fury.io/py/PyMICE.svg
    :target: https://badge.fury.io/py/PyMICE
    :alt: PyPI badge

.. image:: https://travis-ci.org/Neuroinflab/PyMICE.svg?branch=master
    :target: https://travis-ci.org/Neuroinflab/PyMICE
    :alt: Travis badge

.. image:: https://img.shields.io/badge/License-GPL%20v3-blue.svg
    :target: https://www.gnu.org/licenses/gpl-3.0
    :alt: License: GPL v3 badge

.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.832982.svg
   :target: https://doi.org/10.5281/zenodo.832982
   :alt: DOI badge

PyMICE is a Python® library for mice behavioural data analysis.

The library can be used for loading and analysing of data obtained
from IntelliCage™ system in an intuitive way in Python programming language.

The library provides user with an object oriented application programming
interface (API) and a data abstraction layer. It also comes with auxiliary
tools supporting development of analysis workflows, like data validators and
a tool for workflow configuration.


Terms of use
------------

The library is available under `GPL3 license
<http://www.gnu.org/licenses/gpl-3.0>`_.

We ask that  that reference to our paper as well as to the library itself is
provided in any published research making use of PyMICE.

The recommended in-text citation format is:
``PyMICE (Dzik, Puścian, et al. 2017) v. 1.2.0 (Dzik, Łęski, & Puścian 2017)``

and the recommended bibliography entry format:

  Dzik J. M., Łęski S., Puścian A. (July 21, 2017) "PyMICE" computer software
  (v. 1.2.0; RRID:nlx_158570) doi: 10.5281/zenodo.832982

  Dzik J. M., Puścian A., Mijakowska Z., Radwanska K., Łęski S. (June 22, 2017)
  "PyMICE: A Python library for analysis of IntelliCage data" Behavior Research
  Methods doi: 10.3758/s13428-017-0907-5

If the journal does not allow for inclusion of the `resource identifier
<http://journals.plos.org/plosone/article?id=10.1371/journal.pone.0146300>`_
(RRID:nlx_158570) in the bibliography, we ask to provide it in-text:
``PyMICE (RRID:nlx_158570) [1] v. 1.2.0 [2]``

  1. Dzik JM, Puścian A, Mijakowska Z, Radwanska K, Łęski S. PyMICE: A Python
     library for analysis of IntelliCage data. Behav Res Methods. 2017.
     DOI: 10.3758/s13428-017-0907-5
  2. Dzik JM, Łęski S, Puścian A. PyMICE [computer software]. Version 1.2.0.
     Warsaw: Nencki Institute - PAS; 2017. DOI: 10.5281/zenodo.832982

We have provided a solution to facilitate referencing to the library. Please
run::

  >>> help(pm.Citation)

for more information (given that the library is imported as ``pm``).


More details
------------

For more details please see `The project website
<https://neuroinflab.wordpress.com/research/pymice/>`_.


Authors
-------

* The library

  * Jakub M. Dzik a.k.a. Kowalski
  * Szymon Łęski


* Tutorial data

  * Alicja Puścian


Acknowledgement
---------------

JD and SŁ supported by Symfonia NCN grant: UMO-2013/08/W/NZ4/00691.

AP supported by a grant from Switzerland through the Swiss Contribution to the
enlarged European Union (PSPB-210/2010 to Ewelina Knapska and Hans-Peter Lipp).

