Manual
======

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
   .. autoclass:: Timeline

      .. versionadded:: 1.0.0

      .. automethod:: __init__

      .. automethod:: getTimeBounds

         .. versionadded:: 1.0.0

      .. automethod:: sections

      .. py:method:: getTime()

         .. deprecated:: 1.0.0
            Use :py:meth:`getTimeBounds` instead.


   .. py:class:: ExperimentTimeline

      .. deprecated:: 1.0.0
         Use :py:class:`Timeline` instead.


   .. autoclass:: DataValidator

      .. automethod:: __init__

      .. automethod:: __call__


   .. autoclass:: LickometerLogAnalyzer

      .. automethod:: __init__


   .. autoclass:: PresenceLogAnalyzer


   .. autoclass:: FailureInspector

      .. versionadded:: 1.0.0

      .. automethod:: __init__

      .. automethod:: __call__


   .. py:class:: TestMiceData

      .. deprecated:: 1.0.0
         Use :py:class:`FailureInspector` instead.


   .. autofunction:: getTutorialData


   .. autodata:: __PGP_PUBLIC_KEY__
      :annotation: = < ASCII armored PGP public key >

   .. autoclass:: Citation

      .. automethod:: __init__

      .. automethod:: __str__

      .. automethod:: __unicode__

      .. automethod:: cite

      .. autoattribute:: PAPER

      .. automethod:: referencePaper

      .. autoattribute:: SOFTWARE

      .. automethod:: referenceSoftware

      .. autoattribute:: CITE_PAPER

      .. automethod:: citePaper

      .. autoattribute:: CITE_SOFTWARE

      .. automethod:: citeSoftware


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



