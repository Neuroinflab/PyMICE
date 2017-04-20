/*****************************************************************************\
*                                                                             *
*    PyMICE library                                                           *
*                                                                             *
*    Copyright (C) 2014-2017 Jakub M. Dzik a.k.a. Kowalski (Laboratory of        *
*    Neuroinformatics; Nencki Institute of Experimental Biology)              *
*                                                                             *
*    This software is free software: you can redistribute it and/or modify    *
*    it under the terms of the GNU General Public License as published by     *
*    the Free Software Foundation, either version 3 of the License, or        *
*    (at your option) any later version.                                      *
*                                                                             *
*    This software is distributed in the hope that it will be useful,         *
*    but WITHOUT ANY WARRANTY; without even the implied warranty of           *
*    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            *
*    GNU General Public License for more details.                             *
*                                                                             *
*    You should have received a copy of the GNU General Public License        *
*    along with this software.  If not, see http://www.gnu.org/licenses/.     *
*                                                                             *
\*****************************************************************************/
#include <Python.h>

#ifndef PYMICE_H
  #define PYMICE_H

  #ifdef __cplusplus
    extern "C"
    {
  #endif

  static PyObject * pymice_emptyStringToNone(PyObject *, PyObject *);

    #if PY_MAJOR_VERSION >= 3
      PyMODINIT_FUNC PyInit__C(void);

    #else
      PyMODINIT_FUNC init_C(void);

    #endif

  #ifdef __cplusplus
    }
  #endif

#endif


#ifndef PyMODINIT_FUNC  /* declarations for DLL import/export */
  #define PyMODINIT_FUNC void

#endif

