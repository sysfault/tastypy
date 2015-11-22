#include "Python.h"
#include <sched.h>
#include <unistd.h>

PyDoc_STRVAR(_cpuset__doc__, "bind process to cpu\n");

static PyObject *
sched_getcpumask(PyObject *self, PyObject *args)
{
    unsigned long mask;

  unsigned long cur_mask;
  unsigned int len = sizeof(cur_mask);
  pid_t pid;

  if (!PyArg_ParseTuple(args, "i:sched_getcpumask", &pid))
    return NULL;

  if (sched_getaffinity(pid, len,
                        (cpu_set_t *)&cur_mask) < 0) {
    PyErr_SetFromErrno(PyExc_ValueError);
    return NULL;
  }

  return Py_BuildValue("l", cur_mask);
}

static PyObject *
sched_setcpumask(PyObject *self, PyObject *args)
{

  unsigned long new_mask;
  unsigned long cur_mask;
  unsigned int len = sizeof(new_mask);
  pid_t pid;

  if (!PyArg_ParseTuple(args, "il:sched_setcpumask", &pid, &new_mask))
    return NULL;

  if (sched_getaffinity(pid, len,
                        (cpu_set_t *)&cur_mask) < 0) {
    PyErr_SetFromErrno(PyExc_ValueError);
    return NULL;
  }

  if (sched_setaffinity(pid, len, (cpu_set_t *)&new_mask)) {
    PyErr_SetFromErrno(PyExc_ValueError);
    return NULL;
  }

  return Py_BuildValue("l", cur_mask);
}

static PyMethodDef methods[] = {
    {"sched_getcpumask", sched_getcpumask, METH_VARARGS, ""},
    {"sched_setcpumask", sched_setcpumask, METH_VARARGS, ""},
    {NULL, NULL},
};

PyMODINIT_FUNC
init_cpuset(void)
{
    long nrcpus = sysconf(_SC_NPROCESSORS_ONLN);

    PyObject *m = Py_InitModule("_cpuset", methods);
    PyObject *n = Py_BuildValue("i", nrcpus);
    Py_INCREF(n);
    PyObject_SetAttrString(m, "nrcpus", n);
}

