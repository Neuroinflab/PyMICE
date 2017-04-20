/*****************************************************************************\
*                                                                             *
*    PyMICE library                                                           *
*                                                                             *
*    Copyright (C) 2014-2017 Jakub M. Dzik a.k.a. Kowalski (Laboratory of     *
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
#include "pymice.h"

static PyMethodDef pymice_module_methods[] = {
  {"emptyStringToNone", (PyCFunction) pymice_emptyStringToNone, METH_O, "Replace (in place) empty strings in a list with None."},
  {NULL, NULL, 0, NULL}  // Sentinel
};

const char * pymice_module_name = "_C";
const char * pymice_module_doc = "Experimental module for pymice module speedup.";

#if PY_MAJOR_VERSION >= 3
static struct PyModuleDef pymice_module_def = {
  PyModuleDef_HEAD_INIT,
  pymice_module_name,
  pymice_module_doc,
  -1, // m_size
  pymice_module_methods,
  NULL, // m_reload
  NULL, // m_traverse
  NULL, // m_clear
  NULL, // m_free
};
#endif

void emptyStringToNone(PyObject * list)
{
  Py_ssize_t n = PyList_GET_SIZE(list);
  for (Py_ssize_t i = 0; i < n; i++)
  {
    PyObject * item = PyList_GET_ITEM(list, i);
//    if (item != NULL)
//    {
      if (
#if PY_MAJOR_VERSION < 3
          (PyString_CheckExact(item) && PyString_GET_SIZE(item) == 0) ||
#endif
          (PyUnicode_CheckExact(item) && PyUnicode_GET_SIZE(item) == 0))
      {
        Py_DECREF(item);
        Py_INCREF(Py_None);
        PyList_SET_ITEM(list, i, Py_None);
      }
      else if (PyList_CheckExact(item))
      {
        emptyStringToNone(item);
      }
//    }
  }
}

static PyObject * pymice_emptyStringToNone(PyObject * self, PyObject * list)
{
//  if (list != NULL)
//  {
    if (PyList_CheckExact(list))
    {
      emptyStringToNone(list);
      Py_INCREF(list);
      return list;
    }

    PyErr_SetString(PyExc_TypeError,
                    "ERROR @pymice_emptyStringToNone: List must be a list instance (not a subtype).");
//  }
  return NULL;
}


#if PY_MAJOR_VERSION >= 3
PyMODINIT_FUNC PyInit__C(void)
{
  PyObject * m = PyModule_Create(&pymice_module_def);
  return m;
}
#else
PyMODINIT_FUNC init_C(void)
{
  Py_InitModule3(pymice_module_name, pymice_module_methods,
                 pymice_module_doc);
}
#endif

