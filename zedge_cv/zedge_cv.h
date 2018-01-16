// (c) 2014 Zedge Inc.
//
//

#ifndef _ZEDGE_CV_H_
#define _ZEDGE_CV_H_

extern "C" void initzcv();

PyObject* initCvFaceDetector(PyObject* self, PyObject* args);
PyObject* freeCvFaceDetector(PyObject* self, PyObject* args);
PyObject* detectFace(PyObject* self, PyObject* args);

#endif      // _ZEDGE_CV_H_

