%module prio
%{
    #include "libprio/include/mprio.h"
%}


// This macro translates the side-effect nature of the pointer to implementation idiom
// into something more functional. See the SO thread for starters:
// https://stackoverflow.com/questions/26567457/swig-wrapping-typedef-struct
//
%define OPAQUE_POINTER(T)
    %typemap(in) T {
        $1 = (T)PyLong_AsVoidPtr($input);
    }

    %typemap(in) const_ ## T {
        $1 = (const_ ## T)PyLong_AsVoidPtr($input);
    }

    %typemap(in) T* (void *tmp) {
        $1 = (T*)&tmp;
    }

    %typemap(out) T {
        $result = PyLong_FromVoidPtr($1);
    }

    %typemap(argout) T* {
        $result = SWIG_Python_AppendOutput($result,PyLong_FromVoidPtr(*$1));
    }
%enddef

OPAQUE_POINTER(PrioConfig)
OPAQUE_POINTER(PrioServer)
OPAQUE_POINTER(PrioVerifier)
OPAQUE_POINTER(PrioPacketVerify1)
OPAQUE_POINTER(PrioPacketVerify2)
OPAQUE_POINTER(PrioTotalShare)
OPAQUE_POINTER(PublicKey)
OPAQUE_POINTER(PrivateKey)

%inline {
    // This is the original definition of the fixed sized buffer for the
    // random seed.
    //
    //      typedef unsigned char PrioPRGSeed[]
    //
    // We treat all new complex types as opaque pointers managed on the heap.
    // By convention, the pointer referencing the original type is called the
    // handle.
    typedef PrioPRGSeed * PrioPRGSeedHandle;

    PrioPRGSeedHandle PrioPRGSeed_new() {
        return (PrioPRGSeedHandle) malloc(sizeof(PrioPRGSeed));
    }

    void PrioPRGSeed_cleanup(PrioPRGSeedHandle seed) {
        free(seed);
    }
}

// The new type shares most syntax with the other typedefs.
OPAQUE_POINTER(PrioPRGSeedHandle)

%typemap(argout) PrioPRGSeed * {
    $result = SWIG_Python_AppendOutput($result,PyLong_FromVoidPtr($1));
}

// Get the original value from the handle when used as an argument
%typemap(in) const PrioPRGSeed {
    $1 = *(PrioPRGSeedHandle)PyLong_AsVoidPtr($input);
}


// Note: In Python 3, strings are handled as unicode and need to be encoded as UTF-8
// to work properly when matched against these function signature snippets.
//
%typemap(in) (const unsigned char * batch_id, unsigned int batch_id_len) {
    if (!PyString_Check($input)) {
        PyErr_SetString(PyExc_ValueError, "Expecting a byte string");
        SWIG_fail;
    }
    $1 = (unsigned char*) PyString_AsString($input);
    $2 = (unsigned int) PyString_Size($input);
}

// The parameters need to be named when using multi-argument typemaps.
// http://www.swig.org/Doc3.0/SWIGDocumentation.html#Typemaps_multi_argument_typemaps
//
%apply (const unsigned char * batch_id, unsigned int batch_id_len) {
    (const unsigned char *data, unsigned int dataLen),
    (const unsigned char *hex_data, unsigned int dataLen)
}

%include "libprio/include/mprio.h"
