%module prio
%{
    #include "libprio/include/mprio.h"
%}


// This macro translates the side-effect nature of the pointer to implementation idiom
// into something more functional. See the SO thread for starters:
// https://stackoverflow.com/questions/26567457/swig-wrapping-typedef-struct
//
%define OPAQUE_POINTER(T)
    // Cast the pointer handle (PyLong) into the appropriate input type.
    %typemap(in) T {
        $1 = (T)PyLong_AsVoidPtr($input);
    }

    // Ignore the argument in the wrapper
    %typemap(in,numinputs=0) T* (void* tmp) {
        $1 = (T*)&tmp;
    }

    // Append the modified reference to the result list
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
