%module prio
%{
    #include "libprio/include/mprio.h"
%}

// https://stackoverflow.com/questions/26567457/swig-wrapping-typedef-struct
%define OPAQUE_POINTER(type)
%typemap(in) type %{
    $1 = (type)PyLong_AsVoidPtr($input);
%}

%typemap(in,numinputs=0) type* (void* tmp) %{
    $1 = (type*)&tmp;
%}
%typemap(argout) type* %{
    $result = SWIG_Python_AppendOutput($result,PyLong_FromVoidPtr(*$1));
%}
%enddef

OPAQUE_POINTER(PrioConfig)
OPAQUE_POINTER(PrioServer)
OPAQUE_POINTER(PrioVerifier)
OPAQUE_POINTER(PrioPacketVerify1)
OPAQUE_POINTER(PrioPacketVerify2)
OPAQUE_POINTER(PrioTotalShare)
OPAQUE_POINTER(PublicKey)
OPAQUE_POINTER(PrivateKey)

%include "libprio/include/mprio.h"
