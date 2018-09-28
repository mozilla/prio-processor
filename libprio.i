/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

%module prio
%{
#include "libprio/include/mprio.h"
%}

%init %{
Prio_init();
atexit(Prio_clear);
%}

// Handle SECStatus.
%typemap(out) SECStatus {
   if ($1 != SECSuccess) {
       PyErr_SetString(PyExc_RuntimeError, "$symname was not succesful.");
       SWIG_fail;
   }
   $result = Py_None;
}


// Typemaps for dealing with the pointer to implementation idiom.
%define OPAQUE_POINTER(T)

%{
void T ## _PyCapsule_clear(PyObject *capsule) {
    T ptr = PyCapsule_GetPointer(capsule, "T");
    T ## _clear(ptr);
}
%}

// Get the pointer from the capsule
%typemap(in) T, const_ ## T {
    $1 = PyCapsule_GetPointer($input, "T");
}

// Create a new capsule for the new pointer
%typemap(out) T {
    $result = PyCapsule_New($1, "T", T ## _PyCapsule_clear);
}

// Create a temporary stack variable for allocating a new opaque pointer
%typemap(in,numinputs=0) T* (T tmp = NULL) {
    $1 = &tmp;
}

// Return the pointer to the newly allocated memory
%typemap(argout) T* {
    $result = SWIG_Python_AppendOutput($result,PyCapsule_New(*$1, "T", T ## _PyCapsule_clear));
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


// The only way to generate a PRGSeed is to call randomize
%typemap(in,numinputs=0) PrioPRGSeed * (PrioPRGSeed tmp) {
    $1 = &tmp;
}

%typemap(argout) PrioPRGSeed * {
    $result = SWIG_Python_AppendOutput($result,PyBytes_FromStringAndSize((const char*)*$1, PRG_SEED_LENGTH));
}

%typemap(in) const PrioPRGSeed {
    $1 = (unsigned char*)PyBytes_AsString($input);
}


// Read constant data into data-structures.
// Note: In Python 3, strings are handled as unicode and need to be encoded as UTF-8
// to work properly when matched against these function signature snippets.
//
%typemap(in) (const unsigned char *, unsigned int) {
    if (!PyBytes_Check($input)) {
        PyErr_SetString(PyExc_ValueError, "Expecting a byte string");
        SWIG_fail;
    }
    $1 = (unsigned char*) PyBytes_AsString($input);
    $2 = (unsigned int) PyBytes_Size($input);
}

%apply (const unsigned char *, unsigned int) {
    (const unsigned char * batch_id, unsigned int batch_id_len),
    (const unsigned char *data, unsigned int dataLen),
    (const unsigned char *hex_data, unsigned int dataLen)
}


// PublicKey_export
%typemap(in,numinputs=0) unsigned char data[ANY] (unsigned char tmp[$1_dim0]) {
    $1 = tmp;
}

%typemap(argout) unsigned char data[ANY] {
    $result = SWIG_Python_AppendOutput(
        $result,
        PyBytes_FromStringAndSize((const char*)$1, $1_dim0)
    );
}


// PrioClient_encode
%typemap(in) const bool * {
    if (!PyBytes_Check($input)) {
        PyErr_SetString(PyExc_ValueError, "Expecting a byte string");
        SWIG_fail;
    }
    $1 = (bool*) PyBytes_AsString($input);
}

%typemap(in,numinputs=0) (unsigned char **, unsigned int *) (unsigned char *data = NULL, unsigned int len = 0) {
    $1 = &data;
    $2 = &len;
}

%typemap(argout) (unsigned char **, unsigned int *) {
    $result = SWIG_Python_AppendOutput(
        $result, PyBytes_FromStringAndSize((const char *)*$1, *$2));
    // Free malloc'ed data from within PrioClient_encode
    if (*$1) free(*$1);
}

%apply (unsigned char **, unsigned int *) {
    (unsigned char **for_server_a, unsigned int *aLen),
    (unsigned char **for_server_b, unsigned int *bLen)
}


// PrioVerifier_set_data
%typemap(in) (unsigned char * data, unsigned int dataLen) {
    if (!PyBytes_Check($input)) {
        PyErr_SetString(PyExc_ValueError, "Expecting a byte string");
        SWIG_fail;
    }
    $1 = (unsigned char*) PyBytes_AsString($input);
    $2 = (unsigned int) PyBytes_Size($input);
}


// PrioTotalShare_final
%typemap(in) (const_PrioConfig, unsigned long *) {
    $1 = PyCapsule_GetPointer($input, "PrioConfig");
    $2 = malloc(sizeof(long)*PrioConfig_numDataFields($1));
}

%typemap(argout) (const_PrioConfig, unsigned long *) {
    $result = SWIG_Python_AppendOutput(
        $result,
        PyByteArray_FromStringAndSize((const char*)$2, sizeof(long)*PrioConfig_numDataFields($1))
    );
    if ($2) free($2);
}

%apply (const_PrioConfig, unsigned long *) {
    (const_PrioConfig cfg, unsigned long *output)
}


// Define wrapper functions for msgpacker_packer due to the dynamically allocated sbuffer.
// Memory shouldn't be moving around so much, but this wrapper function needs to exist in
// order to marshal data due to typemaps not having side-effects

%define MSGPACK_WRITE_WRAPPER(type)
%inline %{
PyObject* type ## _write_wrapper(const_ ## type p) {
    PyObject* data = NULL;
    msgpack_sbuffer sbuf;
    msgpack_packer pk;
    msgpack_sbuffer_init(&sbuf);
    msgpack_packer_init(&pk, &sbuf, msgpack_sbuffer_write);

    SECStatus rv = type ##_write(p, &pk);
    if (rv == SECSuccess) {
        // move the data outside of this wrapper
        data = PyBytes_FromStringAndSize(sbuf.data, sbuf.size);
    }

    // free msgpacker data-structures
    msgpack_sbuffer_destroy(&sbuf);

    return data;
}
%}
%enddef

MSGPACK_WRITE_WRAPPER(PrioPacketVerify1)
MSGPACK_WRITE_WRAPPER(PrioPacketVerify2)
MSGPACK_WRITE_WRAPPER(PrioTotalShare)


// Unfortunately, unpacking also requires some manual work. We take the binary message and
// copy the data into an unpacker

%apply (const unsigned char*, unsigned int) {
    (const unsigned char *data, unsigned int len)
}

%define MSGPACK_READ_WRAPPER(type)
%inline %{
SECStatus type ## _read_wrapper(type p, const unsigned char *data, unsigned int len, const_PrioConfig cfg) {
    SECStatus rv = SECFailure;
    msgpack_unpacker upk;
    bool result = msgpack_unpacker_init(&upk, len+1);
    if (result) {
        memcpy(msgpack_unpacker_buffer(&upk), data, len);
        msgpack_unpacker_buffer_consumed(&upk, len);
        rv = type ## _read(p, &upk, cfg);
    }
    msgpack_unpacker_destroy(&upk);
    return rv;
}
%}
%enddef

MSGPACK_READ_WRAPPER(PrioPacketVerify1)
MSGPACK_READ_WRAPPER(PrioPacketVerify2)
MSGPACK_READ_WRAPPER(PrioTotalShare)


%include "libprio/include/mprio.h"


// Helpful resources:
// * https://stackoverflow.com/a/38191420
// * http://www.swig.org/Doc3.0/SWIGDocumentation.html#Typemaps_nn2
// * https://stackoverflow.com/questions/26567457/swig-wrapping-typedef-struct
// * http://www.swig.org/Doc3.0/SWIGDocumentation.html#Typemaps_multi_argument_typemaps
// * https://github.com/msgpack/msgpack-c/wiki/v1_1_c_overview
