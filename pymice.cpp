/*****************************************************************************\
*                                                                             *
*    PyMICE library                                                           *
*                                                                             *
*    Copyright (C) 2014-2015 Jakub M. Kowalski (Laboratory of                 *
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

#include <cstring>
#include <cstdio>
#include <ctime>
#include <cstdlib>
#include <cmath>

#include <algorithm>
#include <limits>
#include <list>
#include <utility>
#include <vector>

#include "pymice.h"

//Py_TPFLAGS_BASETYPE -> type can be subclassed :-D

template <class T> void heapify(T * heap, unsigned int size, unsigned int i)
{
  unsigned int node = i;
  unsigned int minimal = i; // already maximal - working at negative values ;)
  unsigned int left = i << 1;
  while (left <= size)
  {
    // some tolerance for values of same order
    if (heap[left] > heap[minimal] && std::numeric_limits<T>::radix * heap[left] > heap[minimal]) minimal = left;
    unsigned int right = left + 1;
    if (left < size && heap[right] > heap[minimal] && std::numeric_limits<T>::radix * heap[right] > heap[minimal]) minimal = right;
    if (minimal == node) return;
    T tmp = heap[node];
    heap[node] = heap[minimal];
    heap[minimal] = tmp;
    node = minimal;
    left = minimal << 1;
  }
}

template <class T> void buildHeap(T * heap, unsigned int size)
{
  for (unsigned int i = size / 2; i > 0; i--)
  {
    heapify(heap, size, i);
  }
}

template <class T> T sumHeap(T * heap, unsigned int size)
{
  switch (size)
  {
    case 0:
      return 0;

    case 1:
      return heap[0];

    case 2:
      return heap[0] + heap[1];

    default:
      heap--;
      buildHeap(heap, size);
    
      while (size > 2)
      {
        if (heap[2] < heap[3])
        {
          heap[2] += heap[1];
          heapify(heap, size, 2);
        }
        else
        {
          heap[3] += heap[1];
          heapify(heap, size, 3);
        }
        heap[1] = heap[size--];
        heapify(heap, size, 1);
      }
      return heap[1] + heap[2];
  }
}

static PyMethodDef pymice_module_methods[] = {
  {"emptyStringToNone", (PyCFunction) pymice_emptyStringToNone, METH_O, "Replace (in place) empty strings in a list with None."},
  {NULL}  /* Sentinel */  
};

void emptyStringToNone(PyObject * list)
{
  Py_ssize_t n = PyList_GET_SIZE(list);
  for (Py_ssize_t i = 0; i < n; i++)
  {
    PyObject * item = PyList_GET_ITEM(list, i);
    if (item != NULL)
    {
      if (PyString_CheckExact(item) && PyString_GET_SIZE(item) == 0 ||
          PyUnicode_CheckExact(item) && PyUnicode_GET_SIZE(item) == 0)
      {
        Py_DECREF(item);
        Py_INCREF(Py_None);
        PyList_SET_ITEM(list, i, Py_None);
      }
      else if (PyList_CheckExact(item))
      {
        emptyStringToNone(item);
      }
    }
  }
}

static PyObject * pymice_emptyStringToNone(PyObject * self, PyObject * list)
{
  if (list != NULL)
  {
    if (PyList_CheckExact(list))
    {
      emptyStringToNone(list);
      Py_INCREF(list);
      return list;
    }
    else
    {
      PyErr_SetString(PyExc_TypeError,
                      "ERROR @pymice_emptyStringToNone: List must be a list instance (not a subtype).");
    }
  }
  return NULL;
}


#ifndef PyMODINIT_FUNC  /* declarations for DLL import/export */
#define PyMODINIT_FUNC void
#endif
PyMODINIT_FUNC
init_C(void) 
{
  srand(time(NULL));
  PyObject * m;
  
  //penna_PennaType.tp_new = PyType_GenericNew;
  m = Py_InitModule3("_C", pymice_module_methods,
                     "Experimental module for pymice module speedup.");

}

