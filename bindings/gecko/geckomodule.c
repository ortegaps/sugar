#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

/* include this first, before NO_IMPORT_PYGOBJECT is defined */
#include <pygobject.h>

void pygecko_register_classes (PyObject *d);

extern PyMethodDef pygecko_functions[];

DL_EXPORT(void)
initgecko(void)
{
    PyObject *m, *d;

    init_pygobject ();

    m = Py_InitModule ("gecko", pygecko_functions);
    d = PyModule_GetDict (m);

    pygecko_register_classes (d);

    if (PyErr_Occurred ()) {
        Py_FatalError ("can't initialise module globalkeys");
    }
}
